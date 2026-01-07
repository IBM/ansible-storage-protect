from __future__ import annotations
from pathlib import Path
from typing import Any, Optional
import re
import os

# Prefer enhanced utils but fall back to utils
try:
    from tasks import utils_enhanced as utils1  # type: ignore
except Exception:  # pragma: no cover
    from tasks import utils as utils1  # type: ignore

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


class ORCH_BA_SERVER_INSTALL:
    def __init__(self, context: dict[str, Any]):
        self.ctx = context
        self.log = context["logger"]

    def run(self, mode: str) -> bool:
        os_name = utils1.os_oskey(self.ctx)
        install_path = utils1.ba_install_dir(self.ctx, os_name)
        target_root = install_path.anchor or "/"

        if not utils1.fs_require_free_mb(self.ctx, min_mb=7500, path=target_root):
            self.log.error("need >=7500 MB free at %s", target_root)
            return False

        if mode == "uninstall":
            return self._uninstall(os_name, install_path)
        if mode == "upgrade":
            return self._upgrade(os_name, install_path)
        return self._install(os_name, install_path)

    def _install(self, os_name: str, install_path: Path) -> bool:
        if utils1.ba_is_installed_by_fs(self.ctx, os_name):
            self.log.info("existing install found → upgrading")
            return self._upgrade(os_name, install_path)

        if not (utils1.fs_remove_tree(install_path, context=self.ctx) and utils1.fs_ensure_dir(install_path, context=self.ctx)):
            self.log.error("failed to prepare %s", install_path)
            return False

        artifact_path, new_version = utils1.artifacts_find_best(os_name, self._artifacts_base(), ARTIFACT_PATTERNS, context=self.ctx)
        if not artifact_path or not new_version:
            self.log.warning("no artifact for %s in %s", os_name, self._artifacts_base())
            return False
        
        self.log.warning("Artifact path: %s", artifact_path)
        self.log.warning("Artifact version (new): %s", new_version)

        if not self._deploy(os_name, install_path, artifact_path, new_version):
            self.log.error("install failed; attempting rollback")
            self._rollback(os_name, install_path)
            return False

        if not self._verify(os_name, install_path):
            self.log.error("post-install verify failed; rolling back")
            self._rollback(os_name, install_path)
            return False

        self.log.info("install complete: %s", new_version)
        return True

    def _upgrade(self, os_name: str, install_path: Path) -> bool:
        current_version = utils1.ba_version_read(self.ctx, os_name)
        artifact_path, candidate_version = utils1.artifacts_find_best(os_name, self._artifacts_base(), ARTIFACT_PATTERNS, context=self.ctx)
        if not artifact_path or not candidate_version:
            self.log.info("no candidate artifact — nothing to do")
            return True
        if not utils1.version_is_newer(current_version, candidate_version):
            self.log.info("already up to date (%s vs %s)", current_version, candidate_version)
            return True

        if not self._uninstall(os_name, install_path):
            self.log.error("uninstall failed; aborting upgrade")
            return False

        if not (utils1.fs_remove_tree(install_path, context=self.ctx) and utils1.fs_ensure_dir(install_path, context=self.ctx)):
            self.log.error("failed to re-create %s", install_path)
            return False

        if not self._deploy(os_name, install_path, artifact_path, candidate_version):
            self.log.error("upgrade install failed; rolling back")
            self._rollback(os_name, install_path)
            return False

        if not self._verify(os_name, install_path):
            self.log.error("post-upgrade verify failed; rolling back")
            self._rollback(os_name, install_path)
            return False

        self.log.info("upgrade complete: %s → %s", current_version, candidate_version)
        return True

    def _uninstall(self, os_name: str, install_path: Path) -> bool:
        if not utils1.ba_is_installed_by_fs(self.ctx, os_name):
            self.log.info("not installed — nothing to uninstall")
            return True
        # optional: stop service first
        ok = utils1.fs_remove_tree(install_path, context=self.ctx)
        if ok:
            self.log.info("removed %s", install_path)
        else:
            self.log.error("failed to remove %s", install_path)
        return ok

    def _artifacts_base(self) -> Path:
        return Path("./artifacts").resolve()

    def _deploy(self, os_name: str, install_path: Path, artifact_path: Path, version: str) -> bool:
        # install steps here
        
        artifact_path_extracted = os.path.join(artifact_path.parent, "extracted")

        self.log.info("Extracting binary: {}".format(artifact_path))

        utils1.extract_binary_package(src=artifact_path, dest=artifact_path_extracted, context=self.ctx)
        
        self.log.info("Extracted location: {}".format(artifact_path_extracted))

        # set password
        if "password" not in self.ctx["data"]:
            self.log.error("Password not provided. Setup requires password to continue installation")
            return False
        
        self.log.info("Password provided for installation")
        __password__ = self.ctx["data"]["password"]

        # update in put response xml file
        xmlfile = os.path.join(artifact_path_extracted, "input", "install_response_sample.xml")
        self.log.info("Considering install response xml file at: " + str(xmlfile))
        utils1.update_xml_value(file_path=xmlfile, xpath="./variables/variable[@name='ssl.password']", new_value=__password__)

        
        self.log.info("Starting installation")

        install_cmd = os.path.join(artifact_path_extracted, "install.bat") + " -s -input {respfile} -acceptLicense".format(respfile=xmlfile)
        self.log.debug("Install command: {}".format(install_cmd))
        
        print(utils1.exec_run(context=self.ctx, cmd=install_cmd))

        return True

        if not utils1.ba_version_write(self.ctx, version, os_name):
            return False
        self.log.info("deployed %s %s from %s", os_name, version, artifact_path.name)
        return True

    def _verify(self, os_name: str, install_path: Path) -> bool:
        if not utils1.fs_exists(install_path, context=self.ctx):
            return False
        if not utils1.ba_is_installed_by_fs(self.ctx, os_name):
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
            if m:
                candidates.append((p, m.group(1)))
        if len(candidates) < 2:
            return None
        candidates.sort(key=lambda t: utils1.version_parse(t[1]))
        return candidates[-2]