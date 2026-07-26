# Platform Support Implementation Summary

## Executive Summary

This document provides a comprehensive plan to extend [`sp_server.py`](plugins/modules/sp_server.py) to support four additional platforms:
- **Linux ppc64le** (IBM Power Architecture)
- **Linux s390x** (IBM Z Architecture)
- **Solaris x86** (Oracle Solaris on x86-64)
- **SLES15 x86** (SUSE Linux Enterprise Server 15 on x86-64)

All four platforms will follow the existing Linux installation flow with minimal platform-specific adjustments.

## Quick Reference

### Artifact Naming Patterns
```
Linux ppc64le:  <version>-<vendor>-<product>-Linuxppc64le.bin
Linux s390x:    <version>-<vendor>-<product>-Linuxs390x.bin
Solaris x86:    <version>-<vendor>-<product>-SolarisX86.bin
SLES15 x86:     <version>-<vendor>-<product>-SLES15X64.bin

Example: 1.2.3.4-IBM-SPOC-Linuxppc64le.bin
Example: 1.2.3.4-IBM-SPOC-SLES15X64.bin
```

### Platform Detection Keys
- **Linux ppc64le**: `osname = "linuxppc64le"`
- **Linux s390x**: `osname = "linuxs390x"`
- **Solaris x86**: `osname = "solarisx86"`
- **SLES15 x86**: `osname = "sles15"`

## Implementation Checklist

### Phase 1: Core Pattern Support ✓ (Planned)

#### File: [`plugins/modules/sp_server.py`](plugins/modules/sp_server.py)

**Location**: Lines 257-269 (ARTIFACT_PATTERNS dictionary)

**Change**: Add four new regex patterns

```python
ARTIFACT_PATTERNS = {
    "windows": r"^\d+\.\d+\.\d+\.\d+-IBM-SPOC-WindowsX64\.exe$",
    "linux": r"([0-9]+(?:\\.[0-9]+){1,3})-[A-Za-z0-9_-]+-LinuxX64\\.bin$",
    "rhel": r"([0-9]+(?:\\.[0-9]+){1,3})-[A-Za-z0-9_-]+-RhelX64\\.bin$",
    "aix": r"([0-9]+(?:\\.[0-9]+){1,3})-[A-Za-z0-9_-]+-AixPPC\\.bin$",
    
    # NEW: Additional platform support
    "linuxppc64le": r"([0-9]+(?:\\.[0-9]+){1,3})-[A-Za-z0-9_-]+-Linuxppc64le\\.bin$",
    "linuxs390x": r"([0-9]+(?:\\.[0-9]+){1,3})-[A-Za-z0-9_-]+-Linuxs390x\\.bin$",
    "solarisx86": r"([0-9]+(?:\\.[0-9]+){1,3})-[A-Za-z0-9_-]+-SolarisX86\\.bin$",
    "sles15": r"([0-9]+(?:\\.[0-9]+){1,3})-[A-Za-z0-9_-]+-SLES15X64\\.bin$",
}
```

**Impact**: Enables artifact pattern matching for new platforms

---

### Phase 2: Platform Detection ✓ (Planned)

#### File: [`plugins/module_utils/sp_server_utils.py`](plugins/module_utils/sp_server_utils.py)

**Location**: Lines 74-101 ([`os_oskey()`](plugins/module_utils/sp_server_utils.py:74) function)

**Change**: Enhanced architecture and OS detection

```python
def os_oskey(context: Dict[str, Any]) -> Dict[str, str]:
    os_data = context.get("os", {}) or {}
    family = (os_data.get("family") or "").lower()
    distro_id = (os_data.get("id") or "").lower()
    arch = (os_data.get("arch") or "").lower()  # NEW: Architecture detection

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

    # Determine distro / specific OS name with architecture awareness
    if os_family == "linux":
        # NEW: Check for specific architectures first
        if arch in {"ppc64le", "ppc64"}:
            os_name = "linuxppc64le"
        elif arch in {"s390x", "s390"}:
            os_name = "linuxs390x"
        else:
            # Check for SLES (SUSE Linux Enterprise Server)
            if distro_id in {"sles", "suse", "sles_sap"}:
                os_name = "sles15"
            else:
                # Existing logic for x86_64
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

**Impact**: Correctly identifies platform based on OS family and architecture

---

### Phase 3: Artifact Discovery ✓ (Planned)

#### File: [`plugins/module_utils/sp_server_utils.py`](plugins/module_utils/sp_server_utils.py)

**Location**: Lines 1013-1040 ([`find_installer()`](plugins/module_utils/sp_server_utils.py:1013) function)

**Change**: Add new platforms to extension mapping

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
    elif ok in ("linux", "lin", "aix", "linuxppc64le", "linuxs390x", "solarisx86", "solaris", "sles15", "sles"):  # UPDATED
        ext = ".bin"
    elif ok in ("rhel", "centos"):
        ext = ".bin"
    else:
        ext = oskey if oskey.startswith(".") else f".{oskey}"
    
    # ... rest of function unchanged
```

