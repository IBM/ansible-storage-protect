#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import subprocess
import re


def run_command(command):
    try:
        # Run the command and capture the output
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode('utf-8').strip(), result.stderr.decode('utf-8'), 0
    except subprocess.CalledProcessError as e:
        return "", e.stderr.decode('utf-8'), e.returncode

def extract_architecture(output):
    # Use regex to extract architecture from the 'lscpu' output
    match = re.search(r'Architecture:\s+(\S+)', output)
    if match:
        return match.group(1)  # Return the architecture value
    else:
        return "Unknown"

# In case the architecture is not found
def extract_disk_info(output):
    # Use regex to extract the disk information from the 'df -h /' output
    # The output usually looks like: Filesystem Size Used Avail Use% Mounted on
    match = re.search(r'(/dev/[^\s]+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(.*)', output)
    if match:
        filesystem = match.group(1)
        size = match.group(2)
        used = match.group(3)
        avail = match.group(4)
        use_percent = match.group(5)
        mounted_on = match.group(6)

        return {
            "filesystem": filesystem,
            "size": size,
            "used": used,
            "avail": avail,
            "use_percent": use_percent,
            "mounted_on": mounted_on
        }
    else:
        return {}

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
    # Normalize the input to lowercase to handle case sensitivity
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





def main():
    # Define the module parameters
    module_args = dict(
        command=dict(type='str', required=True)
    )

    # Instantiate the AnsibleModule object
    module = AnsibleModule(argument_spec=module_args)

    # Get the command from the module parameters
    command = module.params['command']

    # Execute the command
    stdout, stderr, rc = run_command(command)

    # Extract the architecture (or other relevant info) from the output
    if command=='lscpu | grep Architecture':
        if rc == 0:
            architecture = extract_architecture(stdout)
            module.exit_json(changed=True, architecture=architecture)
        else:
            module.fail_json(msg="Command failed", stderr=stderr)

    if command=='df -h /':
        if rc == 0:
            diskoutput = extract_disk_info(stdout)
            module.exit_json(changed=True, architecture=diskoutput)
        else:
            module.fail_json(msg="Command failed", stderr=stderr)

    if command=='cat /etc/os-release':
        if rc == 0:
            osinfo = extract_os_info(stdout)

            is_valid = check_os_compatibility(osinfo['os_name'],osinfo['os_version'])
            osinfo['valid'] = is_valid
            module.exit_json(changed=True, architecture=osinfo)
        else:
            module.fail_json(msg="Command failed", stderr=stderr)

    else:
        if rc == 0:
            output = stdout
            module.exit_json(changed=True, output=output)

if __name__ == '__main__':
    main()
