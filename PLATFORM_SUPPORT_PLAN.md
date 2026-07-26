# Platform Support Implementation Plan

## Overview
This document outlines the implementation plan for adding support for Linux ppc64le, s390x, and Solaris x86 platforms to the `sp_server.py` module.

## Current State Analysis

### 1. Artifact Patterns (sp_server.py lines 257-269)
Currently supports:
- **Windows**: `WindowsX64.exe`
- **Linux**: `LinuxX64.bin`
- **RHEL**: `RhelX64.bin`
- **AIX**: `AixPPC.bin`

### 2. Platform Detection (sp_server_utils.py)
- Uses [`platform.machine()`](plugins/module_utils/sp_server_utils.py:153) to detect architecture
- Uses [`platform.system()`](plugins/module_utils/sp_server_utils.py:122) to detect OS family
- Normalizes OS family in [`os_oskey()`](plugins/module_utils/sp_server_utils.py:74-101) function

### 3. Artifact Discovery (sp_server_utils.py)
- [`find_installer()`](plugins/module_utils/sp_server_utils.py:1013-1131) function determines file extension based on oskey
- Currently maps: windows→.exe, linux/aix/rhel→.bin

### 4. Installation Flow
- Linux platforms use [`install.sh`](plugins/modules/sp_server.py:716) script
- Windows uses [`install.bat`](plugins/modules/sp_server.py:718)
- AIX follows Linux flow with POSIX-compliant shell syntax

## Required Changes

### Change 1: Add New Artifact Patterns
**File**: [`plugins/modules/sp_server.py`](plugins/modules/sp_server.py:257-269)

Add three new patterns to the `ARTIFACT_PATTERNS` dictionary:

```python
ARTIFACT_PATTERNS = {
    "windows": r"^\d+\.\d+\.\d+\.\d+-IBM-SPOC-WindowsX64\.exe$",
    "linux": r"([0-9]+(?:\\.[0-9]+){1,3})-[A-Za-z0-9_-]+-LinuxX64\\.bin$",
    "rhel": r"([0-9]+(?:\\.[0-9]+){1,3})-[A-Za-z0-9_-]+-RhelX64\\.bin$",
    "aix": r"([0-9]+(?:\\.[0-9]+){1,3})-[A-Za-z0-9_-]+-AixPPC\\.bin$",
    
    # NEW PATTERNS
    "linuxppc64le": r"([0-9]+(?:\\.[0-9]+){1,3})-[A-Za-z0-9_-]+-Linuxppc64le\\.bin$",
    "linuxs390x": r"([0-9]+(?:\\.[0-9]+){1,3})-[A-Za-z0-9_-]+-Linuxs390x\\.bin$",
    "solarisx86": r"([0-9]+(?:\\.[0-9]+){1,3})-[A-Za-z0-9_-]+-SolarisX86\\.bin$",
}
```

### Change 2: Update OS Detection Logic
**File**: [`plugins/module_utils/sp_server_utils.py`](plugins/module_utils/sp_server_utils.py:74-101)

Enhance the [`os_oskey()`](plugins/module_utils/sp_server_utils.py:74) function to detect architecture:

```python
def os_oskey(context: Dict[str, Any]) -> Dict[str, str]:
    os_data = context.get("os", {}) or {}
    family = (os_data.get("family") or "").lower()
    distro_id = (os_data.get("id") or "").lower()
    arch = (os_data.get("arch") or "").lower()  # NEW: Get architecture

    # Normalize OS family
    if family == "windows":
        os_family = "windows"
    elif family == "linux":
        os_family = "linux"
    elif family in {"aix", "unix"}:
        os_family = family
    elif family == "sunos":  # NEW: Solaris detection
        os_family = "solaris"
    else:
        os_family = family or "unknown"

    # Determine distro / specific OS name with architecture
    if os_family == "linux":
        # Check for specific architectures
        if arch in {"ppc64le", "ppc64"}:
            os_name = "linuxppc64le"
        elif arch in {"s390x", "s390"}:
            os_name = "linuxs390x"
        else:
            # Normalize common RHEL-family distros under "rhel"
            rhel_like = {"rhel", "centos", "rocky", "almalinux", "oraclelinux"}
            if distro_id in rhel_like:
                os_name = "rhel"
            else:
                os_name = distro_id or "linux"
    elif os_family == "solaris":  # NEW: Solaris handling
        if arch in {"i86pc", "x86_64", "amd64"}:
            os_name = "solarisx86"
        else:
            os_name = "solaris"
    else:
        os_name = distro_id or os_family

    return {"os": os_family, "osname": os_name}
```

### Change 3: Update Artifact Discovery
**File**: [`plugins/module_utils/sp_server_utils.py`](plugins/module_utils/sp_server_utils.py:1013-1131)

Update the [`find_installer()`](plugins/module_utils/sp_server_utils.py:1013) function to handle new platforms:

