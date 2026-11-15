import copy
import unittest
from pathlib import Path

from tools.validate_content_plan import (
    ANALYTICS_SCHEMA,
    PLAN_SCHEMA,
    load_json,
    schema_errors,
    validate_analytics_integrity,
    validate_plan_integrity,
)

ROOT = Path(__file__).resolve().parents[1]


class ContentPlanSchemaTests(unittest.TestCase):
    def setUp(self):
        self.plan = load_json(ROOT / "content-pilot/examples/week-plan.example.json")
        self.analytics = load_json(ROOT / "content-pilot/examples/analytics-snapshot.example.json")

    def test_examples_validate(self):
        self.assertEqual(schema_errors(self.plan, PLAN_SCHEMA, "week plan"), [])
        self.assertEqual(schema_errors(self.analytics, ANALYTICS_SCHEMA, "analytics"), [])
        self.assertEqual(validate_plan_integrity(self.plan)[0], [])
        self.assertEqual(validate_analytics_integrity(self.analytics), [])

    def test_weekly_count_is_derived_from_variable_delivery_list(self):
        errors, summary = validate_plan_integrity(self.plan)
        self.assertEqual(errors, [])
        self.assertEqual(summary["deliveries"], len(self.plan["deliveries"]))
        self.assertEqual(summary["deliveries_by_channel"], {"instagram": 1, "telegram": 1})
        self.assertNotIn("posts_per_day", self.plan)

    def test_duplicate_content_ids_are_rejected_by_integrity_check(self):
        plan = copy.deepcopy(self.plan)
        plan["content_items"].append(copy.deepcopy(plan["content_items"][0]))
        errors, _ = validate_plan_integrity(plan)
        self.assertTrue(any("duplicate content_id" in error for error in errors))

    def test_delivery_must_reference_existing_content(self):
        plan = copy.deepcopy(self.plan)
        plan["deliveries"][0]["content_id"] = "ATZ-C-999999"
        errors, _ = validate_plan_integrity(plan)
        self.assertTrue(any("content_id does not exist" in error for error in errors))

    def test_kpi_value_must_match_numerator_and_denominator(self):
        snapshot = copy.deepcopy(self.analytics)
        snapshot["derived_metrics"]["save_rate_by_reach"]["value"] = 0.5
        errors = validate_analytics_integrity(snapshot)
        self.assertTrue(any("does not match numerator/denominator" in error for error in errors))

    def test_naive_publish_time_is_rejected_by_schema(self):
        plan = copy.deepcopy(self.plan)
        plan["deliveries"][0]["publish_at"] = "2026-11-21T10:30:00"
        errors = schema_errors(plan, PLAN_SCHEMA, "week plan")
        self.assertTrue(any("publish_at" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
