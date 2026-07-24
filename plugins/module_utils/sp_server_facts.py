import csv
import io
import re
import subprocess

from ..module_utils.dsmadmc_adapter import DsmadmcAdapter


class DsmadmcAdapterExtended(DsmadmcAdapter):
    """
    Extended DsmadmcAdapter to add support for the -commadelimited parameter.
    """

    def run_command(
            self, command, auto_exit=True, dataonly=True, exit_on_fail=True,
            commadelimited=True):

        command = (
            f'dsmadmc -servername={self.server_name} -id={self.username} -pass={self.password} '
            + ('-dataonly=yes ' if dataonly else '') +
            ('-commadelimited ' if commadelimited else '') +
            command
        )

        self.json_output['command'] = command
        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            raw_output = result.stdout.decode('utf-8')
            self.json_output['output'] = raw_output

            if auto_exit:
                self.json_output['changed'] = result.returncode == 0
                self.exit_json(**self.json_output)
            return result.returncode, raw_output, None
        except subprocess.CalledProcessError as e:
            if exit_on_fail:
                self.fail_json(msg=e.stderr.decode('utf-8'), rc=e.returncode, **self.json_output)
            return e.returncode, None, e.stderr.decode('utf-8')


class DSMParser:
    """
    A class to parse various output data from the DSM system into structured formats.
    """

    @staticmethod
    def _parse_csv_rows(raw_output):
        """
        Parse DSMADMC -commadelimited output as CSV.

        DSMADMC quotes values that contain thousands separators.  A plain
        split(',') corrupts those values and shifts every following field.
        """
        if not raw_output or not raw_output.strip():
            return []

        rows = csv.reader(io.StringIO(raw_output), skipinitialspace=True)
        return [
            [value.strip() for value in row]
            for row in rows
            if any(value.strip() for value in row)
        ]

    @staticmethod
    def _map_row(query, keys, row, row_number=1):
        if len(row) != len(keys):
            raise ValueError(
                "{0} row {1}: expected {2} fields but received {3}".format(
                    query, row_number, len(keys), len(row)
                )
            )
        return dict(zip(keys, row))

    @staticmethod
    def _single_csv_row(query, keys, raw_output):
        rows = DSMParser._parse_csv_rows(raw_output)
        if len(rows) != 1:
            raise ValueError(
                "{0}: expected 1 data row but received {1}".format(
                    query, len(rows)
                )
            )
        return DSMParser._map_row(query, keys, rows[0])

    @staticmethod
    def _developer_key(label):
        key = re.sub(r"[^A-Za-z0-9]+", "_", label.strip()).strip("_")
        return key.lower()

    @staticmethod
    def _parse_labeled_output(query, dsm_output, first_label):
        parsed_data = {}
        fields_started = False
        first_key = DSMParser._developer_key(first_label)

        for raw_line in dsm_output.splitlines():
            line = raw_line.strip()
            if not fields_started:
                if ":" not in line:
                    continue
                label, _ = line.split(":", 1)
                if DSMParser._developer_key(label) != first_key:
                    continue
                fields_started = True

            if line.startswith("ANS8002I"):
                break
            if not line or ":" not in line:
                continue

            label, value = line.split(":", 1)
            key = DSMParser._developer_key(label)
            if key:
                parsed_data[key] = value.strip()

        if not parsed_data:
            raise ValueError(
                "{0}: no label/value fields were found".format(query)
            )
        return parsed_data

    @staticmethod
    def parse_q_status(dsm_output):
        """
        Parses the 'q status' output into a dictionary.

        Args:
            dsm_output (str): The raw output string from the 'q status' command.

        Returns:
            dict: A dictionary with parsed key-value pairs based on the 'q status' output.
        """
        return DSMParser._parse_labeled_output(
            "q_status", dsm_output, "Server Name"
        )

    @staticmethod
    def parse_q_monitorsettings(dsm_output):
        """
        Parses the 'q monitorsettings' output into a dictionary.

        Args:
            dsm_output (str): The raw output string from the 'q monitorsettings' command.

        Returns:
            dict: A dictionary with parsed key-value pairs based on the 'q monitorsettings' output.
        """
        return DSMParser._parse_labeled_output(
            "q_monitorsettings", dsm_output, "Monitor Status"
        )

    @staticmethod
    def parse_q_db(raw_output):
        """
        Parses the database information output into a structured dictionary.

        Args:
            raw_output (str): The raw output string from the database info query.

        Returns:
            dict: A dictionary with parsed database information (e.g., name, pages, usage).
        """
        keys = [
            "Database Name", "Total Pages", "Usable Pages", "Used Pages",
            "Free Pages"
        ]
        return DSMParser._single_csv_row("q_db", keys, raw_output)

    @staticmethod
    def parse_q_dbspace(raw_output):
        """
        Parses the space information output into a structured dictionary.

        Args:
            raw_output (str): The raw output string from the space info query.

        Returns:
            list: Database directory records with total, used, and free space.
        """
        keys = [
            "Location", "Total Space (MB)", "Used Space (MB)",
            "Free Space (MB)"
        ]
        rows = DSMParser._parse_csv_rows(raw_output)
        if not rows:
            raise ValueError("q_dbspace: expected at least 1 data row")
        return [
            DSMParser._map_row("q_dbspace", keys, row, row_number)
            for row_number, row in enumerate(rows, start=1)
        ]

    @staticmethod
    def parse_q_log(raw_output):
        """
        Parses the space information output into a structured dictionary.

        Args:
            raw_output (str): The raw output string from the space info query.

        Returns:
            dict: A dictionary with parsed space information (total, used, and free space).
        """
        keys = ["Total Space (MB)", "Used Space (MB)", "Free Space (MB)"]
        return DSMParser._single_csv_row("q_log", keys, raw_output)

    @staticmethod
    def parse_q_domain(raw_output):
        """
        Parses policy domain output into a list of domain records.

        Args:
            raw_output (str): The raw output string from the policy info query.

        Returns:
            list: Policy domain records.
        """
        keys = [
            "Policy Domain Name", "Activated Policy Set",
            "Activated Default Mgmt Class", "Number of Registered Nodes",
            "Description"
        ]
        rows = DSMParser._parse_csv_rows(raw_output)
        return [
            DSMParser._map_row("q_domain", keys, row, row_number)
            for row_number, row in enumerate(rows, start=1)
        ]

    @staticmethod
    def parse_q_copygroup(raw_output):
        """
        Parses the policy settings output into a list of dictionaries.

        Args:
            raw_output (str): The raw output string from the policy settings query.

        Returns:
            list: A list of dictionaries, each containing parsed policy setting details.
        """
        keys = [
            "Policy Domain Name", "Policy Set Name", "Mgmt Class Name", "Copy Group Name",
            "Versions Data Exists", "Versions Data Deleted", "Retain Extra Versions", "Retain Only Version"
        ]

        rows = DSMParser._parse_csv_rows(raw_output)
        return [
            DSMParser._map_row("q_copygroup", keys, row, row_number)
            for row_number, row in enumerate(rows, start=1)
        ]

    @staticmethod
    def parse_q_replrule(raw_output):
        """
        Parses the replication rules output into a dictionary.

        Args:
            raw_output (str): The raw output string from the replication rules query.

        Returns:
            dict: A dictionary with parsed replication rules and a footer message.
        """
        keys = [
            "Replication Rule Name", "Target Replication Server", "Active Only", "Enabled"
        ]
        parsed_output = []

        rows = DSMParser._parse_csv_rows(raw_output)
        for row_number, row in enumerate(rows, start=1):
            if row and row[0].startswith("ANR1999I"):
                continue
            values = [value if value else None for value in row]
            parsed_output.append(
                DSMParser._map_row(
                    "q_replrule", keys, values, row_number
                )
            )

        footer_message = "ANR1999I QUERY REPLRULE completed successfully."
        return {"rules": parsed_output, "footer_message": footer_message}

    @staticmethod
    def parse_q_devclass(raw_output):
        """
        Parses device class output into a list of device class records.

        Args:
            raw_output (str): The raw output string from the device class query.

        Returns:
            list: Device class records.
        """
        keys = [
            "Device Class Name", "Device Access Strategy", "Storage Pool Count",
            "Device Type", "Format", "Est/Max Capacity (MB)", "Mount Limit"
        ]

        rows = DSMParser._parse_csv_rows(raw_output)
        parsed_output = []
        for row_number, row in enumerate(rows, start=1):
            values = [value if value else None for value in row]
            parsed_output.append(
                DSMParser._map_row(
                    "q_devclass", keys, values, row_number
                )
            )
        return parsed_output

    @staticmethod
    def parse_q_mgmtclass(raw_output):
        """
        Parses the policy management class output into a list of dictionaries.

        Args:
            raw_output (str): The raw output string from the policy management class query.

        Returns:
            list: A list of dictionaries with parsed policy management class details.
        """
        keys = [
            "Policy Domain Name", "Policy Set Name", "Mgmt Class Name", "Default Mgmt Class?", "Description"
        ]
        rows = DSMParser._parse_csv_rows(raw_output)
        return [
            DSMParser._map_row("q_mgmtclass", keys, row, row_number)
            for row_number, row in enumerate(rows, start=1)
        ]

    @staticmethod
    def parse_q_stgpool(raw_output):
        """
        Parses the storage pool output into a list of dictionaries.

        Args:
            raw_output (str): The raw output string from the storage pool query.

        Returns:
            list: A list of dictionaries with parsed storage pool details.
        """
        keys = [
            "Storage Pool Name", "Device Class Name", "Storage Type", "Estimated Capacity", "Pct Util",
            "Pct Migr", "High Mig Pct", "Low Mig Pct", "Next Storage Pool"
        ]

        rows = DSMParser._parse_csv_rows(raw_output)
        return [
            DSMParser._map_row("q_stgpool", keys, row, row_number)
            for row_number, row in enumerate(rows, start=1)
        ]


