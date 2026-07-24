import unittest

from plugins.modules.diff_analyse import (
    build_change_rows,
    prepare_module_results,
    serialize_rows,
)


class TestDiffAnalyse(unittest.TestCase):

    def compare(self, baseline, current):
        old = prepare_module_results(baseline)
        new = prepare_module_results(current)
        return build_change_rows(old, new)

    def test_obvious_runtime_metrics_do_not_create_drift(self):
        baseline = {
            "q_status": {
                "server_name": "SERVER1",
                "activity_log_number_of_records": "4516",
                "used_space_on_file_system_mb": "41,932.53",
                "free_space_available_mb": "468,777.45",
            },
            "q_dbspace": [
                {
                    "location": "/db1",
                    "total_space_mb": "510,709.98",
                    "used_space_mb": "41,932.57",
                    "free_space_mb": "468,777.41",
                }
            ],
            "q_log": {
                "total_space_mb": "8,192",
                "used_space_mb": "424",
                "free_space_mb": "7,768",
            },
            "q_stgpool": [
                {
                    "storage_pool_name": "BACKUPPOOL",
                    "high_mig_pct": "90",
                    "pct_util": "0.0",
                    "pct_migr": "0.0",
                }
            ],
        }
        current = {
            "q_status": {
                "server_name": "SERVER1",
                "activity_log_number_of_records": "4577",
                "used_space_on_file_system_mb": "41,934.42",
                "free_space_available_mb": "468,775.56",
            },
            "q_dbspace": [
                {
                    "location": "/db1",
                    "total_space_mb": "510,709.98",
                    "used_space_mb": "41,934.44",
                    "free_space_mb": "468,775.54",
                }
            ],
            "q_log": {
                "total_space_mb": "8,192",
                "used_space_mb": "430",
                "free_space_mb": "7,762",
            },
            "q_stgpool": [
                {
                    "storage_pool_name": "BACKUPPOOL",
                    "high_mig_pct": "90",
                    "pct_util": "12.5",
                    "pct_migr": "1.0",
                }
            ],
        }

        rows = self.compare(baseline, current)

        self.assertEqual(
            rows, {"Changed": [], "Added": [], "Removed": []}
        )

    def test_database_space_change_uses_location_identity(self):
        baseline = {
            "q_dbspace": [
                {
                    "location": "/db1",
                    "total_space_mb": "100",
                    "used_space_mb": "40",
                    "free_space_mb": "60",
                }
            ]
        }
        current = {
            "q_dbspace": [
                {
                    "location": "/db1",
                    "total_space_mb": "200",
                    "used_space_mb": "50",
                    "free_space_mb": "150",
                }
            ]
        }

        rows = self.compare(baseline, current)

        self.assertEqual(
            rows["Changed"],
            [
                (
                    "q_dbspace",
                    "[/db1].total_space_mb",
                    "100",
                    "200",
                )
            ],
        )

    def test_reordered_storage_pools_do_not_create_drift(self):
        archive = {
            "storage_pool_name": "ARCHIVEPOOL",
            "high_mig_pct": "90",
            "pct_util": "0.0",
            "pct_migr": "0.0",
        }
        backup = {
            "storage_pool_name": "BACKUPPOOL",
            "high_mig_pct": "90",
            "pct_util": "0.0",
            "pct_migr": "0.0",
        }

        rows = self.compare(
            {"q_stgpool": [archive, backup]},
            {"q_stgpool": [backup, archive]},
        )

        self.assertEqual(
            rows, {"Changed": [], "Added": [], "Removed": []}
        )

    def test_storage_pool_field_change_has_exact_identity_path(self):
        baseline = {
            "q_stgpool": [
                {
                    "storage_pool_name": "BACKUPPOOL",
                    "high_mig_pct": "90",
                }
            ]
        }
        current = {
            "q_stgpool": [
                {
                    "storage_pool_name": "BACKUPPOOL",
                    "high_mig_pct": "85",
                }
            ]
        }

        rows = self.compare(baseline, current)

        self.assertEqual(
            rows["Changed"],
            [
                (
                    "q_stgpool",
                    "[BACKUPPOOL].high_mig_pct",
                    "90",
                    "85",
                )
            ],
        )

    def test_nested_replication_rule_change_uses_rule_name(self):
        baseline = {
            "q_replrule": {
                "rules": [
                    {
                        "replication_rule_name": "ALL_DATA",
                        "enabled": "Yes",
                    }
                ]
            }
        }
        current = {
            "q_replrule": {
                "rules": [
                    {
                        "replication_rule_name": "ALL_DATA",
                        "enabled": "No",
                    }
                ]
            }
        }

        rows = self.compare(baseline, current)

        self.assertEqual(
            rows["Changed"],
            [
                (
                    "q_replrule",
                    "rules[ALL_DATA].enabled",
                    "Yes",
                    "No",
                )
            ],
        )

    def test_added_and_removed_items_have_identity_paths(self):
        baseline = {
            "q_domain": [
                {"policy_domain_name": "STANDARD", "description": "Default"}
            ],
            "q_devclass": [
                {"device_class_name": "OLD_DISK", "device_type": None}
            ],
        }
        current = {
            "q_domain": [
                {"policy_domain_name": "STANDARD", "description": "Default"},
                {"policy_domain_name": "NEW_DOMAIN", "description": "New"},
            ],
            "q_devclass": [],
        }

        rows = self.compare(baseline, current)

        self.assertEqual(
            rows["Added"],
            [
                (
                    "q_domain",
                    "[NEW_DOMAIN]",
                    None,
                    {
                        "policy_domain_name": "NEW_DOMAIN",
                        "description": "New",
                    },
                )
            ],
        )
        self.assertEqual(
            rows["Removed"],
            [
                (
                    "q_devclass",
                    "[OLD_DISK]",
                    {
                        "device_class_name": "OLD_DISK",
                        "device_type": None,
                    },
                    None,
                )
            ],
        )

    def test_copygroup_uses_composite_identity(self):
        baseline = {
            "q_copygroup": [
                {
                    "policy_domain_name": "STANDARD",
                    "policy_set_name": "ACTIVE",
                    "mgmt_class_name": "STANDARD",
                    "copy_group_name": "STANDARD",
                    "retain_extra_versions": "30",
                }
            ]
        }
        current = {
            "q_copygroup": [
                {
                    "policy_domain_name": "STANDARD",
                    "policy_set_name": "ACTIVE",
                    "mgmt_class_name": "STANDARD",
                    "copy_group_name": "STANDARD",
                    "retain_extra_versions": "60",
                }
            ]
        }

        rows = self.compare(baseline, current)

        module, field, old, new = rows["Changed"][0]
        self.assertEqual(module, "q_copygroup")
        self.assertIn("policy_set_name=ACTIVE", field)
        self.assertTrue(field.endswith("].retain_extra_versions"))
        self.assertEqual((old, new), ("30", "60"))

    def test_serialized_report_contains_exact_change_details(self):
        rows = {
            "Changed": [
                (
                    "q_stgpool",
                    "[BACKUPPOOL].high_mig_pct",
                    "90",
                    "85",
                )
            ],
            "Added": [],
            "Removed": [],
        }

        serialized = serialize_rows(rows)

        self.assertEqual(
            serialized["changed"][0],
            {
                "module": "q_stgpool",
                "field": "[BACKUPPOOL].high_mig_pct",
                "previous": "90",
                "current": "85",
            },
        )


if __name__ == "__main__":
    unittest.main()
