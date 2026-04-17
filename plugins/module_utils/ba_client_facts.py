# -*- coding: utf-8 -*-
# IBM Storage Protect BA Client Facts Utility Module

import subprocess
import platform
import re

# Try to import Ansible (for Linux/normal use)
HAS_ANSIBLE = False
try:
    from ansible.module_utils.basic import AnsibleModule, env_fallback
    HAS_ANSIBLE = True
except ImportError:
    # On Windows or standalone execution, Ansible not available
    AnsibleModule = None
    env_fallback = None

# Try relative import first (Ansible module structure)
try:
    from ..module_utils.dsmc_adapter import DsmcAdapter
except ImportError:
    # Fallback to direct import (Windows standalone)
    try:
        from dsmc_adapter import DsmcAdapter
    except ImportError:
        # Create a minimal DsmcAdapter if not available
        class DsmcAdapter:
            def __init__(self, server_name, node_name, password):
                self.server_name = server_name
                self.node_name = node_name
                self.password = password


class DsmcAdapterExtended(DsmcAdapter):
    """
    Extended DsmcAdapter to add support for various query commands with comma-delimited output.
    """

    def run_command(self, command, auto_exit=True, dataonly=True, exit_on_fail=True):
        """
        Run a DSMC command with appropriate parameters.
        
        Args:
            command: The DSMC command to execute
            auto_exit: Whether to automatically exit after command execution
            dataonly: Whether to use -dataonly=yes parameter (ignored for query session)
            exit_on_fail: Whether to fail on command error
            
        Returns:
            tuple: (return_code, stdout, stderr)
        """
        # Build the command based on platform
        system_platform = platform.system().lower()
        is_windows = system_platform.startswith("win")
        is_aix = system_platform == "aix"
        
        if is_windows:
            dsmc_cmd = 'dsmc.exe'
        elif is_aix:
            # AIX: Try to find DSMC in common locations
            dsmc_cmd = self._find_dsmc_aix()
            if not dsmc_cmd:
                if exit_on_fail:
                    self.fail_json(msg="DSMC not found on AIX system. Checked: /usr/bin/dsmc, /opt/tivoli/tsm/client/ba/bin/dsmc, /usr/tivoli/tsm/client/ba/bin/dsmc")
                return 1, "", "DSMC not found"
        else:
            dsmc_cmd = 'dsmc'
        
        # Get user credentials
        user_id = getattr(self, 'user_id', self.node_name)
        password = self.password
        
        # Build full command - dsmc query session works WITHOUT parameters
        # It reads configuration from dsm.opt/dsm.sys
        full_command = f'{dsmc_cmd} {command}'
        
        self.json_output['command'] = full_command
        
        # Prepare input for interactive prompts (user ID and password)
        input_data = f"{user_id}\n{password}\n"
        
        # AIX-specific environment setup
        env = None
        if is_aix:
            import os
            env = os.environ.copy()
            env['LANG'] = 'C'  # Ensure English output for consistent parsing
            env['LC_ALL'] = 'C'
        
        try:
            result = subprocess.run(
                full_command,
                shell=True,
                input=input_data,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30,
                env=env
            )
            raw_output = result.stdout
            self.json_output['output'] = raw_output
            self.json_output['stderr'] = result.stderr

            if auto_exit:
                self.json_output['changed'] = result.returncode == 0
                self.exit_json(**self.json_output)
            
            return result.returncode, raw_output, result.stderr
            
        except subprocess.TimeoutExpired:
            if exit_on_fail:
                self.fail_json(
                    msg="Command timed out after 30 seconds",
                    **self.json_output
                )
            return 1, "", "Timeout"
        except subprocess.CalledProcessError as e:
            if exit_on_fail:
                self.fail_json(
                    msg=e.stderr,
                    rc=e.returncode,
                    **self.json_output
                )
            return e.returncode, None, e.stderr
    
    def _find_dsmc_aix(self):
        """
        Find DSMC binary on AIX system.
        
        Returns:
            str: Path to DSMC binary or None if not found
        """
        import os
        possible_paths = [
            '/usr/bin/dsmc',
            '/opt/tivoli/tsm/client/ba/bin/dsmc',
            '/usr/tivoli/tsm/client/ba/bin/dsmc'
        ]
        
        for path in possible_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path
        
        return None

