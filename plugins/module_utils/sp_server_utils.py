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

import os
import sys
import json
import getpass
import platform
import re
import shutil
import shlex
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Mapping
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement, ElementTree
from xml.dom import minidom
import sp_server_constants
import platform
import socket


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

def os_oskey(context: Dict[str, Any]) -> Dict[str, str]:
    os_data = context.get("os", {}) or {}
    family = (os_data.get("family") or "").lower()
    distro_id = (os_data.get("id") or "").lower()

    # Normalize OS family
    if family == "windows":
        os_family = "windows"
    elif family == "linux":
        os_family = "linux"
    elif family in {"aix", "unix"}:
        os_family = family
    else:
        os_family = family or "unknown"

    # Determine distro / specific OS name
    if os_family == "linux":
        # Normalize common RHEL-family distros under "rhel"
        rhel_like = {"rhel", "centos", "rocky", "almalinux", "oraclelinux"}
        if distro_id in rhel_like:
            os_name = "rhel"
        else:
            os_name = distro_id or "linux"
    else:
        # For non-Linux OS, prefer reported id; fallback to family
        os_name = distro_id or os_family

    return {"os": os_family, "osname": os_name}

# ---------- System discovery ----------

def _read_linux_os_release() -> Dict[str, str]:
    path = "/etc/os-release"
    data: Dict[str, str] = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                data[k] = v.strip().strip('"')
    except Exception:
        pass
    return data


def get_os_info() -> Dict[str, Any]:
    sysname = platform.system() or "Unknown"
    info: Dict[str, Any] = {"family": sysname}

    if sysname == "Linux":
        try:
            import distro  # type: ignore
            info.update(
                {
                    "name": distro.name(pretty=True),
                    "id": distro.id(),
                    "version": distro.version(best=True),
                    "version_parts": {
                        "major": distro.major_version(),
                        "minor": distro.minor_version(),
                    },
                    "like": distro.like(),
                    "codename": distro.codename(),
                }
            )
        except Exception:
            osr = _read_linux_os_release()
            info.update(
                {
                    "name": osr.get("PRETTY_NAME") or "Linux",
                    "id": osr.get("ID"),
                    "version": osr.get("VERSION") or osr.get("VERSION_ID"),
                    "like": osr.get("ID_LIKE"),
                    "codename": osr.get("VERSION_CODENAME"),
                }
            )
        info["kernel"] = platform.release()
        info["arch"] = platform.machine()

    elif sysname == "Windows":
        win_ver = platform.win32_ver()
        info.update(
            {
                "version": win_ver[0],
                "build": platform.version(),
                "release": platform.release(),
                "arch": platform.machine(),
            }
        )

    elif sysname == "Darwin":
        mac_ver = platform.mac_ver()
        info.update(
            {
                "name": "macOS",
                "version": mac_ver[0],
                "release": platform.release(),
                "arch": platform.machine(),
            }
        )
    else:
        info.update({
            "version": platform.version(),
            "release": platform.release(),
            "arch": platform.machine(),
        })

    return info


def _get_memory_info() -> Dict[str, Any]:
    try:
        import psutil  # type: ignore
        vm = psutil.virtual_memory()
        return {
            "total": vm.total,
            "available": getattr(vm, "available", None),
            "used": vm.used,
            "free": vm.free,
            "percent": vm.percent,
        }
    except Exception:
        if os.name == "posix":
            try:
                meminfo: Dict[str, int] = {}
                with open("/proc/meminfo", "r", encoding="utf-8") as f:
                    for line in f:
                        if ":" in line:
                            k, v = line.split(":", 1)
                            parts = v.strip().split()
                            if parts and parts[0].isdigit():
                                meminfo[k] = int(parts[0]) * 1024  # kB -> bytes
                total = meminfo.get("MemTotal")
                free = meminfo.get("MemFree")
                available = meminfo.get("MemAvailable", free)
                used = total - available if total and available else None
                percent = (used / total * 100) if used and total else None
                return {
                    "total": total,
                    "available": available,
                    "used": used,
                    "free": free,
                    "percent": percent,
                }
            except Exception:
                pass
        return {}


