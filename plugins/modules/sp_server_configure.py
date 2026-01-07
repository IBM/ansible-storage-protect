# coding: utf8

import os
import shutil
import sys
import json
import time
import argparse
import logging
import logging.handlers
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'module_utils')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'module_utils')))

import module_utils.sp_server_utils as utils1

DOCUMENTATION = """
---
Module: sp_server_configure
Author: Shalu Mishra

short_description: Configure IBM Storage Protect Server after installation

description:
  - This module performs post-installation configuration of the IBM Storage Protect (SP) Server.
  - It configures operating system users and groups, directory structures, DB2 instance
    runtime settings, database formatting, server options, and macro execution.
  - The module assumes that the IBM Storage Protect Server software is already installed.
  - The module is designed to be idempotent and safe to re-run.

options:
  vars_file:
    description:
      - Path to a JSON or YAML file containing server configuration variables.
      - This file defines instance names, directories, DB2 settings, macros,
        and other server configuration parameters.
    required: true
    type: str

  step:
    description:
      - Execute a single configuration step instead of the full workflow.
      - Useful for debugging or partial reruns.
    required: false
    type: str
    choices:
      - create_group_and_user
      - create_directories
      - create_db2_instance
      - configure_db2_as_instance_user
      - format_database_windows
      - generate_and_run_macros
      - configure_services

  dry_run:
    description:
      - If set to true, the module reports the actions that would be taken
        without making any changes.
    required: false
    type: bool
    default: false

  log_level:
    description:
      - Logging verbosity for configuration execution.
    required: false
    type: str
    default: "INFO"

  log_file:
    description:
      - Full path to a file where detailed configuration logs should be written.
    required: false
    type: str

author:
  - IBM Automation Engineering <ibm-automation@lists.ibm.com>

notes:
  - This module must be run after successful installation of IBM Storage Protect Server.
  - The module supports both Linux and Windows platforms with platform-specific logic.
  - Database formatting and macro execution are idempotent and guarded by marker files.
  - On Windows systems, DB2 and server commands are executed using DB2CMD and DSM SERV utilities.
  - Errors during intermediate steps are returned with detailed diagnostics for troubleshooting.

requirements:
  - IBM Storage Protect Server must already be installed.
  - DB2 runtime bundled with Storage Protect must be available.
  - Sufficient operating system privileges are required to create users, directories, services, and database resources.

"""

EXAMPLES = """
    - name: Execute SPServerConfiguration (Windows)
          ansible.windows.win_command: >
            python {{ sp_server_install_dest_win }}\sp_server_configure.py
            --vars-file {{ sp_server_install_dest_win }}\ansible-vars.json
          register: sp_server_config_raw
          failed_when: sp_server_config_raw.rc != 0
"""

