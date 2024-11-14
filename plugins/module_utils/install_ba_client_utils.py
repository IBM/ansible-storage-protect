import logging
import re
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
        result = disk_space

        if not result['status']:
            self.incompatible_reasons.append(result['message'])
            return  # Early return if disk space info is invalid

        # Converting the 'avail' value to a float and compare with 1.4GB
        available_space = result.get('avail', '').replace('G', '')  # Removeing 'G' to convert to numeric
        try:
            available_space = float(available_space)  # Converting to float
        except ValueError:
            self.incompatible_reasons.append("Invalid available disk space value.")
            return

        if available_space > 1.4:
            logging.info("Disk space is valid: Available space is greater than 1.4GB.")
        else:
            self.incompatible_reasons.append("Insufficient disk space. Available space is less than 1.4GB.")
            logging.error("Disk space check failed: Insufficient space.")

    def check_os(self):
        """Check if the operating system is compatible."""
        os_info = self.system_info.get("OS Release Info", "")
        if os_info:
            os_name = os_info.get("os_name", "")
            os_version = os_info.get("os_version", "")
            logging.debug(f"OS check: {os_name} {os_version}")
            if not check_os_compatibility(os_name, os_version):
                self.incompatible_reasons.append(f"Incompatible OS. {os_name} {os_version} is not supported.")
        else:
            self.incompatible_reasons.append("Failed to extract OS info.")


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
        """Performing all compatibility checks and returning the result."""

        self.check_architecture()
        self.check_disk_space()
        self.check_os()
        self.check_filesystem()
        self.check_java()

        if not self.incompatible_reasons:

            return {"compatible": True, "reason": "System is compatible."}


        return {"compatible": False, "reason": "Incompatible system.", "details": self.incompatible_reasons}



class SystemInfoCollector:
    """Collects system information using shell commands and processes the output."""

    def __init__(self, command_executor):
        self.command_executor = command_executor

    def collect(self):
        """Collects system information like architecture, disk space, OS details, etc."""
        system_info = {}

        # Collect architecture info

        lscpu_output = self.command_executor.execute("lscpu")
        system_info['Architecture'] = extract_architecture(lscpu_output)


        # Collect disk space info

        df_output = self.command_executor.execute("df -h /")

        system_info['Filesystem Disk Space'] = extract_disk_info(df_output)

        # Collect OS release info

        os_release_output = self.command_executor.execute("cat /etc/os-release")
        os_info = extract_os_info(os_release_output)
        system_info['OS Release Info'] = os_info


        # Collect filesystem type info

        fs_type_output = self.command_executor.execute("df -T /")
        system_info['Filesystem Type'] = fs_type_output.splitlines()[1].split()[1]  # Extract file system type


        # Collect Java version info

        java_version_output = self.command_executor.execute("java -version 2>&1")
        if "not found" in java_version_output:
            system_info['Java Version'] = "Java is not installed on the system."
        else:
            system_info['Java Version'] = java_version_output.splitlines()[0]


        return system_info



# Helper functions
def extract_architecture(output):
    # Use regex to extract architecture from the 'lscpu' output
    match = re.search(r'Architecture:\s+(\S+)', output)
    if match:
        return match.group(1)  # Return the architecture value
    else:
        return "Unknown"


def extract_disk_info(output):
    """Extract disk space information from the df -h / output."""
    logging.debug(f"Raw df output: {output}")
    if not isinstance(output, str) or not output.strip():

        return {"status": False, "message": "Invalid or empty disk space output."}

    # Use regex to extract the disk information from the 'df -h /' output
    match = re.search(r'(/dev/[^\s]+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(.*)', output)
    if match:
        filesystem = match.group(1)
        size = match.group(2)
        used = match.group(3)
        avail = match.group(4)
        use_percent = match.group(5)
        mounted_on = match.group(6)


        return {
            "status": True,
            "filesystem": filesystem,
            "size": size,
            "used": used,
            "avail": avail,
            "use_percent": use_percent,
            "mounted_on": mounted_on
        }
    else:
        logging.error("Failed to parse disk space information.")
        return {"status": False, "message": "Failed to parse disk space information."}




def extract_os_info(output):
    # Use regex to extract the OS name and version from the '/etc/os-release' output
    name_match = re.search(r'NAME="([^"]+)"', output)
    version_id_match = re.search(r'VERSION_ID="([^"]+)"', output)

    if name_match and version_id_match:
        name = name_match.group(1)
        version = version_id_match.group(1)
        return {
            "os_name": name,
            "os_version": version
        }
    else:
        return {}


def check_os_compatibility(os_name, os_version):
    os_name = os_name.strip().lower()
    os_version = os_version.strip().lower()

    # RHEL versions starting with 6, 7, 8, or 9 are compatible
    if "red" in os_name and os_version[0] in ['6', '7', '8', '9']:
        return True

    # Specific compatible Ubuntu versions
    ubuntu_versions = ["14.04", "16.04", "18.04", "20.04", "22.04"]
    if "ubuntu" in os_name and os_version in ubuntu_versions:
        return True

    # If none of the conditions are met, return False
    return False


