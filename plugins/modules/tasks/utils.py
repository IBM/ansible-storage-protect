from __future__ import annotations
"""
Small, reusable task primitives for orchestrations — with structured logging.

All functions accept an optional `context` carrying a `logger` (from the main
framework). When provided, functions log at DEBUG/INFO/WARNING/ERROR levels.
They also aim to return simple booleans or tiny dicts to be pipeline-friendly.

Naming convention: <area>_<action>
  os_*        : OS helpers
  fs_*        : filesystem helpers
  file_*      : file read/write helpers
  exec_*      : command/process helpers
  winreg_*    : Windows Registry helpers (no-ops on non-Windows)
  svc_*       : service helpers (systemd/Windows)
  pkg_*       : package manager helpers (RPM-focused example)
  version_*   : version parsing/compare helpers
  artifacts_* : artifact discovery helpers (find latest build for oskey)
  ba_*        : BA Server tiny utilities (paths/version)
"""

import json
import os
import platform
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional
import xml.etree.ElementTree as ET

# -----------------------------
# Logging helper
# -----------------------------

def _get_log(context: Optional[dict[str, Any]]):
    return (context or {}).get("logger") if isinstance(context, dict) else None


def _debug(context, msg, *args):
    log = _get_log(context)
    if log:
        log.debug(msg, *args)


def _info(context, msg, *args):
    log = _get_log(context)
    if log:
        log.info(msg, *args)


def _warning(context, msg, *args):
    log = _get_log(context)
    if log:
        log.warning(msg, *args)


def _error(context, msg, *args):
    log = _get_log(context)
    if log:
        log.error(msg, *args)

# -----------------------------
# OS helpers
# -----------------------------

def os_oskey(context: dict[str, Any]) -> str:
    fam = (context["os"]["family"] or "").lower()
    if fam == "windows":
        return "windows"
    if fam == "linux":
        distro_id = (context["os"].get("id") or "").lower()
        if distro_id in {"rhel", "centos", "rocky", "almalinux"}:
            return "rhel"
        return "linux"
    if fam == "aix":
        return "aix"
    return fam or "unknown"

# -----------------------------
# Filesystem helpers
# -----------------------------

def fs_disk_free_mb(path: str | Path, *, context: Optional[dict[str, Any]] = None) -> int:
    p = Path(path)
    du = shutil.disk_usage(p)
    free_mb = int(du.free / (1024 * 1024))
    _debug(context, "Disk free %s: %s MB", p, free_mb)
    return free_mb


def fs_require_free_mb(context: dict[str, Any], min_mb: int, path: str | Path) -> bool:
    free = fs_disk_free_mb(path, context=context)
    _info(context, "Free space at %s: %s MB (required: %s MB)", path, free, min_mb)
    ok = free >= min_mb
    if not ok:
        _error(context, "Insufficient free space at %s: have %s MB, need %s MB", path, free, min_mb)
    return ok


def fs_exists(path: str | Path, *, context: Optional[dict[str, Any]] = None) -> bool:
    exists = Path(path).exists()
    _debug(context, "Exists(%s) -> %s", path, exists)
    return exists


def fs_ensure_dir(path: str | Path, *, context: Optional[dict[str, Any]] = None) -> bool:
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        _debug(context, "Ensured dir %s", path)
        return True
    except Exception as e:
        _error(context, "Failed to ensure dir %s: %s", path, e)
        return False


def fs_remove_tree(path: str | Path, *, context: Optional[dict[str, Any]] = None) -> bool:
    try:
        p = Path(path)
        if p.exists():
            shutil.rmtree(p)
            _info(context, "Removed directory tree %s", p)
        else:
            _debug(context, "No-op remove; path not found: %s", p)
        return True
    except Exception as e:
        _error(context, "Failed to remove %s: %s", path, e)
        return False

def extract_binary_package(src, dest, *, context: Optional[dict[str, Any]] = None):
        """Extract tarball and ensure RPMs exist"""

        if platform.system().lower() == "windows":
            _info(context, "Extracting binary package for windows")
            _debug(context, "Source package: {}".format(src))
            _debug(context, "Destination location: {}".format(dest))
            if (os.path.exists(dest)):
                cmd=f"powershell -Command \"Remove-Item -Path '{dest}' -Recurse -Force -ErrorAction SilentlyContinue\""
                exec_run(context=context, cmd=cmd)

            cmd=f"\"{src}\" -q -d \"{dest}\""
            exec_run(context=context, cmd=cmd)
            return True
        else:
            _error(context, "Extract binary for platform {} is not implemented".format(platform.system()))
            return False



def update_xml_value(file_path, xpath, new_value):
    tree = ET.parse(file_path)
    root = tree.getroot()

    element = root.find(xpath)
    if element is not None:
        element.set('value', str(new_value))
        tree.write(file_path, encoding='UTF-8', xml_declaration=True)
        print(f"Updated {xpath} to {new_value}")
    else:
        print(f"No element found for XPath: {xpath}")



# -----------------------------
# File read/write helpers
# -----------------------------

