import copy
import json
import re
import threading
import unittest
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from tools.run_content_engine import (
    OWNER_SITE,
    OWNER_HANDLE,
    PLAN_SCHEMA,
    SOURCE_DEFAULT,
    count_reference_mismatch,
    enrich,
    schema_errors,
    validate_source,
    write_daily_catalog,
    preserve_local_workspace,
    renderer,
)
from tools.serve_content_studio import Handler


class ContentEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads(SOURCE_DEFAULT.read_text(encoding="utf-8"))

    def test_source_is_read_only_and_generated_plan_validates(self):
        original = copy.deepcopy(self.source)
        summary = validate_source(self.source)
        generated, deliveries = enrich(self.source)
        self.assertEqual(summary["deliveries"], 84)
        self.assertEqual(len(deliveries), 84)
        self.assertEqual(schema_errors(generated, PLAN_SCHEMA, "generated plan"), [])
        self.assertIn("AtoZ horizontal lockup — white", deliveries[0]["_visual_svg"])
        self.assertNotIn("APPROVAL-REQUIRED.invalid", deliveries[0]["_visual_svg"])
        self.assertNotIn("APPROVED_SOCIAL_HANDLE", deliveries[0]["_visual_svg"])
        self.assertTrue(any("AtoZ horizontal lockup — white" in d["_visual_svg"] for d in deliveries))
        self.assertEqual(self.source, original)
        self.assertTrue(all(d.get("cta", {}).get("target_url") == OWNER_SITE for d in generated["deliveries"] if d.get("cta")))
        self.assertTrue(all(OWNER_HANDLE in d.get("caption", "") for d in generated["deliveries"] if d.get("caption")))
        self.assertTrue(all("atozfnb.info" not in d.get("caption", "") for d in generated["deliveries"]))

    def test_test_creatives_use_only_approved_brand_palette_and_lockups(self):
        allowed = {token["hex"].upper() for token in renderer.BRAND_COLORS.values() if isinstance(token, dict) and "hex" in token}
        allowed.add("#FFFFFF")
        for pillar in renderer.PILLARS:
            for style in ("editorial", "formal", "minimal", "artwork", "retro", "handwritten-accent"):
                with self.subTest(pillar=pillar, style=style):
                    svg = renderer.make_card("نمونهٔ آزمون", "متن نمونه برای بازبینی هویت AtoZ", pillar, style=style)
                    self.assertLessEqual({color.upper() for color in re.findall(r"#[0-9A-Fa-f]{3,8}\b", svg)}, allowed)
                    self.assertIn("AtoZ horizontal lockup", svg)
                    self.assertIn(f'data-pillar-icon="{renderer.PILLARS[pillar]["id"]}"', svg)
                    self.assertIn('data-header="owner-review-week-01"', svg)
                    self.assertIn('data-footer="owner-review-atoz"', svg)
                    self.assertNotIn("ATOZ", svg)
        leadership_dark = renderer.make_card("نمونهٔ آزمون", "متن نمونه", 2)
        self.assertIn('data-section-accent="#FFB400"', leadership_dark)

    def test_repository_preview_exposes_all_week_one_creatives(self):
        preview = Path(__file__).resolve().parents[1] / "content-pilot/test-output"
        manifest = json.loads((preview / "preview-manifest.json").read_text(encoding="utf-8"))
        expected_ids = {delivery["delivery_id"] for delivery in self.source["deliveries"]}
        self.assertEqual({item["delivery_id"] for item in manifest["items"]}, expected_ids)
        self.assertEqual(manifest["count"], 84)
        self.assertTrue(all((preview / item["preview"]).is_file() for item in manifest["items"]))
        self.assertTrue((preview / "index.html").is_file())

    def test_unresolved_count_discrepancy_is_parsed_without_rewriting(self):
        mismatch = count_reference_mismatch(self.source["notes"])
        self.assertEqual(mismatch, {"reference_count": 64, "difference": 20})
        generated, _ = enrich(self.source)
        self.assertEqual(len(generated["deliveries"]), 84)
        self.assertTrue(any("اختلاف" in note for note in generated["notes"]))

    def test_week_output_is_day_first_and_grouped_by_format(self):
        generated, deliveries = enrich(self.source)
        with TemporaryDirectory() as temporary:
            output = Path(temporary)
            write_daily_catalog(output, generated, deliveries)
            week_index = json.loads((output / "daily-index.json").read_text(encoding="utf-8"))
            self.assertEqual(week_index["delivery_count"], 84)
            self.assertEqual(len(week_index["days"]), 7)
            self.assertTrue((output / "index.html").is_file())
            week_html = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn("کاروسل‌ها", week_html)
            self.assertIn("brand-assets/primary/white/horizontal.svg", week_html)
            self.assertEqual((output / "brand-assets/primary/white/horizontal.svg").read_bytes(), (Path(__file__).resolve().parents[1] / "logo/primary/white/horizontal.svg").read_bytes())
            self.assertEqual((output / "brand-assets/primary/color/horizontal.svg").read_bytes(), (Path(__file__).resolve().parents[1] / "logo/primary/color/horizontal.svg").read_bytes())
            self.assertEqual((output / "brand-assets/fonts/Vazirmatn-Regular.ttf").read_bytes(), (Path(__file__).resolve().parents[1] / "tools/fonts/Vazirmatn-Regular.ttf").read_bytes())
            for day in ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]:
                root = output / day
                self.assertTrue((root / "index.html").is_file())
                self.assertIn("brand-assets/primary/white/horizontal.svg", (root / "index.html").read_text(encoding="utf-8"))
                self.assertTrue((root / "daily-manifest.json").is_file())
                for category in ["01-reels", "02-carousels", "03-posts", "04-stories", "05-web-telegram"]:
                    self.assertTrue((root / category / "index.html").is_file())
            manifest = json.loads((output / "شنبه" / "daily-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(sum(manifest["categories"].values()), manifest["delivery_count"])
            reel = next(output.glob("شنبه/01-reels/ATZ-D-*.html"))
            self.assertIn("<video controls", reel.read_text(encoding="utf-8"))
            carousel = next(output.glob("شنبه/02-carousels/ATZ-D-*.html"))
            self.assertEqual(carousel.read_text(encoding="utf-8").count("<img loading=\"lazy\""), 8)

    def test_copy_outline_has_complete_carousel_and_reel_structures(self):
        generated, deliveries = enrich(self.source)
        carousels = [d for d in deliveries if d["format_id"] == "carousel"]
        reels = [d for d in deliveries if d["format_id"] in {"micro_reel", "mini_reel", "main_reel", "animated_reel"}]
        self.assertTrue(carousels)
        self.assertTrue(reels)
        self.assertTrue(all(len(d["_slide_copy"]) == 8 for d in carousels))
        self.assertTrue(all(len(d["_scene_copy"]) == 3 for d in reels))
        self.assertTrue(all(d["_copy_outline"]["claim_policy"] == "no-new-claims; owner-review-required" for d in deliveries))

    def test_safe_rebuild_preserves_local_review_and_intake_state(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            previous, stage = root / "previous", root / "stage"
            previous.mkdir(); stage.mkdir()
            (previous / "review-state.json").write_text('{"ATZ-C-000001":{"status":"approved"}}', encoding="utf-8")
            (previous / "intake-drafts.json").write_text('[{"id":"ATZ-I-000001"}]', encoding="utf-8")
            (previous / "intake").mkdir()
            (previous / "intake" / "ATZ-I-000001.md").write_text("kept", encoding="utf-8")
            preserve_local_workspace(previous, stage)
            self.assertIn("approved", (stage / "review-state.json").read_text(encoding="utf-8"))
            self.assertIn("ATZ-I-000001", (stage / "intake-drafts.json").read_text(encoding="utf-8"))
            self.assertEqual((stage / "intake" / "ATZ-I-000001.md").read_text(encoding="utf-8"), "kept")

    def test_local_review_and_draft_api(self):
        with TemporaryDirectory() as temporary:
            output = Path(temporary)
            (output / "plan.json").write_text(json.dumps(self.source, ensure_ascii=False), encoding="utf-8")
            (output / "review-state.json").write_text("{}", encoding="utf-8")
            (output / "intake-drafts.json").write_text("[]", encoding="utf-8")
            server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, output=output))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"

            def post(path, payload):
                request = Request(base + path, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
                with urlopen(request, timeout=10) as response:
                    return response.status, json.loads(response.read().decode("utf-8"))

            try:
                payload = {"title": "آزمون موتور", "pillar_id": "finance-market", "persona": "مدیر کافه", "problem": "مسئلهٔ آزمون", "thesis": "فرضیهٔ قابل بازبینی", "format_id": "carousel", "evidence_level": "hypothesis"}
                status, preview = post("/api/draft/preview", payload)
                self.assertEqual(status, 200)
                self.assertEqual(len(preview["slides"]), 8)
                status, review = post("/api/review", {"content_id": "ATZ-C-000001", "status": "approved", "note": "test"})
                self.assertEqual(status, 200)
                self.assertFalse(review["review_state"]["ATZ-C-000001"]["publication_triggered"])
                status, draft = post("/api/draft", payload)
                self.assertEqual(status, 201)
                self.assertTrue((output / "intake" / draft["draft"]["id"] / "brief.fa.md").is_file())
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
