import  json
class DSMParser:
    """
    A class to parse various output data from the DSM system into structured formats.
    """

    @staticmethod
    def parse_q_status(dsm_output):
        """
        Parses the 'q status' output into a dictionary.

        Args:
            dsm_output (str): The raw output string from the 'q status' command.

        Returns:
            dict: A dictionary with parsed key-value pairs based on the 'q status' output.
        """
        labels = [
            "Monitor Status", "Status Refresh Interval (Minutes)", "Status Retention (Hours)",
            "Monitor Message Alerts", "Alert Update Interval (Minutes)", "Alert to Email",
            "Send Alert Summary to Administrators", "Alert from Email Address", "Alert SMTP Host",
            "Alert SMTP Port", "Alert Active Duration (Minutes)", "Alert Inactive Duration (Minutes)",
            "Alert Closed Duration (Minutes)", "Monitoring Admin", "Monitored Group", "Monitored Servers",
            "At-Risk Interval for Applications", "Skipped files as At-Risk for Applications?",
            "At-Risk Interval for Virtual Machines", "Skipped files as At-Risk for Virtual Machines?",
            "At-Risk Interval for Systems", "Skipped files as At-Risk for Systems?"
        ]

        values = dsm_output.split(',')
        parsed_data = dict(zip(labels, values))

        return parsed_data

    @staticmethod
    def parse_q_monitorsettings(dsm_output):
        """
        Parses the 'q monitorsettings' output into a dictionary.

        Args:
            dsm_output (str): The raw output string from the 'q monitorsettings' command.

        Returns:
            dict: A dictionary with parsed key-value pairs based on the 'q monitorsettings' output.
        """
        labels = [
            "Monitor Status", "Status Refresh Interval (Minutes)", "Status Retention (Hours)",
            "Monitor Message Alerts", "Alert Update Interval (Minutes)", "Alert to Email",
            "Send Alert Summary to Administrators", "Alert from Email Address", "Alert SMTP Host",
            "Alert SMTP Port", "Alert Active Duration (Minutes)", "Alert Inactive Duration (Minutes)",
            "Alert Closed Duration (Minutes)", "Monitoring Admin", "Monitored Group", "Monitored Servers",
            "At-Risk Interval for Applications", "Skipped files as At-Risk for Applications?",
            "At-Risk Interval for Virtual Machines", "Skipped files as At-Risk for Virtual Machines?",
            "At-Risk Interval for Systems", "Skipped files as At-Risk for Systems?"
        ]

        values = dsm_output.split(',')
        parsed_data = dict(zip(labels, values))

        return parsed_data

    @staticmethod
    def parse_q_db(raw_output):
        """
        Parses the database information output into a structured dictionary.

        Args:
            raw_output (str): The raw output string from the database info query.

        Returns:
            dict: A dictionary with parsed database information (e.g., name, pages, usage).
        """
        raw_data = raw_output.splitlines()[0]
        parsed_data = [item.strip().replace('"', '') for item in raw_data.split(",")]

        parsed_output = {
            "Database Name": parsed_data[0],
            "Total Pages": parsed_data[1],
            "Usable Pages": parsed_data[2],
            "Used Pages": parsed_data[3],
            "Free Pages": parsed_data[4]
        }

        return parsed_output

    @staticmethod
    def parse_q_dbspace(raw_output):
        """
        Parses the space information output into a structured dictionary.

        Args:
            raw_output (str): The raw output string from the space info query.

        Returns:
            dict: A dictionary with parsed space information (total, used, and free space).
        """
        parsed_values = [item.strip().replace('"', '') for item in raw_output.strip().split(",")]
        parsed_output = {
            "Total Space (MB)": parsed_values[0],
            "Used Space (MB)": parsed_values[1],
            "Free Space (MB)": parsed_values[2]
        }

        return parsed_output

    def parse_q_log(raw_output):
        """
        Parses the space information output into a structured dictionary.

        Args:
            raw_output (str): The raw output string from the space info query.

        Returns:
            dict: A dictionary with parsed space information (total, used, and free space).
        """
        parsed_values = [item.strip().replace('"', '') for item in raw_output.strip().split(",")]
        parsed_output = {
            "Total Space (MB)": parsed_values[0],
            "Used Space (MB)": parsed_values[1],
            "Free Space (MB)": parsed_values[2]
        }

        return parsed_output

    @staticmethod
    def parse_q_domain(raw_output):
        """
        Parses the policy information output into a structured dictionary.

        Args:
            raw_output (str): The raw output string from the policy info query.

        Returns:
            dict: A dictionary with parsed policy information (e.g., domain name, nodes).
        """
        parsed_values = [item.strip() for item in raw_output.strip().split(",")]
        parsed_output = {
            "Policy Domain Name": parsed_values[0],
            "Activated Policy Set": parsed_values[1],
            "Activated Default Mgmt Class": parsed_values[2],
            "Number of Registered Nodes": parsed_values[3],
            "Description": parsed_values[4]
        }

        return parsed_output

    @staticmethod
    def parse_q_copygroup(raw_output):
        """
        Parses the policy settings output into a list of dictionaries.

        Args:
            raw_output (str): The raw output string from the policy settings query.

        Returns:
            list: A list of dictionaries, each containing parsed policy setting details.
        """
        rows = raw_output.strip().split("\n")
        keys = [
            "Policy Domain Name", "Policy Set Name", "Mgmt Class Name", "Copy Group Name",
            "Versions Data Exists", "Versions Data Deleted", "Retain Extra Versions", "Retain Only Version"
        ]

        parsed_output = []
        for row in rows:
            values = [value.strip() for value in row.split(",")]
            parsed_output.append(dict(zip(keys, values)))

        return parsed_output

    @staticmethod
    def parse_q_replrule(raw_output):
        """
        Parses the replication rules output into a dictionary.

        Args:
            raw_output (str): The raw output string from the replication rules query.

        Returns:
            dict: A dictionary with parsed replication rules and a footer message.
        """
        rows = raw_output.strip().split("\n")
        keys = [
            "Replication Rule Name", "Target Replication Server", "Active Only", "Enabled"
        ]
        parsed_output = []

        for row in rows:
            if row.startswith("ANR1999I"):
                continue
            values = [value.strip() if value else None for value in row.split(",")]
            parsed_output.append(dict(zip(keys, values)))

        footer_message = "ANR1999I QUERY REPLRULE completed successfully."
        return {"rules": parsed_output, "footer_message": footer_message}

    @staticmethod
    def parse_q_devclass(raw_output):
        """
        Parses the device class output into a dictionary.

        Args:
            raw_output (str): The raw output string from the device class query.

        Returns:
            dict: A dictionary with parsed device class details.
        """
        keys = [
            "Device Class Name", "Device Access Strategy", "Storage Pool Count",
            "Device Type", "Format", "Est/Max Capacity (MB)", "Mount Limit"
        ]

        values = [value.strip() if value else None for value in raw_output.strip().split(",")]
        parsed_output = dict(zip(keys, values))

        return parsed_output

    @staticmethod
    def parse_storage_space(raw_output):
        """
        Parses the storage space output into a dictionary.

        Args:
            raw_output (str): The raw output string from the storage space query.

        Returns:
            dict: A dictionary with parsed storage space details.
        """
        keys = [
            "Location", "Total Space of File System (MB)", "Used Space on File System (MB)", "Free Space (MB)"
        ]
        values = [value.strip('\"') for value in raw_output.strip().split(",")]
        parsed_output = dict(zip(keys, values))

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
        rows = [line.strip() for line in raw_output.strip().split("\n") if line.strip()]

        parsed_output = []
        for row in rows:
            values = [value.strip() for value in row.split(",")]
            parsed_output.append(dict(zip(keys, values)))

        return parsed_output

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

        rows = [line.strip() for line in raw_output.strip().split("\n") if line.strip()]
        parsed_output = []

        for row in rows:
            values = [value.strip() for value in row.split(",")]
            parsed_output.append(dict(zip(keys, values)))

        return parsed_output


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