def file_read_text(path: str | Path, default: str = "", *, context: Optional[dict[str, Any]] = None) -> str:
    p = Path(path)
    try:
        data = p.read_text(encoding="utf-8")
        _debug(context, "Read %d bytes from %s", len(data), p)
        return data
    except Exception as e:
        if default == "":
            _warning(context, "Unable to read %s: %s", p, e)
        else:
            _info(context, "Unable to read %s (%s); using default", p, e)
        return default


def file_write_text(path: str | Path, content: str, *, context: Optional[dict[str, Any]] = None) -> bool:
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        _debug(context, "Wrote %d bytes to %s", len(content), p)
        return True
    except Exception as e:
        _error(context, "Failed writing %s: %s", path, e)
        return False

# -----------------------------
# Exec helpers
# -----------------------------

def exec_run(context: dict[str, Any], cmd: list[str] | str, *, shell: bool = False, timeout: Optional[int] = None,
             check: bool = False, capture_output: bool = True) -> dict[str, Any]:
    log = _get_log(context)
    if context.get("dry_run"):
        if log:
            log.info("[DRY-RUN] Would run: %s", cmd)
        return {"rc": 0, "stdout": "", "stderr": "", "cmd": cmd, "dry_run": True}
    try:
        completed = subprocess.run(
            cmd,
            shell=shell,
            timeout=timeout,
            check=check,
            capture_output=capture_output,
            text=True,
        )
        if completed.returncode == 0:
            _info(context, "Exec OK: %s", cmd)
        else:
            _warning(context, "Exec rc=%s: %s\nstderr: %s", completed.returncode, cmd, completed.stderr)
        return {"rc": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr, "cmd": cmd}
    except subprocess.CalledProcessError as e:
        _error(context, "Exec failed rc=%s: %s\nstderr: %s", e.returncode, cmd, e.stderr)
        return {"rc": e.returncode, "stdout": e.stdout, "stderr": e.stderr, "cmd": cmd}
    except Exception as e:
        _error(context, "Exec exception for %s: %s", cmd, e)
        return {"rc": 127, "stdout": "", "stderr": str(e), "cmd": cmd}

# -----------------------------
# Windows registry helpers
# -----------------------------

def winreg_query_value(root: str, subkey: str, name: str, *, context: Optional[dict[str, Any]] = None) -> Optional[str]:
    if platform.system().lower() != "windows":
        _debug(context, "winreg_query_value skipped (non-Windows)")
        return None
    try:
        import winreg  # type: ignore
        root_map = {
            "HKLM": winreg.HKEY_LOCAL_MACHINE,
            "HKCU": winreg.HKEY_CURRENT_USER,
            "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
            "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
        }
        hive = root_map[root]
        with winreg.OpenKey(hive, subkey) as k:
            val, _ = winreg.QueryValueEx(k, name)
            _debug(context, "winreg %s/%s:%s -> %s", root, subkey, name, val)
            return str(val)
    except FileNotFoundError:
        _warning(context, "winreg key not found: %s/%s:%s", root, subkey, name)
        return None
    except Exception as e:
        _error(context, "winreg query error for %s/%s:%s — %s", root, subkey, name, e)
        return None

# -----------------------------
# Service helpers (basic)
# -----------------------------

def svc_stop(context: dict[str, Any], name: str) -> bool:
    if platform.system().lower() == "windows":
        r = exec_run(context, ["sc", "stop", name])
        ok = r["rc"] == 0
        if not ok:
            _warning(context, "Failed to stop service %s (rc=%s)", name, r["rc"])
        return ok
    r = exec_run(context, ["systemctl", "stop", name])
    ok = r["rc"] == 0
    if not ok:
        _warning(context, "Failed to stop service %s (rc=%s)", name, r["rc"])
    return ok


def svc_start(context: dict[str, Any], name: str) -> bool:
    if platform.system().lower() == "windows":
        r = exec_run(context, ["sc", "start", name])
        ok = r["rc"] == 0
        if not ok:
            _warning(context, "Failed to start service %s (rc=%s)", name, r["rc"])
        return ok
    r = exec_run(context, ["systemctl", "start", name])
    ok = r["rc"] == 0
    if not ok:
        _warning(context, "Failed to start service %s (rc=%s)", name, r["rc"])
    return ok

# -----------------------------
# Package helpers (RPM example)
# -----------------------------

def pkg_rpm_is_installed(context: dict[str, Any], pkg: str) -> bool:
    r = exec_run(context, ["rpm", "-q", pkg])
    ok = r["rc"] == 0
    _info(context, "RPM installed? %s -> %s", pkg, ok)
    return ok

# -----------------------------
# Version helpers
# -----------------------------

def version_parse(v: str) -> tuple:
    parts = re.split(r"[^0-9A-Za-z]+", v)
    norm = []
    for p in parts:
        if p.isdigit():
            norm.append((0, int(p)))
        elif p:
            norm.append((1, p))
    return tuple(norm)


def version_is_newer(current: Optional[str], candidate: str) -> bool:
    if not current:
        _debug(None, "version_is_newer: no current -> True")
        return True
    newer = version_parse(candidate) > version_parse(current)
    return newer

