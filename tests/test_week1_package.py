import json
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "پیش انتشار/ماه اول/هفته اول"
DAYS = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]


class WeekOnePackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads((PACKAGE / "plan.json").read_text(encoding="utf-8"))

    def test_has_seven_days_and_requested_records(self):
        self.assertEqual(len(self.plan["content_items"]), 28)
        self.assertEqual(len(self.plan["assets"]), 38)
        self.assertEqual(len(self.plan["deliveries"]), 84)
        self.assertEqual([row["delivery_id"] for row in self.plan["deliveries"]],
                         [f"ATZ-D-{i:06d}" for i in range(1, 85)])
        for day in DAYS:
            self.assertTrue((PACKAGE / day / "README.md").is_file())

    def test_aggregate_channels_and_manual_timing(self):
        counts = Counter(row["channel_id"] for row in self.plan["deliveries"])
        self.assertEqual(counts, {"website": 7, "telegram": 7, "instagram": 70})
        stories = sum(row["format_id"] == "story" for row in self.plan["deliveries"])
        self.assertEqual(stories, 35)
        self.assertTrue(all(row["planned_time_local"] is None for row in self.plan["deliveries"]))
        self.assertTrue(all("publish_at" not in row for row in self.plan["deliveries"]))
        daily_counts = Counter(row["planned_day_index"] for row in self.plan["deliveries"])
        self.assertGreater(len(set(daily_counts.values())), 1, "Do not impose a fixed daily cadence")

    def test_every_delivery_has_copy_and_png_svg(self):
        for row in self.plan["deliveries"]:
            base = PACKAGE / DAYS[row["planned_day_index"] - 1] / row["content_id"] / row["delivery_id"]
            for filename in ("creative.png", "creative.svg", "metadata.json", "caption.txt", "hashtags.txt"):
                with self.subTest(delivery=row["delivery_id"], filename=filename):
                    self.assertTrue((base / filename).is_file())
            if row["format_id"] == "carousel":
                self.assertTrue((base / "slides/slide-08.png").is_file())
                self.assertTrue((base / "slides/slide-08.svg").is_file())
            if row["format_id"] == "story":
                self.assertTrue((base / "copy.html").is_file())
            if row["channel_id"] == "website":
                self.assertTrue((base / "website-draft.md").is_file())
                self.assertTrue((base / "website-draft.html").is_file())
            if row["channel_id"] == "telegram":
                self.assertTrue((base / "telegram-post.txt").is_file())

    def test_reels_have_video_and_original_sfx_without_narration(self):
        reels = [row for row in self.plan["deliveries"] if row["format_id"] in {"micro_reel", "mini_reel", "main_reel", "animated_reel"}]
        self.assertEqual(len(reels), 16)
        for row in reels:
            base = PACKAGE / DAYS[row["planned_day_index"] - 1] / row["content_id"] / row["delivery_id"]
            self.assertTrue((base / "reel.mp4").is_file())
            self.assertTrue((base / "audio/original-sfx.wav").is_file())
            self.assertTrue((base / "reel-source/scene-01.svg").is_file())

    def test_all_registry_paths_exist(self):
        for row in self.plan["assets"]:
            with self.subTest(asset=row["asset_id"]):
                self.assertTrue((PACKAGE / row["path"]).is_file(), row["path"])


if __name__ == "__main__":
    unittest.main()
