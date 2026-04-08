SCENARIOS = {
    "known_signal_easy": {
        "reports": [
            {
                "report_id": "OPS-EASY-001",
                "patient_age": 9,
                "patient_sex": "urban_bus",
                "drugs": ["RouteSync v4.2 autopilot assist"],
                "suspect_drug": "RouteSync",
                "reaction": "Repeated GPS drift in the riverfront tunnel corridor",
                "onset_days": 11,
                "severity": "mild",
                "outcome": "not_recovered",
                "similar_reports_last_30d": 1264,
            }
        ],
        "ground_truth": {
            "classification": "known_side_effect",
            "suspect_drug": "RouteSync",
            "severity_assessment": "mild",
            "recommended_action": "log_and_monitor",
        },
        "drug_interaction_db": {
            "RouteSync": {
                "known_reactions": ["temporary gps drift", "urban canyon reroute lag", "delayed lane confidence"],
                "class_note": "Tunnel re-acquisition drift is a documented platform behavior with existing mitigations.",
            }
        },
    },
    "cluster_signal_medium": {
        "reports": [
            {
                "report_id": "OPS-MED-001",
                "patient_age": 2,
                "patient_sex": "warehouse_robot",
                "drugs": ["PalletPilot"],
                "suspect_drug": "PalletPilot",
                "reaction": "unexpected low-speed stop with aisle congestion",
                "onset_days": 9,
                "severity": "moderate",
                "outcome": "not_recovered",
                "similar_reports_last_30d": 5,
            },
            {
                "report_id": "OPS-MED-002",
                "patient_age": 3,
                "patient_sex": "warehouse_robot",
                "drugs": ["PalletPilot"],
                "suspect_drug": "PalletPilot",
                "reaction": "forklift escort trigger followed by emergency halt",
                "onset_days": 13,
                "severity": "severe",
                "outcome": "not_recovered",
                "similar_reports_last_30d": 5,
            },
            {
                "report_id": "OPS-MED-003",
                "patient_age": 2,
                "patient_sex": "warehouse_robot",
                "drugs": ["PalletPilot"],
                "suspect_drug": "PalletPilot",
                "reaction": "persistent aisle slowdown and queue cascade",
                "onset_days": 7,
                "severity": "moderate",
                "outcome": "not_recovered",
                "similar_reports_last_30d": 5,
            },
            {
                "report_id": "OPS-MED-004",
                "patient_age": 4,
                "patient_sex": "warehouse_robot",
                "drugs": ["PalletPilot"],
                "suspect_drug": "PalletPilot",
                "reaction": "navigation freeze requiring remote operations intervention",
                "onset_days": 11,
                "severity": "severe",
                "outcome": "not_recovered",
                "similar_reports_last_30d": 5,
            },
        ],
        "ground_truth": {
            "classification": "new_signal",
            "suspect_drug": "PalletPilot",
            "severity_assessment": "severe",
            "recommended_action": "escalate",
        },
        "drug_interaction_db": {
            "PalletPilot": {
                "known_reactions": ["minor scan retries", "brief docking jitter"],
                "approval_date": "5 months ago",
                "label_note": "No documented freeze or aisle-blocking regression under escort traffic.",
            }
        },
    },
    "confounded_hard": {
        "reports": [
            {
                "report_id": "OPS-HARD-001",
                "patient_age": 5,
                "patient_sex": "fulfillment_sorter",
                "drugs": [
                    "FlowManager",
                    "PriorityLane",
                    "DockWatch",
                    "TelemetryBridge",
                    "VisionPatch",
                    "LabelOCR",
                ],
                "suspect_drug": "LabelOCR",
                "reaction": "Sort lane overload with queue depth 4x baseline and thermal shutdown risk",
                "onset_days": 6,
                "severity": "critical",
                "outcome": "not_recovered",
                "similar_reports_last_30d": 1,
            }
        ],
        "ground_truth": {
            "classification": "new_signal",
            "suspect_drug": "FlowManager+VisionPatch",
            "severity_assessment": "critical",
            "recommended_action": "escalate",
        },
        "drug_interaction_db": {
            "VisionPatch": {
                "strong_metabolic_inhibitor": True,
                "interacts_with": ["FlowManager", "SortCore"],
                "interaction_note": "The patch sharply increases queue recomputation latency; throughput limits and telemetry monitoring are required.",
            },
            "FlowManager": {
                "narrow_therapeutic_index": True,
                "known_reactions": ["queue oscillation", "load shedding"],
                "requires_level_monitoring": True,
            },
        },
    },
}
