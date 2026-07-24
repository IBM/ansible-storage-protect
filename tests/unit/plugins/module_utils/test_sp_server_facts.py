import unittest
from pathlib import Path
from unittest import mock

from plugins.module_utils.sp_server_facts import (
    DSMParser,
    DsmadmcAdapterExtended,
    SpServerResponseMapper,
)


class TestDSMParser(unittest.TestCase):

    STATUS_FIXTURE = (
        Path(__file__).parent / "fixtures" / "q_status_list.txt"
    )
    MONITORSETTINGS_FIXTURE = (
        Path(__file__).parent
        / "fixtures"
        / "q_monitorsettings_list.txt"
    )

    def test_q_db_preserves_thousands_separators(self):
        raw_output = (
            '"TSMDB1","294,920","293,368","236,524","56,844"\n'
        )

        parsed = DSMParser.parse_q_db(raw_output)

        self.assertEqual(parsed["Database Name"], "TSMDB1")
        self.assertEqual(parsed["Total Pages"], "294,920")
        self.assertEqual(parsed["Usable Pages"], "293,368")
        self.assertEqual(parsed["Used Pages"], "236,524")
        self.assertEqual(parsed["Free Pages"], "56,844")

    def test_q_dbspace_returns_every_database_directory(self):
        raw_output = (
            '"/db/tsmdb001","200,501.98","108,211.39","92,290.58"\n'
            '"/db/tsmdb002","200,501.98","108,211.39","92,290.58"\n'
        )

        parsed = DSMParser.parse_q_dbspace(raw_output)

        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0]["Location"], "/db/tsmdb001")
        self.assertEqual(parsed[0]["Total Space (MB)"], "200,501.98")
        self.assertEqual(parsed[0]["Used Space (MB)"], "108,211.39")
        self.assertEqual(parsed[0]["Free Space (MB)"], "92,290.58")
        self.assertEqual(parsed[1]["Location"], "/db/tsmdb002")

    def test_q_status_uses_labels_from_status_output(self):
        raw_output = self.STATUS_FIXTURE.read_text(encoding="utf-8")

        parsed = DSMParser.parse_q_status(raw_output)

        self.assertEqual(len(parsed), 77)
        self.assertEqual(parsed["server_name"], "TESTSERVER")
        self.assertEqual(parsed["server_host_name_or_ip_address"], "")
        self.assertEqual(parsed["server_tcp_ip_port_number"], "1500")
        self.assertEqual(
            parsed["server_installation_date_time"],
            "07/22/26   10:04:59"
        )
        self.assertEqual(parsed["authentication"], "On")
        self.assertEqual(parsed["availability"], "Enabled")
        self.assertEqual(
            parsed["database_directories"],
            (
                "/test/dbspace01,/test/dbspace02,"
                "/test/dbspace03,/test/dbspace04"
            )
        )
        self.assertEqual(
            parsed["total_space_of_file_system_mb"], "510,709.98"
        )
        self.assertEqual(parsed["last_refresh_date_time"], "")
        self.assertNotIn("monitor_status", parsed)
        self.assertNotIn("server_date_time", parsed)
        self.assertNotIn("server_command", parsed)

    def test_q_monitorsettings_uses_all_live_labels(self):
        raw_output = self.MONITORSETTINGS_FIXTURE.read_text(
            encoding="utf-8"
        )

        parsed = DSMParser.parse_q_monitorsettings(raw_output)

        self.assertEqual(len(parsed), 30)
        self.assertEqual(parsed["monitor_status"], "Off")
        self.assertEqual(parsed["alert_smtp_port"], "25")
        self.assertEqual(parsed["monitoring_admin"], "")
        self.assertEqual(
            parsed["at_risk_interval_for_object_clients"], "24"
        )
        self.assertEqual(parsed["maximum_deployment_packages"], "4")
        self.assertEqual(parsed["deploy_package_manager"], "On")
        self.assertEqual(parsed["security_notification"], "On")
        self.assertEqual(
            parsed["security_notification_last_update_date_time"], ""
        )
        self.assertEqual(parsed["deploy_package_updates"], "On")
        self.assertNotIn("server_date_time", parsed)
        self.assertNotIn("server_command", parsed)

    def test_q_domain_preserves_multiple_rows_and_description_commas(self):
        raw_output = (
            '"STANDARD","STANDARD","STANDARD","1",'
            '"Installed default policy domain."\n'
            '"STANDARD","ACTIVE","STANDARD","4",'
            '"Primary policy, protected by QA"\n'
        )

        parsed = DSMParser.parse_q_domain(raw_output)

        self.assertEqual(len(parsed), 2)
        self.assertEqual(
            parsed[0]["Description"], "Installed default policy domain."
        )
        self.assertEqual(
            parsed[1]["Description"], "Primary policy, protected by QA"
        )

    def test_q_copygroup_preserves_multiple_rows(self):
        raw_output = (
            "STANDARD,ACTIVE,STANDARD,STANDARD,2,1,30,60\n"
            "STANDARD,STANDARD,STANDARD,STANDARD,2,1,30,60\n"
        )

        parsed = DSMParser.parse_q_copygroup(raw_output)

        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0]["Policy Set Name"], "ACTIVE")
        self.assertEqual(parsed[1]["Policy Set Name"], "STANDARD")
        self.assertEqual(parsed[0]["Versions Data Exists"], "2")
        self.assertEqual(parsed[0]["Retain Only Version"], "60")

    def test_q_replrule_skips_footer_and_preserves_empty_target(self):
        raw_output = (
            "ACTIVE_DATA,,Yes,Yes\n"
            "ACTIVE_DATA_HIGH_PRIORITY,,Yes,Yes\n"
            "ALL_DATA,,No,Yes\n"
            "ALL_DATA_HIGH_PRIORITY,,No,Yes\n"
            "ANR1999I QUERY REPLRULE completed successfully.\n"
        )

        parsed = DSMParser.parse_q_replrule(raw_output)

        self.assertEqual(len(parsed["rules"]), 4)
        self.assertEqual(
            parsed["rules"][0]["Replication Rule Name"], "ACTIVE_DATA"
        )
        self.assertIsNone(
            parsed["rules"][0]["Target Replication Server"]
        )
        self.assertEqual(parsed["rules"][2]["Active Only"], "No")
        self.assertEqual(
            parsed["footer_message"],
            "ANR1999I QUERY REPLRULE completed successfully."
        )

        mapped = SpServerResponseMapper.map_to_developer_friendly(parsed)
        self.assertEqual(
            mapped["rules"][0]["replication_rule_name"], "ACTIVE_DATA"
        )
        self.assertIsNone(
            mapped["rules"][0]["target_replication_server"]
        )

    def test_q_devclass_returns_a_list_and_preserves_empty_fields(self):
        parsed = DSMParser.parse_q_devclass("DISK,Random,3,,,,\n")

        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["Device Class Name"], "DISK")
        self.assertEqual(parsed[0]["Device Access Strategy"], "Random")
        self.assertEqual(parsed[0]["Storage Pool Count"], "3")
        self.assertIsNone(parsed[0]["Device Type"])
        self.assertIsNone(parsed[0]["Mount Limit"])

    def test_q_mgmtclass_preserves_multiple_rows(self):
        raw_output = (
            "STANDARD,ACTIVE,STANDARD,Yes,"
            "Installed default management class.\n"
            "STANDARD,STANDARD,STANDARD,Yes,"
            "Installed default management class.\n"
        )

        parsed = DSMParser.parse_q_mgmtclass(raw_output)

        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0]["Policy Set Name"], "ACTIVE")
        self.assertEqual(parsed[1]["Policy Set Name"], "STANDARD")
        self.assertEqual(parsed[0]["Default Mgmt Class?"], "Yes")
        self.assertEqual(
            parsed[0]["Description"],
            "Installed default management class."
        )

    def test_q_stgpool_preserves_multiple_rows_and_empty_next_pool(self):
        raw_output = (
            "ARCHIVEPOOL,DISK,DEVCLASS,0.0 M,0.0,0.0,90,70,\n"
            "BACKUPPOOL,DISK,DEVCLASS,5 G,0.0,0.0,90,70,\n"
            "SPACEMGPOOL,DISK,DEVCLASS,0.0 M,0.0,0.0,90,70,\n"
        )

        parsed = DSMParser.parse_q_stgpool(raw_output)

        self.assertEqual(len(parsed), 3)
        self.assertEqual(parsed[0]["Storage Pool Name"], "ARCHIVEPOOL")
        self.assertEqual(parsed[1]["Estimated Capacity"], "5 G")
        self.assertEqual(parsed[2]["Storage Pool Name"], "SPACEMGPOOL")
        self.assertEqual(parsed[0]["Next Storage Pool"], "")

    def test_q_db_rejects_wrong_column_count(self):
        raw_output = '"TSMDB1","294","920","293","368","236"\n'

        with self.assertRaisesRegex(
                ValueError, "expected 5 fields but received 6"):
            DSMParser.parse_q_db(raw_output)

    def test_q_dbspace_rejects_wrong_column_count(self):
        raw_output = '"/db/tsmdb001","200,501.98","108,211.39"\n'

        with self.assertRaisesRegex(
                ValueError, "expected 4 fields but received 3"):
            DSMParser.parse_q_dbspace(raw_output)

    def test_q_log_preserves_numeric_thousands_separators(self):
        parsed = DSMParser.parse_q_log('"8,192",424,"7,768"\n')

        self.assertEqual(parsed["Total Space (MB)"], "8,192")
        self.assertEqual(parsed["Used Space (MB)"], "424")
        self.assertEqual(parsed["Free Space (MB)"], "7,768")

    def test_developer_friendly_mapping_includes_database_fields(self):
        parsed = {
            "q_db": DSMParser.parse_q_db(
                '"TSMDB1","294,920","293,368","236,524","56,844"\n'
            ),
            "q_dbspace": DSMParser.parse_q_dbspace(
                '"/db/tsmdb001","200,501.98","108,211.39","92,290.58"\n'
            ),
        }

        mapped = SpServerResponseMapper.map_to_developer_friendly(parsed)

        self.assertEqual(mapped["q_db"]["database_name"], "TSMDB1")
        self.assertEqual(mapped["q_db"]["total_pages"], "294,920")
        self.assertEqual(
            mapped["q_dbspace"][0]["location"], "/db/tsmdb001"
        )
        self.assertEqual(
            mapped["q_dbspace"][0]["total_space_mb"], "200,501.98"
        )


class TestDsmadmcAdapterExtended(unittest.TestCase):

    def test_status_command_can_disable_comma_delimited_output(self):
        adapter = DsmadmcAdapterExtended(
            argument_spec={},
            direct_params={
                "server_name": "TESTSERVER",
                "username": "testadmin",
                "password": "testpassword",
                "request_timeout": 10,
            },
        )
        completed = mock.Mock(returncode=0, stdout=b"", stderr=b"")

        with mock.patch(
                "plugins.module_utils.sp_server_facts.subprocess.run",
                return_value=completed) as run:
            adapter.run_command(
                "-displaymode=list q status",
                auto_exit=False,
                dataonly=False,
                commadelimited=False
            )

        command = run.call_args.args[0]
        self.assertNotIn("-dataonly=yes", command)
        self.assertNotIn("-commadelimited", command)
        self.assertTrue(command.endswith("-displaymode=list q status"))


if __name__ == "__main__":
    unittest.main()
