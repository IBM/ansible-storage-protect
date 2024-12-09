import logging
import re
import  os
import subprocess

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
    """Collects system information using commands and processes the output."""

    def __init__(self, command_executor):
        self.command_executor = command_executor

    def collect(self):
        """Collects system information like architecture, disk space, OS details, etc."""
        system_info = {}

        # Collect architecture info
        lscpu_output, lscpu_code, lscpu_err = self.command_executor.execute("lscpu")
        if lscpu_code == 0:
            system_info['Architecture'] = extract_architecture(lscpu_output)
        else:
            system_info['Architecture'] = f"Error: {lscpu_output}"

        # Collect disk space info
        df_output, df_code, df_err = self.command_executor.execute("df -h /")
        if df_code == 0:
            system_info['Filesystem Disk Space'] = extract_disk_info(df_output)
        else:
            system_info['Filesystem Disk Space'] = f"Error: {df_output}"

        # Collect OS release info
        os_release_output, os_release_code, os_release_err = self.command_executor.execute("cat /etc/os-release")
        if os_release_code == 0:
            os_info = extract_os_info(os_release_output)
            system_info['OS Release Info'] = os_info
        else:
            system_info['OS Release Info'] = f"Error: {os_release_output}"

        # Collect filesystem type info
        fs_type_output, fs_type_code, fs_type_err = self.command_executor.execute("df -T /")
        if fs_type_code == 0:
            system_info['Filesystem Type'] = fs_type_output.splitlines()[1].split()[1]  # Extract file system type
        else:
            system_info['Filesystem Type'] = f"Error: {fs_type_output}"

        # Collect Java version info
        java_version_output, java_version_code, java_version_err = self.command_executor.execute("java -version 2>&1")
        if java_version_code != 0:
            system_info['Java Version'] = "Java is not installed on the system."
        else:
            system_info['Java Version'] = java_version_output.splitlines()[0]

        return system_info


# Helper functions
def extract_architecture(output):
    # Using regex to extract architecture from the 'lscpu' output
    match = re.search(r'Architecture:\s+(\S+)', output)
    if match:
        return match.group(1)  # Return the architecture value
    else:
        return "Unknown"


def extract_disk_info(output):
    """Extracting disk space information from the df -h / output."""
    logging.debug(f"Raw df output: {output}")
    if not isinstance(output, str) or not output.strip():

        return {"status": False, "message": "Invalid or empty disk space output."}

    # Using regex to extract the disk information from the 'df -h /' output
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
    # Using regex to extract the OS name and version from the '/etc/os-release' output
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


    return False


def extract_tar(module, path, dest_folder):
    """
    This function checks if the .tar file exists and extracts it to the destination folder.
    """
    try:

        module.log(msg=f"Checking if file {path} exists on the remote host.")
        if not os.path.exists(path):
            module.fail_json(msg=f"Error: File {path} does not exist on the remote host.")
        module.log(msg=f"File {path} found.")


        module.log(msg=f"Checking if destination folder {dest_folder} exists.")
        if not os.path.exists(dest_folder):
            module.log(msg=f"Destination folder {dest_folder} does not exist. Creating it.")
            os.makedirs(dest_folder)
        else:
            module.log(msg=f"Destination folder {dest_folder} already exists.")


        extract_command = f"tar -xvf {path} -C {dest_folder}"
        module.log(msg=f"Running extract command: {extract_command}")


        rc, stdout, stderr = module.run_command(extract_command)


        if rc != 0:
            module.fail_json(msg=f"Failed to extract tar file. Command Error: {stderr}")


        module.log(msg="Tar file extracted successfully.")
        return {'changed': True, 'msg': 'Tar file extracted successfully.'}

    except PermissionError as e:
        module.fail_json(msg=f"Permission denied error: {str(e)}. Check directory permissions for {dest_folder}.")
    except FileNotFoundError as e:
        module.fail_json(msg=f"File not found error: {str(e)}. Ensure the tar file {path} exists.")
    except Exception as e:
        module.fail_json(msg=f"An unexpected error occurred: {str(e)}")


def install_rpm_packages_in_sequence(directory):
    """
    Installs RPM packages in the specified sequence.
    Returns a dictionary of installation results.
    """
    sequence = {
        "GSKit": [],
        "API": [],
        "BA": [],
        "Additional": []
    }

    # Categorize packages into the specified sequence
    try:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.rpm'):
                    filepath = os.path.join(root, file)
                    if "gskit" in file.lower():
                        sequence["GSKit"].append(filepath)
                    elif "api" in file.lower():
                        sequence["API"].append(filepath)
                    elif "ba" in file.lower():
                        sequence["BA"].append(filepath)
                    elif "additional" in file.lower():
                        sequence["Additional"].append(filepath)
    except Exception as e:
        raise Exception(f"Error identifying RPM packages: {str(e)}")

    # Install packages in the defined sequence
    results = {}
    for category in ["GSKit", "API", "BA", "Additional"]:
        for package in sequence[category]:
            command = f'sudo rpm -ivh {package}'
            try:
                stdout, rc, err = CommandExecutor.execute(command)
                results[package] = {
                    "rc": rc,
                    "stdout": stdout,
                    "stderr":err
                }
            except Exception as e:
                results[package] = {"error": str(e)}
    return results



def parse_dsm_output(output):
    """
    Parses the output of the DSM command and checks for specific warning messages.

    Args:
        output (str): The output from the DSM command.

    Returns:
        str: A message indicating the status of the installation or configuration.
    """
    if "ANS0990W" in output:
        return "BA Client installed successfully. Configure the dsm.opt and dsm.sys", True

    # You can add more conditions here if necessary to check other warnings or errors
    return "BA Client installation encountered issues. Please check the logs for details.", False