class DSMCParser:
    """
    A class to parse various output data from the DSMC (BA Client) system into structured formats.
    """

    @staticmethod
    def parse_q_version(dsmc_output):
        """
        Parses the 'query session' output to extract version information.
        
        Args:
            dsmc_output (str): The raw output string from the 'query session' command.
            
        Returns:
            dict: A dictionary with parsed version information.
        """
        version_info = {}
        
        # Extract version from output
        version_match = re.search(r'Client Version\s+(\d+),\s*Release\s+(\d+),\s*Level\s+(\d+)\.(\d+)', dsmc_output)
        if version_match:
            version_info['client_version'] = f"{version_match.group(1)}.{version_match.group(2)}.{version_match.group(3)}.{version_match.group(4)}"
        
        # Extract client name
        name_match = re.search(r'(IBM Storage Protect|IBM Spectrum Protect|Tivoli Storage Manager)', dsmc_output)
        if name_match:
            version_info['client_name'] = name_match.group(1)
        
        # Extract API version if available
        api_match = re.search(r'API Version\s+(\d+\.\d+\.\d+\.\d+)', dsmc_output)
        if api_match:
            version_info['api_version'] = api_match.group(1)
        
        return version_info

    @staticmethod
    def parse_q_session(dsmc_output):
        """
        Parses the 'query session' output into a dictionary.
        
        Args:
            dsmc_output (str): The raw output string from the 'query session' command.
            
        Returns:
            dict: A dictionary with parsed session information.
        """
        session_info = {}
        
        # Parse comma-delimited output
        lines = dsmc_output.strip().split('\n')
        for line in lines:
            if 'Server Name' in line or 'Server name' in line:
                parts = line.split(',')
                if len(parts) >= 1:
                    session_info['server_name'] = parts[0].strip().replace('"', '')
            
            if 'Server address' in line or 'Server Address' in line:
                match = re.search(r'(\d+\.\d+\.\d+\.\d+):(\d+)', line)
                if match:
                    session_info['server_address'] = match.group(1)
                    session_info['server_port'] = match.group(2)
            
            if 'Node name' in line or 'Node Name' in line:
                parts = line.split(':')
                if len(parts) >= 2:
                    session_info['node_name'] = parts[1].strip().replace('"', '')
        
        return session_info

    @staticmethod
    def parse_q_schedule(dsmc_output):
        """
        Parses the 'query schedule' output into a list of dictionaries.
        
        Args:
            dsmc_output (str): The raw output string from the 'query schedule' command.
            
        Returns:
            list: A list of dictionaries with parsed schedule information.
        """
        schedules = []
        lines = dsmc_output.strip().split('\n')
        
        keys = [
            "Schedule Name", "Action", "Objects", "Options", "Server Window Start",
            "Duration", "Schedule Style", "Day of Week", "Month", "Day of Month",
            "Week of Month", "Last Run", "Next Run", "Status"
        ]
        
        for line in lines:
            if line.strip() and not line.startswith('ANR'):
                values = [v.strip().replace('"', '') for v in line.split(',')]
                if len(values) >= len(keys):
                    schedules.append(dict(zip(keys, values)))
        
        return schedules

    @staticmethod
    def parse_q_filespace(dsmc_output):
        """
        Parses the 'query filespace' output into a list of dictionaries.
        
        Args:
            dsmc_output (str): The raw output string from the 'query filespace' command.
            
        Returns:
            list: A list of dictionaries with parsed filespace information.
        """
        filespaces = []
        lines = dsmc_output.strip().split('\n')
        
        keys = [
            "Filespace Name", "FSID", "Platform", "Filespace Type", "Capacity (MB)",
            "Pct Util", "Last Backup Start", "Last Backup Completion"
        ]
        
        for line in lines:
            if line.strip() and not line.startswith('ANR'):
                values = [v.strip().replace('"', '') for v in line.split(',')]
                if len(values) >= 3:  # At least filespace name, FSID, and platform
                    # Pad values if needed
                    while len(values) < len(keys):
                        values.append('')
                    filespaces.append(dict(zip(keys, values[:len(keys)])))
        
        return filespaces

    @staticmethod
    def parse_q_backup(dsmc_output):
        """
        Parses the 'query backup' output into backup statistics.
        
        Args:
            dsmc_output (str): The raw output string from the 'query backup' command.
            
        Returns:
            dict: A dictionary with parsed backup statistics.
        """
        backup_info = {
            'total_files': 0,
            'total_size_mb': 0,
            'files_list': []
        }
        
        lines = dsmc_output.strip().split('\n')
        
        for line in lines:
            if line.strip() and not line.startswith('ANR'):
                parts = line.split(',')
                if len(parts) >= 3:
                    file_info = {
                        'file_path': parts[0].strip().replace('"', ''),
                        'size_bytes': parts[1].strip().replace('"', '') if len(parts) > 1 else '0',
                        'backup_date': parts[2].strip().replace('"', '') if len(parts) > 2 else ''
                    }
                    backup_info['files_list'].append(file_info)
                    backup_info['total_files'] += 1
        
        return backup_info

    @staticmethod
    def parse_q_archive(dsmc_output):
        """
        Parses the 'query archive' output into archive statistics.
        
        Args:
            dsmc_output (str): The raw output string from the 'query archive' command.
            
        Returns:
            dict: A dictionary with parsed archive statistics.
        """
        archive_info = {
            'total_files': 0,
            'total_size_mb': 0,
            'archives_list': []
        }
        
        lines = dsmc_output.strip().split('\n')
        
        for line in lines:
            if line.strip() and not line.startswith('ANR'):
                parts = line.split(',')
                if len(parts) >= 3:
                    file_info = {
                        'file_path': parts[0].strip().replace('"', ''),
                        'size_bytes': parts[1].strip().replace('"', '') if len(parts) > 1 else '0',
                        'archive_date': parts[2].strip().replace('"', '') if len(parts) > 2 else ''
                    }
                    archive_info['archives_list'].append(file_info)
                    archive_info['total_files'] += 1
        
        return archive_info

    @staticmethod
    def parse_q_inclexcl(dsmc_output):
        """
        Parses the 'query inclexcl' output into include/exclude rules.
        
        Args:
            dsmc_output (str): The raw output string from the 'query inclexcl' command.
            
        Returns:
            dict: A dictionary with parsed include/exclude rules.
        """
        rules = {
            'include_rules': [],
            'exclude_rules': []
        }
        
        lines = dsmc_output.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('INCLUDE'):
                rules['include_rules'].append(line)
            elif line.startswith('EXCLUDE'):
                rules['exclude_rules'].append(line)
        
        return rules

    @staticmethod
    def parse_q_systeminfo(dsmc_output):
        """
        Parses system information from DSMC output.
        
        Args:
            dsmc_output (str): The raw output string.
            
        Returns:
            dict: A dictionary with parsed system information.
        """
        system_info = {
            'hostname': platform.node(),
            'os_type': platform.system(),
            'os_version': platform.version(),
            'architecture': platform.machine(),
            'python_version': platform.python_version()
        }
        
        # Extract additional info from dsmc output if available
        if 'Operating system' in dsmc_output:
            os_match = re.search(r'Operating system\s*:\s*(.+)', dsmc_output)
            if os_match:
                system_info['client_os'] = os_match.group(1).strip()
        
        return system_info

    @staticmethod
    def parse_q_options(dsmc_output):
        """
        Parses the 'query options' output into configuration options.
        
        Args:
            dsmc_output (str): The raw output string from the 'query options' command.
            
        Returns:
            dict: A dictionary with parsed configuration options.
        """
        options = {}
        
        lines = dsmc_output.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('ANR') and not line.startswith('#'):
                # Parse option lines (format: OPTION_NAME value)
                parts = line.split(None, 1)
                if len(parts) == 2:
                    option_name = parts[0].lower()
                    option_value = parts[1].strip()
                    options[option_name] = option_value
        
        return options


