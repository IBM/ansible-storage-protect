# Platform Support Implementation Architecture

## System Architecture Overview

```mermaid
graph TD
    A[User Request] --> B[sp_server.py Main]
    B --> C[Get OS Info]
    C --> D[platform.system]
    C --> E[platform.machine]
    D --> F[os_oskey Function]
    E --> F
    F --> G{OS Family?}
    
    G -->|Windows| H[WindowsX64]
    G -->|Linux x86_64| I[LinuxX64 or RhelX64]
    G -->|Linux ppc64le| J[Linuxppc64le]
    G -->|Linux s390x| K[Linuxs390x]
    G -->|Solaris x86| L[SolarisX86]
    G -->|AIX| M[AixPPC]
    
    H --> N[Find Artifact]
    I --> N
    J --> N
    K --> N
    L --> N
    M --> N
    
    N --> O[Artifact Discovery]
    O --> P{Match Pattern?}
    P -->|Yes| Q[Extract Version]
    P -->|No| R[Error: No Artifact]
    
    Q --> S[Deploy Installation]
    S --> T{OS Type?}
    
    T -->|Windows| U[install.bat]
    T -->|Linux/Unix| V[install.sh]
    
    V --> W[dos2unix conversion]
    W --> X[Execute Installation]
    U --> X
    
    X --> Y[Service Management]
    Y --> Z{Platform?}
    
    Z -->|Windows| AA[sc commands]
    Z -->|Linux| AB[systemd]
    Z -->|AIX| AC[SRC]
    Z -->|Solaris| AD[SMF]
    
    AA --> AE[Installation Complete]
    AB --> AE
    AC --> AE
    AD --> AE
```

## Artifact Pattern Matching Flow

```mermaid
graph LR
    A[Artifact File] --> B{Check Extension}
    B -->|.exe| C[Windows Pattern]
    B -->|.bin| D[Unix Pattern]
    
    C --> E[Match WindowsX64.exe]
    D --> F{Check Platform String}
    
    F -->|LinuxX64| G[Standard Linux]
    F -->|RhelX64| H[RHEL Family]
    F -->|AixPPC| I[AIX Power]
    F -->|Linuxppc64le| J[Linux Power]
    F -->|Linuxs390x| K[Linux Z]
    F -->|SolarisX86| L[Solaris x86]
    
    G --> M[Extract Version]
    H --> M
    I --> M
    J --> M
    K --> M
    L --> M
    
    M --> N[Select Best Match]
```

## Platform Detection Logic

```mermaid
graph TD
    A[Start Detection] --> B[Get platform.system]
    B --> C{System Type?}
    
    C -->|Linux| D[Get platform.machine]
    C -->|Windows| E[Return windows]
    C -->|AIX| F[Return aix]
    C -->|SunOS| G[Get platform.machine]
    
    D --> H{Architecture?}
    H -->|x86_64| I[Check Distro]
    H -->|ppc64le| J[Return linuxppc64le]
    H -->|s390x| K[Return linuxs390x]
    
    I --> L{Distro Type?}
    L -->|RHEL-like| M[Return rhel]
    L -->|Other| N[Return linux]
    
    G --> O{Architecture?}
    O -->|i86pc/x86_64| P[Return solarisx86]
    O -->|Other| Q[Return solaris]
    
    E --> R[Final OS Key]
    F --> R
    J --> R
    K --> R
    M --> R
    N --> R
    P --> R
    Q --> R
```

## Service Management by Platform

```mermaid
graph TD
    A[Service Operation] --> B{Platform?}
    
    B -->|Windows| C[Windows Services]
    B -->|Linux| D[systemd]
    B -->|AIX| E[SRC]
    B -->|Solaris| F[SMF]
    
    C --> C1[sc start/stop]
    C --> C2[sc config]
    C --> C3[sc delete]
    
    D --> D1[systemctl start/stop]
    D --> D2[systemctl enable/disable]
    D --> D3[systemctl daemon-reload]
    
    E --> E1[startsrc/stopsrc]
    E --> E2[mkitab/rmitab]
    E --> E3[rmssys]
    
    F --> F1[svcadm enable/disable]
    F --> F2[svcs status]
    F --> F3[svcadm clear]
```

## Installation Flow Comparison

```mermaid
graph LR
    A[Installation Start] --> B{Platform Type?}
    
    B -->|Windows| C[Windows Flow]
    B -->|Linux x64| D[Linux Flow]
    B -->|Linux ppc64le| D
    B -->|Linux s390x| D
    B -->|Solaris x86| E[Solaris Flow]
    B -->|AIX| F[AIX Flow]
    
    C --> C1[install.bat]
    C1 --> C2[Windows IM]
    
    D --> D1[install.sh]
    D1 --> D2[dos2unix]
    D2 --> D3[Unix IM]
    
    E --> E1[install.sh]
    E1 --> E2[Solaris IM]
    
    F --> F1[install.sh]
    F1 --> F2[POSIX patch]
    F2 --> F3[AIX IM]
    
    C2 --> G[Complete]
    D3 --> G
    E2 --> G
    F3 --> G
```

## Key Implementation Points

### 1. Architecture Detection
- **Linux ppc64le**: Detected via `platform.machine()` returning `ppc64le` or `ppc64`
- **Linux s390x**: Detected via `platform.machine()` returning `s390x` or `s390`
- **Solaris x86**: Detected via `platform.system()` = `SunOS` + `platform.machine()` = `i86pc`/`x86_64`/`amd64`

### 2. Artifact Naming Convention
All new platforms follow the pattern:
```
<version>-<vendor>-<product>-<platform>.bin

Examples:
- 1.2.3.4-IBM-SPOC-Linuxppc64le.bin
- 1.2.3.4-IBM-SPOC-Linuxs390x.bin
- 1.2.3.4-IBM-SPOC-SolarisX86.bin
```

### 3. Installation Script Compatibility
- **Linux ppc64le & s390x**: Use standard Linux `install.sh` with systemd
- **Solaris x86**: Use `install.sh` with SMF service management
- All require `dos2unix` conversion for line endings

### 4. Service Management Differences

| Platform | Service System | Start Command | Enable Command |
|----------|---------------|---------------|----------------|
| Windows | Windows Services | `sc start` | `sc config start=auto` |
| Linux x64 | systemd | `systemctl start` | `systemctl enable` |
| Linux ppc64le | systemd | `systemctl start` | `systemctl enable` |
| Linux s390x | systemd | `systemctl start` | `systemctl enable` |
| Solaris x86 | SMF | `svcadm enable` | `svcadm enable` |
| AIX | SRC | `startsrc -s` | `mkitab` |