class SpServerResponseMapper:
    mapping = {
        "Copy Group Name": "copy_group_name",
        "Mgmt Class Name": "mgmt_class_name",
        "Policy Domain Name": "policy_domain_name",
        "Policy Set Name": "policy_set_name",
        "Retain Extra Versions": "retain_extra_versions",
        "Retain Only Version": "retain_only_version",
        "Versions Data Deleted": "versions_data_deleted",
        "Versions Data Exists": "versions_data_exists",
        "Free Space (MB)": "free_space_mb",
        "Total Space (MB)": "total_space_mb",
        "Used Space (MB)": "used_space_mb",
        "Location": "location",
        "Database Name": "database_name",
        "Total Pages": "total_pages",
        "Usable Pages": "usable_pages",
        "Used Pages": "used_pages",
        "Free Pages": "free_pages",
        "Replication Rule Name": "replication_rule_name",
        "Target Replication Server": "target_replication_server",
        "Active Only": "active_only",
        "Enabled": "enabled",
        "Device Access Strategy": "device_access_strategy",
        "Device Class Name": "device_class_name",
        "Device Type": "device_type",
        "Est/Max Capacity (MB)": "est_max_capacity_mb",
        "Format": "format",
        "Mount Limit": "mount_limit",
        "Storage Pool Count": "storage_pool_count",
        "Activated Default Mgmt Class": "activated_default_mgmt_class",
        "Activated Policy Set": "activated_policy_set",
        "Description": "description",
        "Number of Registered Nodes": "number_of_registered_nodes",
        "Monitor Message Alerts": "monitor_message_alerts",
        "Monitor Status": "monitor_status",
        "Monitored Group": "monitored_group",
        "Monitored Servers": "monitored_servers",
        "Monitoring Admin": "monitoring_admin",
        "Send Alert Summary to Administrators": "send_alert_summary_to_administrators",
        "Skipped files as At-Risk for Applications?": "skipped_files_at_risk_for_applications",
        "Skipped files as At-Risk for Systems?": "skipped_files_at_risk_for_systems",
        "Skipped files as At-Risk for Virtual Machines?": "skipped_files_at_risk_for_virtual_machines",
        "Status Refresh Interval (Minutes)": "status_refresh_interval_minutes",
        "Status Retention (Hours)": "status_retention_hours",
        "Estimated Capacity": "estimated_capacity",
        "High Mig Pct": "high_mig_pct",
        "Low Mig Pct": "low_mig_pct",
        "Next Storage Pool": "next_storage_pool",
        "Pct Migr": "pct_migr",
        "Pct Util": "pct_util",
        "Storage Pool Name": "storage_pool_name",
        "Storage Type": "storage_type",
        "Alert Active Duration (Minutes)": "alert_active_duration_minutes",
        "Default Mgmt Class?": "default_mgmt_class",
        "Alert Closed Duration (Minutes)": "alert_closed_duration_min",
        "Alert Inactive Duration (Minutes)": "alert_inactive_duration_minutes",
        "Alert SMTP Host": "alert_smtp_host",
        "Alert SMTP Port": "alert_smtp_port",
        "Alert Update Interval (Minutes)": "alert_update_interval_min",
        "Alert from Email Address": "alert_email_address",
        "Alert to Email": "alert_email",
        "At-Risk Interval for Applications": "at_risk_interval_applications",
        "At-Risk Interval for Systems": "at_risk_interval_systems",
        "At-Risk Interval for Virtual Machines": "at_risk_interval_vm",
    }

    @staticmethod
    def map_to_developer_friendly(json_data):

        if isinstance(json_data, dict):
            # Recursively map each key-value pair in the dictionary
            return {SpServerResponseMapper.mapping.get(key, key): SpServerResponseMapper.map_to_developer_friendly(value)
                    for key, value in json_data.items()}
        elif isinstance(json_data, list):
            # Recursively map each item in the list
            return [SpServerResponseMapper.map_to_developer_friendly(item) for item in json_data]
        else:
            return json_data