class BAClientResponseMapper:
    """
    Maps BA Client response keys to developer-friendly snake_case format.
    """
    
    mapping = {
        "Schedule Name": "schedule_name",
        "Action": "action",
        "Objects": "objects",
        "Options": "options",
        "Server Window Start": "server_window_start",
        "Duration": "duration",
        "Schedule Style": "schedule_style",
        "Day of Week": "day_of_week",
        "Month": "month",
        "Day of Month": "day_of_month",
        "Week of Month": "week_of_month",
        "Last Run": "last_run",
        "Next Run": "next_run",
        "Status": "status",
        "Filespace Name": "filespace_name",
        "FSID": "fsid",
        "Platform": "platform",
        "Filespace Type": "filespace_type",
        "Capacity (MB)": "capacity_mb",
        "Pct Util": "pct_util",
        "Last Backup Start": "last_backup_start",
        "Last Backup Completion": "last_backup_completion",
        "Client Version": "client_version",
        "Client Name": "client_name",
        "API Version": "api_version",
        "Server Name": "server_name",
        "Server Address": "server_address",
        "Server Port": "server_port",
        "Node Name": "node_name",
        "File Path": "file_path",
        "Size Bytes": "size_bytes",
        "Backup Date": "backup_date",
        "Archive Date": "archive_date",
        "Total Files": "total_files",
        "Total Size MB": "total_size_mb",
        "Include Rules": "include_rules",
        "Exclude Rules": "exclude_rules",
        "Hostname": "hostname",
        "OS Type": "os_type",
        "OS Version": "os_version",
        "Architecture": "architecture",
        "Python Version": "python_version",
        "Client OS": "client_os"
    }

    @staticmethod
    def map_to_developer_friendly(json_data):
        """
        Recursively maps response keys to snake_case format.
        
        Args:
            json_data: Dictionary, list, or primitive value to map
            
        Returns:
            Mapped data structure with developer-friendly keys
        """
        if isinstance(json_data, dict):
            # Recursively map each key-value pair in the dictionary
            return {
                BAClientResponseMapper.mapping.get(key, key.lower().replace(' ', '_').replace('(', '').replace(')', '')): 
                BAClientResponseMapper.map_to_developer_friendly(value)
                for key, value in json_data.items()
            }
        elif isinstance(json_data, list):
            # Recursively map each item in the list
            return [BAClientResponseMapper.map_to_developer_friendly(item) for item in json_data]
        else:
            return json_data

# Made with Bob