def get_system_info() -> Dict[str, Any]:
    uname = platform.uname()
    try:
        user = getpass.getuser()
    except Exception:
        user = None

    try:
        if os.name == "nt":
            root = Path(os.getcwd().split(":")[0] + ":\\")
        else:
            root = Path("/")
        du = shutil.disk_usage(root)
        disk = {"total": du.total, "used": du.used, "free": du.free}
    except Exception:
        disk = {}

    try:
        load_avg = os.getloadavg()  # type: ignore[attr-defined]
    except Exception:
        load_avg = None

    return {
        "hostname": socket.gethostname(),
        "fqdn": socket.getfqdn(),
        "user": user,
        "python": sys.version.split(" ")[0],
        "implementation": platform.python_implementation(),
        "machine": uname.machine,
        "processor": uname.processor,
        "cpu_count": os.cpu_count(),
        "load_avg": load_avg,
        "disk_root": disk,
        "memory": _get_memory_info(),
    }


# -----------------------------
# Filesystem helpers
# -----------------------------

def fs_disk_free_mb(path: Path, *, context: Optional[dict[str, Any]] = None) -> int:
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

        _info(context, "Extracting binary package for windows")
        _debug(context, "Source package: {}".format(src))
        _debug(context, "Destination location: {}".format(dest))

        cmd = ""
        if platform.system().lower() == "windows":
            
            if (os.path.exists(dest)):
                cmd=f"powershell -Command \"Remove-Item -Path '{dest}' -Recurse -Force -ErrorAction SilentlyContinue\""
                exec_run(context=context, cmd=cmd)

            cmd=f"\"{src}\" -q -d \"{dest}\""

        else:
            if (str(dest).strip() != "" and str(dest).strip() != "/" and os.path.exists(dest)):
                cmd = f"sudo rm -rf {dest}"
                exec_run(context=context, cmd=cmd)

            _info(context=context, msg="Providing execute permissions to binary: " + str(src))
            cmd = f"sudo chmod +x {src}"
            prem_resp = exec_run(context=context, cmd=cmd)
            _info(context=context, msg=prem_resp)
            cmd=f"{src} -q -d {dest}"
            
        
        try:
            resp = exec_run(context=context, cmd=cmd)
            return resp["rc"] == 0
        except Exception as e:
            _error(e)
            return False



def update_package_offering(xml_filepath: str, install_data: Dict[str, Dict[str, Any]]) -> None:

    tree = ET.parse(xml_filepath)
    root = tree.getroot()

    # Find or create <install> element
    install_elem = root.find("install")
    if install_elem is None:
        install_elem = ET.SubElement(root, "install")
        install_elem.set("modify", "false")

    # Clear existing <offering> elements under <install>
    for child in list(install_elem):
        if child.tag == "offering":
            install_elem.remove(child)

    # Add new <offering> elements from install_data
    for _, comp in install_data.items():
        offering_attrib = {
            "id": str(comp.get("id", "")),
            "profile": str(comp.get("profile", "")),
            "features": str(comp.get("features", "")),
            "installFixes": "none",
        }
        ET.SubElement(install_elem, "offering", attrib=offering_attrib)

    # Write back to file, preserving XML declaration
    tree.write(xml_filepath, encoding="UTF-8", xml_declaration=True)


def update_xml_value(file_path, xpath, new_value):
    tree = ET.parse(file_path)
    root = tree.getroot()

    element = root.find(xpath)
    if element is not None:
        element.set('value', str(new_value))
        tree.write(file_path, encoding='UTF-8', xml_declaration=True)
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

def replace_text_in_file(file_path: str, old_text: str, new_text: str) -> bool:
    try:
        content = file_read_text(path=file_path)
        updated_content = content.replace(old_text, new_text)

        file_write_text(path=file_path, content=updated_content)

        return True
    except Exception:
        return False



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

# -----------------------
# JSON ops
# -----------------------
def read_json_file(path: str | Path, default: str = None, *, context: Optional[dict[str, Any]] = None) -> dict:
    p = Path(path)
    try:
        if not p.exists() or not p.is_file():
            _error(context=context, msg="File not found")
            return None
        else:
            raw_data = p.read_text(encoding="utf-8")
            _debug(context, "Read %d bytes from %s", len(raw_data), p)
            return json.loads(raw_data)
    except Exception as e:
        _error(context=context, msg="Error reading json file: " + str(e))
        return default

