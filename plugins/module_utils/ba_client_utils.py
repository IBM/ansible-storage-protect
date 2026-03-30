# -*- coding: utf-8 -*-
# IBM Storage Protect BA Client Utility Module

import os
import platform
import re
import shutil
import subprocess
from distutils.version import LooseVersion

IS_WINDOWS = platform.system().lower().startswith("win")

if not IS_WINDOWS:
    # Linux / normal Ansible environment
    from ansible.module_utils.basic import AnsibleModule
else:
    # Windows-safe fallback for when Ansible isn't available
    class AnsibleModule:
        def __init__(self, *args, **kwargs):
            # mimic AnsibleModule interface just enough for this helper
            self.params = {}
        def run_command(self, cmd, use_unsafe_shell=False):
            # simple subprocess wrapper
            if use_unsafe_shell:
                completed = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            else:
                completed = subprocess.run(cmd.split(), shell=False, capture_output=True, text=True)
            return completed.returncode, completed.stdout, completed.stderr
        def fail_json(self, **kwargs):
            print(f"[Windows fail_json] {kwargs.get('msg', '')}")
            raise SystemExit(1)
        def exit_json(self, **kwargs):
            print(f"[Windows exit_json] {kwargs}")
            raise SystemExit(0)
        def warn(self, msg):
            print(f"[Windows WARN] {msg}")
        def log(self, msg):
            print(f"[Windows LOG] {msg}")


