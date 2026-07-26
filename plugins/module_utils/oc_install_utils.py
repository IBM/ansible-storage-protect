"""
Utilities for cross-platform IBM Storage Protect Operations Center (OC) installation.

Supports Linux, RHEL-family, AIX, and Windows. Reuses sp_server_utils primitives for
extract, IMCL detection, and install orchestration.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import logging
import os
import re
import ssl
import base64
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

from . import sp_server_constants
from . import sp_server_utils as sp_utils

OC_PACKAGE_ID = sp_server_constants.offerings_metadata["oc"]["id"]
OC_PACKAGE_META = sp_server_constants.offerings_metadata["oc"]

# Platform tokens expected in GSA / NextGenUI artifact filenames.
# SPOC drops use names like 8.2.1.000-IBM-SPOC-Linuxx86_64.bin.
OC_PLATFORM_MARKERS = {
    "windows": ["WindowsX64"],
    "linux": ["LinuxX64", "Linuxx86_64"],
    "rhel": ["RhelX64", "LinuxX64", "Linuxx86_64"],
    "aix": ["AixPPC", "-AIX"],
}

OC_ARTIFACT_EXTENSIONS = {
    "windows": ".exe",
    "linux": ".bin",
    "rhel": ".bin",
    "aix": ".bin",
}

AIX_TSM_INSTALL_DIR = "/usr/tivoli/tsm"
UNIX_TSM_INSTALL_DIR = "/opt/tivoli/tsm"
AIX_OC_INSTALL_DEST = "/tmp/oc_binary"
UNIX_OC_INSTALL_DEST = "/opt/oc_binary"
AIX_IM_CANDIDATES = (
    "/usr/IBM/InstallationManager",
    "/opt/IBM/InstallationManager",
)


def default_install_dest(oskey: Optional[str] = None) -> str:
    if os.name == "nt":
        return r"C:\temp\oc_binary"
    if oskey == "aix":
        return AIX_OC_INSTALL_DEST
    return UNIX_OC_INSTALL_DEST


DEFAULT_INSTALL_DEST = default_install_dest()


def default_tsm_install_dir(oskey: Optional[str] = None) -> str:
    if oskey == "aix":
        return AIX_TSM_INSTALL_DIR
    return UNIX_TSM_INSTALL_DIR


def resolve_im_install_dir(oskey: Optional[str], override: Optional[str] = None) -> str:
    """Return IM root, probing common AIX locations when not explicitly set."""
    if override:
        return override
    if oskey == "aix":
        for candidate in AIX_IM_CANDIDATES:
            if os.path.isdir(candidate):
                return candidate
        return AIX_IM_CANDIDATES[0]
    if os.name == "nt":
        return r"C:\Program Files\IBM\Installation Manager"
    return "/opt/IBM/InstallationManager"


def sp_server_binary_candidates(install_dir: str) -> List[str]:
    """Return dsmserv paths to check for an existing SP Server install."""
    return [
        os.path.join(install_dir, "server", "bin", "dsmserv"),
        os.path.join(AIX_TSM_INSTALL_DIR, "server", "bin", "dsmserv"),
        os.path.join(UNIX_TSM_INSTALL_DIR, "server", "bin", "dsmserv"),
    ]

OC_SERVICE_COMMANDS = {
    "linux": {
        "status": "systemctl is-active opscenter.service",
        "restart": "systemctl restart opscenter.service",
    },
    "rhel": {
        "status": "systemctl is-active opscenter.service",
        "restart": "systemctl restart opscenter.service",
    },
    "aix": {
        "status": "lssrc -s opscenter 2>/dev/null || echo inactive",
        "restart": "stopsrc -s opscenter 2>/dev/null; startsrc -s opscenter",
    },
    "windows": {
        "status": 'sc query "opscenter" 2>nul || sc query "Operations Center"',
        "restart": 'sc stop "opscenter" & sc start "opscenter"',
    },
}

# Stream large GSA binaries to disk; loading multi-GB installers into memory
# fails on memory-constrained AIX hosts.
GSA_DOWNLOAD_CHUNK_SIZE = 8 * 1024 * 1024

# IM package group on SP 8.2 hosts with server already installed.
DEFAULT_IM_PROFILE_ID = "IBM Storage Protect"

OC_SSL_SPECIAL_CHARS = set("~#$%^@*_-+=|(){}[]:;<>,.?/")


def validate_ssl_password(password: Optional[str]) -> Optional[str]:
    """Return an error message when the OC SSL password fails IM policy checks."""
    if not password:
        return "ssl_password is required for install/upgrade (or set OC_SSL_PASSWORD)"
    special_count = sum(1 for char in password if char in OC_SSL_SPECIAL_CHARS)
    if special_count < 2:
        return (
            "ssl_password must contain at least two non-alphanumeric characters. "
            "Valid characters: ~ # $ % ^ @ * _ - + = | ( ) { } [ ] : ; < > , . ? /"
        )
    return None


def format_oc_status_message(
    *,
    installed_version: Optional[str],
    validation: Dict[str, Any],
    secure_port: str,
    installed: bool,
) -> str:
    """Build a human-readable success or skip message for playbook output."""
    version = installed_version or "unknown"
    service_state = "running" if validation.get("service_running") else "not running"
    action = "installed successfully" if installed else "already installed"
    return (
        f"IBM Storage Protect Operations Center {action} "
        f"(version {version}). opscenter service is {service_state}. "
        f"Web UI: https://<host>:{secure_port}/oc"
    )


class GSAAccessError(Exception):
    """Raised when GSA HTTP access fails."""


def _normalize_base_url(url: str) -> str:
    return url if url.endswith("/") else url + "/"


def detect_platform(context: Dict[str, Any]) -> str:
    """Return normalized platform key: windows, rhel, linux, or aix."""
    return sp_utils.os_oskey(context)["osname"]


def build_context(params: Dict[str, Any]) -> Dict[str, Any]:
    """Build orchestration context consumed by sp_server_utils helpers."""
    logger = logging.getLogger("ibm.storage_protect.oc_install")
    logger.handlers.clear()
    logger.addHandler(logging.NullHandler())
    logger.setLevel(logging.DEBUG)

    os_info = sp_utils.get_os_info()
    oskey = sp_utils.os_oskey({"os": os_info})["osname"]
    im_param = params.get("install_location_im")
    tsm_param = params.get("install_location_tsm")
    dest_param = params.get("oc_install_dest")

    if oskey == "aix":
        if not im_param or im_param == "/opt/IBM/InstallationManager":
            im_root = resolve_im_install_dir("aix")
        else:
            im_root = im_param
        if not tsm_param or tsm_param == UNIX_TSM_INSTALL_DIR:
            tsm_root = AIX_TSM_INSTALL_DIR
        else:
            tsm_root = tsm_param
        if not dest_param or dest_param == UNIX_OC_INSTALL_DEST:
            params["oc_install_dest"] = AIX_OC_INSTALL_DEST
    else:
        im_root = resolve_im_install_dir(oskey, im_param)
        tsm_root = tsm_param or default_tsm_install_dir(oskey)

    ansible_vars = {
        "profile_id": params.get("profile_id") or DEFAULT_IM_PROFILE_ID,
        "install_location_tsm": tsm_root,
        "install_location_im": im_root,
        "install_location_im_linux": im_root,
        "repository_location": params.get("repository_location", "repository"),
        "secure_port": params.get("secure_port", "9443"),
        "ssl_password": params.get("ssl_password", ""),
        "license_value": "",
        "sp_mode": "upgrade" if params.get("state") == "upgrade" else "install",
        "offerings": {
            "server": False,
            "stagent": False,
            "devices": False,
            "oc": True,
            "ossm": False,
        },
    }

    return {
        "logger": logger,
        "os": os_info,
        "system": sp_utils.get_system_info(),
        "ansible_vars_data": ansible_vars,
        "params": params,
    }


def _gsa_ssl_context(context: Dict[str, Any]) -> ssl.SSLContext:
    """Build TLS context for GSA HTTPS access."""
    validate = context.get("params", {}).get("gsa_validate_certs", True)
    if validate:
        return ssl.create_default_context()
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _gsa_build_request(url: str, context: Dict[str, Any]) -> urllib.request.Request:
    request = urllib.request.Request(url, headers={"User-Agent": "ibm.storage_protect.oc_install/1.0"})
    params = context.get("params", {})
    username = params.get("gsa_username")
    password = params.get("gsa_password") or ""
    if username:
        token = base64.b64encode(f"{username}:{password}".encode()).decode("ascii")
        request.add_header("Authorization", f"Basic {token}")
    return request


def _gsa_urlopen(url: str, context: Dict[str, Any], timeout: int = 120):
    """Open a GSA URL; caller must use as a context manager."""
    request = _gsa_build_request(url, context)
    try:
        return urllib.request.urlopen(
            request,
            timeout=timeout,
            context=_gsa_ssl_context(context),
        )
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            raise GSAAccessError(
                f"GSA returned HTTP 401 Unauthorized for {url}. "
                "Provide gsa_username and gsa_password, or stage the installer locally "
                "and set artifact_path."
            ) from exc
        raise GSAAccessError(f"GSA returned HTTP {exc.code} for {url}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        reason = str(getattr(exc, "reason", exc))
        if "CERTIFICATE_VERIFY_FAILED" in reason or "certificate verify failed" in reason.lower():
            raise GSAAccessError(
                f"Failed to access GSA URL {url}: {exc}. "
                "The target host cannot verify the GSA TLS certificate. "
                "Set gsa_validate_certs=false, use an http:// GSA URL, install CA "
                "certificates on the host, or stage the installer with artifact_path."
            ) from exc
        raise GSAAccessError(f"Failed to access GSA URL {url}: {exc}") from exc


def _gsa_read_url(url: str, context: Dict[str, Any], timeout: int = 120) -> bytes:
    with _gsa_urlopen(url, context, timeout=timeout) as response:
        return response.read()


def _gsa_download_to_file(
    url: str,
    dest_path: str,
    context: Dict[str, Any],
    timeout: int = 120,
) -> None:
    """Stream a GSA artifact to disk without loading it entirely into memory."""
    temp_path = f"{dest_path}.part"
    if os.path.isfile(temp_path):
        try:
            os.remove(temp_path)
        except OSError:
            pass

    try:
        with _gsa_urlopen(url, context, timeout=timeout) as response:
            with open(temp_path, "wb") as handle:
                while True:
                    chunk = response.read(GSA_DOWNLOAD_CHUNK_SIZE)
                    if not chunk:
                        break
                    handle.write(chunk)
        os.replace(temp_path, dest_path)
    except Exception:
        if os.path.isfile(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        raise


def _fetch_url_text(url: str, context: Dict[str, Any], timeout: int = 120) -> str:
    return _gsa_read_url(url, context, timeout).decode("utf-8", errors="replace")


def list_gsa_artifacts(base_url: str, context: Dict[str, Any], timeout: int = 120) -> List[str]:
    """Return artifact filenames discovered from an HTTP GSA directory listing."""
    url = _normalize_base_url(base_url)
    body = _fetch_url_text(url, context, timeout)

    names: List[str] = []
    for match in re.finditer(r'href=["\']([^"\']+)["\']', body, flags=re.IGNORECASE):
        href = match.group(1).strip()
        if href in ("../", "./", "/") or href.startswith("?"):
            continue
        filename = href.split("/")[-1]
        if filename and filename not in names:
            names.append(filename)
    return names


def resolve_gsa_listing(
    base_url: str,
    context: Dict[str, Any],
    timeout: int = 120,
    _depth: int = 0,
) -> Tuple[str, List[str]]:
    """Return effective GSA URL and filenames, following LATEST._ln pointers if needed."""
    if _depth > 3:
        return _normalize_base_url(base_url), []

    url = _normalize_base_url(base_url)
    filenames = list_gsa_artifacts(url, context, timeout)

    if any(name.lower().endswith((".bin", ".exe")) for name in filenames):
        return url, filenames

    for name in filenames:
        if not name.endswith("._ln"):
            continue
        pointer_url = url + name
        try:
            pointer_body = _fetch_url_text(pointer_url, context, timeout).strip().splitlines()[0].strip()
        except GSAAccessError as exc:
            sp_utils._warning(context, "Failed to read GSA pointer %s: %s", pointer_url, exc)
            continue

        if pointer_body.startswith("http"):
            next_url = _normalize_base_url(pointer_body)
        else:
            next_url = _normalize_base_url(urljoin(url, pointer_body))

        sp_utils._info(context, "Following GSA pointer %s -> %s", name, next_url)
        return resolve_gsa_listing(next_url, context, timeout, _depth + 1)

    return url, filenames


def _version_prefixes(version: Optional[str]) -> List[str]:
    if not version:
        return []
    prefixes = [version if version.endswith("-") else f"{version}-"]
    parts = version.split(".")
    if len(parts) > 3:
        prefixes.append(".".join(parts[:3]) + "-")
    if len(parts) > 2:
        prefixes.append(".".join(parts[:2]) + "-")
    return list(dict.fromkeys(prefixes))


def select_artifact_name(
    filenames: List[str],
    oskey: str,
    version: Optional[str] = None,
) -> Optional[str]:
    """Pick the best artifact filename for the target platform and version."""
    oskeys_to_try = [oskey]
    if oskey == "rhel":
        oskeys_to_try.append("linux")

    for candidate_oskey in oskeys_to_try:
        markers = OC_PLATFORM_MARKERS.get(candidate_oskey, [])
        extension = OC_ARTIFACT_EXTENSIONS.get(candidate_oskey)
        if not markers or not extension:
            continue

        candidates = [
            name
            for name in filenames
            if name.lower().endswith(extension.lower())
            and any(marker.lower() in name.lower() for marker in markers)
        ]
        if version:
            version_matches = []
            for prefix in _version_prefixes(version):
                version_matches.extend([name for name in candidates if name.startswith(prefix)])
            if version_matches:
                candidates = version_matches

        if not candidates:
            continue

        def version_key(name: str) -> Tuple:
            prefix = name.split("-", 1)[0]
            return sp_utils.version_parse(prefix)

        candidates.sort(key=version_key, reverse=True)
        return candidates[0]

    return None


def download_artifact(
    base_url: str,
    filename: str,
    dest_dir: str,
    context: Dict[str, Any],
    timeout: int = 120,
) -> str:
    """Download artifact from GSA to dest_dir. Returns local file path."""
    url = _normalize_base_url(base_url) + filename
    local_path = os.path.join(dest_dir, filename)

    if os.path.isfile(local_path) and os.path.getsize(local_path) > 0:
        sp_utils._info(context, "Artifact already present at %s; skipping download", local_path)
        return local_path

    sp_utils.fs_ensure_dir(dest_dir, context=context)

    try:
        _gsa_download_to_file(url, local_path, context, timeout=timeout)
    except GSAAccessError as exc:
        sp_utils._error(context, "%s", exc)
        raise
    except MemoryError as exc:
        raise GSAAccessError(
            f"Out of memory while downloading {filename} from GSA. "
            "Stage the installer on the host with artifact_path, or download with "
            "ansible.builtin.get_url on the controller and copy it to the target."
        ) from exc

    if oskey_is_unix_like(context):
        os.chmod(local_path, 0o755)

    sp_utils._info(context, "Downloaded artifact to %s", local_path)
    return local_path


def oskey_is_unix_like(context: Dict[str, Any]) -> bool:
    oskey = detect_platform(context)
    return oskey in {"linux", "rhel", "aix"}


def get_installed_version(context: Dict[str, Any], oskey: str) -> Optional[str]:
    status = sp_utils.ba_is_installed(context, oskey=oskey, install_data=OC_PACKAGE_META)
    if not status.get("status"):
        return None
    return status.get("data", {}).get("installedpackages", {}).get(OC_PACKAGE_ID)


def requires_skip_upgrade_check(context: Dict[str, Any], oskey: str) -> bool:
    """
    Return True when install.sh will treat the host as an upgrade.

    install.sh requires -skipUpgradeCheck for silent runs when SP components already
    exist on the host, even if this module is adding OC for the first time.
    """
    if get_installed_version(context, oskey):
        return True

    imcl_path = (
        context["ansible_vars_data"].get("install_location_im")
        or "/opt/IBM/InstallationManager"
    )
    imcl_bin = os.path.join(imcl_path, "eclipse", "tools", "imcl")
    if os.path.isfile(imcl_bin):
        resp = sp_utils.exec_run(
            context=context,
            cmd=f"{imcl_bin} listInstalledPackages",
        )
        if resp.get("rc") == 0:
            imcl_output = (resp.get("stdout") or "").lower()
            if "com.tivoli.dsm" in imcl_output:
                return True

    install_dir = context["ansible_vars_data"].get("install_location_tsm") or default_tsm_install_dir(oskey)
    if any(os.path.isfile(path) for path in sp_server_binary_candidates(install_dir)):
        return True

    if oskey in {"linux", "rhel"}:
        rpm_resp = sp_utils.exec_run(context=context, cmd="rpm -qa 'TIVsm-*'", shell=True)
        if (rpm_resp.get("stdout") or "").strip():
            return True

    if oskey == "aix":
        lslpp_resp = sp_utils.exec_run(
            context=context,
            cmd="lslpp -L 2>/dev/null | grep -iE 'tivoli\\.tsm|tivoli\\.dsm'",
            shell=True,
        )
        if (lslpp_resp.get("stdout") or "").strip():
            return True

    return False


def resolve_repository_dir(extracted_dir: str) -> str:
    """Return absolute path to Installation Manager repository inside extracted payload."""
    for name in ("repository", "Repository"):
        candidate = os.path.join(extracted_dir, name)
        if os.path.isdir(candidate):
            return os.path.abspath(candidate)

    for root, dirs, _ in os.walk(extracted_dir):
        for name in ("repository", "Repository"):
            if name in dirs:
                return os.path.abspath(os.path.join(root, name))

    return os.path.abspath(os.path.join(extracted_dir, "repository"))


def build_oc_response_xml(xml_path: str, context: Dict[str, Any]) -> str:
    """Generate Installation Manager response XML for OC-only install."""
    inputdata = context["ansible_vars_data"]
    mode = inputdata.get("sp_mode", "install")
    builder = sp_utils.AgentInputXMLBuilder(context=context)
    xml_dir = os.path.dirname(xml_path)
    if xml_dir:
        os.makedirs(xml_dir, exist_ok=True)
    return builder.generate(filename=xml_path, inputdata=inputdata, mode=mode)


def run_install_script(
    context: Dict[str, Any],
    extracted_dir: str,
    xml_path: str,
    oskey: str,
    is_upgrade: bool = False,
) -> Tuple[bool, Dict[str, Any]]:
    """Execute install.sh / install.bat from extracted installer payload."""
    script_name = "install.bat" if oskey == "windows" else "install.sh"
    script_path = os.path.join(extracted_dir, script_name)
    result: Dict[str, Any] = {"script_path": script_path, "response_xml": xml_path}
    skip_upgrade_err = "-skipUpgradeCheck flag is required"

    if not os.path.isfile(script_path):
        sp_utils._error(context, "Install script not found: %s", script_path)
        result["msg"] = f"Install script not found: {script_path}"
        return False, result

    def _normalize_install_script() -> None:
        sp_utils.exec_run(context=context, cmd=f"chmod +x {script_path}", shell=True)
        if oskey in {"linux", "rhel"}:
            dos2unix = sp_utils.exec_run(context=context, cmd=f"dos2unix {script_path}", shell=True)
            if dos2unix.get("rc") != 0:
                sp_utils.exec_run(context=context, cmd=f"sed -i 's/\\r$//' {script_path}", shell=True)
        elif oskey == "aix":
            sp_utils.exec_run(
                context=context,
                cmd=(
                    f"sed 's/\\r$//' {script_path} > {script_path}.nl "
                    f"&& mv {script_path}.nl {script_path}"
                ),
                shell=True,
            )

    def _prepare_script(upgrade_flag: bool) -> bool:
        if oskey in {"linux", "rhel", "aix"}:
            _normalize_install_script()

        if upgrade_flag and oskey in {"linux", "rhel", "aix"}:
            backup_path = f"{script_path}.backup"
            if os.path.isfile(backup_path):
                sp_utils.exec_run(
                    context=context,
                    cmd=f"cp {backup_path} {script_path}",
                    shell=True,
                )
            if not sp_utils.patch_install_sh_for_upgrade(script_path, context=context):
                result["msg"] = "Failed to patch install.sh for upgrade scenario"
                return False
        return True

    def _build_install_cmd(upgrade_flag: bool) -> str:
        install_args = f'-s -input {xml_path} -acceptLicense'
        if upgrade_flag:
            install_args += " -skipUpgradeCheck"
        install_cmd = f'cd "{extracted_dir}" && ./{script_name} {install_args}'
        if oskey == "aix":
            install_cmd = (
                "ulimit -f unlimited && ulimit -c unlimited && ulimit -n unlimited && "
                + install_cmd
            )
        return install_cmd

    upgrade_flag = is_upgrade
    response: Dict[str, Any] = {}
    for attempt in range(2):
        if attempt == 1:
            stdout = (response.get("stdout") or "")
            if skip_upgrade_err not in stdout:
                break
            upgrade_flag = True
            result["retried_with_skip_upgrade_check"] = True
            sp_utils._info(
                context,
                "install.sh requires -skipUpgradeCheck; retrying as upgrade",
            )

        if not _prepare_script(upgrade_flag):
            return False, result

        install_cmd = _build_install_cmd(upgrade_flag)
        result["install_cmd"] = install_cmd
        response = sp_utils.exec_run(context=context, cmd=install_cmd, shell=True)
        result.update(response)
        if response.get("rc") == 0:
            return True, result

    sp_utils._error(context, "Install script failed: %s", response)
    return False, result


def validate_service(context: Dict[str, Any], oskey: str) -> bool:
    """Best-effort service validation; IMCL package check remains authoritative."""
    commands = OC_SERVICE_COMMANDS.get(oskey, OC_SERVICE_COMMANDS["linux"])
    response = sp_utils.exec_run(context=context, cmd=commands["status"], shell=True)
    output = (response.get("stdout") or "") + (response.get("stderr") or "")
    output_lower = output.lower()
    if oskey == "aix":
        return "active" in output_lower and "inoperative" not in output_lower
    if response.get("rc") == 0:
        return True
    return "active" in output_lower or "running" in output_lower


def validate_installation(context: Dict[str, Any], oskey: str) -> Dict[str, Any]:
    """Validate OC package via IMCL and optional service check."""
    package_status = sp_utils.ba_is_installed(context, oskey=oskey, install_data=OC_PACKAGE_META)
    installed_version = None
    if package_status.get("status"):
        installed_version = package_status.get("data", {}).get("installedpackages", {}).get(OC_PACKAGE_ID)

    result = {
        "package_installed": bool(installed_version),
        "installed_version": installed_version,
        "service_running": validate_service(context, oskey) if installed_version else False,
        "platform": oskey,
    }
    result["valid"] = result["package_installed"]
    return result


def configure_oc_admin(module, admin_name: str) -> Tuple[bool, str]:
    """Apply basic OC configuration using dsmadmc."""
    from .dsmadmc_adapter import DsmadmcAdapter

    adapter = DsmadmcAdapter(argument_spec=module.argument_spec, direct_params=module.params)
    rc, out, err = adapter.run_command(
        f"update admin {admin_name} sessionsecurity=transitional",
        auto_exit=False,
    )
    if rc == 0:
        return True, out
    return False, out or str(err)


class OCInstallManager:
    """Orchestrates OC download, install, configure, and validation."""

    def __init__(self, module):
        self.module = module
        self.params = module.params
        self.context = build_context(self.params)
        self.oskey = detect_platform(self.context)
        self.changed = False

    def run(self) -> Dict[str, Any]:
        state = self.params["state"]
        if state == "absent":
            self.module.fail_json(msg="state=absent is not yet supported by oc_install")

        target_version = self.params.get("oc_version")
        force = self.params.get("force", False)
        current_version = get_installed_version(self.context, self.oskey)

        if current_version and not force:
            if target_version and not sp_utils.version_is_newer(current_version, target_version):
                validation = validate_installation(self.context, self.oskey)
                if self.params.get("configure") and self.params.get("admin_name"):
                    self._maybe_configure()
                return self._result(
                    changed=self.changed,
                    msg=format_oc_status_message(
                        installed_version=current_version,
                        validation=validation,
                        secure_port=str(self.params.get("secure_port", "9443")),
                        installed=False,
                    ),
                    installed_version=current_version,
                    validation=validation,
                    success=True,
                )

        artifact_path = self._resolve_artifact_path()
        extracted_dir = os.path.join(os.path.dirname(artifact_path), "extracted")

        if not os.path.isdir(extracted_dir):
            if not sp_utils.extract_binary_package(artifact_path, extracted_dir, context=self.context):
                self.module.fail_json(msg="Failed to extract Operations Center installer")

        repository_dir = resolve_repository_dir(extracted_dir)
        if not os.path.isdir(repository_dir):
            self.module.fail_json(
                msg="Operations Center repository directory not found in extracted installer",
                extracted_dir=extracted_dir,
                expected_repository=repository_dir,
            )

        xml_path = os.path.join(extracted_dir, "input", "install_response_sample.xml")

        is_upgrade = (
            self.params.get("state") == "upgrade"
            or requires_skip_upgrade_check(self.context, self.oskey)
        )
        # install.sh needs -skipUpgradeCheck on hosts with existing SP packages, but the
        # response XML must stay in install mode so ssl.password and profile data are
        # written for a new OC offering on an existing package group.
        self.context["ansible_vars_data"]["sp_mode"] = "install"
        self.context["ansible_vars_data"]["repository_location"] = repository_dir

        build_oc_response_xml(xml_path, self.context)

        install_ok, install_result = run_install_script(
            self.context, extracted_dir, xml_path, self.oskey, is_upgrade=is_upgrade,
        )
        if not install_ok:
            self.module.fail_json(
                msg="Operations Center installation failed",
                is_upgrade=is_upgrade,
                install_rc=install_result.get("rc"),
                install_stdout=install_result.get("stdout"),
                install_stderr=install_result.get("stderr"),
                install_cmd=install_result.get("install_cmd"),
                retried_with_skip_upgrade_check=install_result.get(
                    "retried_with_skip_upgrade_check", False,
                ),
                extracted_dir=extracted_dir,
                response_xml=xml_path,
            )

        self.changed = True
        validation = validate_installation(self.context, self.oskey)
        if not validation["valid"]:
            self.module.fail_json(
                msg="Operations Center install completed but validation failed",
                validation=validation,
            )

        if self.params.get("configure") and self.params.get("admin_name"):
            self._maybe_configure()

        installed_version = validation.get("installed_version") or target_version
        secure_port = str(self.params.get("secure_port", "9443"))
        return self._result(
            changed=True,
            msg=format_oc_status_message(
                installed_version=installed_version,
                validation=validation,
                secure_port=secure_port,
                installed=True,
            ),
            installed_version=installed_version,
            artifact=artifact_path,
            validation=validation,
            success=True,
            oc_url=f"https://<host>:{secure_port}/oc",
        )

    def _resolve_artifact_path(self) -> str:
        dest_dir = self.params["oc_install_dest"]
        sp_utils.fs_ensure_dir(dest_dir, context=self.context)

        local_artifact = self.params.get("artifact_path")
        if local_artifact and os.path.isfile(local_artifact):
            return local_artifact

        local_search = sp_utils.find_installer(
            oskey=self.oskey,
            base_dir=dest_dir,
            version=self.params.get("oc_version"),
            name_markers=OC_PLATFORM_MARKERS.get(self.oskey),
        )
        if local_search.get("status") and local_search["data"].get("installerfile"):
            return local_search["data"]["installerfile"]

        base_url = self.params.get("gsa_base_url")
        effective_url, filenames = resolve_gsa_listing(
            base_url,
            self.context,
            timeout=self.params.get("download_timeout", 120),
        )
        selected = select_artifact_name(
            filenames,
            self.oskey,
            version=self.params.get("oc_version"),
        )
        if not selected:
            installer_files = [
                f for f in filenames if f.lower().endswith((".bin", ".exe"))
            ]
            war_files = [f for f in filenames if f.lower().endswith(".war")]
            markers = OC_PLATFORM_MARKERS.get(self.oskey, [])
            hint = None
            if installer_files:
                hint = (
                    f"Found installer binaries but none match platform '{self.oskey}'. "
                    f"Expected filename markers: {', '.join(markers)}"
                )
            elif war_files:
                hint = (
                    "This GSA directory contains NextGenUI WAR/ZIP artifacts only "
                    f"({', '.join(filenames)}). Use artifact_path with a platform "
                    ".bin/.exe installer or a GSA path that ships SPOC install images."
                )
            self.module.fail_json(
                msg="No Operations Center artifact found for platform "
                f"'{self.oskey}' at {effective_url}",
                platform=self.oskey,
                gsa_base_url=base_url,
                gsa_resolved_url=effective_url,
                available_artifacts=filenames,
                hint=hint,
            )

        return download_artifact(
            effective_url,
            selected,
            dest_dir,
            self.context,
            timeout=self.params.get("download_timeout", 120),
        )

    def _maybe_configure(self) -> None:
        ok, output = configure_oc_admin(self.module, self.params["admin_name"])
        if not ok:
            self.module.fail_json(msg="Operations Center install succeeded but configuration failed", stdout=output)
        self.changed = True

    def _result(self, **kwargs) -> Dict[str, Any]:
        payload = {
            "platform": self.oskey,
            "changed": kwargs.get("changed", self.changed),
            "msg": kwargs.get("msg", ""),
        }
        for key in ("installed_version", "artifact", "validation", "success", "oc_url"):
            if key in kwargs and kwargs[key] is not None:
                payload[key] = kwargs[key]
        return payload