**Impact**: Ensures correct file extension lookup for new platforms

---

### Phase 4: Installation Script Handling ✓ (Planned)

#### File: [`plugins/modules/sp_server.py`](plugins/modules/sp_server.py)

**Location**: Lines 726-738 (Linux line ending conversion)

**Change**: Include new platforms in dos2unix conversion

```python
# Linux line endings for Linux-based platforms
if os_name.lower().strip() in ["linux", "linuxppc64le", "linuxs390x", "solarisx86", "sles15"]:  # UPDATED
    cmd = "dos2unix " + install_script_fullfilepath
    exec_perm_resp = utils1.exec_run(cmd=cmd, context=self.ctx)
    
    if exec_perm_resp["rc"] != 0:
        self.log.error("Error while converting binary to linux line endings")
        self.log.error(exec_perm_resp)
        return False
    else:
        self.log.debug("Converted binary to linux line endings")
```

**Impact**: Ensures proper line ending conversion for Unix-based platforms

---

**Location**: Lines 743-749 (Upgrade scenario handling)

**Change**: Include new platforms in upgrade patch logic

```python
# For upgrade scenarios, patch install.sh to filter -skipUpgradeCheck
if is_upgrade and os_name.lower().strip() in ["linux", "aix", "linuxppc64le", "linuxs390x", "solarisx86", "sles15"]:  # UPDATED
    self.log.info("Upgrade scenario detected - patching install.sh to filter -skipUpgradeCheck")
    # ... patching logic
```

**Impact**: Ensures upgrade scenarios work correctly on new platforms

---

### Phase 5: Service Management (Solaris-specific) ✓ (Planned)

#### File: [`plugins/module_utils/sp_server_utils.py`](plugins/module_utils/sp_server_utils.py)

**Locations**: Multiple service management functions (lines 650-850)

**Changes Required**:

1. **[`svc_start()`](plugins/module_utils/sp_server_utils.py:806)** - Add Solaris SMF support
2. **[`svc_stop()`](plugins/module_utils/sp_server_utils.py:783)** - Add Solaris SMF support
3. **[`svc_enable()`](plugins/module_utils/sp_server_utils.py:829)** - Add Solaris SMF support
4. **[`svc_delete()`](plugins/module_utils/sp_server_utils.py:723)** - Add Solaris SMF support
5. **[`svc_create()`](plugins/module_utils/sp_server_utils.py:650)** - Add Solaris SMF support

**Example Implementation** (for [`svc_start()`](plugins/module_utils/sp_server_utils.py:806)):

```python
def svc_start(context: dict[str, Any], name: str) -> bool:
    system = platform.system().lower()
    
    if system == "windows":
        r = exec_run(context, "sc start " + str(name))
        ok = r["rc"] == 0
        if not ok:
            _warning(context, "Failed to start service %s (rc=%s)", name, r["rc"])
        return ok
    
    elif system == "aix":
        r = exec_run(context, f"startsrc -s {name}")
        ok = r["rc"] == 0
        if not ok:
            _warning(context, "Failed to start AIX service %s (rc=%s)", name, r["rc"])
        return ok
    
    elif system == "sunos":  # NEW: Solaris SMF
        r = exec_run(context, f"svcadm enable {name}")
        ok = r["rc"] == 0
        if not ok:
            _warning(context, "Failed to start Solaris service %s (rc=%s)", name, r["rc"])
        return ok
    
    # Default: Linux systemd
    r = exec_run(context, "systemctl start " + str(name))
    ok = r["rc"] == 0
    if not ok:
        _warning(context, "Failed to start service %s (rc=%s)", name, r["rc"])
    return ok
```

**Impact**: Enables proper service management on Solaris using SMF

**Note**: Linux ppc64le and s390x use standard systemd, so no additional changes needed.

---

## Platform-Specific Notes

### Linux ppc64le (IBM Power)
- **Architecture**: `ppc64le` or `ppc64`
- **Service Manager**: systemd (same as Linux x64)
- **Shell**: bash/sh compatible
- **Special Requirements**: None - follows standard Linux flow

### Linux s390x (IBM Z)
- **Architecture**: `s390x` or `s390`
- **Service Manager**: systemd (same as Linux x64)
- **Shell**: bash/sh compatible
- **Special Requirements**: None - follows standard Linux flow

### SLES15 x86 (SUSE Linux Enterprise Server 15)
- **Architecture**: `x86_64`
- **Distribution ID**: `sles`, `suse`, or `sles_sap`
- **Service Manager**: systemd (same as Linux x64)
- **Shell**: bash/sh compatible
- **Special Requirements**: None - follows standard Linux flow
- **Notes**: SLES uses zypper package manager but installation follows standard binary deployment