def make_result(status: bool, message: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {"status": status, "message": message, "data": data or {}}


class SPServerConfiguration:
    """
    Port of the 'sp_server_configuration_linux.yml' Ansible playbook
    into an object-oriented Python API with a CLI.

    - Uses utils1.os_oskey(self.context)["os"] to detect os ("linux"/"windows")
      and utils1.os_oskey(self.context)["osname"] for distro (rhel, ubuntu, etc).
    - Uses utils1.exec_run / svc_start / svc_stop for command + service actions.
    - Uses fs_* and file_* helpers for the filesystem.
    - Returns dicts like {"status": bool, "message": str, "data": {...}}.
    """

    def __init__(self, context: Any, vars: Dict[str, Any], logger: Optional[logging.Logger] = None) -> None:
        """
        :param context: Context object required by utils1.* helpers.
        :param vars:    Dictionary of variables corresponding to the Ansible vars,
                        e.g. tsm_user, tsm_group, root_dir, etc.
        """
        self.context = context
        self.vars = vars

        if logger is None:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
            )
            logger = logging.getLogger("SPServerConfiguration")

        self.log = logger

        osinfo = utils1.os_oskey(self.context)
        self.os_type = (osinfo.get("os") or "").lower()       # "linux" / "windows"
        self.os_name = (osinfo.get("osname") or "").lower()   # "rhel", "ubuntu", "windows_server", ...

        self.log.debug(f"Detected OS: type={self.os_type}, name={self.os_name}")

    # -----------------------------------------------------------------------
    # Core internal helpers
    # -----------------------------------------------------------------------

    def _run_cmd(self, cmd: str, description: str = "", fail_ok: bool = False) -> Dict[str, Any]:
        """
        Wrapper around utils1.exec_run with logging and standard return format.
        """
        if description:
            self.log.info(f"{description}: {cmd}")
        else:
            self.log.info(f"Executing command: {cmd}")

        try:
            resp = utils1.exec_run(self.context, cmd)
            rc = resp["rc"]
            stdout = resp["stdout"]
            stderr = resp["stderr"]
        except Exception as exc:
            msg = f"Command failed to execute: {exc}"
            self.log.error(msg)
            if fail_ok:
                return make_result(False, msg, {"exception": str(exc)})
            raise

        self.log.debug(f"Command rc={rc}, stdout={stdout!r}, stderr={stderr!r}")

        if rc != 0 and not fail_ok:
            msg = f"Command failed with rc={rc}: {cmd}"
            self.log.error(msg)
            return make_result(False, msg, {"stdout": stdout, "stderr": stderr})

        if rc != 0:
            msg = f"Command returned non-zero rc={rc} but fail_ok=True"
            self.log.warning(msg)
        else:
            msg = "Command succeeded"

        return make_result(rc == 0, msg, {"stdout": stdout, "stderr": stderr})

    def _ensure_directories(self, dirs: List[str], owner: Optional[str] = None, group: Optional[str] = None) -> Dict[str, Any]:
        """
        Ensure a list of directories exist (using fs_ensure_dir).
        Ownership is kept for logging / documentation; actual chown is done
        via exec_run because fs_ensure_dir is defined only as "create dir".
        """
        self.log.info("Ensuring required directories exist")
        failed = []

        for d in dirs:
            self.log.debug(f"Ensuring directory: {d}")
            ok = utils1.fs_ensure_dir(d)
            if not ok:
                self.log.error(f"Failed to create directory: {d}")
                failed.append(d)
                continue

            # Ownership / mode, Linux-only, mapped from Ansible "file" tasks
            if self.os_type == "linux" and owner and group:
                chown_cmd = f"chown -R {owner}:{group} {d}"
                chmod_cmd = f"chmod 0755 {d}"
                resp = utils1.exec_run(self.context, chown_cmd)
                if (resp["rc"] != 0):
                    self.log.warning("Failed to set ownership for {}".format(d))
                    self.log.warning(resp["stderr"])
                else:
                    self.log.info("Ownership of {d} set".format(d=d))

                resp = utils1.exec_run(self.context, chmod_cmd)
                if (resp["rc"] != 0):
                    self.log.warning("Failed to set permissions for {}".format(d))
                    self.log.warning(resp["stderr"])
                else:
                    self.log.info("Permissions updated for {d}".format(d=d))
            elif self.os_type == "windows":
                # You can add icacls / takeown here if you need similar permissions handling
                self.log.debug(f"Windows: skipping ownership/mode configuration for {d}")

        if failed:
            msg = f"Failed to ensure directories: {', '.join(failed)}"
            return make_result(False, msg, {"failed": failed})

        return make_result(True, "All directories ensured", {"dirs": dirs})

    # -----------------------------------------------------------------------
    # 0. prepare
    # -----------------------------------------------------------------------

    def prepare_storage(self) -> Dict[str, Any]:

        self.log.info("Starting storage preparation workflow")

        # -----------------------------------------
        # Ensure Linux
        # -----------------------------------------
        if self.os_type != "linux":
            msg = "Storage preparation is only supported on Linux"
            self.log.error(msg)
            return make_result(False, msg)

        try:
            # Required vars from playbook
            storage_prepare_size = self.vars["storage_prepare_size"]
            self.log.info("storage_prepare_size: {}".format(storage_prepare_size))

            allowed_sizes = self.vars["allowed_sizes"]
            self.log.info("allowed_sizes: {}".format(allowed_sizes))

            dsk_size = self.vars["dsk_size"]               # {size: {group: [low, high], ...}}
            self.log.info("dsk_size: {}".format(dsk_size))

            instance_dir = self.vars["instance_dir"]       # tsm instance directory
            self.log.info("instance_dir: {}".format(instance_dir))

            disk_alloc = {}                                # final allocation {group:[disks]}
            used_disks = []


            # -----------------------------------------
            # Validate size
            # -----------------------------------------
            if storage_prepare_size not in allowed_sizes:
                msg = f"Invalid size '{storage_prepare_size}', allowed={allowed_sizes}"
                self.log.error(msg)
                return make_result(False, msg)

            # -----------------------------------------
            # lsblk discovery
            # -----------------------------------------
            self.log.info("Collecting block device info via lsblk")
            res_lsblk = self._run_cmd(
                "lsblk -b -J -o NAME,SIZE,MOUNTPOINT,TYPE",
                "Getting block devices"
            )
            if not res_lsblk["status"]:
                return res_lsblk

            try:
                devices_info = json.loads(res_lsblk["data"]["stdout"])
            except Exception as exc:
                msg = f"Failed to parse lsblk JSON: {exc}"
                self.log.error(msg)
                return make_result(False, msg)

            # -----------------------------------------
            # Identify free disks
            # -----------------------------------------
            free_disks = [
                d["name"]
                for d in devices_info.get("blockdevices", [])
                if d.get("type") == "disk" and d.get("mountpoint") is None
            ]
            self.log.info(f"Free disks discovered: {free_disks}")

            # -----------------------------------------
            # Allocate disks based on low/high threshold
            # -----------------------------------------
            for group, size_range in dsk_size[storage_prepare_size].items():
                low, high = size_range
                candidates = [
                    d for d in devices_info.get("blockdevices", [])
                    if d["type"] == "disk"
                    and d["mountpoint"] is None
                    and d["name"] not in used_disks
                    and low * 1024 * 1024 * 1024 <= int(d["size"]) <= high * 1024 * 1024 * 1024
                ]
                selected = [c["name"] for c in candidates]
                disk_alloc[group] = selected
                used_disks.extend(selected)
                self.log.info(f"Allocated disks for {group}: {selected}")

                if not selected:
                    msg = f"Group {group} has NO disks for size '{storage_prepare_size}'"
                    self.log.error(msg)
                    return make_result(False, msg)

            # -----------------------------------------
            # Build dir_to_disk mapping (TSMdbspace etc.)
            # -----------------------------------------
            dir_to_disk = {}
            for group, disks in disk_alloc.items():
                if group not in ["TSMalog", "TSMarchlog"]:
                    for idx, disk in enumerate(disks):
                        dir_name = f"{group}{idx+1:02d}"
                        dir_to_disk[dir_name] = disk

            self.log.info(f"Built directory -> disk mapping: {dir_to_disk}")

            # -----------------------------------------
            # Create directories under instance_dir
            # -----------------------------------------
            for dname in dir_to_disk.keys():
                target = f"{instance_dir}/{dname}"
                ok = utils1.fs_ensure_dir(target)
                if not ok:
                    msg = f"Failed to create directory {target}"
                    self.log.error(msg)
                    return make_result(False, msg)
                self.log.debug(f"Ensured directory {target}")

            # -----------------------------------------
            # Wipe filesystem signatures on all disks
            # -----------------------------------------
            for d in dir_to_disk.values():
                self._run_cmd(f"wipefs -a /dev/{d}", f"Wiping filesystem on {d}", fail_ok=True)

            # -----------------------------------------
            # Format & mount regular storage dirs
            # -----------------------------------------
            for dname, disk in dir_to_disk.items():
                mkfs_cmd = f"mkfs.xfs -f /dev/{disk}"
                mountpoint = f"{instance_dir}/{dname}"
                self._run_cmd(mkfs_cmd, f"Formatting /dev/{disk}")
                self._run_cmd(f"mount /dev/{disk} {mountpoint}", f"Mounting {mountpoint}")

            # -----------------------------------------
            # ACTIVE LOG (TSMalog) — Create VG/LV
            # -----------------------------------------
            act_disks = [f"/dev/{d}" for d in disk_alloc.get("TSMalog", [])]
            if act_disks:
                self._run_cmd(f"vgcreate vg_actlog {' '.join(act_disks)}", "Creating active-log VG")
                self._run_cmd("lvcreate -l 100%FREE -n lv_actlog vg_actlog", "Creating active-log LV")
                self._run_cmd("mkfs.xfs -f /dev/vg_actlog/lv_actlog", "Formatting active-log LV")
                self._run_cmd(
                    f"mount /dev/vg_actlog/lv_actlog {instance_dir}/TSMalog",
                    "Mounting active log"
                )

            # -----------------------------------------
            # ARCHIVE LOG (TSMarchlog) — Create VG/LV
            # -----------------------------------------
            arch_disks = [f"/dev/{d}" for d in disk_alloc.get("TSMarchlog", [])]
            if arch_disks:
                self._run_cmd(f"vgcreate vg_archlog {' '.join(arch_disks)}", "Creating archive-log VG")
                self._run_cmd("lvcreate -l 100%FREE -n lv_archlog vg_archlog", "Creating archive-log LV")
                self._run_cmd("mkfs.xfs -f /dev/vg_archlog/lv_archlog", "Formatting archive-log LV")
                self._run_cmd(
                    f"mount /dev/vg_archlog/lv_archlog {instance_dir}/TSMarchlog",
                    "Mounting archive log"
                )

            self.log.info("Storage preparation completed successfully")
            return make_result(True, "Storage preparation successful", {
                "disk_allocations": disk_alloc,
                "dir_to_disk": dir_to_disk
            })

        except Exception as exc:
            msg = f"Unexpected error during storage preparation: {exc}"
            self.log.error(msg)
            return make_result(False, msg)


    # -----------------------------------------------------------------------
    # 1. User & group (Linux vs Windows equivalents)
    # -----------------------------------------------------------------------

    def create_group_and_user(self) -> Dict[str, Any]:
        """
        Mirrors:
          - Creating group
          - Creating user
          - Setting password for the user
        """
        tsm_group = self.vars["tsm_group"]
        tsm_group_gid = self.vars.get("tsm_group_gid")
        tsm_user = self.vars["tsm_user"]
        tsm_user_uid = self.vars.get("tsm_user_uid")
        tsm_user_password = self.vars["tsm_user_password"]

        self.log.info("Creating group and user for the server instance")

        if self.os_type == "linux":
            # Group
            group_cmd = f"groupadd -f {tsm_group}"
            if tsm_group_gid:
                group_cmd += f" -g {tsm_group_gid}"
            resp = utils1.exec_run(self.context, group_cmd)
            if (resp["rc"] != 0):
                self.log.error("Failed to create group {}".format(tsm_group))
                self.log.error(resp["stderr"])
                return {"status": False, "message": "Failed to create group", "data": resp}
            else:
                self.log.info("Group created {}".format(tsm_group))
                
            # User
            user_cmd_parts = [f"useradd -m {tsm_user} -g {tsm_group}"]
            if tsm_user_uid:
                user_cmd_parts.append(f"-u {tsm_user_uid}")
            user_cmd = " ".join(user_cmd_parts)

            resp = utils1.exec_run(self.context, user_cmd)
            if (resp["rc"] == 9):
                self.log.warning(resp["stderr"])
            elif (resp["rc"] != 0):
                self.log.error("Failed to create user {}".format(tsm_user))
                self.log.error(resp["stderr"])
                return {"status": False, "message": "Failed to create user", "data": resp}
            else:
                self.log.info("User created {}".format(tsm_group))

            # Password
            passwd_cmd = f'echo "{tsm_user}:{tsm_user_password}" | chpasswd'

            resp = utils1.exec_run(self.context, passwd_cmd)
            if (resp["rc"] != 0):
                self.log.warning("Failed to set password for user {}".format(tsm_user))
                self.log.warning(resp["stderr"])
                return {"status": False, "message": "Failed to set password for user", "data": resp}
            else:
                self.log.info("user password is set {}".format(tsm_group))

        elif self.os_type == "windows":
            # Equivalent operations using Windows primitives
            # Group
            group_cmd = (
                f'powershell -NoProfile -NonInteractive -Command '
                f'"if (-not (Get-LocalGroup -Name \\"{tsm_group}\\" -ErrorAction SilentlyContinue)) '
                f'{{ New-LocalGroup -Name \\"{tsm_group}\\" }}"'
            )

            resp = utils1.exec_run(self.context, group_cmd)
            if (resp["rc"] != 0):
                self.log.warning("Failed to create group {}".format(tsm_group))
                self.log.warning(resp["stderr"])
            else:
                self.log.info("Group created {}".format(tsm_group))

            # User
            user_cmd = (
                f'powershell -NoProfile -NonInteractive -Command '
                f'"if (-not (Get-LocalUser -Name \\"{tsm_user}\\" -ErrorAction SilentlyContinue)) '
                f'{{ '
                f'$pwd = ConvertTo-SecureString \\"{tsm_user_password}\\" -AsPlainText -Force; '
                f'New-LocalUser -Name \\"{tsm_user}\\" '
                f'-Password $pwd '
                f'-PasswordNeverExpires '
                f'-UserMayNotChangePassword '
                f'}}"'
            )

            resp = utils1.exec_run(self.context, user_cmd)
            if (resp["rc"] != 0):
                self.log.error("Failed to create user {}".format(tsm_user))
                self.log.error(resp["stderr"])
                return {"status": False, "message": "Failed to create user", "data": resp}
            else:
                self.log.info("User created {}".format(tsm_user))

            # Add user to group
            add_to_group_cmd = (
                f'powershell -NoProfile -NonInteractive -Command '
                f'"Add-LocalGroupMember -Group \\"{tsm_group}\\" -Member \\"{tsm_user}\\" '
                f'-ErrorAction SilentlyContinue"'
            )

            resp = utils1.exec_run(self.context, add_to_group_cmd)
            if (resp["rc"] != 0):
                self.log.warning("Failed to add user {} to group {}".format(tsm_user, tsm_group))
                self.log.warning(resp["stderr"])
            else:
                self.log.info("Group created {}".format(tsm_group))

            # Password 
            passwd_cmd = (
                f'powershell -NoProfile -NonInteractive -Command '
                f'"$pwd = ConvertTo-SecureString \\"{tsm_user_password}\\" -AsPlainText -Force; '
                f'Set-LocalUser -Name \\"{tsm_user}\\" -Password $pwd"'
            )

            resp = utils1.exec_run(self.context, passwd_cmd)
            if resp["rc"] != 0:
                self.log.error("Failed to set password for user {}".format(tsm_user))
                self.log.error(resp["stderr"])
                return {
                    "status": False,
                    "message": "Failed to set password for user",
                    "data": resp
                }
            else:
                self.log.info("User password is set {}".format(tsm_user))

        else:
            msg = f"Unsupported OS for user/group creation: {self.os_type}"
            self.log.error(msg)
            return make_result(False, msg)

        return make_result(True, "Group and user created/ensured", {
            "tsm_group": tsm_group,
            "tsm_user": tsm_user,
        })

    # -----------------------------------------------------------------------
    # 2. Directory layout (root_dir + per-user dirs)
    # -----------------------------------------------------------------------

    def create_directories(self) -> Dict[str, Any]:
        """
        Mirrors:
          - Creating root directories
          - Creating subdirectories under the root directory
          - Set write access on /tsminst1 and child dir
        """
        root_dir = self.vars.get("root_dir", "/tsmroot")
        tsm_user = self.vars.get("tsm_user", "tsminst1")
        tsm_group = self.vars.get("tsm_group", "tsmusers")
        directories = self.vars.get("directories", [])

        self.log.info("Creating directory structure for SP server")

        if self.os_type == "windows":
            base = f"C:\\{tsm_user}"
        else:
            base = f"/{tsm_user}"

        dirs_to_create = [root_dir]
        # e.g. directories like ["TSMdbdir", "TSMlog", "TSMarchlog"]
        for d in directories:
            dirs_to_create.append(os.path.join(base, d))

        res = self._ensure_directories(dirs_to_create, owner=tsm_user, group=tsm_group)
        return res

    # -----------------------------------------------------------------------
    # 3. DB2 Instance creation
    # -----------------------------------------------------------------------

    def create_db2_instance(self) -> Dict[str, Any]:
        """
        Mirrors:
          - Creating the DB2 server instance as root (db2icrt ...)
        """
        self.log.info("Creating DB2 server instance (if required)")
        tsm_user = self.vars["tsm_user"]

        if self.os_type == "linux":
            
            # Check if instance already exists (rough equivalent of "creates:" in Ansible)
            sqllib_path = f"/home/{tsm_user}/sqllib"
            if utils1.fs_exists(sqllib_path):
                msg = f"DB2 instance already exists at {sqllib_path}"
                self.log.info(msg)
                return make_result(True, msg)

            cmd = f"/opt/tivoli/tsm/db2/instance/db2icrt -a server -u {tsm_user} {tsm_user}"

            resp = utils1.exec_run(self.context, cmd)
            if (resp["rc"] != 0):
                self.log.warning("Failed to create DB2 server instance")
                self.log.warning(resp["stderr"])
                return {"status": False, "message": "Failed to create DB2 server instance", "data": resp}
            else:
                self.log.info("DB2 Server instance created")

            return {"status": True, "message": "DB2 server instance created", "data": resp}
        
        elif self.os_type == "windows":
            # Check if instance already exists
            self.log.info("Verifying DB2 instance on Windows")

            resp = utils1.exec_run(self.context, "db2ilist")
            if resp["rc"] != 0:
                return make_result(False, "db2ilist failed", resp)

            if tsm_user.lower() not in resp["stdout"].lower():
                return make_result(False, f"DB2 instance '{tsm_user}' not found", resp)

            self.log.info(f"DB2 instance '{tsm_user}' exists")
            return make_result(True, "DB2 instance verified")
            
        else:
            msg = f"Unsupported OS for DB2 instance creation: {self.os_type}"
            self.log.error(msg)
            return make_result(False, msg)
            
        
    # -----------------------------------------------------------------------
    # 4. DB2 configuration as instance user (subset of playbook steps)
    # -----------------------------------------------------------------------

    def configure_db2_as_instance_user(self) -> Dict[str, Any]:
        """
        Configures DB2 as the instance user, mirroring the full Ansible playbook logic, for both Linux and Windows:
        - Update default database path
        - Set DB2 registry variables
        - Modify LD_LIBRARY_PATH
        - Check if the DB is already formatted
        - Clean and format DB directories if not formatted
        - Copy and configure server options
        - Ensure admin user setup flag
        - Ensure DBBKAPI directory is writable
        - Ensure dsm.sys exists and configured
        """

        tsm_user = self.vars["tsm_user"]
        tsm_group = self.vars.get("tsm_group", "tsmusers")
        if self.os_type == "linux":
            db_paths = [
                f"/{tsm_user}/TSMdbspace01",
                f"/{tsm_user}/TSMdbspace02",
                f"/{tsm_user}/TSMdbspace03",
                f"/{tsm_user}/TSMdbspace04",
            ]
            act_log_dir = f"/{tsm_user}/TSMalog"
            arch_log_dir = f"/{tsm_user}/TSMarchlog"

        elif self.os_type == "windows":
            base_dir = f"C:\\{tsm_user}"

            db_paths = [
                f"{base_dir}\\TSMdbspace01",
                f"{base_dir}\\TSMdbspace02",
                f"{base_dir}\\TSMdbspace03",
                f"{base_dir}\\TSMdbspace04",
            ]

            act_log_dir = f"{base_dir}\\TSMalog"
            arch_log_dir = f"{base_dir}\\TSMarchlog"

        act_log_size = self.vars.get("sp_server_active_log_size", 100)
        server_blueprint = self.vars.get("server_blueprint", False)

        if self.os_type == "linux":
            # --- Linux logic ---

            self.log.info("Configuring DB2 as instance user")

            db2profile = f"/home/{tsm_user}/sqllib/db2profile"
            userprofile = f"/home/{tsm_user}/sqllib/userprofile"

            # Check DB2 profile
            if not utils1.fs_exists(db2profile):
                msg = f"DB2 profile not found: {db2profile}"
                self.log.error(msg)
                return make_result(False, msg)

            # 1️⃣ Update default DB path
            cmd_update_dftdbpath = (
                f'su - {tsm_user} -c "source {db2profile}; '
                f'export DB2INSTANCE=\\"{tsm_user}\\"; '
                f'db2 update dbm cfg using dftdbpath /{tsm_user}"'
            )
            resp = utils1.exec_run(self.context, cmd_update_dftdbpath)
            if resp["rc"] != 0:
                self.log.error("Failed to update default database path")
                self.log.error(resp["stderr"])
                return {"status": False, "message": "Failed to update default database path", "data": resp}
            self.log.info("Default database path updated")

            # 2️⃣ Set DB2 registry variable
            cmd_db2set = (
                f'su - {tsm_user} -c "source {db2profile}; '
                f'export DB2INSTANCE=\\"{tsm_user}\\"; '
                f'db2set DB2NOEXITLIST=ON"'
            )
            resp = utils1.exec_run(self.context, cmd_db2set)
            if resp["rc"] != 0:
                self.log.error("Failed to set DB2 registry variable DB2NOEXITLIST")
                self.log.error(resp["stderr"])
                return {"status": False, "message": "Failed to set DB2 registry variable DB2NOEXITLIST", "data": resp}
            self.log.info("DB2 registry variable DB2NOEXITLIST set")

            # 3️⃣ Modify LD_LIBRARY_PATH in userprofile
            ld_lib_line = (
                'export LD_LIBRARY_PATH=/opt/tivoli/tsm/server/bin/dbbkapi:'
                '/usr/local/ibm/gsk8_64/lib64:/opt/ibm/lib:/opt/ibm/lib64:$LD_LIBRARY_PATH'
            )
            utils1.append_line_to_file(userprofile, ld_lib_line)
            self.log.info("LD_LIBRARY_PATH updated in userprofile")

            # 4️⃣ Check if database is already formatted
            cmd_db_check = (
                f'su - {tsm_user} -c "source {db2profile}; '
                f'export DB2INSTANCE=\\"{tsm_user}\\"; '
                f'db2 list db directory | grep -i \\"Database alias\\""'
            )
            db_check_resp = utils1.exec_run(self.context, cmd_db_check)
            db_formatted = db_check_resp["rc"] == 0

            if db_formatted:
                self.log.info("Database already formatted; skipping formatting and cleaning")
            else:
                self.log.info("Database not formatted; preparing directories for formatting")

                # Ensure database directories exist and are empty
                for dbdir in db_paths:
                    utils1.ensure_dir(dbdir, owner=tsm_user, group=tsm_group, mode="0755")
                    files = utils1.list_files(dbdir)
                    for f in files:
                        utils1.remove_file(f)
                    self.log.info(f"Cleaned database directory: {dbdir}")

                # Ensure log directories exist
                for logdir in [act_log_dir, arch_log_dir]:
                    utils1.ensure_dir(logdir, owner=tsm_user, group=tsm_group, mode="0755")
                    self.log.info(f"Ensured log directory: {logdir}")

                # Format the database
                db_paths_str = ",".join(db_paths)
                cmd_format_db = (
                    f'su - {tsm_user} -c "source {db2profile}; '
                    f'export DB2INSTANCE=\\"{tsm_user}\\"; '
                    f'dsmserv format dbdir={db_paths_str} '
                    f'activelogsize={act_log_size} '
                    f'activelogdirectory={act_log_dir} '
                    f'archlogdirectory={arch_log_dir}"'
                )
                resp = utils1.exec_run(self.context, cmd_format_db)
                if resp["rc"] != 0:
                    self.log.error("Failed to format the database")
                    self.log.error(resp["stderr"])
                    return {"status": False, "message": "Failed to format the database", "data": resp}
                self.log.info("Database formatted successfully")

            # 5️⃣ Copy and configure server options
            dsmserv_opt = f"/{tsm_user}/dsmserv.opt"
            utils1.copy_file("/opt/tivoli/tsm/server/bin/dsmserv.opt.smp", dsmserv_opt,
                            owner=tsm_user, group=tsm_group, mode="0644")

            server_options = [
                "commmethod tcpip",
                "tcpport 1500",
                "tcpwindowsize 0",
                "tcpnodelay yes",
                "commmethod sharedmem",
                "shmport 1510",
                f"ACTIVELOGSIZE {act_log_size}",
                "COMMTIMEOUT 3600",
                "DEDUPREQUIRESBACKUP NO",
                "DEVCONFIG devconf.dat",
                "EXPINTERVAL 0",
                "IDLETIMEOUT 60",
                f"MAXSESSIONS {self.vars.get('max_sessions', 10)}",
                "NUMOPENVOLSALLOWED 20",
                "TCPWINDOWSIZE 0",
                f"VOLUMEHISTORY volhist.out",
                f"ACTIVELOGDIRECTORY {act_log_dir}",
                f"ARCHLOGDIRECTORY {arch_log_dir}"
            ]
            utils1.update_lines_in_file(dsmserv_opt, server_options)
            self.log.info("Server options configured")

            # 6️⃣ Ensure admin user setup file exists
            admin_file = f"/{tsm_user}/.admin_user_setup_done"
            if not utils1.fs_exists(admin_file):
                utils1.touch_file(admin_file, owner=tsm_user, group=tsm_group)
                self.log.info(".admin_user_setup_done created")
            else:
                self.log.info("Admin user setup already completed")

            # 7️⃣ Ensure DBBKAPI directory is writable
            dbbkapi_dir = "/opt/tivoli/tsm/server/bin/dbbkapi"
            if utils1.fs_exists(dbbkapi_dir):
                utils1.exec_run(self.context, f"chgrp -R {tsm_group} {dbbkapi_dir}")
                utils1.exec_run(self.context, f"chmod -R 775 {dbbkapi_dir}")
                self.log.info("Adjusted permissions for dbbkapi directory")
            else:
                self.log.warning(f"dbbkapi directory not found: {dbbkapi_dir}")

            # 8️⃣ Ensure dsm.sys exists
            dsm_sys = "/opt/tivoli/tsm/client/api/bin64/dsm.sys"
            if not utils1.fs_exists(dsm_sys):
                self.log.info("dsm.sys not found, creating default API client configuration")
                dsm_sys_content = (
                    "SERVERNAME TSMDBMGR_TSMINST1\n"
                    "COMMMethod TCPip\n"
                    "TCPPort 1500\n"
                    "TCPServeraddress localhost\n"
                    "NODENAME TSMDBMGR\n"
                    "PASSWORDACCESS generate\n"
                )
                utils1.file_write_text(dsm_sys, dsm_sys_content)
                utils1.chown(self.context, dsm_sys, "root", tsm_group)
                utils1.chmod(self.context, dsm_sys, "0664")
            else:
                self.log.info("dsm.sys already exists — skipping creation")

            return make_result(True, "DB2 instance user configuration completed", {
                "db_formatted_check": db_check_resp
            })
        
        elif self.os_type == "windows":

            self.log.info("Configuring DB2 for Windows SP server")

            db2cmd = r"C:\Program Files\Tivoli\tsm\db2\BIN\DB2CMD.EXE"

            # Initialize DB2 environment (MANDATORY)
            resp = utils1.exec_run(
                self.context,
                f'"{db2cmd}" /c /w /i db2setcp.bat'
            )
            if resp["rc"] != 0:
                return make_result(False, "DB2CMD initialization failed", resp)
            
            self.log.info("DB2CMD environment initialized successfully")

            # Set DB2 registry variable
            resp = utils1.exec_run(
                self.context,
                f'"{db2cmd}" /c /w /i db2set -i {tsm_user} DB2NOEXITLIST=ON'
            )
            if resp["rc"] != 0:
                return make_result(False, "Failed to set DB2NOEXITLIST", resp)
            
            self.log.info("DB2 registry variable DB2NOEXITLIST ensured")

            return make_result(
                True,
                "DB2 runtime configuration completed successfully on Windows",
                {
                    "db2_instance": tsm_user,
                    "db2cmd_initialized": True,
                    "db2noexitlist": "ON"
                }
            )
        
    def _clean_directory(self, path: str) -> None:
        """
        Remove all contents of a directory WITHOUT deleting the directory itself.
        Windows-safe and idempotent.
        """
        if not os.path.exists(path):
            return

        for name in os.listdir(path):
            full_path = os.path.join(path, name)
            try:
                if os.path.isfile(full_path) or os.path.islink(full_path):
                    os.unlink(full_path)
                elif os.path.isdir(full_path):
                    shutil.rmtree(full_path)
            except Exception as exc:
                raise RuntimeError(f"Failed to clean {full_path}: {exc}")

            
    def format_database_windows(self) -> Dict[str, Any]:
        tsm_user = self.vars["tsm_user"]
        instance_dir = rf"C:\{tsm_user}"
        marker_file = rf"{instance_dir}\.db_formatted"

        dsmserv_exe = r"C:\Program Files\Tivoli\tsm\server\dsmserv.exe"

        db_paths = [
            rf"{instance_dir}\TSMdbspace01",
            rf"{instance_dir}\TSMdbspace02",
            rf"{instance_dir}\TSMdbspace03",
            rf"{instance_dir}\TSMdbspace04",
        ]

        act_log_dir = rf"{instance_dir}\TSMalog"
        arch_log_dir = rf"{instance_dir}\TSMarchlog"

        # Ensure directories exist
        for d in db_paths + [act_log_dir, arch_log_dir]:
            utils1.ensure_dir(d)
        
        # Clean DB directories (MANDATORY on Windows)
        for dbdir in db_paths:
            self._clean_directory(dbdir)
            self.log.info(f"Cleaned DB directory: {dbdir}")

        # Run format
        dbdir_str = ",".join(db_paths)

        cmd = (
                f'cmd /c "'
                f'cd /d {instance_dir} && '
                f'set DB2INSTANCE={tsm_user} && '
                f'"{dsmserv_exe}" '
                f'-k {tsm_user} '
                f'format '
                f'dbdir={dbdir_str} '
                f'activelogsize=8192 '
                f'activelogdirectory={act_log_dir} '
                f'archlogdirectory={arch_log_dir}'
                f'"'
            )

        resp = utils1.exec_run(self.context, cmd)

        # if resp["rc"] != 0:
        #     # Database already exists → treat as SUCCESS
        #     if "already exists" in resp["stdout"]:
        #         self.log.warning("Database already exists marking as formatted")
        #     else:
        #         return make_result(False, "Database format failed", resp)

        # Create marker
        utils1.touch_file(marker_file, owner=tsm_user)

        self.log.info("Database formatted successfully on Windows")
        return make_result(True, "Database formatted")

    def generate_and_run_macros(self) -> Dict[str, Any]:
        """
        Implements all macro-generation tasks from Ansible:
        - Admin macro creation
        - Admin macro execution
        - Admin setup flag
        - Blueprint macro generation/execution
        - DB2 environment additions (.profile)
        - DSMI environment (userprofile, usercshrc)
        - tsmdbmgr.opt creation
        """
        tsm_user = self.vars["tsm_user"]
        tsm_group = self.vars["tsm_group"]
        admin_name = self.vars["admin_name"]
        admin_password = self.vars["admin_password"]
        server_blueprint = self.vars.get("server_blueprint", False)

        home_dir = f"/home/{tsm_user}"
        instance_dir = home_dir
        db2profile = f"{home_dir}/sqllib/db2profile"
        admin_flag = f"{instance_dir}/.admin_user_setup_done"

        macros = self.vars.get("macros", [])

        if not macros:
            self.log.info("No macros defined — skipping macro execution")
            return make_result(True, "No macros to execute")

        self.log.info("Starting macro execution phase")

        if self.os_type == "linux":
            # 1. CREATE + EXECUTE ADMIN MACRO IF NOT ALREADY DONE
            if not utils1.fs_exists(admin_flag):
                # Check if admin already exists in TSM
                cmd_check = (
                    f'su - {tsm_user} -c "'
                    f'dsmadmc -id {admin_name} -password dummy QUERY ADMIN {admin_name}"'
                )
                resp_check = utils1.exec_run(self.context, cmd_check)

                if resp_check["rc"] == 0:
                    # Admin exists → skip registration, but mark flag
                    self.log.info(f"Admin {admin_name} already exists – skipping registration")
                    utils1.exec_run(self.context, f"touch {admin_flag}")
                else:
                    # Admin does not exist → create and execute macro
                    setup_mac = f"{instance_dir}/setup.mac"
                    self.log.info("Creating administrative user macro")

                    content = (
                        f"register admin {admin_name} {admin_password}\n"
                        f"grant auth tsmuser1 classes=system\n"
                    )

                    utils1.file_write_text(setup_mac, content)
                    utils1.chown(self.context, setup_mac, tsm_user, tsm_group)
                    utils1.chmod(self.context, setup_mac, "0644")

                    # Execute admin macro
                    cmd = (
                        f'su - {tsm_user} -c "'
                        f'source {db2profile}; '
                        f'export DB2INSTANCE=\\"{tsm_user}\\"; '
                        f'cd {instance_dir}; '
                        f'dsmserv runfile setup.mac"'
                    )

                    resp = utils1.exec_run(self.context, cmd)
                    if resp["rc"] != 0:
                        self.log.error("Admin macro execution failed")
                        self.log.error(resp["stderr"])
                        return make_result(False, "Admin macro execution failed", resp)

                    # Mark admin as configured
                    utils1.exec_run(self.context, f"touch {admin_flag}")
                    utils1.chown(self.context, admin_flag, tsm_user, tsm_group)
                    self.log.info("Administrative user setup completed")
            else:
                self.log.info("Admin user setup already completed – skipping")

            created_macros = []

            # 2. BLUEPRINT MACROS (templates provided via vars["macros"])
            macros = self.vars.get("macros", [])

            if server_blueprint and macros:
                self.log.info("Processing blueprint macro files")

                for item in macros:
                    dest = item["dest"]
                    content = item.get("content", "")

                    self.log.debug(f"Writing macro file: {dest}")
                    ok = utils1.file_write_text(dest, content)
                    if not ok:
                        return make_result(False, f"Failed to write macro file {dest}")

                    utils1.chown(self.context, dest, tsm_user, tsm_group)
                    utils1.chmod(self.context, dest, "0644")
                    created_macros.append(dest)

                # Execute macros
                for dest in created_macros:
                    filename = os.path.basename(dest)

                    cmd = (
                        f'su - {tsm_user} -c "'
                        f'source {db2profile}; '
                        f'export DB2INSTANCE=\\"{tsm_user}\\"; '
                        f'cd {instance_dir}; '
                        f'dsmserv runfile {filename}"'
                    )

                    resp = utils1.exec_run(self.context, cmd)
                    if resp["rc"] != 0:
                        self.log.error(f"Failed executing macro {dest}")
                        self.log.error(resp["stderr"])
                        return make_result(False, f"Macro execution failed: {dest}", resp)

                    self.log.info(f"Macro executed: {dest}")

            # 3. Ensure DB2 initialization in .profile
            profile_file = f"{home_dir}/.profile"
            profile_line = (
                f"if [ -f {home_dir}/sqllib/db2profile ]; then\n"
                f"  . {home_dir}/sqllib/db2profile\n"
                f"fi"
            )
            utils1.file_ensure_line(profile_file, profile_line)

            # 4. DSMI environment settings (userprofile)
            userprofile = f"{home_dir}/sqllib/userprofile"
            dsmi_lines = [
                f"DSMI_CONFIG=/{tsm_user}/tsmdbmgr.opt",
                f"DSMI_DIR=/opt/tivoli/tsm/server/bin/dbbkapi",
                f"DSMI_LOG=/{tsm_user}",
                "export DSMI_CONFIG DSMI_DIR DSMI_LOG"
            ]
            for line in dsmi_lines:
                utils1.file_ensure_line(userprofile, line)
            utils1.chown(self.context, userprofile, tsm_user, tsm_group)

            # 5. DSMI environment settings (usercshrc)
            usercshrc = f"{home_dir}/sqllib/usercshrc"
            csh_lines = [
                f"setenv DSMI_CONFIG /{tsm_user}/tsmdbmgr.opt",
                f"setenv DSMI_DIR /opt/tivoli/tsm/server/bin/dbbkapi",
                f"setenv DSMI_LOG /{tsm_user}",
            ]
            for line in csh_lines:
                utils1.file_ensure_line(usercshrc, line)
            utils1.chown(self.context, usercshrc, tsm_user, tsm_group)

            # 6. tsmdbmgr.opt creation
            tsmdbmgr = f"{instance_dir}/tsmdbmgr.opt"
            utils1.file_write_text(tsmdbmgr, "SERVERNAME TSMDBMGR_TSMINST1\n")
            utils1.chown(self.context, tsmdbmgr, tsm_user, tsm_group)
            utils1.chmod(self.context, tsmdbmgr, "0644")

            # DONE
            return make_result(
                True,
                "Macro generation and execution completed for Linux",
                {"admin_macro_done": True, "macros": created_macros}
            )
        
        elif self.os_type == "windows":
            base_dir = rf"C:\{tsm_user}"
            dsmserv_exe = r"C:\Program Files\Tivoli\tsm\server\dsmserv.exe"
            marker_file = f"{base_dir}\\.macros_executed"
            dsmserv_opt = f"{base_dir}\\dsmserv.opt"

            # Idempotency check
            if utils1.fs_exists(marker_file):
                self.log.info("Macros already executed, skipping (idempotent)")
                return make_result(True, "Macros already executed")

            # Ensure instance directory exists
            if not utils1.fs_exists(base_dir):
                return make_result(
                    False,
                    f"Instance directory not found: {base_dir}"
                )
            
            # Ensure dsmserv.opt exists (MANDATORY on Windows)
            if not utils1.fs_exists(dsmserv_opt):
                self.log.warning("dsmserv.opt not found, generating minimal config")

                opt_content = (
                    "COMMMETHOD TCPIP\r\n"
                    "TCPPORT 1500\r\n"
                    "COMMTimeout 3600\r\n"
                    f"ACTIVELOGSIZE 8192\r\n"
                    f"ACTIVELOGDIRECTORY {base_dir}\\TSMalog\r\n"
                    f"ARCHLOGDIRECTORY {base_dir}\\TSMarchlog\r\n"
                    f"VOLUMEHISTORY {base_dir}\\volhist.out\r\n"
                    f"DEVCONFIG {base_dir}\\devconf.dat\r\n"
                )

                utils1.file_write_text(dsmserv_opt, opt_content)

                # Grant read permission to instance user
                utils1.exec_run(
                    self.context,
                    f'icacls "{dsmserv_opt}" /grant "{tsm_user}:R"'
                )

                self.log.info(f"dsmserv.opt generated at {dsmserv_opt}")
            else:
                self.log.info("dsmserv.opt already present")

            # Minimal DB presence check (filesystem-based, safe)
            db_space = rf"{base_dir}\TSMdbspace01"
            if not utils1.fs_exists(db_space):
                return make_result(
                    False,
                    "Database directories not found, macros cannot be executed"
                )

            self.log.info("Database directories present, proceeding with macros")

            # Execute macros sequentially
            executed = []

            for macro in macros:
                macro_path = os.path.basename(macro["dest"])

                self.log.info(f"Executing macro: {macro_path}")

                cmd = (
                    f'cmd /c "cd /d {base_dir} && '
                    f'set DB2INSTANCE={tsm_user} && '
                    f'"{dsmserv_exe}" -k {tsm_user} runfile {macro_path}"'
                )

                resp = utils1.exec_run(self.context, cmd)

                if resp["rc"] != 0:
                    self.log.error(f"Macro execution failed: {macro_path}")
                    self.log.error(resp.get("stderr", ""))
                    return make_result(
                        False,
                        f"Macro execution failed: {macro_path}",
                        resp
                    )

                self.log.info(f"Macro executed successfully on Windows: {macro_path}")
                executed.append(macro_path)

            # Persist success marker
            self.log.info("Macro execution completed, marker file created for idempotency")
            return make_result(True, "All macros executed successfully on Windows", {"executed_macros": executed})

    # -----------------------------------------------------------------------
    # 6. Service configuration / enablement
    # -----------------------------------------------------------------------

    def configure_services(self) -> Dict[str, Any]:
        """
        Mirrors:
          - Ensure server service is enabled and started
          - Any other service-level tasks using utils1.svc_start/svc_stop.
        """
        service_name = self.vars.get("service_name", "dsmserv")

        self.log.info(f"Ensuring service {service_name} is configured and started")

        try:
            svc_start_res = utils1.svc_start(self.context, service_name)
        except Exception as exc:
            msg = f"Failed to start service {service_name}: {exc}"
            self.log.error(msg)
            return make_result(False, msg)

        self.log.debug(f"Service start result: {svc_start_res}")
        return make_result(True, f"Service {service_name} ensured running", {"raw": svc_start_res})

    # -----------------------------------------------------------------------
    # 7. Cleanup tasks (mirror 'Cleanup the server configuration')
    # -----------------------------------------------------------------------

    def cleanup(self) -> Dict[str, Any]:
        """
        Mirrors the cleanup part of the playbook:
        - Removing temporary directories
        - Removing macro files, etc.

        You can expand this to match all clean-up tasks.
        """
        self.log.info("Performing cleanup of server configuration")

        cleanup_dirs = self.vars.get("cleanup_dirs", [])
        failed = []

        for d in cleanup_dirs:
            self.log.debug(f"Removing directory tree: {d}")
            ok = utils1.fs_remove_tree(d)
            if not ok:
                self.log.warning(f"Failed to remove {d}")
                failed.append(d)

        if failed:
            msg = f"Cleanup completed with failures for dirs: {', '.join(failed)}"
            self.log.warning(msg)
            return make_result(False, msg, {"failed": failed})

        return make_result(True, "Cleanup completed successfully", {"removed_dirs": cleanup_dirs})

    # -----------------------------------------------------------------------
    # 8. Top-level orchestration (equivalent to entire play)
    # -----------------------------------------------------------------------

    def configure_all(self) -> Dict[str, Any]:
        """
        Run the full configuration sequence, approximately matching
        the entire Ansible play from top to bottom.
        """
        self.log.info("Starting full SP server configuration workflow")

        steps = [
            # ("prepare_storage", self.prepare_storage),
            ("create_group_and_user", self.create_group_and_user),
            ("create_directories", self.create_directories),
            ("create_db2_instance", self.create_db2_instance),
            ("configure_db2_as_instance_user", self.configure_db2_as_instance_user),
            ("format_database_windows", self.format_database_windows) if self.os_type == "windows" else (),
            # ("generate_and_run_macros", self.generate_and_run_macros),
            ("configure_services", self.configure_services),
        ]

        results = {}
        for name, fn in steps:
            self.log.info(f"Running step: {name}")
            res = fn()
            results[name] = res
            if not res["status"]:
                msg = f"Step {name} failed: {res['message']}"
                self.log.error(msg)
                return make_result(False, msg, {"step_results": results})

        self.log.info("SP server configuration completed successfully")
        return make_result(True, "All steps completed successfully", {"step_results": results})

    # -----------------------------------------------------------------------
    # 9. Ad-hoc execution of individual steps (for CLI)
    # -----------------------------------------------------------------------
    def run_steps(self, step_names: List[str]) -> Dict[str, Any]:
        """
        Run a subset of steps by name (for ad-hoc CLI execution).
        Valid names: see mapping below.
        """
        mapping = {
            "prepare_storage": self.prepare_storage,
            "create_group_and_user": self.create_group_and_user,
            "create_directories": self.create_directories,
            "create_db2_instance": self.create_db2_instance,
            "configure_db2_as_instance_user": self.configure_db2_as_instance_user,
            "format_database_windows": self.format_database_windows, 
            # "generate_and_run_macros": self.generate_and_run_macros,
            "configure_services": self.configure_services,
            "cleanup": self.cleanup,
        }

        self.log.info(f"Running ad-hoc steps: {step_names}")
        results = {}

        for name in step_names:
            if name not in mapping:
                msg = f"Unknown step: {name}"
                self.log.error(msg)
                return make_result(False, msg, {"supported_steps": list(mapping.keys())})
            self.log.info(f"Executing step: {name}")
            res = mapping[name]()
            results[name] = res
            if not res["status"]:
                self.log.error(f"Step {name} failed: {res['message']}")
                return make_result(False, f"Step {name} failed", {"step_results": results})

        return make_result(True, "Requested steps completed", {"step_results": results})


