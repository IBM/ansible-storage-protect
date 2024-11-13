from ansible.module_utils.command_executor import CommandExecutor


class CompatibilityChecker:
    """Checks system compatibility based on defined requirements."""

    def __init__(self, system_info):
        self.system_info = system_info
        self.incompatible_reasons = []

    def check_architecture(self):
        """Check if the system architecture is x86_64."""
        architecture = self.system_info.get("Architecture", "")
        if "x86_64" not in architecture:
            self.incompatible_reasons.append("Incompatible architecture. x86_64 required.")

    def check_disk_space(self):
        """Check if the system has sufficient disk space."""
        disk_space = self.system_info.get("Filesystem Disk Space", "")
        lines = disk_space.splitlines()
        root_line = next((line for line in lines if "/dev/mapper/rhel-root" in line), None)
        if root_line:
            used_space = int(float(root_line.split()[2].replace('G', '')))
            if used_space < 1.5:
                self.incompatible_reasons.append("Insufficient disk space. 1.5 GB required.")

    def check_os(self):
        """Check if the operating system is compatible."""
        supported_os_versions = [
            {"name": "SLES 11", "min_version": "11(3)"},
            {"name": "SLES 12", "min_version": "12"},
            {"name": "SLES 15", "min_version": "15 (Starting with 8.1.6)"},
            {"name": "RHEL 6", "min_version": "6 (Starting with 6.3)"},
            {"name": "RHEL 7", "min_version": "7"},
            {"name": "RHEL 8", "min_version": "8 (Starting with 8.1.9)"},
            {"name": "RHEL 9", "min_version": "9 (Starting with 8.1.15)"},
            {"name": "Ubuntu 14.04 LTS", "min_version": "14.04 LTS"},
            {"name": "Ubuntu 16.04 LTS", "min_version": "16.04 LTS"},
            {"name": "Ubuntu 18.04 LTS", "min_version": "18.04 LTS (Starting with 8.1.6)"},
            {"name": "Ubuntu 20.04 LTS", "min_version": "20.04 LTS (Starting with 8.1.10)"},
            {"name": "Ubuntu 22.04 LTS", "min_version": "22.04 LTS (Starting with 8.1.15)"}
        ]

        os_info = self.system_info.get("OS Release Info", "")
        os_version_found = False
        for os_version in supported_os_versions:
            if os_version["name"] in os_info:
                os_version_found = True
                if os_version["min_version"] not in os_info:
                    self.incompatible_reasons.append(
                        f"OS version not compatible. Required: {os_version['min_version']}")
                break

        if not os_version_found:
            self.incompatible_reasons.append(
                "Incompatible OS. Supported OS versions: " + ", ".join([os['name'] for os in supported_os_versions]))

    def check_filesystem(self):
        """Check if the filesystem type is supported."""
        filesystem_type = self.system_info.get("Filesystem Type", "")
        if filesystem_type not in ['xfs', 'ext2', 'ext3']:
            self.incompatible_reasons.append(f"Incompatible filesystem type. Supported types: xfs, ext2, ext3")

    def check_java(self):
        """Check if Java is installed on the system."""
        java_version = self.system_info.get("Java Version", "")
        if "Java is not installed on the system." in java_version:
            self.incompatible_reasons.append("Java is not installed. Please install Java.")

    def check_compatibility(self):
        """Performing all compatibility checks and returnin the result."""
        self.check_architecture()
        self.check_disk_space()
        self.check_os()
        self.check_filesystem()
        self.check_java()

        if not self.incompatible_reasons:
            return {"compatible": True, "reason": "System is compatible."}
        return {"compatible": False, "reason": "Incompatible system.", "details": self.incompatible_reasons}


class SystemInfoCollector:
    """Collects system information by executing commands."""

    def __init__(self, command_executor):
        self.command_executor = command_executor

    def collect(self):
        """Collects system information and returns a dictionary."""
        command_mapping = {
            "lscpu | grep Architecture": "Architecture",
            "df -h /": "Filesystem Disk Space",
            "cat /etc/os-release": "OS Release Info",
            "df -T": "Filesystem Type",
            "java -version": "Java Version",
        }
        result = {}
        for command, description in command_mapping.items():
            if command == "java -version":
                output = CommandExecutor.execute("which java")
                if "no java" in output:
                    output = "Java is not installed on the system."
            else:
                output = self.command_executor.execute(command)

            result[description] = output
        return result