# -----------------------------
# Exec helpers
# -----------------------------

def exec_run(context: dict[str, Any], cmd: list[str] | str, *, shell: bool = False, timeout: Optional[int] = None,
             check: bool = False, capture_output: bool = True) -> dict[str, Any]:
    # split for linux
    os_name = os_oskey(context=context)["os"]
    if (os_name.lower() == "linux" and type(cmd) is not List):
        cmd = shlex.split(cmd)
        # cmd = cmd.split(" ")
    if (os_name.lower() != "linux" and type(cmd) is List):
        cmd = " ".join(cmd)

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
        r = exec_run(context, "sc stop " + str(name))
        ok = r["rc"] == 0
        if not ok:
            _warning(context, "Failed to stop service %s (rc=%s)", name, r["rc"])
        return ok
    r = exec_run(context, "systemctl stop " + str(name))
    ok = r["rc"] == 0
    if not ok:
        _warning(context, "Failed to stop service %s (rc=%s)", name, r["rc"])
    return ok


def svc_start(context: dict[str, Any], name: str) -> bool:
    if platform.system().lower() == "windows":
        r = exec_run(context, "sc start " + str(name))
        ok = r["rc"] == 0
        if not ok:
            _warning(context, "Failed to start service %s (rc=%s)", name, r["rc"])
        return ok
    r = exec_run(context, "systemctl start " + str(name))
    ok = r["rc"] == 0
    if not ok:
        _warning(context, "Failed to start service %s (rc=%s)", name, r["rc"])
    return ok

# -----------------------------
# Package helpers (RPM example)
# -----------------------------

def pkg_rpm_is_installed(context: dict[str, Any], pkg: str) -> bool:
    r = exec_run(context, "rpm -q " + str(pkg))
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

def _parse_version(version_str: str) -> Tuple[int, ...]:
    """Convert dotted version string '1.2.3.4' → (1,2,3,4) safely."""
    parts = version_str.split(".")
    nums = []
    for p in parts:
        try:
            nums.append(int(p))
        except ValueError:
            nums.append(0)
    return tuple(nums)


