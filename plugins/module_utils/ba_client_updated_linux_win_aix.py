# ba_client_utils.py
# -*- coding: utf-8 -*-
"""
IBM Storage Protect BA Client Utility Module
Supports Windows, Linux, and AIX
"""

import os
import platform
import shutil
from distutils.version import LooseVersion


class BAClientHelper:
    def __init__(self, module):
        self.module = module

    # -------------------------
    # Generic helpers
    # -------------------------
    def run_cmd(self, cmd, use_unsafe_shell=False, check_rc=True):
        rc, out, err = self.module.run_command(cmd, use_unsafe_shell=use_unsafe_shell)
        if check_rc and rc != 0:
            self.module.fail_json(msg=f"Command failed: {cmd}\nError: {err}")
        return rc, out, err

    def log(self, msg):
        if hasattr(self.module, "log"):
            try:
                self.module.log(msg)
                return
            except Exception:
                pass
        if hasattr(self.module, "warn"):
            self.module.warn(msg)
        else:
            print(f"LOG: {msg}")

    def file_exists(self, path):
        return os.path.exists(path)

    def resolve_package_source(self, package_source):
        """Return an existing installer path, including .tar <-> .tar.Z fallbacks on AIX."""
        if not package_source:
            return package_source
        if self.file_exists(package_source):
            return package_source
        if self.is_aix():
            if package_source.endswith(".tar.Z"):
                alt = package_source[:-2]
                if self.file_exists(alt):
                    self.log(f"Using uncompressed package: {alt}")
                    return alt
            elif package_source.endswith(".tar"):
                alt = f"{package_source}.Z"
                if self.file_exists(alt):
                    self.log(f"Using compressed package: {alt}")
                    return alt
        return package_source

    # -------------------------
    # OS detection
    # -------------------------
    def is_windows(self):
        return platform.system().lower().startswith("win")

    def is_aix(self):
        return platform.system().upper() == "AIX"

    def is_linux(self):
        return platform.system().lower() == "linux"

    def _aix_dsmc_candidates(self):
        return [
            "/usr/tivoli/tsm/client/ba/bin64/dsmc",
            "/usr/tivoli/tsm/client/ba/bin/dsmc",
            "/opt/tivoli/tsm/client/ba/bin64/dsmc",
            "/opt/tivoli/tsm/client/ba/bin/dsmc",
        ]

    def _find_dsmc_binary(self):
        for path in self._aix_dsmc_candidates():
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path
        return None

    def _aix_install_image_dir(self, extract_dir):
        """Return directory containing AIX installp images and ensure a .toc exists."""
        image_dir = extract_dir
        for root, _, files in os.walk(extract_dir):
            if any(name.lower().endswith(".bff") for name in files):
                image_dir = root
                break

        self.run_cmd(
            f'/usr/sbin/inutoc "{image_dir}"',
            use_unsafe_shell=True,
            check_rc=False,
        )
        return image_dir

    # -------------------------
    # Version helpers
    # -------------------------
    def is_newer_version(self, target, current):
        try:
            return LooseVersion(target) > LooseVersion(current)
        except Exception:
            return target != current

    # -------------------------
    # Installed check
    # -------------------------
    def _aix_fileset_version(self, fileset):
        """Return committed fileset level from lslpp, handling AIX wrapped output."""
        rc, out, _ = self.run_cmd(f"lslpp -Lc {fileset}", check_rc=False)
        if rc == 0 and out.strip():
            for line in out.splitlines():
                line = line.strip()
                if not line or ":" not in line:
                    continue
                name, _, level = line.partition(":")
                if name.strip() == fileset and level.strip():
                    return level.strip()

        rc, out, _ = self.run_cmd(f"lslpp -L {fileset}", check_rc=False)
        out_lower = (out or "").lower()
        if rc != 0 or "not found" in out_lower:
            return None

        lines = out.splitlines()
        for idx, line in enumerate(lines):
            if fileset not in line:
                continue
            parts = line.split()
            if len(parts) >= 3 and parts[2] == "C":
                return parts[1]
            if line.strip() == fileset and idx + 1 < len(lines):
                next_parts = lines[idx + 1].split()
                if len(next_parts) >= 3 and next_parts[2] == "C":
                    return next_parts[0]
                if len(next_parts) >= 2 and next_parts[1] == "C":
                    return next_parts[0]
        return None

    def check_installed(self):
        if self.is_windows():
            cmd = 'reg query "HKLM\\SOFTWARE\\IBM\\ADSM\\CurrentVersion" /v PTF'
            rc, out, _ = self.run_cmd(cmd, check_rc=False)
            if rc == 0 and "PTF" in out:
                return True, out.strip().split()[-1]
            return False, None

        if self.is_aix():
            version = self._aix_fileset_version("tivoli.tsm.client.ba.64bit.base")
            if version:
                return True, version
            return False, None

        # Linux
        rc, out, _ = self.run_cmd("rpm -q TIVsm-BA", check_rc=False)
        if rc == 0:
            ver = out.strip().replace("TIVsm-BA-", "").split(".x86_64")[0]
            return True, ver.replace("-", ".")
        return False, None

    # -------------------------
    # System prereqs
    # -------------------------
    def verify_system_prereqs(self):
        min_disk_mb = 1500

        if not self.is_windows():
            try:
                if os.geteuid() != 0:
                    self.module.fail_json(
                        msg="Root privileges required to install BA Client on Unix systems"
                    )
            except AttributeError:
                pass

        if self.is_windows():
            rc, _, _ = self.run_cmd(
                'whoami /groups | find "Administrators"', check_rc=False
            )
            if rc != 0:
                self.module.fail_json(
                    msg="Admin privileges required to install BA Client on Windows"
                )

        if self.is_aix():
            rc, out, _ = self.run_cmd("uname -p", check_rc=False)
            aix_arch = out.strip().lower() if rc == 0 else ""
            if "power" not in aix_arch:
                self.module.fail_json(
                    msg=f"Incompatible AIX architecture: {aix_arch}. POWER required."
                )
        elif self.is_linux():
            if platform.machine() != "x86_64":
                self.module.fail_json(
                    msg=f"Incompatible Linux architecture: {platform.machine()}"
                )

        check_path = "/usr" if self.is_aix() else "/"

        try:
            free_mb = shutil.disk_usage(check_path).free // (1024 * 1024)
        except Exception as e:
            self.module.fail_json(
                msg=f"Unable to determine disk space for {check_path}: {str(e)}"
            )

        if free_mb < min_disk_mb:
            self.module.fail_json(
                msg=(
                    f"Insufficient disk space on {check_path}. "
                    f"Required {min_disk_mb} MB, available {free_mb} MB"
                )
            )

    # -------------------------
    # Extraction
    # -------------------------
    def extract_package(self, src, dest):
        if not os.path.exists(src):
            self.module.fail_json(msg=f"Package source not found: {src}")

        os.makedirs(dest, exist_ok=True)

        if self.is_aix():
            # Handle .tar.Z files on AIX (IBM recommends zcat | tar)
            if src.endswith('.tar.Z'):
                cmd = f'cd "{dest}" && zcat "{src}" | tar -xf -'
                rc, _, err = self.run_cmd(cmd, use_unsafe_shell=True, check_rc=False)
                if rc != 0:
                    cmd = f'cd "{dest}" && gunzip -c "{src}" | tar -xf -'
                    rc, _, err = self.run_cmd(cmd, use_unsafe_shell=True, check_rc=False)
                if rc != 0:
                    self.module.fail_json(msg=f"Extraction failed: {err}")
            else:
                cmd = f'cd "{dest}" && tar -xf "{src}"'
                rc, _, err = self.run_cmd(cmd, use_unsafe_shell=True, check_rc=False)
                if rc != 0:
                    self.module.fail_json(msg=f"Extraction failed: {err}")
        else:
            cmd = f'tar -xf "{src}" -C "{dest}"'
            rc, _, err = self.run_cmd(cmd, use_unsafe_shell=True, check_rc=False)
            if rc != 0:
                self.module.fail_json(msg=f"Extraction failed: {err}")

        return dest

    # -------------------------
    # Install
    # -------------------------
    def install_ba_client(self, package_source, install_path, temp_dir):
        if self.is_windows():
            if package_source.lower().endswith(".msi"):
                cmd = f'msiexec.exe /i "{package_source}" /qn'
            else:
                cmd = f'"{package_source}" /S'
            self.run_cmd(cmd, use_unsafe_shell=True)
            return True

        if self.is_aix():
            extract_dir = "/usr/tsm_ba_aix_extract"
            if os.path.isdir(extract_dir):
                shutil.rmtree(extract_dir)
            self.extract_package(package_source, extract_dir)
            install_dir = self._aix_install_image_dir(extract_dir)

            install_steps = [
                "tivoli.tsm.client.api.64bit",
                "tivoli.tsm.client.ba.64bit",
            ]
            install_output = []
            for filesets in install_steps:
                cmd = f'installp -acXYgd "{install_dir}" {filesets}'
                rc, out, err = self.run_cmd(cmd, use_unsafe_shell=True, check_rc=False)
                install_output.append(
                    {"filesets": filesets, "rc": rc, "stdout": out, "stderr": err}
                )
                if rc != 0:
                    self.module.fail_json(
                        msg=f"installp failed for {filesets}",
                        install_dir=install_dir,
                        install_output=install_output,
                    )
            self._aix_install_output = install_output
            return True

        extract_dir = temp_dir
        rpm_dir = self.extract_package(package_source, extract_dir)
        cmd = f'cd "{rpm_dir}" && rpm -ivh --force --nodeps *.rpm'
        self.run_cmd(cmd, use_unsafe_shell=True)
        self.module.warn("BA Client installed successfully on Linux")
        return True

    # -------------------------
    # Verification
    # -------------------------
    def post_installation_verification(self, ba_client_version, state):
        installed, installed_version = self.check_installed()
        if not installed:
            diagnostics = {}
            if self.is_aix():
                _, lslpp_out, _ = self.run_cmd(
                    "lslpp -L | grep -i tivoli.tsm.client",
                    use_unsafe_shell=True,
                    check_rc=False,
                )
                diagnostics = {
                    "dsmc_candidates": self._aix_dsmc_candidates(),
                    "dsmc_found": self._find_dsmc_binary(),
                    "lslpp_client_filesets": lslpp_out,
                    "install_output": getattr(self, "_aix_install_output", []),
                }
            self.module.fail_json(
                msg="BA Client installation verification failed",
                diagnostics=diagnostics,
            )

        requested = str(ba_client_version)
        if installed_version and self.is_newer_version(installed_version, requested):
            return {
                "is_installation_successful": True,
                "ba_client_version": installed_version,
                "dsmc_path": self._find_dsmc_binary() if self.is_aix() else None,
                "msg": (
                    f"BA Client already installed at newer version {installed_version} "
                    f"(requested {requested})"
                ),
            }

        return {
            "is_installation_successful": True,
            "ba_client_version": installed_version or ba_client_version,
            "dsmc_path": self._find_dsmc_binary() if self.is_aix() else None,
        }

    # -------------------------
    # Uninstall
    # -------------------------
    def uninstall_ba_client(self):
        if self.is_windows():
            self.run_cmd(
                'wmic product where "Name like \'%%Tivoli%%\'" call uninstall /nointeractive',
                check_rc=False
            )
            return True

        if self.is_aix():
            self.run_cmd(
                "installp -u "
                "tivoli.tsm.client.webgui "
                "tivoli.tsm.client.ba.64bit.image "
                "tivoli.tsm.client.ba.64bit.common "
                "tivoli.tsm.client.ba.64bit.base "
                "tivoli.tsm.client.api.64bit",
                check_rc=False
            )
            self.run_cmd(
                "installp -u tivoli.tsm.filepath.rte",
                check_rc=False
            )
            return True

        self.run_cmd("rpm -e TIVsm-BA", check_rc=False)
        return True

    # -------------------------
    # Upgrade
    # -------------------------
    def upgrade_ba_client(
        self,
        package_source,
        desired_version,
        install_path,
        ba_client_version,
        state,
        temp_dir,
    ):
        installed, installed_version = self.check_installed()
        if not installed:
            self.module.fail_json(msg="BA Client not installed; cannot upgrade")

        self.log(f"Upgrading BA Client from {installed_version} to {desired_version}")
        self.uninstall_ba_client()
        self.install_ba_client(package_source, install_path, temp_dir)
        return {"changed": True, "msg": "BA Client upgraded successfully"}
