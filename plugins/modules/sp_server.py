#!/usr/bin/env python3
"""
Auto Orchestrate — tiny, batteries included orchestration runner for host discovery + reusable tasks.

Replaces the earlier PLAYBOOK concept with **ORCHESTRATIONs** (index-of-steps) and **tasks** (reusable units).

Highlights
- Structured logging to console and rotating file (DEBUG/INFO/WARNING/ERROR).
- argparse CLI suitable for Jenkins/Ansible/CLI.
- Cross-platform system + OS discovery (Linux/Windows/macOS).  
  * Linux distro detection via `distro` if present, fallback to /etc/os-release.
  * Memory/disk/CPU via stdlib; optional `psutil` for richer stats if available.
- Pluggable **orchestration discovery**: scans a folder for classes named `ORCH_<Name>` with a `run(mode)` method.
- Simple **task runner**: orchestrations can call functions from `tasks/` by dotted path (e.g. `ba_server:is_installed`).
- Shared `context` injected into orchestrations and available for tasks.
- Exit codes and fail-fast behavior for pipelines.

Suggested repo layout
.
├── auto_orchestrate.py   # this file
├── orchestrations/       # ORCH_ classes live here
│   ├── __init__.py
│   └── ba_server.py      # defines class ORCH_BA_SERVER_INSTALL
└── tasks/                # Reusable tasks live here (plain functions)
    ├── __init__.py
    └── ba_server.py      # e.g., is_installed(), install(), upgrade(), uninstall()

Example orchestration (drop under orchestrations/ba_server.py)
    class ORCH_BA_SERVER_INSTALL:
        Orchestration for BA Server lifecycle (install/upgrade/uninstall).
        def __init__(self, context):
            self.ctx = context
            self.log = context["logger"]
            self.run_task = context["run_task"]
        def run(self, mode: str):
            osfam = self.ctx["os"]["family"].lower()
            if mode == "install":
                if self.run_task("ba_server:is_installed"):
                    self.log.info("BA Server already installed; switching to upgrade path")
                    return self.run("upgrade")
                # choose installer by OS
                if osfam == "windows":
                    return self.run_task("ba_server:install_windows")
                elif osfam == "linux":
                    # Optional: branch by distro id (rhel/centos/ubuntu)
                    distro_id = (self.ctx["os"].get("id") or "").lower()
                    if distro_id in {"rhel", "centos", "rocky", "almalinux"}:
                        return self.run_task("ba_server:install_rhel")
                    return self.run_task("ba_server:install_linux_generic")
                else:
                    self.log.error("Unsupported OS for install: %s", osfam)
                    return False
            elif mode == "upgrade":
                return self.run_task("ba_server:upgrade")
            elif mode == "uninstall":
                return self.run_task("ba_server:uninstall")
            else:
                self.log.error("Unknown mode: %s", mode)
                return False

Example tasks (drop under tasks/ba_server.py)
    def is_installed(context):
        Return True if BA Server appears installed on this host.
        log = context["logger"]
        osfam = context["os"]["family"].lower()
        if osfam == "windows":
            # TODO: query registry or installed programs list
            log.debug("(windows) Checking registry for BA Server…")
            return False
        else:
            # e.g., presence of a service or binary
            from shutil import which
            return which("ba-server") is not None

    def install_rhel(context):
        log = context["logger"]
        if context["dry_run"]:
            log.info("[DRY-RUN] Would install BA Server via yum/dnf on RHEL-like systems")
            return True
        # TODO: run package manager commands
        log.info("Installing BA Server on RHEL…")
        return True

    def install_windows(context):
        log = context["logger"]
        log.info("Installing BA Server on Windows…")
        return True

    def install_linux_generic(context):
        context["logger"].info("Installing BA Server on generic Linux…")
        return True

    def upgrade(context):
        context["logger"].info("Upgrading BA Server…")
        return True

    def uninstall(context):
        context["logger"].info("Uninstalling BA Server…")
        return True

Usage
  python3 auto_orchestrate.py --list
  python3 auto_orchestrate.py --name BA_SERVER_INSTALL --mode install
  python3 auto_orchestrate.py --name BA_SERVER_INSTALL --mode upgrade --log-level DEBUG
  python3 auto_orchestrate.py --dry-run --show-context

"""

import argparse
import logging
import logging.handlers
import os
import re

import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'module_utils')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'module_utils')))

import module_utils.sp_server_utils as utils1
import module_utils.sp_server_constants as sp_server_constants

