import re


class SPClientPreChecks:

    @staticmethod
    def parse_lscpu_architecture(output):
        """
        Parses the architecture from lscpu output and returns whether it is x86_64 or not.
        """
        match = re.search(r'Architecture:\s+(\S+)', output)
        if match:
            architecture = match.group(1)
            return architecture == 'x86_64'
        return False

    @staticmethod
    def parse_df_h_output(output):
        """
        Parses the 'df -h' output to determine if disk space is sufficient for installation.
        """
        match = re.search(r'(/dev/[^\s]+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\d+%)\s+(\S+)', output)
        if match:
            size = match.group(2)
            size_match = re.match(r'(\d+(\.\d+)?)\s*(\w+)', size)
            if size_match:
                size_value = float(size_match.group(1))
                size_unit = size_match.group(3)

                if size_unit == 'G':
                    size_value_in_gb = size_value
                elif size_unit == 'M':
                    size_value_in_gb = size_value / 1024
                else:
                    size_value_in_gb = size_value

                return size_value_in_gb >= 1.5
        return False

    @staticmethod
    def parse_os_release(output):
        """
        Parses /etc/os-release content to check if the OS is supported.
        """
        parsed_data = {}
        pattern = r'(\S+)="([^"]+)"'
        matches = re.findall(pattern, output)

        for match in matches:
            key, value = match
            parsed_data[key] = value

        supported_os_ids = ["rhel", "ubuntu", "sles"]
        supported_os_versions = [
            "SLES 12", "SLES 15", "RHEL 7", "RHEL 8", "RHEL 9",
            "Ubuntu 14.04 LTS", "Ubuntu 20.04 LTS", "Ubuntu 22.04 LTS"
        ]
        unsupported_os_versions = ["RHEL 6", "SLES 11"]

        if "ID" in parsed_data and parsed_data["ID"].lower() in supported_os_ids:
            return True
        if "VERSION" in parsed_data and any(
                os_version in parsed_data["VERSION"] for os_version in supported_os_versions):
            if any(unsupported_version in parsed_data["VERSION"] for unsupported_version in unsupported_os_versions):
                return False
            return True
        return False

    @staticmethod
    def parse_uname_r(output):
        """
        Parses 'uname -r' output to extract kernel version, distribution, and architecture.
        """
        pattern = r'([\d\.]+)-([\d\.]+)\.([\d]+)\.([\w]+)_([\d]+)\.([a-zA-Z0-9_]+)'
        match = re.match(pattern, output)

        if match:
            return {
                "kernel_version": match.group(1),
                "major_minor_version": match.group(2),
                "distribution": match.group(3),
                "version_id": match.group(4),
                "architecture": match.group(6)
            }
        return None

    @staticmethod
    def check_filesystem_compatibility(df_output):
        """
        Checks if the filesystem type in 'df' output is supported.
        """
        supported_filesystems = ['xfs', 'ext2', 'ext3']
        lines = df_output.splitlines()

        for line in lines:
            columns = line.split()
            if len(columns) > 1:
                fs_type = columns[1]
                if fs_type in supported_filesystems:
                    return True
        return False

    @staticmethod
    def check_java_availability(output):
        """
        Checks if Java is available by looking for its version in the output.
        """
        if "command not found" in output:
            return False

        java_version_pattern = re.compile(r"openjdk version|java version")
        return bool(java_version_pattern.search(output))



# commad_parser_mapping = {
#     "lscpu | grep Architecture":parse_lscpu_architecture,
#     "df -h /":parse_df_h_output,
#     "cat /etc/os-release":parse_os_release,
#     "df -T":check_filesystem_compatibility,
#     "java -version":check_java_availability
# }