# -----------------------------
# Artifact helpers
# -----------------------------

def artifacts_find_best(
    oskey: str,
    base_dir: str | Path,
    patterns: dict[str, str | re.Pattern],
    *,
    context: Optional[dict[str, Any]] = None,
    recursive: bool = False,
    case_insensitive: bool = True,
) -> tuple[Optional[Path], Optional[str]]:
    base = Path(base_dir) / oskey
    if not base.exists():
        _warning(context, "Artifacts base not found: %s", base)
        return None, None

    # Get pattern by oskey (accept str or compiled); default if missing
    raw = (
        patterns.get(oskey)
        or patterns.get(oskey.lower())
        or patterns.get(oskey.upper())
    )
    if isinstance(raw, re.Pattern):
        flags = raw.flags | (re.IGNORECASE if case_insensitive else 0)
        pat = re.compile(raw.pattern, flags)
    else:
        expr = str(raw) if raw else r"ba[-_]?server[-_]?([0-9][\w\.-]+)\..+$"
        flags = re.IGNORECASE if case_insensitive else 0
        pat = re.compile(expr, flags)

    # Fallback version finder if the main pattern has no capture group
    version_finder = re.compile(r"(\d+(?:[._-]\d+)*)", re.IGNORECASE)

    files = base.rglob("*") if recursive else base.iterdir()
    matches: list[tuple[Path, str]] = []

    for p in files:
        if not p.is_file():
            continue
        m = pat.search(p.name)
        if not m:
            continue

        # Safe group extraction
        ver: Optional[str] = None
        try:
            if m.lastindex and m.lastindex >= 1:
                ver = m.group(1)
        except IndexError:
            # Pattern matched but didn’t define group(1)
            ver = None

        if not ver:
            # Fallback: try to infer version from filename
            fm = version_finder.search(p.stem)
            ver = fm.group(1) if fm else p.stem  # last resort: whole stem

        matches.append((p, ver))
        _debug(context, "artifact match: %s -> %s", p.name, ver)

    if not matches:
        _warning(
            context,
            "No artifacts matched for %s in %s (pattern=%s, ci=%s)",
            oskey, base, pat.pattern, bool(pat.flags & re.IGNORECASE),
        )
        return None, None

    # Sort by parsed version
    try:
        matches.sort(key=lambda t: version_parse(t[1]))
    except Exception as e:
        _warning(context, "Version sort fallback due to: %s; using lexical", e)
        matches.sort(key=lambda t: t[1])

    best = matches[-1]
    _info(context, "Artifact matched for %s -> %s (%s)", oskey, best[0].name, best[1])
    return best



# -----------------------------
# BA Server micro-utilities (tiny building blocks)
# -----------------------------

def ba_install_dir(context: dict[str, Any], oskey: Optional[str] = None) -> Path:
    oskey = oskey or os_oskey(context)
    default = {
        "windows": Path(os.getenv("BA_INSTALL_DIR_WINDOWS", r"C:\\Program Files\\BA Server")),
        "rhel": Path(os.getenv("BA_INSTALL_DIR_RHEL", "/opt/ba-server")),
        "linux": Path(os.getenv("BA_INSTALL_DIR_LINUX", "/opt/ba-server")),
        "aix": Path(os.getenv("BA_INSTALL_DIR_AIX", "/opt/ba-server")),
    }
    p = default.get(oskey) or Path("/opt/ba-server")
    _debug(context, "ba_install_dir(%s) -> %s", oskey, p)
    return p


def ba_version_read(context: dict[str, Any], oskey: Optional[str] = None) -> Optional[str]:
    install_dir = ba_install_dir(context, oskey)
    f = install_dir / "VERSION"
    try:
        v = f.read_text(encoding="utf-8").strip()
        _debug(context, "Read VERSION=%s from %s", v, f)
        return v
    except Exception as e:
        _warning(context, "VERSION not readable at %s: %s", f, e)
        return None


def ba_version_write(context: dict[str, Any], version: str, oskey: Optional[str] = None) -> bool:
    install_dir = ba_install_dir(context, oskey)
    try:
        install_dir.mkdir(parents=True, exist_ok=True)
        (install_dir / "VERSION").write_text(version, encoding="utf-8")
        _debug(context, "Wrote VERSION=%s to %s", version, install_dir / "VERSION")
        return True
    except Exception as e:
        _error(context, "Failed to write VERSION at %s: %s", install_dir, e)
        return False


def ba_binary_path(context: dict[str, Any], oskey: Optional[str] = None) -> Path:
    install_dir = ba_install_dir(context, oskey)
    p = install_dir / ("ba-server.exe" if (os_oskey(context) == "windows") else "bin/ba-server")
    _debug(context, "ba_binary_path -> %s", p)
    return p


def ba_is_installed_by_fs(context: dict[str, Any], oskey: Optional[str] = None) -> bool:
    exists = ba_binary_path(context, oskey).exists()
    _info(context, "Installed by FS check -> %s", exists)
    return exists