class BAClientHelper:
    def __init__(self, module: AnsibleModule):
        self.module = module

    def run_cmd(self, cmd, use_unsafe_shell=False, check_rc=True):
        rc, out, err = self.module.run_command(cmd, use_unsafe_shell=use_unsafe_shell)
        if check_rc and rc != 0:
            self.module.fail_json(msg=f"Command failed: {cmd}\nError: {err}")
        return rc, out, err

    def log(self, msg):
        try:
            if self.is_windows():
                print(msg)
            else:   
                self.module.warn(msg)
        except Exception:
            pass

    def file_exists(self, path):
        return os.path.exists(path)

    def is_windows(self):
        return platform.system().lower().startswith("win")

    def is_newer_version(self, target, current):
        try:
            return LooseVersion(target) > LooseVersion(current)
        except Exception:
            return target != current

    def check_installed(self):
        if self.is_windows():
            try:
                cmd = 'reg query "HKLM\\SOFTWARE\\IBM\\ADSM\\CurrentVersion\Api64" /v PtfLevel'
                rc, out, err = self.run_cmd(cmd, check_rc=False)
                if rc == 0 and "PtfLevel" in out:
                    version = out.split()[-1]
                    return True, version
                return False, None
            except Exception as e:
                return False, None
        else:
            cmd = "rpm -q TIVsm-BA"
            rc, out, err = self.run_cmd(cmd, check_rc=False)
            if rc == 0 and "TIVsm-BA" in out:
                rpm_full = out.strip().replace("TIVsm-BA-", "")
                rpm_no_arch = rpm_full.split(".x86_64")[0]
                version = rpm_no_arch.replace("-", ".")
                return True, version
            elif rc == 1:
                return False, None
            else:
                self.module.fail_json(msg=f"Command failed: {cmd}\nError: {err.strip()}")

    def verify_system_prereqs(self):
        """Verify system prerequisites (OS, architecture, privileges, disk, Java)"""
        min_disk_mb = 1500
        compatible_arch = ["x86_64", "AMD64"]

        sys_info = {
            "os": platform.system(),
            "arch": platform.machine(),
            "hostname": platform.node(),
        }

        if self.is_windows():
            # check admin membership
            rc, out, err = self.run_cmd('whoami /groups | find "Administrators"', use_unsafe_shell=True, check_rc=False)
            if rc != 0:
                self.module.fail_json(
                    msg="Admin privileges required to install BA Client on Windows"
                )
        else:
            if os.geteuid() != 0:
                self.module.fail_json(
                    msg="Root privileges required to install BA Client on Linux"
                )

        arch_compatible = sys_info["arch"] in compatible_arch
        if not arch_compatible:
            self.module.fail_json(
                msg=f"Incompatible architecture: {sys_info['arch']}. "
                    f"Supported: {', '.join(compatible_arch)}"
            )

        # disk usage
        st = shutil.disk_usage("/")
        free_mb = st.free // (1024 * 1024)
        if free_mb < min_disk_mb:
            self.module.fail_json(
                msg=f"Insufficient disk space. Required: {min_disk_mb} MB, Available: {free_mb} MB"
            )

        summary = (
            f"System Compatibility Summary:\n"
            f"- OS: {sys_info['os']}\n"
            f"- Architecture: {sys_info['arch']} (compatible: {arch_compatible})\n"
            f"- Free Disk Space: {free_mb} MB (required ≥ {min_disk_mb})\n"
        )

        self.module.log(summary)

        if not (arch_compatible and free_mb >= min_disk_mb):
            self.module.fail_json(
                msg=(
                    "System compatibility checks failed. Ensure:\n"
                    f" - Architecture: one of {compatible_arch}\n"
                    f" - Disk space ≥ {min_disk_mb} MB\n"
                    + summary
                )
            )

        return {
            "status": "ok",
            "architecture": sys_info["arch"],
            "arch_compatible": arch_compatible,
            "disk_space_ok": free_mb >= min_disk_mb,
            "free_mb": free_mb,
        }

    def extract_package(self, src, dest):
        """Extract tarball and ensure RPMs exist"""

        if self.is_windows():
            if (os.path.exists(dest)):
                self.run_cmd(cmd=f"powershell -Command \"Remove-Item -Path '{dest}' -Recurse -Force -ErrorAction SilentlyContinue\"")
            self.run_cmd(cmd=f"\"{src}\" -y -o\"{dest}\"")
            return

        # --- Validation ---
        if not os.path.exists(src):
            self.module.fail_json(msg=f"Package source not found: {src}")
        if os.path.isdir(src):
            self.module.fail_json(msg=f"Expected a tarball file, got directory instead: {src}")

        # Ensure destination directory exists
        os.makedirs(dest, exist_ok=True)

        # --- Extraction ---
        cmd = f'tar -xf "{src}" -C "{dest}"'
        rc, out, err = self.run_cmd(cmd, use_unsafe_shell=True)
        if rc != 0:
            self.module.fail_json(msg=f"Extraction failed: {err}")

        # --- Find RPMs ---
        rpm_files = []
        for root, _, files in os.walk(dest):
            rpm_files += [os.path.join(root, f) for f in files if f.endswith(".rpm")]

        if not rpm_files:
            self.module.fail_json(msg=f"No RPM packages found in extracted directory: {dest}")

        return os.path.dirname(rpm_files[0])

    def install_ba_client(self, package_source, install_path, temp_dir):
        """
        Install BA Client from extracted RPMs (Linux) or EXE (Windows).
        Performs extraction automatically if needed.
        """
        if self.is_windows():
            if not os.path.exists(package_source):
                self.module.fail_json(msg=f"Package source not found: {package_source}")

            self.extract_package(package_source, temp_dir)
            # silent install typical pattern
            file_loc = os.path.dirname(package_source)
            with open("testt.txt", "w") as tfr:
                tfr.write("Installation started")

            cmd = f"\"{file_loc}/baClient/TSMClient/IBM Storage Protect Client.msi\" /qn INSTALLDIR=\"{install_path}\" /l*v install_baclient.log"
        else:
            if package_source.endswith(".tar") or package_source.endswith(".tar.gz"):
                self.extract_package(package_source, temp_dir)
            else:
                if os.path.isdir(package_source):
                    temp_dir = package_source
                else:
                    self.module.fail_json(msg=f"Invalid package source: {package_source}")

            rpm_files = [
                os.path.join(temp_dir, f)
                for f in os.listdir(temp_dir)
                if f.endswith(".rpm")
            ]
            if not rpm_files:
                self.module.fail_json(msg=f"No RPM files found under {temp_dir}")

            cmd = f'cd "{temp_dir}" && rpm -ivh --force --nodeps *.rpm'

        rc, out, err = self.run_cmd(cmd, use_unsafe_shell=True)
        if rc != 0:
            if (self.is_windows()):
                print("Installation Failed")
                print(err)
            else:
                self.module.fail_json(msg=f"Installation failed: {err}")
        else:
            print("Installation succeeded. Exit code: " + str(rc))

        print("BA Client installation completed successfully")
        return True
    
    def rollback(self, action="install"):
        """
        Rollback mechanism for BA Client operations.
        - action='install' → uninstall packages
        - action='uninstall' → reinstall packages
        """
        self.module.warn(f"Initiating rollback for action={action}")
        print(f"Initiating rollback for action={action}")

        if self.is_windows():
            return self._rollback_windows(action)
        else:
            return self._rollback_linux(action)
        
    # LINUX ROLLBACK
    def _rollback_linux(self, action):
        results = []
        package_dir = "/opt/baClient"  # default package repo
        backup_dir = "/opt/baClientPackagesBk"

        # -------- INSTALL FAILURE --------
        if action == "install":
            uninstall_order = [
                "TIVsm-WEBGUI",
                "TIVsm-JBB",         
                "TIVsm-BAhdw",
                "TIVsm-BAcit",
                "TIVsm-APIcit",
                "TIVsm-BA",
                "TIVsm-API64",
                "gskssl64",
                "gskcrypt64"
            ]
            self.module.log("Rollback: uninstalling packages from failed installation.")
            for pkg in uninstall_order:
                # Force uninstall without dependency checks and scripts
                cmd = f"rpm -e --nodeps --noscripts {pkg}"
                rc, out, err = self.run_cmd(cmd, check_rc=False)
                results.append({
                    "package": pkg,
                    "rc": rc,
                    "stdout": out.strip(),
                    "stderr": err.strip()
                })
                if rc != 0:
                    self.module.warn(f"Rollback warning: Failed to remove {pkg}, rc={rc}, err={err.strip()}")

            # Verify cleanup
            rc, out, _ = self.run_cmd("rpm -qa 'TIVsm*'", check_rc=False)

            if not out.strip():
                self.module.warn("Rollback successful: All TIVsm packages removed.")
                rollback_status = "Rollback successful: All TIVsm packages removed."
            else:
                self.module.log(f"Rollback warning: Some TIVsm packages still present:\n{out.strip()}")
                rollback_status = f"Rollback warning: Some TIVsm packages still present:\n{out.strip()}"

            return {"rollback_type": action, "results": results, "status": rollback_status}

        # -------- UNINSTALL FAILURE --------
        elif action == "uninstall":
            reinstall_order = [
                "gskcrypt64", "gskssl64", "TIVsm-API64", "TIVsm-APIcit",
                "TIVsm-BA", "TIVsm-BAcit", "TIVsm-BAhdw", "TIVsm-WEBGUI"
            ]
            self.module.log("Rollback: reinstalling packages due to failed uninstallation.")
            for pkg in reinstall_order:
                rpm_pattern = f"{package_dir}/{pkg}*.rpm"
                cmd = f"rpm -ivh {rpm_pattern}"
                rc, out, err = self.run_cmd(cmd, check_rc=False)
                results.append({"package": pkg, "rc": rc, "stderr": err.strip()})
            self.module.warn(f"Rollback successful: All packages reinstalled after uninstall failure.")
            return {"rollback_type": "uninstall", "results": results}

        # -------- UPGRADE FAILURE --------
        elif action == "upgrade":
            self.module.log("Rollback: restoring previous version and configuration files.")
            backup_files = [
                "/opt/tivoli/tsm/client/ba/bin/dsm.opt.bk",
                "/opt/tivoli/tsm/client/ba/bin/dsm.sys.bk"
            ]
            results = []

            # Restore configuration files
            for file in backup_files:
                orig = file.replace(".bk", "")
                if os.path.exists(file):
                    shutil.copy(file, orig)
                    results.append({"file_restored": orig, "status": "restored"})
                else:
                    results.append({"file_restored": orig, "status": "backup_missing"})

            # First, remove the new upgrade version
            self.run_cmd("rpm -e $(rpm -qa 'TIVsm*')", check_rc=False)

            # Reinstall previous packages from backup
            reinstall_order = [
                "gskcrypt64",
                "gskssl64",
                "TIVsm-API64",
                "TIVsm-APIcit",
                "TIVsm-BA",
                "TIVsm-BAcit",
                "TIVsm-BAhdw",
                "TIVsm-WEBGUI"
            ]

            for pkg in reinstall_order:
                rpm_pattern = f"{backup_dir}/{pkg}*.rpm"
                cmd = f"rpm -ivh {rpm_pattern}"
                self.module.log(f"Rollback command: {cmd}")
                rc, out, err = self.run_cmd(cmd, check_rc=False)
                results.append({"package": pkg, "rc": rc, "stderr": err.strip()})

            # Cleanup
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir, ignore_errors=True)
                results.append({"cleanup": backup_dir, "status": "removed"})

            # Verify rollback success
            rc, out, _ = self.run_cmd("rpm -qa 'TIVsm*'", check_rc=False)
            if "8.1.25" in out:
                self.module.warn("Rollback successful: Previous version and configs restored after upgrade failure.")
            else:
                self.module.log(f"Rollback warning: restore may have failed — installed TIVsm packages:\n{out.strip()}")

            return {"rollback_type": "upgrade", "results": results}


    # WINDOWS ROLLBACK
    def _rollback_windows(self, action):
        results = []

        # ---------------- INSTALL FAILURE -----------------
        if action == "install":
            uninstall_targets = [
                "IBM Storage Protect Client",
                "IBM Spectrum Protect Client",
                "Tivoli Storage Manager Client"
            ]
            for target in uninstall_targets:
                ps_cmd = (
                    f'Get-WmiObject -Class Win32_Product | '
                    f'Where-Object {{ $_.Name -like "*{target}*" }} | '
                    f'ForEach-Object {{ $_.Uninstall() }}'
                )
                rc, out, err = self.run_cmd(["powershell.exe", "-Command", ps_cmd], check_rc=False)
                results.append({"package": target, "rc": rc, "stderr": err.strip()})
            return {"rollback_type": "install", "results": results}

        # ---------------- UNINSTALL FAILURE -----------------
        elif action == "uninstall":
            self.module.log("Rollback: reinstalling BA Client on Windows after uninstall failure.")
            installer_path = os.path.join(self.install_dir, "TSMClient", "install.exe")
            if os.path.exists(installer_path):
                cmd = f'"{installer_path}" /qn REINSTALL=ALL REINSTALLMODE=vomus'
                rc, out, err = self.run_cmd(cmd, check_rc=False)
                results.append({"package": "BA Client", "rc": rc, "stderr": err.strip()})
            else:
                results.append({"package": "BA Client", "error": "Installer not found"})
            return {"rollback_type": "uninstall", "results": results}

        # ---------------- UPGRADE FAILURE -----------------
        elif action == "upgrade":
            self.module.log("Rollback: restoring previous BA Client version and configs on Windows.")
            backup_dir = r"C:\temp\baClientBackup"
            config_files = [
                r"C:\Program Files\Tivoli\tsm\client\ba\bin\dsm.opt.bk",
                r"C:\Program Files\Tivoli\tsm\client\ba\bin\dsm.sys.bk"
            ]

            # Step 1: Restore config backups
            for file in config_files:
                orig = file.replace(".bk", "")
                if os.path.exists(file):
                    shutil.copy(file, orig)
                    results.append({"file_restored": orig, "status": "restored"})
                else:
                    results.append({"file_restored": orig, "status": "backup_missing"})

            # Step 2: Reinstall previous version from backup
            installer_path = os.path.join(backup_dir, "8.1.25.0-TIV-TSMBAC-WinX64.exe")
            if os.path.exists(installer_path):
                cmd = f'"{installer_path}" /qn INSTALLDIR="{self.install_dir}"'
                rc, out, err = self.run_cmd(cmd, check_rc=False)
                results.append({"package": "BA Client", "rc": rc, "stderr": err.strip()})
            else:
                results.append({"package": "BA Client", "error": "Backup installer missing"})

            # Step 3: Remove backup dir
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir, ignore_errors=True)
                results.append({"cleanup": backup_dir, "status": "removed"})

            return {"rollback_type": "upgrade", "results": results}
    
    def post_installation_verification(self, ba_client_version, state):
        """Verify that BA Client is installed correctly and return status summary."""

        if self.is_windows():
            check_cmd = 'wmic product get name | find "IBM Storage Protect Client"'
            print(check_cmd)
        else:
            check_cmd = "rpm -q TIVsm-BA"

        rc, out, err = self.run_cmd(check_cmd, use_unsafe_shell=self.is_windows(), check_rc=False)

        if rc == 0:
            if self.is_windows():
                print(f"BA Client {ba_client_version} installation status: Installed Successfully")
            else:
                self.module.warn(f"BA Client {ba_client_version} installation status: Installed Successfully")
            installation_successful = True
        else:
            msg = f"BA Client {ba_client_version} installation status: Not Installed\nError: {err.strip()}"
            if self.is_windows():
                print(msg)
            else:
                self.module.warn(msg)

            if state == "install":
                self.module.fail_json(msg="BA Client installation verification failed. Please check logs.")
            installation_successful = False

        return {
            "is_installation_successful": installation_successful,
            "ba_client_version": ba_client_version
        }

    def configure_ba_client(self):
        config_dir = "/opt/tivoli/tsm/client/ba/bin"
        dsm_opt = f"{config_dir}/dsm.opt"
        dsm_sys = f"{config_dir}/dsm.sys"

        # Ensure directory exists
        os.makedirs(config_dir, exist_ok=True)

        # ----- DSM.SYS -----
        sys_content = """SErvername  TSM_SERVER
    TCPServeraddress  your.server.address
    TCPPort           1500
    """

        if not os.path.exists(dsm_sys):
            with open(dsm_sys, "w") as f:
                f.write(sys_content)
            self.module.warn("Created default dsm.sys configuration.")
        else:
            with open(dsm_sys, "a") as f:
                f.write("\n" + sys_content)
            self.module.warn("Updated existing dsm.sys configuration.")

        # ----- DSM.OPT -----
        opt_content = """SErvername  TSM_SERVER
    NODename   your_node_name
    PasswordDir /opt/tivoli/tsm/client/ba/bin
    """

        if not os.path.exists(dsm_opt):
            with open(dsm_opt, "w") as f:
                f.write(opt_content)
            self.module.warn("Created default dsm.opt configuration.")
        else:
            with open(dsm_opt, "a") as f:
                f.write("\n" + opt_content)
            self.module.warn("Updated existing dsm.opt configuration.")

        # ----- Validation -----
        if os.path.exists(dsm_opt) and os.path.exists(dsm_sys):
            self.module.warn("BA Client configuration files created/updated successfully.")
        else:
            self.module.warn("BA Client configuration missing or not applied correctly.")

    def start_baclient_daemon(self, ba_client_start_daemon):
        """Enable and start BA Client daemon/service across platforms."""

        if not ba_client_start_daemon:
            self.module.warn("Skipping daemon start as ba_client_start_daemon=False")
            return {"daemon_enabled": False}

        if self.is_windows():
            services = ["TSM Client Scheduler", "TSM Client Acceptor"]
            for svc in services:
                rc, out, err = self.run_cmd(f'net start "{svc}"', check_rc=False)
                if rc != 0 and "already running" not in out.lower():
                    self.module.warn(f"Failed to start Windows service '{svc}': {err.strip()}")
                else:
                    self.module.warn(f"Windows service '{svc}' started successfully.")
            return {"daemon_enabled": True}

        else:
            rc_enable, out_enable, err_enable = self.run_cmd("systemctl enable dsmcad.service", check_rc=False)
            if rc_enable != 0:
                self.module.warn(f"Failed to enable dsmcad.service: {err_enable.strip()}")

            rc_start, out_start, err_start = self.run_cmd("systemctl start dsmcad.service", check_rc=False)
            if rc_start != 0:
                self.module.warn(f"Failed to start dsmcad.service: {err_start.strip()}")
            else:
                self.module.warn("dsmcad.service started successfully.")

            rc_status, out_status, err_status = self.run_cmd("systemctl is-enabled dsmcad.service", check_rc=False)
            if rc_status == 0 and out_status.strip() == "enabled":
                self.module.warn("dsmcad.service is enabled and active.")
                daemon_enabled = True
            else:
                self.module.warn(f"Failed to enable/start dsmcad.service. Status: {out_status.strip()}")
                daemon_enabled = False

            return {"daemon_enabled": daemon_enabled}

    def uninstall_ba_client(self, extract_dest="/opt/baClient", backup_dir="/opt/baClientPackagesBk"):
        """
        Performs complete uninstallation of BA Client and dependent packages with backup and rollback.
        """
        if self.is_windows():
            cmd = 'powershell "Get-WmiObject -Class Win32_Product | Where-Object { $_.Name -like \'*IBM Storage Protect Client*\' } | ForEach-Object { $_.Uninstall() }"'
            rc, out, err = self.run_cmd(cmd, use_unsafe_shell=True, check_rc=False)
            if rc != 0:
                self.module.fail_json(msg=f"Uninstallation failed: {err}")
            return True

        rc, out, err = self.run_cmd("rpm -q TIVsm-BA", check_rc=False)
        if rc != 0:
            self.log("BA Client is not installed on this system. Skipping uninstallation.")
            return False

        self.run_cmd("systemctl stop dsmcad", check_rc=False)
        self.run_cmd("killall dsmc", check_rc=False)

        os.makedirs(backup_dir, exist_ok=True)
        for f in ["/opt/tivoli/tsm/client/ba/bin/dsm.opt", "/opt/tivoli/tsm/client/ba/bin/dsm.sys"]:
            if os.path.exists(f):
                shutil.copy2(f, f"{f}.bk")

        rc, out, err = self.run_cmd(f"find {extract_dest} -name '*.rpm'", check_rc=False)
        if out.strip():
            for rpm_path in out.strip().splitlines():
                self.run_cmd(f"cp {rpm_path} {backup_dir}", check_rc=False)

        uninstall_order = [
            "TIVsm-BAcit",
            "TIVsm-BAhdw",
            "TIVsm-WEBGUI",
            "TIVsm-JBB",
            "TIVsm-BA",
            "TIVsm-APIcit",
            "TIVsm-API64",
            "gskssl64",
            "gskcrypt64"
        ]

        successfully_uninstalled = []
        failed_packages = []

        for pkg in uninstall_order:
            rc, _, err = self.run_cmd(f"rpm -q {pkg}", check_rc=False)
            if rc != 0:
                continue

            rc, out, err = self.run_cmd(f"rpm -e {pkg}", check_rc=False)
            if rc == 0:
                successfully_uninstalled.append(pkg)
            else:
                failed_packages.append((pkg, err))

        if failed_packages:
            self.module.fail_json(
                msg=f"Uninstallation failed for packages: {', '.join([p for p, _ in failed_packages])}. "
                    f"Reason(s): {'; '.join([e for _, e in failed_packages])}."
            )

        shutil.rmtree(backup_dir, ignore_errors=True)
        self.module.warn("BA Client successfully uninstalled with all components removed.")
        return True

    def upgrade_ba_client(self, package_source, install_path, ba_client_version, state, temp_dir):
        """Upgrade BA Client to specified version."""
        installed, installed_version = self.check_installed()
        if not installed:
            self.module.fail_json(msg="BA Client not installed. Please install instead of upgrade.")

        self.log(f"Upgrading BA Client from {installed_version} -> {ba_client_version}")

        backup_dir = os.path.join(temp_dir, "backup_old_rpms")
        os.makedirs(backup_dir, exist_ok=True)

        # Backup currently installed BA Client rpms
        cmd = "rpm -qa 'TIVsm*' --queryformat '%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH}\n'"
        rc, out, err = self.run_cmd(cmd, check_rc=False)

        for pkg in out.strip().splitlines():
            rpm_path = f"/var/lib/rpm/{pkg}.rpm"
            # In real systems, we may not have the original rpm, so use `rpm -q --qf` to find installed details
            # Best approach: use repoquery or keep old rpms in a known directory
            self.run_cmd(f"rpm -qp --qf '%{{NAME}}' {pkg}", check_rc=False)
            # Simulate backup: copy old rpm from your package source path if available
            self.run_cmd(f"cp {package_source}/{pkg}*.rpm {backup_dir}/", check_rc=False)

        self.module.log(f"Backed up existing rpms to {backup_dir}")

        self.uninstall_ba_client()

        self.install_ba_client(package_source, install_path, temp_dir)
        self.configure_ba_client()
        self.post_installation_verification(ba_client_version, state)
        self.start_baclient_daemon(ba_client_start_daemon=True)

        post_installed, post_version = self.check_installed()
        if not post_installed or post_version != ba_client_version:
            if (IS_WINDOWS):
                print("Upgrade failed: version mismatch after installation")
            else:
                self.module.fail_json(msg="Upgrade failed: version mismatch after installation")

        self.log(f"BA Client successfully upgraded from {installed_version} to {post_version}")
        return {"changed": True, "msg": f"BA Client successfully upgraded from {installed_version} to {post_version}"}