def find_installer(
    oskey: str,
    base_dir: str,
    case_insensitive: bool = False,
    version: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Artifact naming pattern:
        <version>-<name>-<platform>.exe
        <version>-<name>-<platform>.bin

    Example:
        1.2.3.4-company-product-WindowsX64.exe
    """
    # Resolve extension
    ok = oskey.lower()
    print("="*5)
    print(ok)
    if ok in ("windows", "win"):
        ext = ".exe"
    elif ok in ("linux", "lin"):
        ext = ".bin"
    elif ok in ("rhel", "centos"):
        ext = ".bin"
    else:
        ext = oskey if oskey.startswith(".") else f".{oskey}"

    base_path = Path(base_dir)
    if not base_path.is_dir():
        return {
            "status": False,
            "message": f"Base directory does not exist: {base_dir}",
            "data": {"installerfile": None, "other_files": []},
        }

    # Gather candidates
    candidates = []
    for entry in base_path.iterdir():
        if not entry.is_file():
            continue
        if case_insensitive:
            if entry.suffix.lower() == ext.lower():
                candidates.append(entry)
        else:
            if entry.suffix == ext:
                candidates.append(entry)

    if not candidates:
        return {
            "status": False,
            "message": f"No files with extension '{ext}' found in {base_dir}",
            "data": {"installerfile": None, "other_files": []},
        }

    # Extract version from prefix before first hyphen
    def extract_version_str(path: Path) -> Optional[str]:
        filename = path.name
        name_no_ext = filename[: -len(path.suffix)] if path.suffix else filename
        if "-" not in name_no_ext:
            return None
        return name_no_ext.split("-", 1)[0]

    chosen = None
    others: List[Path] = []

    if version is not None:

        def matches_version(path: Path) -> bool:
            name = path.name
            name_cmp = name.lower() if case_insensitive else name
            prefix = f"{version}-"
            prefix_cmp = prefix.lower() if case_insensitive else prefix
            return name_cmp.startswith(prefix_cmp)

        matches = [p for p in candidates if matches_version(p)]

        if not matches:
            return {
                "status": False,
                "message": f"No installer found for version '{version}'.",
                "data": {"installerfile": None, "other_files": []},
            }

        matches.sort(key=lambda p: p.name)
        chosen = matches[0]
        others = matches[1:]
        msg = f"Found installer for version '{version}'."

    else:
        # No version → choose newest version
        versioned = []
        for p in candidates:
            vstr = extract_version_str(p)
            if not vstr:
                continue
            versioned.append((p, vstr, _parse_version(vstr)))

        if not versioned:
            # fallback: lexicographically last file
            candidates.sort(key=lambda p: p.name)
            chosen = candidates[-1]
            others = candidates[:-1]
            msg = "No version data found; selected last file by name."
        else:
            # sort by parsed version descending
            versioned.sort(key=lambda x: x[2], reverse=True)
            chosen = versioned[0][0]
            others = [item[0] for item in versioned[1:]]
            msg = f"Selected latest version '{versioned[0][1]}'"

    return {
        "status": chosen is not None,
        "message": msg if chosen else "No installer selected.",
        "data": {
            "installerfile": str(chosen) if chosen else None,
            "other_files": [str(o) for o in others],
        },
    }



def artifacts_find_best_old(
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


def append_line_to_file(path: str, line: str) -> bool:
    """
    Safely append a line to a file if it does not already exist.
    """
    try:
        # Read and check if line already present
        if os.path.exists(path):
            with open(path, "r") as f:
                content = f.read()
            if line in content:
                return True

        # Append line
        with open(path, "a") as f:
            f.write(line + "\n")

        return True
    except Exception as e:
        print(f"append_line_to_file failed: {e}")
        return False


def ensure_dir(path: str, owner: str = None, group: str = None, mode: str = None, context=None) -> bool:
    """
    Wrapper around fs_ensure_dir that also applies owner/group/mode.
    Mirrors Ansible 'file: state=directory'.
    """
    ok = fs_ensure_dir(path, context=context)
    if not ok:
        return False

    try:
        if owner or group:
            shutil.chown(path, user=owner, group=group)

        if mode:
            os.chmod(path, int(mode, 8))

        _debug(context, f"Directory ensured with permissions: {path}")
        return True

    except Exception as e:
        _error(context, f"Failed to set permissions on {path}: {e}")
        return False

def list_files(path: str) -> list[str]:
    try:
        return [os.path.join(path, f) for f in os.listdir(path)]
    except Exception:
        return []

def remove_file(path: str) -> bool:
    try:
        if os.path.isfile(path):
            os.remove(path)
        return True
    except Exception:
        return False
    
def copy_file(src: str, dest: str, owner=None, group=None, mode=None) -> bool:
    try:
        shutil.copy2(src, dest)
        if owner or group:
            shutil.chown(dest, user=owner, group=group)
        if mode:
            os.chmod(dest, int(mode, 8))
        return True
    except Exception as e:
        return False

def update_lines_in_file(path: str, lines: list[str]) -> bool:
    try:
        existing = ""
        if os.path.exists(path):
            with open(path, "r") as f:
                existing = f.read()

        with open(path, "a") as f:
            for ln in lines:
                if ln not in existing:
                    f.write(ln + "\n")

        return True
    except Exception:
        return False

def touch_file(path: str, owner=None, group=None) -> bool:
    try:
        Path(path).touch(exist_ok=True)
        if owner or group:
            shutil.chown(path, user=owner, group=group)
        return True
    except Exception:
        return False

def chown(context, path: str, owner: str = None, group: str = None) -> bool:
    """
    Change owner/group of a file or directory.
    Mirrors Ansible's 'owner' and 'group' behavior.
    """
    try:
        shutil.chown(path, user=owner, group=group)
        _debug(context, f"chown applied: {path} -> {owner}:{group}")
        return True
    except Exception as e:
        _error(context, f"Failed chown on {path}: {e}")
        return False

def chmod(context, path: str, mode: str) -> bool:
    """
    Update file permissions; mode string like '0644'.
    """
    try:
        os.chmod(path, int(mode, 8))
        _debug(context, f"chmod applied: {path} -> {mode}")
        return True
    except Exception as e:
        _error(context, f"Failed chmod on {path}: {e}")
        return False

def file_ensure_line(path: str, line: str, context=None) -> bool:
    """
    Ensures that a specific line exists in a file.
    Equivalent to Ansible's lineinfile (basic replacement).
    """
    try:
        # Create file if missing
        if not os.path.exists(path):
            with open(path, "w") as f:
                f.write(line + "\n")
            _debug(context, f"Created file and added line: {path}")
            return True

        # Read contents
        with open(path, "r") as f:
            lines = f.read().splitlines()

        # Do nothing if already present
        if line in lines:
            _debug(context, f"Line already present in {path}")
            return True

        # Append the line
        with open(path, "a") as f:
            f.write(line + "\n")

        _debug(context, f"Line appended to {path}")
        return True

    except Exception as e:
        _error(context, f"Failed to ensure line in {path}: {e}")
        return False

# -----------------------------
# BA Server micro-utilities (tiny building blocks)
# -----------------------------

def ba_install_dir(context: dict[str, Any], oskey: Optional[str] = None) -> Path:
    oskey = oskey or os_oskey(context)["os"]
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
    p = install_dir / ("ba-server.exe" if (os_oskey(context)["os"] == "windows") else "bin/ba-server")
    _debug(context, "ba_binary_path -> %s", p)
    return p


def ba_is_installed(context: dict[str, Any], oskey: Optional[str] = None, install_data: Dict[str, Dict[str, Any]] = {}) -> dict:
    print(install_data)

    ret_data = {"status": True, "message": "", "data": {"installedpackages": {}}}

    imcl_path = None

    if oskey.lower() == "windows":
        imcl_path = context["ansible_vars_data"].get("install_location_im", "/opt/IBM/InstallationManager")
        
        if imcl_path is None:
            # look up in registry
            imcl_path  = winreg_query_value(root="HKLM", subkey="SOFTWARE\\IBM\\Installation Manager", name="location")
    else:
        imcl_path = context["ansible_vars_data"].get("install_location_im", "/opt/IBM/InstallationManager")
    
    IMCL_BIN_PATH = os.path.join(imcl_path, "eclipse", "tools", "imcl")
    
    _debug(context=context, msg="IMCL Bin Path: {}".format(IMCL_BIN_PATH))

    if (not fs_exists(path=IMCL_BIN_PATH, context=context)):
        _msg = "IMCL not found. Considering not installed"
        _info(context=context, msg=_msg)
        ret_data["status"] = False
        ret_data["message"] = _msg
        return ret_data


    cmd = IMCL_BIN_PATH + " listInstalledPackages"
    resp = exec_run(context=context, cmd=cmd)

    _info(context=context, msg=resp)

    if "rc" not in resp:
        ret_data["status"] = False
        ret_data["message"] = "Error while fetching list of installed packages from IMCL."
        return ret_data
    else:
        if resp["rc"] == 0:
            # render stdout and list
            stdlines = resp["stdout"].split("\n")

            for line in stdlines:
                # for offerings_components in install_data:
                package_id = install_data["id"]
                package_version = None

                if str(package_id).lower() in str(line).lower():
                    # Note: not needed as upgrade is upgrade
                    ret_data["status"] = True

                    package_version = str(line).replace(package_id + "_", "")

                    _msg = "IMCL identified package {pn} with version {pv} installed".format(pn=package_id, pv=package_version)
                    _info(context=context, msg=_msg)

                    if "installedpackages" not in ret_data["data"]:
                        ret_data["data"]["installedpackages"] = {}

                    ret_data["data"]["installedpackages"][package_id] = package_version

                if ret_data["status"]:
                    ret_data["message"] = "SP Server packages are installed: " + str(len(ret_data["data"]["installedpackages"]))
                return ret_data
            else:
                ret_data["status"] = False
                ret_data["message"] = "SP Server packages not installed"
                return ret_data
        else:
            ret_data["status"] = False
            ret_data["message"] = "Error while fetching list of installed packages: " + str(resp["rc"])
            _error(context, "Error while fetching list of installed packages: " + str(resp["rc"]))
            _error(context, resp)
            return ret_data

def find_ba_server_password(context: dict[str, Any], args):
    pwd_in_envvar = os.getenv("SP_BA_SERVER_PASSWORD", None)

    if (pwd_in_envvar is not None):
        return pwd_in_envvar
    elif (args.serverpassword is not None):
        return args.serverpassword
    else:
        return None




class AgentInputXMLBuilder:
    """
    Build IBM Installation Manager response XMLs for install/upgrade/uninstall.

    Usage (simple):
        builder = AgentInputXMLBuilder(constants=constants)
        builder.generate("example-output.xml", inputdata, mode="install")

    Usage (reusing internals elsewhere):
        root = builder.build_install_tree(inputdata)
        xml_bytes = builder.to_pretty_xml_bytes(root)
        builder.write_xml("file.xml", xml_bytes)
    """

    def __init__(self, context: dict[str, Any], *, default_repository_location: str = "repository"):
        """
        Parameters
        ----------
        constants : Any
            Module or object exposing:
              - offerings_metadata: Dict[str, Dict[str, str]]
              - preferences: Dict[str, str]
        default_repository_location : str
            Default path/URL for <server><repository location="..."/>
        """
        self.constants = sp_server_constants
        self.default_repository_location = default_repository_location
        self.os_family = str(get_os_info()["family"]).lower()

    # ---------- Public, reusable helpers (you can call these directly) ----------

    @staticmethod
    def text_bool(x: bool) -> str:
        return "true" if bool(x) else "false"

    @staticmethod
    def to_pretty_xml_bytes(elem: ET.Element) -> bytes:
        """Return pretty-printed XML bytes (UTF-8)."""
        rough = ET.tostring(elem, encoding="utf-8")  # FIXED
        reparsed = minidom.parseString(rough)
        return reparsed.toprettyxml(indent="  ", encoding="utf-8")

    @staticmethod
    def write_xml(filename: str, xml_bytes: bytes) -> str:
        with open(filename, "wb") as f:
            f.write(xml_bytes)
        return filename

    # Leaf builders (fully reusable in other contexts)

    def add_repository(self, root: Element, location: Optional[str] = None) -> None:
        """Add <server><repository location='...'/></server>."""
        server = SubElement(root, "server")
        SubElement(server, "repository", {"location": location or self.default_repository_location})

    def add_preferences(self, root: Element, preferences: Mapping[str, str]) -> None:
        """Add <preference name='...' value='...'/> for each pair."""
        for name, value in preferences.items():
            SubElement(root, "preference", {"name": str(name), "value": str(value)})

    def add_offering(
        self,
        parent: Element,
        offering_meta: Mapping[str, Any],
        *,
        selected: Optional[bool] = None,
    ) -> None:
        """
        Add a single <offering .../> to parent.

        offering_meta expected keys:
          - id (str) [required]
          - profile (str) [recommended]
          - features (str, optional)
          - installFixes (str, optional; default 'none')
        """
        attrs = {
            "profile": offering_meta.get("profile", ""),
            "id": offering_meta["id"],
            "installFixes": offering_meta.get("installFixes", "none"),
        }
        if offering_meta.get("features"):
            attrs["features"] = offering_meta["features"]
        if selected is not None:
            attrs["selected"] = self.text_bool(selected)
        SubElement(parent, "offering", attrs)

    # ---------- Tree builders for each mode (also reusable) ----------

    def build_install_tree(self, inputdata: Mapping[str, Any]) -> Element:
        """
        Build the <agent-input> tree for 'install' mode.

        Expected keys in inputdata (subset is fine):
          - profile_id (str)
          - install_location (str)
          - repository_location (str)
          - secure_port (int|str)
          - ssl_password (str)
          - license_value (str)
          - offerings (Dict[str, bool])
        """
        profile_id = inputdata.get("profile_id", "IBM Tivoli Storage Manager")
        install_dir = inputdata.get("install_location_tsm", "/opt/tivoli/tsm")
        license_value = inputdata.get("license_value", "")
        secure_port = str(inputdata.get("secure_port", "11090"))
        ssl_password = inputdata.get("ssl_password", "")

        root = Element("agent-input", {"clean": "true", "temporary": "true"})

        # variables
        variables = SubElement(root, "variables")
        SubElement(variables, "variable", {"name": "license.selection", "value": license_value})
        SubElement(variables, "variable", {"name": "port", "value": secure_port})
        SubElement(variables, "variable", {"name": "ssl.password", "value": ssl_password})
        SubElement(variables, "variable", {"name": "enable.SP800131a", "value": ""})

        v_install = SubElement(variables, "variable", {"name": "install.dir", "value": install_dir})
        # Optional Windows override (harmless on non-Windows)
        SubElement(
            v_install,
            "if",
            {"name": "platform:os", "equals": "win32", "value": r"C:\Program Files\Tivoli\TSM"},
        )

        # repository
        # repository_location = inputdata.get("sp_server_install_dest_win", "C:/temp/baserver" ) if self.os_family == "windows" else inputdata.get("sp_server_install_dest_lin", "/tmp/baserver")
        # repository_location = repository_location + "/artifacts/extracted/repository"
        repository_location = "repository"
        self.add_repository(root, repository_location)

        # profile data keys that align with common IM response usage
        profile = SubElement(root, "profile", {"id": profile_id, "installLocation": "${install.dir}"})
        SubElement(profile, "data", {
            "key": "user.license,com.tivoli.dsm.server",
            "value": "${license.selection}",
        })
        SubElement(profile, "data", {
            "key": "user.securePortNumber,com.tivoli.dsm.gui.offering",
            "value": "${port}",
        })
        SubElement(profile, "data", {
            "key": "user.enableSP800_131,com.tivoli.dsm.gui.offering",
            "value": "${enable.SP800131a}",
        })
        SubElement(profile, "data", {
            "key": "user.SSL_PASSWORD",
            "value": "${ssl.password}",
        })

        # offerings (selected=true for install)
        install = SubElement(root, "install", {"modify": "false"})
        self._add_selected_offerings_block(install, inputdata.get("offerings", {}), selected=True)

        # preferences
        self.add_preferences(root, self.constants.preferences)
        return root

    def build_upgrade_tree(self, inputdata: Mapping[str, Any]) -> Element:
        """
        Build the <agent-input> tree for 'upgrade' mode.
        Mirrors 'install' structure without variables/profile (typical update scenario).
        """
        root = Element("agent-input", {"clean": "true", "temporary": "true"})
        self.add_repository(root, inputdata.get("repository_location"))

        install = SubElement(root, "install", {"modify": "false"})
        self._add_selected_offerings_block(install, inputdata.get("offerings", {}), selected=True)

        self.add_preferences(root, self.constants.preferences)
        return root

    def build_uninstall_tree(self, inputdata: Mapping[str, Any]) -> Element:
        """
        Build the <agent-input> tree for 'uninstall' mode.
        Emits one <uninstall modify='false'> per selected offering.
        """
        root = Element("agent-input", {"clean": "true", "temporary": "true"})
        offerings = inputdata.get("offerings", {}) or {}

        for name, enabled in offerings.items():
            if not enabled:
                continue
            meta = self.constants.offerings_metadata.get(name)
            if not meta:
                continue
            uninstall = SubElement(root, "uninstall", {"modify": "false"})
            self.add_offering(uninstall, meta, selected=None)

        return root

    # ---------- Orchestrator (main entry point) ----------

    def generate(self, filename: str, inputdata: Mapping[str, Any], mode: str) -> str:
        """
        Generate and write the XML for given mode. Returns written filename.
        """
        mode_norm = (mode or "").strip().lower()
        if mode_norm not in {"install", "upgrade", "uninstall"}:
            raise ValueError("mode must be one of: install, upgrade, uninstall")

        if mode_norm == "install":
            root = self.build_install_tree(inputdata)
        elif mode_norm == "upgrade":
            root = self.build_upgrade_tree(inputdata)
        else:
            root = self.build_uninstall_tree(inputdata)

        xml_bytes = self.to_pretty_xml_bytes(root)
        return self.write_xml(filename, xml_bytes)

    # ---------- Internal helpers ----------

    def _add_selected_offerings_block(
        self,
        parent_block: Element,
        offerings_flags: Mapping[str, bool],
        *,
        selected: bool,
    ) -> None:
        """
        Add offerings to a given block (<install>), honoring boolean flags.
        Unknown offerings (not in constants) are skipped.
        """
        offerings_flags = offerings_flags or {}
        for name, is_on in offerings_flags.items():
            if not is_on:
                continue
            meta = self.constants.offerings_metadata.get(name)
            if not meta:
                # Unknown offering name -> skip silently for resilience
                continue
            self.add_offering(parent_block, meta, selected=selected)