### Solaris x86
- **Architecture**: `i86pc`, `x86_64`, or `amd64`
- **Service Manager**: SMF (Service Management Facility)
- **Shell**: POSIX-compliant sh
- **Special Requirements**: 
  - SMF commands: `svcadm`, `svcs`, `svcprop`
  - Different service management approach
  - May require additional SMF manifest configuration

---

## Testing Strategy

### 1. Unit Tests
```python
# Test artifact pattern matching
def test_artifact_patterns():
    patterns = ARTIFACT_PATTERNS
    assert re.match(patterns["linuxppc64le"], "1.2.3.4-IBM-SPOC-Linuxppc64le.bin")
    assert re.match(patterns["linuxs390x"], "1.2.3.4-IBM-SPOC-Linuxs390x.bin")
    assert re.match(patterns["solarisx86"], "1.2.3.4-IBM-SPOC-SolarisX86.bin")
    assert re.match(patterns["sles15"], "1.2.3.4-IBM-SPOC-SLES15X64.bin")

# Test OS detection
def test_os_detection():
    # Mock context for ppc64le
    ctx_ppc = {"os": {"family": "Linux", "arch": "ppc64le"}}
    result = os_oskey(ctx_ppc)
    assert result["osname"] == "linuxppc64le"
    
    # Mock context for s390x
    ctx_s390 = {"os": {"family": "Linux", "arch": "s390x"}}
    result = os_oskey(ctx_s390)
    assert result["osname"] == "linuxs390x"
    
    # Mock context for Solaris
    ctx_sol = {"os": {"family": "SunOS", "arch": "i86pc"}}
    result = os_oskey(ctx_sol)
    assert result["osname"] == "solarisx86"
    
    # Mock context for SLES15
    ctx_sles = {"os": {"family": "Linux", "id": "sles", "arch": "x86_64"}}
    result = os_oskey(ctx_sles)
    assert result["osname"] == "sles15"
```

### 2. Integration Tests
- Deploy test artifacts on actual target systems
- Verify installation completes successfully
- Verify service creation and startup
- Test upgrade scenarios
- Test uninstallation

### 3. Regression Tests
- Ensure existing platforms still work:
  - Windows x64
  - Linux x64
  - RHEL x64
  - AIX PPC
- Verify no breaking changes

---

## Files Modified Summary

| File | Lines Changed | Purpose |
|------|---------------|---------|
| [`plugins/modules/sp_server.py`](plugins/modules/sp_server.py) | 257-269, 726, 743 | Add artifact patterns, update platform checks |
| [`plugins/module_utils/sp_server_utils.py`](plugins/module_utils/sp_server_utils.py) | 74-101, 1013-1040, 650-850 | OS detection, artifact discovery, service management |

**Total Estimated Changes**: ~60-80 lines of code across 2 files

---

## Implementation Timeline

1. **Day 1**: Implement core changes (Phases 1-4)
2. **Day 2**: Implement Solaris service management (Phase 5)
3. **Day 3**: Unit testing and code review
4. **Day 4-5**: Integration testing on target platforms
5. **Day 6**: Documentation and release preparation

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Solaris SMF compatibility issues | Medium | High | Test thoroughly on actual Solaris systems |
| Architecture detection failures | Low | High | Add fallback detection mechanisms |
| Artifact naming inconsistencies | Low | Medium | Document naming conventions clearly |
| Service management differences | Medium | Medium | Implement platform-specific handlers |
| Regression on existing platforms | Low | High | Comprehensive regression testing |

---

## Next Steps

1. **Review this plan** with the development team
2. **Switch to Code mode** to implement the changes
3. **Create feature branch** for development
4. **Implement changes** following the checklist above
5. **Test thoroughly** on all target platforms
6. **Update documentation** with new platform support
7. **Submit for code review**
8. **Merge and release**

---

## Questions for Stakeholders

1. Do we have access to test systems for all three platforms?
2. Are there any additional platform-specific requirements not covered?
3. What is the priority order for these platforms?
4. Should we implement all three simultaneously or phase them?
5. Are there any compliance or security requirements specific to these platforms?

---

## Additional Resources

- **Platform Support Plan**: [`PLATFORM_SUPPORT_PLAN.md`](PLATFORM_SUPPORT_PLAN.md)
- **Architecture Diagrams**: [`IMPLEMENTATION_DIAGRAM.md`](IMPLEMENTATION_DIAGRAM.md)
- **Current Implementation**: [`plugins/modules/sp_server.py`](plugins/modules/sp_server.py)
- **Utility Functions**: [`plugins/module_utils/sp_server_utils.py`](plugins/module_utils/sp_server_utils.py)

---

**Document Version**: 1.0  
**Last Updated**: 2026-05-27  
**Status**: Ready for Implementation