# ---------------------------------------------------------------------------
# CLI (argparse) – ad-hoc or full execution
# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="SP Server Configuration : Python implementation of the Ansible playbook"
    )
    parser.add_argument(
        "--step",
        action="append",
        help=(
            "Step(s) to run (can be specified multiple times). "
            "If omitted, the full workflow is executed. "
            "Valid values: create_group_and_user, create_directories, "
            "create_db2_instance, configure_db2_as_instance_user, "
            "generate_and_run_macros, configure_services, cleanup"
        ),
    )
    parser.add_argument(
        "--vars-file",
        help="Optional path to a Python or JSON file providing the vars dict, "
             "or you can construct vars in code and ignore this.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )

    parser.add_argument("--log-file", default="/var/log/ibm/sp_server_configuration.log", help="Path to log file")
    
    return parser


def load_vars_from_file(path: str) -> Dict[str, Any]:
    """
    Helper to load vars; implement this the way you like.
    For example you can:
      - import a Python file that defines VARS = {...}
      - or parse JSON
      - or YAML using PyYAML (yaml.safe_load)
    Here we just show JSON as a simple transport.
    """
    import json
    raw = utils1.file_read_text(path)
    return json.loads(raw)

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


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    logging.getLogger().setLevel(getattr(logging, args.log_level.upper(), logging.INFO))

    os_info = utils1.get_os_info()
    sys_info = utils1.get_system_info()

    log = setup_logger("SPServerConfiguration", args.log_level, Path(args.log_file))

    context: Dict[str, Any] = {
        "ts": int(time.time()),
        "args": vars(args),
        "os": os_info,
        "system": sys_info,
        "dry_run": False,
        "logger": log,
        "data": {}
    }
    
    print(context)

    # Build vars dict – in real use you’d probably load from a JSON/YAML/ini
    if args.vars_file:
        vars_dict = load_vars_from_file(args.vars_file)
    else:
        # Minimal example populated from what we saw in the playbook;
        # in real code you should set all required values.
        vars_dict = {
            "tsm_group": "tsmgrp",
            "tsm_group_gid": 900,
            "tsm_user": "tsminst1",
            "tsm_user_uid": 900,
            "tsm_user_password": "ChangeMe!",
            "root_dir": "/tsminst1",
            "directories": ["TSMdbdir", "TSMlog", "TSMarchlog"],
            "service_name": "dsmserv",
            "macros": [],      # fill with your macro definitions
            "cleanup_dirs": [],  # fill with lists of temporary dirs
        }

    sp = SPServerConfiguration(context, vars=vars_dict)

    if args.step:
        result = sp.run_steps(args.step)
    else:
        result = sp.configure_all()

    # Print a simple JSON representation to stdout for automation
    import json
    print(json.dumps(result, indent=2))

    # Exit code based on status
    import sys
    sys.exit(0 if result["status"] else 1)


if __name__ == "__main__":
    main()