ARTIFACT_PATTERNS = {
    # Example: 1.2.1.0-ORGI-SPOC-WindowsX64.exe
    "windows": r"^\d+\.\d+\.\d+\.\d+-IBM-SPOC-WindowsX64\.exe$",

    # Example: 1.2.1.0-ORGI-SPOC-LinuxX64.bin
    "linux": r"([0-9]+(?:\\.[0-9]+){1,3})-[A-Za-z0-9_-]+-LinuxX64\\.bin$",

    # Example: 1.2.1.0-ORGI-SPOC-RhelX64.bin
    "rhel": r"([0-9]+(?:\\.[0-9]+){1,3})-[A-Za-z0-9_-]+-RhelX64\\.bin$",

    # Example: 1.2.1.0-ORGI-SPOC-AixPPC.bin
    "aix": r"([0-9]+(?:\\.[0-9]+){1,3})-[A-Za-z0-9_-]+-AixPPC\\.bin$",
}


# ---------- Logging setup ----------

def setup_logger(name: str, level: str, log_file: Path) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.handlers.clear()
    logger.propagate = False

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(getattr(logging, level.upper(), logging.INFO))
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    log_file.parent.mkdir(parents=True, exist_ok=True)
    fh = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    logger.debug("Logger initialized (level=%s, file=%s)", level, log_file)
    return logger




# ---------- CLI ----------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Host discovery + orchestration runner",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--name", "-n", help="Name of the ORCH_ to run (without prefix). If omitted, all are run.")
    p.add_argument("--mode", "-m", default="install", choices=["install", "upgrade", "uninstall"], help="Lifecycle mode to pass to the orchestration")
    p.add_argument("--serverpassword", "-sp", default=None, help="provide server password for encryption")
    p.add_argument("--newversion", "-nv", default=None, help="provide new installation version of the artifact", required=False)
    p.add_argument("--componentname", "-cn", help="provide component name for operation", required=True)
    p.add_argument("--list", action="store_true", help="List discovered orchestrations and exit")
    p.add_argument("--fail-fast", action="store_true", help="Stop on first orchestration failure")
    p.add_argument("--dry-run", action="store_true", help="Tell orchestrations/tasks to simulate actions where supported")
    p.add_argument("--show-context", action="store_true", help="Print gathered context as JSON and exit")

    p.add_argument("--log-file", default="/var/log/ibm/sp_server_setup.log", help="Path to log file")
    p.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Console log level")
    return p

