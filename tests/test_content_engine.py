import copy
import json
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
        self.assertEqual(self.source, original)
        self.assertTrue(all(d.get("cta", {}).get("target_url") == OWNER_SITE for d in generated["deliveries"] if d.get("cta")))
        self.assertTrue(all(OWNER_HANDLE in d.get("caption", "") for d in generated["deliveries"] if d.get("caption")))
        self.assertTrue(all("atozfnb.info" not in d.get("caption", "") for d in generated["deliveries"]))

    def test_unresolved_count_discrepancy_is_parsed_without_rewriting(self):
        mismatch = count_reference_mismatch(self.source["notes"])
        self.assertEqual(mismatch, {"reference_count": 64, "difference": 20})
        generated, _ = enrich(self.source)
        self.assertEqual(len(generated["deliveries"]), 84)
        self.assertTrue(any("اختلاف" in note for note in generated["notes"]))

    def test_copy_outline_has_complete_carousel_and_reel_structures(self):
        generated, deliveries = enrich(self.source)
        carousels = [d for d in deliveries if d["format_id"] == "carousel"]
        reels = [d for d in deliveries if d["format_id"] in {"micro_reel", "mini_reel", "main_reel", "animated_reel"}]
        self.assertTrue(carousels)
        self.assertTrue(reels)
        self.assertTrue(all(len(d["_slide_copy"]) == 8 for d in carousels))
        self.assertTrue(all(len(d["_scene_copy"]) == 3 for d in reels))
        self.assertTrue(all(d["_copy_outline"]["claim_policy"] == "no-new-claims; owner-review-required" for d in deliveries))

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