```python
def find_installer(
    oskey: str,
    base_dir: str,
    case_insensitive: bool = False,
    version: Optional[str] = None,
) -> Dict[str, Any]:
    # Resolve extension
    ok = oskey.lower()
    if ok in ("windows", "win"):
        ext = ".exe"
    elif ok in ("linux", "lin", "aix", "linuxppc64le", "linuxs390x", "solarisx86", "solaris"):  # UPDATED
        ext = ".bin"
    elif ok in ("rhel", "centos"):
        ext = ".bin"
    else:
        ext = oskey if oskey.startswith(".") else f".{oskey}"
    
    # ... rest of function remains the same
```

### Change 4: Installation Script Handling
**File**: [`plugins/modules/sp_server.py`](plugins/modules/sp_server.py:716-738)

The installation script logic already handles Linux generically. Verify that new platforms follow the same flow:

```python
install_script_filename = "install.sh"
if os_name.lower().strip() == "windows":
    install_script_filename = "install.bat"

# Linux line endings for Linux-based platforms (including new ones)
if os_name.lower().strip() in ["linux", "linuxppc64le", "linuxs390x", "solarisx86"]:  # UPDATED
    cmd = "dos2unix " + install_script_fullfilepath
    exec_perm_resp = utils1.exec_run(cmd=cmd, context=self.ctx)
    # ... error handling
```

### Change 5: Service Management for Solaris
**File**: [`plugins/module_utils/sp_server_utils.py`](plugins/module_utils/sp_server_utils.py:700-850)

Add Solaris-specific service management using SMF (Service Management Facility):

```python
def svc_start(context: dict[str, Any], name: str) -> bool:
    system = platform.system().lower()
    
    if system == "windows":
        r = exec_run(context, "sc start " + str(name))
        # ... existing code
    elif system == "aix":
        r = exec_run(context, f"startsrc -s {name}")
        # ... existing code
    elif system == "sunos":  # NEW: Solaris SMF
        r = exec_run(context, f"svcadm enable {name}")
        ok = r["rc"] == 0
        if not ok:
            _warning(context, "Failed to start Solaris service %s (rc=%s)", name, r["rc"])
        return ok
    else:  # Linux (systemd)
        r = exec_run(context, "systemctl start " + str(name))
        # ... existing code
```

Similar updates needed for:
- [`svc_stop()`](plugins/module_utils/sp_server_utils.py:783)
- [`svc_enable()`](plugins/module_utils/sp_server_utils.py:829)
- [`svc_delete()`](plugins/module_utils/sp_server_utils.py:723)
- [`svc_create()`](plugins/module_utils/sp_server_utils.py:650)

### Change 6: Upgrade Scenario Handling
**File**: [`plugins/modules/sp_server.py`](plugins/modules/sp_server.py:743-749)

Update the upgrade patch logic to include new platforms:

```python
# For upgrade scenarios, patch install.sh to filter -skipUpgradeCheck
if is_upgrade and os_name.lower().strip() in ["linux", "aix", "linuxppc64le", "linuxs390x", "solarisx86"]:  # UPDATED
    self.log.info("Upgrade scenario detected - patching install.sh to filter -skipUpgradeCheck")
    # ... patching logic
```

## Implementation Summary

### Files to Modify

1. **[`plugins/modules/sp_server.py`](plugins/modules/sp_server.py)**
   - Add 3 new artifact patterns (lines 257-269)
   - Update Linux line ending conversion logic (line 726)
   - Update upgrade patch logic (line 743)

2. **[`plugins/module_utils/sp_server_utils.py`](plugins/module_utils/sp_server_utils.py)**
   - Update [`os_oskey()`](plugins/module_utils/sp_server_utils.py:74) function for architecture detection
   - Update [`find_installer()`](plugins/module_utils/sp_server_utils.py:1013) to handle new platforms
   - Add Solaris SMF support to service management functions (lines 650-850)

### Platform-Specific Considerations

#### Linux ppc64le (Power Architecture)
- Uses standard Linux installation flow
- Binary format: `.bin`
- Service management: systemd
- Shell: bash/sh compatible

#### Linux s390x (IBM Z Architecture)
- Uses standard Linux installation flow
- Binary format: `.bin`
- Service management: systemd
- Shell: bash/sh compatible

#### Solaris x86
- Uses standard Unix installation flow
- Binary format: `.bin`
- Service management: SMF (Service Management Facility)
- Shell: POSIX-compliant sh
- Commands: `svcadm`, `svcs`, `svcprop`

## Testing Strategy

1. **Unit Testing**
   - Test artifact pattern matching for new platforms
   - Test OS detection with mocked architecture values
   - Test installer discovery for new binary names

2. **Integration Testing**
   - Test installation on actual ppc64le system
   - Test installation on actual s390x system
   - Test installation on actual Solaris x86 system
   - Verify service creation and management

3. **Regression Testing**
   - Ensure existing platforms (Windows, Linux x64, RHEL, AIX) still work
   - Verify no breaking changes to existing functionality

## Rollout Plan

1. Implement changes in development branch
2. Test with sample artifacts for each new platform
3. Validate on actual target systems
4. Update documentation
5. Merge to main branch
6. Release with version notes

## Documentation Updates Needed

- Update README.md with supported platforms
- Add platform-specific installation notes
- Document artifact naming conventions
- Update troubleshooting guide for new platforms