# ---------- Define Class ----------
class BA_SERVER_SETUP:
    def __init__(self, context: dict[str, Any]):
        self.ctx = context
        self.log = context["logger"]

        if utils1.fs_exists(path="ansible-vars.json"):
            self.ansible_vars_data = utils1.read_json_file(path="ansible-vars.json")
            self.ctx["ansible_vars_data"] = self.ansible_vars_data
        else:
            raise FileNotFoundError("ansible-vars.json")


    def run(self, mode: str) -> bool:
        os_name = utils1.os_oskey(self.ctx)["os"]
        install_path = utils1.ba_install_dir(self.ctx, os_name)
        target_root = install_path.anchor or "/"

        if not utils1.fs_require_free_mb(self.ctx, min_mb=7500, path=target_root):
            self.log.error("need >=7500 MB free at %s", target_root)
            return False

        if mode == "uninstall":
            return self._uninstall(os_name, install_path)
        if mode == "upgrade":
            install_component_name = self.ctx["args"]["componentname"]
            component_id = sp_server_constants.offerings_metadata[install_component_name]["id"]
            return self._upgrade(os_name, install_path, component_id)
        return self._install(os_name, install_path)

    def _install(self, os_name: str, install_path: Path) -> bool:

        install_component_name = self.ctx["args"]["componentname"]
        component_id = sp_server_constants.offerings_metadata[install_component_name]["id"]
        
        # For Windows, clean up IBM Installation Manager AND DB2 remnants BEFORE checking if installed
        # This prevents conflicts with existing IM/DB2 during installation
        if os_name.lower().strip() == "windows":
            import shutil
            
            # First, query all DB2 services (not just DB2TSM1)
            self.log.info("Detecting and removing all DB2 services...")
            try:
                query_cmd = 'sc query state= all | findstr /i "DB2"'
                result = utils1.exec_run(context=self.ctx, cmd=query_cmd)
                if result.get('rc') == 0 and result.get('stdout'):
                    # Extract service names from output
                    import re
                    service_names = re.findall(r'SERVICE_NAME:\s+(\S+)', result.get('stdout', ''))
                    self.log.info(f"Found DB2 services: {service_names}")
                    
                    # Stop and remove each DB2 service
                    for service in service_names:
                        try:
                            stop_cmd = f'sc stop "{service}"'
                            utils1.exec_run(context=self.ctx, cmd=stop_cmd)
                            delete_cmd = f'sc delete "{service}"'
                            utils1.exec_run(context=self.ctx, cmd=delete_cmd)
                            self.log.info(f"Stopped and removed DB2 service: {service}")
                        except Exception as e:
                            self.log.debug(f"Could not remove service {service}: {e}")
            except Exception as e:
                self.log.debug(f"Could not query DB2 services: {e}")
            
            # Also try to remove known DB2TSM1 services explicitly
            db2_services = ["DB2GOVERNOR_DB2TSM1", "DB2LICD_DB2TSM1", "DB2MGMTSVC_DB2TSM1", "DB2REMOTECMD_DB2TSM1"]
            for service in db2_services:
                try:
                    stop_cmd = f'sc stop "{service}"'
                    utils1.exec_run(context=self.ctx, cmd=stop_cmd)
                    delete_cmd = f'sc delete "{service}"'
                    utils1.exec_run(context=self.ctx, cmd=delete_cmd)
                    self.log.info(f"Stopped and removed DB2 service: {service}")
                except Exception as e:
                    self.log.debug(f"Could not remove service {service}: {e}")
            
            # Remove ALL IBM DB2 registry keys (more aggressive)
            self.log.info("Removing all IBM DB2 registry keys...")
            registry_keys = [
                r'HKLM\SOFTWARE\IBM\DB2',
                r'HKLM\SOFTWARE\WOW6432Node\IBM\DB2',
                r'HKLM\SOFTWARE\IBM\SQLLIB',
                r'HKLM\SOFTWARE\WOW6432Node\IBM\SQLLIB',
                r'HKLM\SYSTEM\CurrentControlSet\Services\DB2'
            ]
            for reg_key in registry_keys:
                try:
                    reg_delete_cmd = f'reg delete "{reg_key}" /f'
                    utils1.exec_run(context=self.ctx, cmd=reg_delete_cmd)
                    self.log.info(f"Removed registry key: {reg_key}")
                except Exception as e:
                    self.log.debug(f"Could not remove registry key {reg_key}: {e}")
            
            # Remove DB2 directories (more comprehensive)
            self.log.info("Removing all DB2 directories...")
            db2_dirs = [
                r"C:\ProgramData\IBM\DB2",
                r"C:\Program Files\Tivoli\TSM\db2",
                r"C:\Program Files\IBM\SQLLIB",
                r"C:\Program Files (x86)\IBM\SQLLIB",
                r"C:\Program Files\IBM\DB2",
                r"C:\Program Files (x86)\IBM\DB2"
            ]
            for db2_dir in db2_dirs:
                if os.path.exists(db2_dir):
                    try:
                        # Use PowerShell for more forceful removal
                        ps_cmd = f'powershell -Command "Remove-Item -Path \'{db2_dir}\' -Recurse -Force -ErrorAction SilentlyContinue"'
                        utils1.exec_run(context=self.ctx, cmd=ps_cmd)
                        self.log.info(f"Removed DB2 directory: {db2_dir}")
                    except Exception as e:
                        self.log.warning(f"Could not remove DB2 directory {db2_dir}: {e}")
            
            # Remove lock file
            imlock_path = r"C:\ProgramData\IBM\Installation Manager\.imlock"
            if os.path.exists(imlock_path):
                try:
                    os.remove(imlock_path)
                    self.log.info(f"Removed existing IBM Installation Manager lock file: {imlock_path}")
                except Exception as e:
                    self.log.warning(f"Could not remove lock file {imlock_path}: {e}")
            
            # Remove IBM Installation Manager directory to force fresh install
            im_dir = r"C:\Program Files\IBM\Installation Manager"
            if os.path.exists(im_dir):
                try:
                    shutil.rmtree(im_dir)
                    self.log.info(f"Removed existing IBM Installation Manager directory: {im_dir}")
                except Exception as e:
                    self.log.warning(f"Could not remove IBM Installation Manager directory {im_dir}: {e}")
            
            # Also clean up shared IBM directory
            ibm_shared_dir = r"C:\Program Files\IBM\IBMIMShared"
            if os.path.exists(ibm_shared_dir):
                try:
                    shutil.rmtree(ibm_shared_dir)
                    self.log.info(f"Removed IBM shared directory: {ibm_shared_dir}")
                except Exception as e:
                    self.log.warning(f"Could not remove IBM shared directory {ibm_shared_dir}: {e}")
        
        _installstatus = utils1.ba_is_installed(self.ctx, oskey=os_name, install_data=sp_server_constants.offerings_metadata[install_component_name])
        # if _installstatus["status"]:
        #     self.log.info(_installstatus["message"])
        #     self.log.info("Proceeding for upgrade activities")
        #     return self._upgrade(os_name, install_path, component_id)
        # else:
        self.log.debug(_installstatus)


        if not (utils1.fs_remove_tree(install_path, context=self.ctx) and utils1.fs_ensure_dir(install_path, context=self.ctx)):
            self.log.error("failed to prepare %s", install_path)
            return False

        artifact_path_data = utils1.find_installer(oskey=os_name, base_dir=str(self._artifacts_base()), version=self.ctx["args"]["newversion"])
        new_version = self.ctx["args"]["newversion"]
    
        if (not artifact_path_data["status"]):
            self.log.error(artifact_path_data["message"])
            return artifact_path_data["status"]
        
        self.log.info(artifact_path_data["message"])
        self.log.info(artifact_path_data["data"]["installerfile"])

        if not self._deploy(os_name, install_path, Path(artifact_path_data["data"]["installerfile"]), new_version):
            self.log.error("install failed; attempting rollback")
            self._rollback(os_name, install_path)
            return False

        # if not self._verify(os_name, install_path):
        #     self.log.error("post-install verify failed; rolling back")
        #     self._rollback(os_name, install_path)
        #     return False

        self.log.info("install complete: %s", new_version)
        return True

    def _upgrade(self, os_name: str, install_path: Path, component_id:str) -> bool:

        install_component_name = self.ctx["args"]["componentname"]
        _installstatus = utils1.ba_is_installed(self.ctx, oskey=os_name, install_data=sp_server_constants.offerings_metadata[install_component_name])
        

        if not _installstatus["status"]:
            self.log.error(_installstatus["message"])
            return False
        
        current_version = None
        if component_id in _installstatus["data"]["installedpackages"]:
            current_version = _installstatus["data"]["installedpackages"][component_id]
        
        if current_version is None:
            self.log.error("SP Server package com.tivoli.dsm.server is not installed")
            return False

        candidate_version = self.ctx["args"]["newversion"]
        artifact_path_data = utils1.find_installer(oskey=os_name, base_dir=str(self._artifacts_base()), version=candidate_version)

        if (not artifact_path_data["status"]):
            self.log.error(artifact_path_data["message"])
            return False


        if not utils1.version_is_newer(current_version, candidate_version):
            self.log.info("already up to date (%s vs %s) - no upgrade required", current_version, candidate_version)
            return True

        # Pass installed packages dict to uninstall so it knows exact versions
        if not self._uninstall(os_name, install_path, installed_packages=_installstatus["data"]["installedpackages"]):
            self.log.error("uninstall failed; aborting upgrade")
            return False

        if not (utils1.fs_remove_tree(install_path, context=self.ctx) and utils1.fs_ensure_dir(install_path, context=self.ctx)):
            self.log.error("failed to re-create %s", install_path)
            return False

        if not self._deploy(os_name, install_path, Path(artifact_path_data["data"]["installerfile"]), candidate_version):
            self.log.error("upgrade install failed; rolling back")
            self._rollback(os_name, install_path)
            return False

        # if not self._verify(os_name, install_path):
        #     self.log.error("post-upgrade verify failed; rolling back")
        #     self._rollback(os_name, install_path)
        #     return False

        self.log.info("upgrade complete: %s -> %s", current_version, candidate_version)
        return True

    def _uninstall(self, os_name: str, install_path: Path, installed_packages: dict | None = None) -> bool:

        """
        get location of IBM Installation manager:
        HKEY_LOCAL_MACHINE\\SOFTWARE\\IBM\\Installation Manager
            location key

        Then call /eclipse/tools/imcl
        then use the uninstall xml file
        with silent parameters and uninstall
        
        Parameters:
            installed_packages: Dict of package_id -> version 
        """

        ibm_im_location_reg = None

        if os_name.lower().strip() == "windows":
            # Try to get from registry first
            ibm_im_location_reg = utils1.winreg_query_value(root="HKLM", subkey="SOFTWARE\\IBM\\Installation Manager", name="location")
            
            # If registry query fails, check common installation paths
            if ibm_im_location_reg is None:
                self.log.warning("Installation Manager location not found in registry, checking common paths...")
                common_paths = [
                    "C:\\Program Files\\IBM\\Installation Manager",
                    "C:\\Program Files (x86)\\IBM\\Installation Manager",
                    "C:\\ProgramData\\IBM\\Installation Manager"
                ]
                for path in common_paths:
                    # Verify that the path contains the eclipse/tools/imcl structure
                    imcl_path = os.path.join(path, "eclipse", "tools", "imcl.exe")
                    if os.path.exists(imcl_path):
                        ibm_im_location_reg = path
                        self.log.info("Found Installation Manager at: {}".format(path))
                        self.log.debug("Verified imcl.exe exists at: {}".format(imcl_path))
                        break
        else:
            ibm_im_location_reg = self.ansible_vars_data.get("install_location_im_linux")  # type: ignore
            if ibm_im_location_reg is None:
                ibm_im_location_reg = self.ansible_vars_data.get("install_location_im", "/opt/IBM/InstallationManager")  # type: ignore

        self.log.info("Identified Installation Manager path:")
        self.log.info(ibm_im_location_reg)
        
        if ibm_im_location_reg is None:
            self.log.error("IBM Installation Manager location not found. Cannot proceed with uninstall.")
            self.log.error("For Windows: Check if IBM Installation Manager is installed at common paths or registry key exists at HKLM\\SOFTWARE\\IBM\\Installation Manager")
            self.log.error("For Linux: Ensure 'install_location_im_linux' is set in ansible variables or Installation Manager is at /opt/IBM/InstallationManager")
            return False
        
        install_manager_imcl = os.path.join(ibm_im_location_reg, "eclipse", "tools", "imcl")
        self.log.info("install manager path considered: " + str(install_manager_imcl))

        artifact_path_data = utils1.find_installer(oskey=os_name, base_dir=str(self._artifacts_base()), version=self.ctx["args"]["newversion"])
        new_version = self.ctx["args"]["newversion"]
    
        if (not artifact_path_data["status"]):
            self.log.error(artifact_path_data["message"])
            return artifact_path_data["status"]

        resp = self._undeploy(os_name=os_name, imcl_loc=install_manager_imcl, artifact_path=Path(artifact_path_data["data"]["installerfile"]), installed_packages=installed_packages)
        return resp

    def _artifacts_base(self) -> Path:
        return Path("./artifacts").resolve()

    def _deploy(self, os_name: str, install_path: Path, artifact_path: Path, version: str) -> bool:
        # install steps here
        
        artifact_path_extracted = os.path.join(artifact_path.parent, "extracted")

        self.log.info("Extracting binary: {}".format(artifact_path))

        if not utils1.extract_binary_package(src=artifact_path, dest=artifact_path_extracted, context=self.ctx):
            self.log.error("Extrat of binary failed")
            return False
        
        self.log.info("Extracted location: {}".format(artifact_path_extracted))

        # set password
        if "password" not in self.ctx["data"]:
            self.log.error("Password not provided. Setup requires password to continue installation")
            return False
        
        self.log.info("Password provided for installation")
        __password__ = self.ctx["data"]["password"]
        install_component_name = self.ctx["args"]["componentname"]

        # generate response xml file
        xmlfile = os.path.join(artifact_path_extracted, "input", "install_response_sample.xml")
        self.log.info("Considering install response xml file at: " + str(xmlfile))

        self.log.debug("XML File before updating with offerings:")
        self.log.debug(utils1.file_read_text(path=xmlfile))

        InputXMLBuilder = utils1.AgentInputXMLBuilder(context=self.ctx)
        # Always use "install" mode for _deploy, even during upgrade
        # (upgrade flow: uninstall old -> install new)
        InputXMLBuilder.generate(
            filename=xmlfile,
            inputdata=self.ansible_vars_data,  # type: ignore
            mode="install"
        )

        # update in put response xml file
        # xmlfile = os.path.join(artifact_path_extracted, "input", "install_response_sample.xml")
        # self.log.info("Considering install response xml file at: " + str(xmlfile))
        # utils1.update_xml_value(file_path=xmlfile, xpath="./variables/variable[@name='ssl.password']", new_value=__password__)

        # utils1.update_xml_value(file_path=xmlfile, xpath="./profile/data[@key='user.SSL_PASSWORD']", new_value=__password__)

        # lic_key_path = "./profile/data[@key='user.license,{}']".format(sp_server_constants.offerings_metadata[install_component_name]["id"])

        # TODO: NOTE: this is new entry to xml file
        # TODO: later enhance to populate this properly

        # lic_key_option_path = "./profile/data[@key='user.license_option,{}']".format(sp_server_constants.offerings_metadata[install_component_name]["id"])
        # print(lic_key_path)
        # utils1.update_xml_value(file_path=xmlfile, xpath=lic_key_path, new_value="tsm")
        # utils1.update_xml_value(file_path=xmlfile, xpath=lic_key_option_path, new_value="A")

        # <data key="user.license,com.tivoli.dsm.server" value="tsm" />
        # oldtext = '<data key="user.license,{id}" value="{val}" />'.format(id=sp_server_constants.offerings_metadata[install_component_name]["id"], val="tsm")
        # newtext = oldtext + "\n" + '<data key="user.license_option,{id}" value="{val}" />'.format(id=sp_server_constants.offerings_metadata[install_component_name]["id"], val="A")
        # utils1.replace_text_in_file(file_path=xmlfile, old_text=oldtext, new_text=newtext)

        self.log.debug("XML File after updating with offerings:")
        self.log.debug(utils1.file_read_text(path=xmlfile))

        # for updating the offerings (or packages to install)
        
        current_data = utils1.ba_is_installed(context=self.ctx, oskey=os_name, install_data=sp_server_constants.offerings_metadata[install_component_name])

        print("current_data: {}".format(current_data))
        final_installdata = {}

        if install_component_name in current_data["data"]["installedpackages"]:
            if utils1.version_is_newer(current=current_data["data"]["installedpackages"][install_component_name], candidate=version):
                final_installdata[install_component_name] = sp_server_constants.offerings_metadata[install_component_name]
            else:
                self.log.warning("Component {} is attempting to install older version. Skipping install/upgrade".format(install_component_name))
                self.log.warning("Current installed version: {}, Candidate install version: {}".format(current_data["data"]["installedpackages"][install_component_name], version))
        else:
            final_installdata[install_component_name] = sp_server_constants.offerings_metadata[install_component_name]

        print("final_installdata: {}".format(final_installdata))

        # for offerings_components in install_metadata:
        #     if offerings_components in current_data["data"]["installedpackages"]:
        #         if utils1.version_is_newer(current=current_data["data"]["installedpackages"][offerings_components], candidate=version):
        #             final_installdata[offerings_components] = install_metadata[offerings_components]
        #         else:
        #             self.log.warning("Component {} is attempting to install older version. Skipping install/upgrade".format(offerings_components))
        #             self.log.warning("Current installed version: {}, Candidate install version: {}".format(current_data["data"]["installedpackages"][offerings_components], version))




        utils1.update_package_offering(xml_filepath=xmlfile, install_data=final_installdata)
        self.log.debug("XML File updated with offerings:")
        self.log.debug(utils1.file_read_text(path=xmlfile))
        
        self.log.info("Starting installation")

        install_script_filename = "install.sh"
        if os_name.lower().strip() == "windows":
            install_script_filename = "install.bat"

        install_script_fullfilepath = os.path.join(artifact_path_extracted, install_script_filename)
        self.log.debug("install_script_fullfilepath: " + str(install_script_fullfilepath))

        # linux line endings for linux playform execution
        # TODO: is this required (or need to fix in build only?)

        if (os_name.lower().strip() == "linux"):
            # cmd = "sudo sed -i 's/\r$//' " + install_script_fullfilepath
            cmd = "dos2unix " + install_script_fullfilepath
            print(":::::")
            print(cmd)
            exec_perm_resp = utils1.exec_run(context=self.ctx, cmd=cmd)

            if (exec_perm_resp["rc"] != 0):
                self.log.error("Error while converting binary to linux line endings")
                self.log.error(exec_perm_resp)
                return False
            else:
                self.log.debug("Converted binary to linux line endings")

        install_cmd = install_script_fullfilepath + " -s -input {respfile} -acceptLicense".format(respfile=xmlfile)
        
        self.log.debug("Install command: {}".format(install_cmd))
        
        resp = utils1.exec_run(context=self.ctx, cmd=install_cmd)
        self.log.debug(resp)

        return resp["rc"] == 0
    
    def _undeploy(self, os_name: str, imcl_loc: str, artifact_path: Path, installed_packages: dict | None = None) -> bool:
        self.log.info("Starting to undeploy/uninstall using imcl at: {}".format(imcl_loc))

        artifact_path_extracted = os.path.join(artifact_path.parent, "extracted")

        # update input response cml file
        # TODO: see if xml file needs a change
        # self.log.info("Considering uninstall response xml file at: " + str(xmlfile))
        # utils1.update_xml_value(file_path=xmlfile, xpath="./variables/variable[@name='ssl.password']", new_value=__password__)

        xmlfile = os.path.join(artifact_path_extracted, "input", "uninstall_response_sample.xml")
        InputXMLBuilder = utils1.AgentInputXMLBuilder(context=self.ctx)
        
        # Pass installed packages to XML builder so it can include versions
        inputdata_with_versions = dict(self.ansible_vars_data)  # type: ignore
        if installed_packages:
            inputdata_with_versions["installed_packages"] = installed_packages  # type: ignore
            
        InputXMLBuilder.generate(
            filename=xmlfile,
            inputdata=inputdata_with_versions,  # type: ignore
            mode="uninstall"  # Always use "uninstall" mode for _undeploy
        )

        uninstall_cmd = imcl_loc + " -s -input " + artifact_path_extracted +"/input/uninstall_response_sample.xml -acceptLicense"
        self.log.debug("Uninstall command: {}".format(uninstall_cmd))

        resp = utils1.exec_run(context=self.ctx, cmd=uninstall_cmd)

        self.log.info("Resp from uninstall execution: {}".format(resp))

        if resp["rc"] == 0:
            # Extract version from uninstall output
            version_info = "Unknown"
            if "stdout" in resp and resp["stdout"]:
                # Parse output like: "Uninstalled com.tivoli.dsm.server_8.2.0.20251121_0706 from..."
                import re
                match = re.search(r'com\.tivoli\.dsm\.server_(\S+)', resp["stdout"])
                if match:
                    version_info = match.group(1)
            
            # Clean up Windows user and group after successful uninstall
            if os_name.lower().strip() == "windows":
                self._cleanup_windows_user_group()
                
            # Print final summary
            self.log.info("UNINSTALL COMPLETED SUCCESSFULLY")
            self.log.info("Uninstalled Version: {}".format(version_info))
            self.log.info("  ✓ SP Server software removed")
            self.log.info("System is now clean and ready for fresh installation")
        
        return resp["rc"] == 0

    def _cleanup_windows_user_group(self) -> None:
        """Clean up Windows user, group, folders, and registry entries created during installation"""
        tsm_user = self.ansible_vars_data.get("tsm_user", "tsminst1")  # type: ignore
        tsm_group = self.ansible_vars_data.get("tsm_group", "tsmusers")  # type: ignore
        
        self.log.info("Starting comprehensive Windows cleanup...")
        
        # 1. Remove user
        self.log.info("Removing Windows user...")
        user_del_cmd = f'net user "{tsm_user}" /delete'
        resp = utils1.exec_run(context=self.ctx, cmd=user_del_cmd)
        if resp["rc"] == 0:
            self.log.info("Removed user: {}".format(tsm_user))
        else:
            self.log.warning("Failed to remove user {} (may not exist): {}".format(tsm_user, resp["stderr"]))
        
        # 2. Remove group
        self.log.info("Removing Windows group...")
        group_del_cmd = f'net localgroup "{tsm_group}" /delete'
        resp = utils1.exec_run(context=self.ctx, cmd=group_del_cmd)
        if resp["rc"] == 0:
            self.log.info("Removed group: {}".format(tsm_group))
        else:
            self.log.warning("Failed to remove group {} (may not exist): {}".format(tsm_group, resp["stderr"]))
        
        # 3. Remove TSM instance and root folders
        self.log.info("Removing TSM folders...")
        folders_to_remove = [
            f"C:\\{tsm_user}",  # e.g., C:\tsminst1
            "C:\\tsmroot",
            "C:\\Program Files\\Tivoli\\TSM\\server",  # Server installation
            "C:\\Program Files\\Tivoli\\TSM\\server_install",  # Server install temp files (CRITICAL for reinstall)
            "C:\\Program Files\\Tivoli\\TSM\\db2",  # DB2 files
            "C:\\Program Files\\IBM\\IBMIMShared"  # IBM IM Shared (if safe to remove)
        ]
        
        for folder in folders_to_remove:
            if utils1.fs_exists(path=folder, context=self.ctx):
                self.log.info("Removing folder: {}".format(folder))
                cmd = f'powershell -Command "Remove-Item -Path \'{folder}\' -Recurse -Force -ErrorAction SilentlyContinue"'
                resp = utils1.exec_run(context=self.ctx, cmd=cmd)
                if resp["rc"] == 0:
                    self.log.info("Removed folder: {}".format(folder))
                else:
                    self.log.warning("Failed to remove folder {}: {}".format(folder, resp["stderr"]))
            else:
                self.log.debug("Folder does not exist, skipping: {}".format(folder))
        
        # 5. Remove Tivoli and DB2 registry entries
        self.log.info("Removing Tivoli and DB2 registry entries...")
        registry_keys = [
            "HKLM\\SOFTWARE\\Tivoli",
            "HKLM\\SOFTWARE\\IBM\\ADSM",
            "HKLM\\SOFTWARE\\IBM\\DB2"  # DB2 registry entries
        ]
        
        for reg_key in registry_keys:
            self.log.info("Removing registry key: {}".format(reg_key))
            cmd = f'reg delete "{reg_key}" /f'
            resp = utils1.exec_run(context=self.ctx, cmd=cmd)
            if resp["rc"] == 0:
                self.log.info("Removed registry key: {}".format(reg_key))
            else:
                self.log.debug("Registry key not found or already deleted: {}".format(reg_key))
        
        self.log.info("Windows cleanup completed")


    def _verify(self, os_name: str, install_path: Path) -> bool:
        install_component_name = self.ctx["args"]["componentname"]
        _installstatus = utils1.ba_is_installed(self.ctx, oskey=os_name, install_data=sp_server_constants.offerings_metadata[install_component_name])
        
        if not _installstatus["status"]:
            return False
        return True

    def _rollback(self, os_name: str, install_path: Path) -> bool:
        prev = self._previous_artifact(os_name)
        if not prev:
            self.log.warning("no previous artifact to roll back to")
            return False
        prev_path, prev_version = prev
        utils1.fs_remove_tree(install_path, context=self.ctx)
        utils1.fs_ensure_dir(install_path, context=self.ctx)
        ok = self._deploy(os_name, install_path, prev_path, prev_version)
        if ok:
            self.log.info("rolled back to %s", prev_version)
        else:
            self.log.error("rollback failed to %s", prev_version)
        return ok

    def _previous_artifact(self, os_name: str) -> Optional[tuple[Path, str]]:
        base = self._artifacts_base() / os_name
        if not base.exists():
            return None
        pat = re.compile(ARTIFACT_PATTERNS.get(os_name, r"ba[-_]?server[-_]?([0-9][\w\.-]+)\..+$"), re.I)
        candidates: list[tuple[Path, str]] = []
        for p in base.iterdir():
            if not p.is_file():
                continue
            m = pat.search(p.name)
            if m is not None and (m.lastindex or 0) >= 1:
                candidates.append((p, m.group(1)))
        if len(candidates) < 2:
            return None
        candidates.sort(key=lambda t: utils1.version_parse(t[1]))
        return candidates[-2]


# ---------- Main ----------

def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    log = setup_logger("sp_server_setup", args.log_level, Path(args.log_file))

    os_info = utils1.get_os_info()
    sys_info = utils1.get_system_info()

    context: Dict[str, Any] = {
        "ts": int(time.time()),
        "args": vars(args),
        "os": os_info,
        "system": sys_info,
        "logger": log,
        "dry_run": bool(args.dry_run),
        "data": {}
    }

    # pre-checks for required details
    if args.mode == "install" or args.mode == "upgrade":
        _pwd = utils1.find_ba_server_password(context=context, args=args)
        if _pwd is None:
            log.error("BA Server Password is required for installation")
            log.error("provide in environment variables as SP_BA_SERVER_PASSWORD=<password>")
            log.error("or provide as CLI arg --serverpassword=<password>")
            sys.exit(-1)
        else:
            context["data"]["password"] = _pwd
            log.debug("Password extracted and used in context payload")
            del _pwd

    baserversetup = BA_SERVER_SETUP(context=context)
    status = baserversetup.run(mode=args.mode)
    if (not status):
        log.error("Execution failed. Exiting now.")
        sys.exit(-1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    raise SystemExit(main())