#!/usr/bin/env python3
"""Validate AtoZ.FnB content-plan and analytics JSON documents."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
PLAN_SCHEMA = ROOT / "content-pilot/schemas/week-plan.schema.json"
ANALYTICS_SCHEMA = ROOT / "content-pilot/schemas/analytics-snapshot.schema.json"


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path}: {exc}") from exc


def schema_errors(document, schema_path: Path, label: str) -> list[str]:
    schema = load_json(schema_path)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"{label}: {'.'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(document), key=lambda e: list(map(str, e.absolute_path)))
    ]


def parse_dt(value: str, path: str, errors: list[str]) -> datetime | None:
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError):
        errors.append(f"{path}: expected an ISO-8601 date-time")
        return None
    if result.utcoffset() is None:
        errors.append(f"{path}: timezone offset is required")
        return None
    return result


def validate_plan_integrity(plan: dict) -> tuple[list[str], dict]:
    errors: list[str] = []
    content_items = plan.get("content_items", [])
    deliveries = plan.get("deliveries", [])
    assets = plan.get("assets", [])

    def unique(values: list[str], label: str) -> None:
        duplicates = sorted({item for item in values if values.count(item) > 1})
        if duplicates:
            errors.append(f"duplicate {label}: {', '.join(duplicates)}")

    content_ids = [row["content_id"] for row in content_items]
    delivery_ids = [row["delivery_id"] for row in deliveries]
    asset_ids = [row["asset_id"] for row in assets]
    schedule_keys = [row["schedule_key"] for row in deliveries]
    unique(content_ids, "content_id")
    unique(delivery_ids, "delivery_id")
    unique(asset_ids, "asset_id")
    unique(schedule_keys, "schedule_key")

    known_content = set(content_ids)
    known_delivery = set(delivery_ids)
    known_asset = set(asset_ids)
    known_entity = known_content | known_delivery | known_asset
    for item in content_items:
        for asset_id in item.get("linked_asset_ids", []):
            if asset_id not in known_asset:
                errors.append(f"{item.get('content_id', '<content>')}: linked_asset_id {asset_id} does not exist")
    for relation in plan.get("relationships", []):
        for endpoint in ("from_id", "to_id"):
            value = relation.get(endpoint)
            if isinstance(value, str) and value.startswith("ATZ-") and value not in known_entity:
                errors.append(f"relationship {endpoint} {value} does not exist")
    timezone_name = plan.get("timezone")
    zone = None
    if timezone_name:
        try:
            zone = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            errors.append(f"unknown IANA timezone: {timezone_name}")

    active_channels = set(plan.get("active_channels", []))
    counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    for row in deliveries:
        delivery_id = row.get("delivery_id", "<delivery>")
        if row.get("content_id") not in known_content:
            errors.append(f"{delivery_id}: content_id does not exist in this plan")
        if row.get("channel_id") not in active_channels:
            errors.append(f"{delivery_id}: channel is not listed in active_channels")
        counts[row.get("channel_id", "unknown")] += 1
        status_counts[row.get("status", "unknown")] += 1
        day_index = row.get("planned_day_index")
        day_names = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]
        if isinstance(day_index, int) and 1 <= day_index <= 7 and row.get("day_name_fa") != day_names[day_index - 1]:
            errors.append(f"{delivery_id}: day_name_fa does not match planned_day_index")
        planned_at = row.get("publish_at")
        if planned_at:
            timestamp = parse_dt(planned_at, f"{delivery_id}.publish_at", errors)
            if timestamp and zone and timestamp.astimezone(zone).utcoffset() != timestamp.utcoffset():
                errors.append(f"{delivery_id}.publish_at: offset does not match plan timezone {timezone_name}")
        published_at = row.get("published_at")
        if row.get("status") in {"published", "measured"} and not row.get("platform_post_id"):
            errors.append(f"{delivery_id}: published delivery is missing platform_post_id")
        if published_at:
            parse_dt(published_at, f"{delivery_id}.published_at", errors)
        for asset_id in row.get("asset_ids", []):
            if asset_id not in known_asset:
                errors.append(f"{delivery_id}: asset_id {asset_id} does not exist in this plan")

    for asset in assets:
        if asset.get("content_id") and asset["content_id"] not in known_content:
            errors.append(f"{asset.get('asset_id')}: unknown content_id {asset['content_id']}")
        if asset.get("delivery_id") and asset["delivery_id"] not in known_delivery:
            errors.append(f"{asset.get('asset_id')}: unknown delivery_id {asset['delivery_id']}")

    period = plan.get("period", {})
    try:
        start = datetime.fromisoformat(period["start_date"])
        end = datetime.fromisoformat(period["end_date"])
        if end < start:
            errors.append("period.end_date precedes period.start_date")
    except (KeyError, TypeError, ValueError):
        pass  # JSON Schema reports malformed/missing dates.

    summary = {
        "content_items": len(content_items),
        "deliveries": len(deliveries),
        "deliveries_by_channel": dict(sorted(counts.items())),
        "deliveries_by_status": dict(sorted(status_counts.items())),
        "assets": len(assets),
    }
    declared = plan.get("computed_summary", {})
    for key in ("content_items", "deliveries", "assets", "deliveries_by_channel"):
        if key in declared and declared[key] != summary[key]:
            errors.append(f"computed_summary.{key} does not match plan records")
    if "instagram_feed_deliveries" in declared:
        actual = sum(1 for row in deliveries if row.get("channel_id") == "instagram" and row.get("format_id") != "story")
        if declared["instagram_feed_deliveries"] != actual:
            errors.append("computed_summary.instagram_feed_deliveries does not match plan records")
    if "instagram_story_deliveries" in declared:
        actual = sum(1 for row in deliveries if row.get("channel_id") == "instagram" and row.get("format_id") == "story")
        if declared["instagram_story_deliveries"] != actual:
            errors.append("computed_summary.instagram_story_deliveries does not match plan records")
    return errors, summary


def validate_analytics_integrity(snapshot: dict) -> list[str]:
    errors: list[str] = []
    window = snapshot.get("window", {})
    start = parse_dt(window.get("start_at"), "window.start_at", errors)
    end = parse_dt(window.get("end_at"), "window.end_at", errors)
    if start and end:
        if end < start:
            errors.append("window.end_at precedes window.start_at")
        expected_hours = (end - start).total_seconds() / 3600
        actual_hours = window.get("age_hours")
        if actual_hours is not None and abs(expected_hours - actual_hours) > 1:
            errors.append(f"window.age_hours is {actual_hours}, expected about {expected_hours:.1f}")

    for metric_id, metric in snapshot.get("derived_metrics", {}).items():
        numerator = metric.get("numerator")
        denominator = metric.get("denominator")
        value = metric.get("value")
        if denominator == 0:
            if value is not None:
                errors.append(f"derived_metrics.{metric_id}: value must be null when denominator is zero")
        elif numerator is not None and denominator is not None and value is not None:
            expected = numerator / denominator
            if abs(expected - value) > 0.001:
                errors.append(f"derived_metrics.{metric_id}: value {value} does not match numerator/denominator ({expected:.4f})")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=ROOT / "content-pilot/examples/week-plan.example.json")
    parser.add_argument("--analytics", type=Path, default=ROOT / "content-pilot/examples/analytics-snapshot.example.json")
    parser.add_argument("--plan-only", action="store_true", help="Validate only the production plan; do not load the illustrative analytics fixture")
    args = parser.parse_args()

    try:
        plan = load_json(args.plan)
        analytics = None if args.plan_only else load_json(args.analytics)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2

    errors = schema_errors(plan, PLAN_SCHEMA, "week plan")
    if analytics is not None:
        errors += schema_errors(analytics, ANALYTICS_SCHEMA, "analytics")
    plan_errors, summary = validate_plan_integrity(plan)
    errors += plan_errors
    if analytics is not None:
        errors += validate_analytics_integrity(analytics)
        if analytics.get("delivery_id") not in {row.get("delivery_id") for row in plan.get("deliveries", [])}:
            errors.append("analytics.delivery_id does not exist in the plan")

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Validation passed.")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if analytics is not None:
        print("Analytics snapshot: schema, timezone window, and derived KPI formulas are valid.")
    else:
        print("Plan-only validation: no analytics or performance data loaded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
