"""Tests for furnimesh.py's PURE half — category parsing, JSON-LD model
parsing, and the fetch plan. No network, no Blender: the HTML fixtures are
synthetic strings shaped like the live pages probed 2026-08-22 (category pages
carry plain quoted model hrefs; model pages carry a schema.org `3DModel` block
whose `encoding` list names the direct download URLs).

The property pinned hardest is the same one mesh_import pins: FAIL CLOSED — a
page with no 3DModel block must RAISE, because "no downloads found" printing
like "an empty catalogue" is how a site change would go unnoticed.
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import furnimesh as FM  # noqa: E402


def _model_page(name="A Lamp", encs=None):
    encs = encs if encs is not None else [
        {"@type": ["MediaObject", "DataDownload"],
         "contentUrl": "https://storage.googleapis.com/furnimesh-3d/gbl-files/X.glb",
         "encodingFormat": "model/gltf-binary", "contentSize": "36801052"},
        {"@type": ["MediaObject", "DataDownload"],
         "contentUrl": "https://storage.googleapis.com/furnimesh-3d/obj-files/Y.zip",
         "encodingFormat": "model/obj", "contentSize": "30203598"},
    ]
    ld = {"@context": "https://schema.org", "@type": "3DModel",
          "name": name, "encoding": encs}
    return ('<html><script type="application/ld+json">'
            + json.dumps({"@type": "WebSite", "name": "FurniMesh"})
            + '</script><script type="application/ld+json">'
            + json.dumps(ld) + "</script></html>")


class TestCatPath(unittest.TestCase):
    def test_short_and_slashed_forms_agree(self):
        self.assertEqual(FM.cat_path("lighting/table-lamp"),
                         "/library/lighting/table-lamp/")
        self.assertEqual(FM.cat_path("/library/lighting/table-lamp/"),
                         "/library/lighting/table-lamp/")


class TestModelLinks(unittest.TestCase):
    HTML = ('x "/library/lighting/table-lamp/a-modern-lamp-ab12cd/" y '
            '"/library/lighting/table-lamp/a-modern-lamp-ab12cd/" dup '
            '"/library/seating/armchair/an-armchair-zz99xx/" other-cat '
            '"/library/lighting/table-lamp/" the-category-itself '
            '"/library/lighting/table-lamp/another-lamp-ef34gh/" z')

    def test_only_this_category_deduped_in_order(self):
        got = FM.model_links(self.HTML, "lighting/table-lamp")
        self.assertEqual(got, [
            "/library/lighting/table-lamp/a-modern-lamp-ab12cd/",
            "/library/lighting/table-lamp/another-lamp-ef34gh/"])

    def test_slug_is_the_last_segment(self):
        self.assertEqual(FM.slug_of("/library/decor/vase/a-tall-vase-q1w2e3/"),
                         "a-tall-vase-q1w2e3")

    def test_empty_html_is_an_empty_list(self):
        self.assertEqual(FM.model_links("", "decor/vase"), [])


class TestParseModel(unittest.TestCase):
    def test_reads_name_and_per_format_urls_and_sizes(self):
        m = FM.parse_model(_model_page("Patinated Lamp"))
        self.assertEqual(m["name"], "Patinated Lamp")
        self.assertEqual(m["formats"]["glb"]["bytes"], 36801052)
        self.assertTrue(m["formats"]["glb"]["url"].endswith("X.glb"))
        self.assertIn("obj", m["formats"])

    def test_no_3dmodel_block_raises(self):
        html = ('<script type="application/ld+json">'
                '{"@type": "WebSite"}</script>')
        with self.assertRaises(ValueError):
            FM.parse_model(html)

    def test_unparseable_ld_json_is_skipped_not_fatal(self):
        html = ('<script type="application/ld+json">{broken</script>'
                + _model_page())
        self.assertEqual(FM.parse_model(html)["formats"]["glb"]["bytes"],
                         36801052)

    def test_unknown_encoding_format_is_ignored(self):
        m = FM.parse_model(_model_page(encs=[
            {"contentUrl": "u", "encodingFormat": "model/gltf-binary",
             "contentSize": "10"},
            {"contentUrl": "v", "encodingFormat": "model/x-new-thing",
             "contentSize": "20"}]))
        self.assertEqual(sorted(m["formats"]), ["glb"])


class TestPlanFetch(unittest.TestCase):
    ROWS = [{"slug": "a", "path": "/library/x/y/a/", "page": 1},
            {"slug": "b", "path": "/library/x/y/b/", "page": 1},
            {"slug": "c", "path": "/library/x/y/c/", "page": 2}]

    def test_cached_and_over_limit_are_skipped_with_reasons(self):
        keep, skip = FM.plan_fetch(self.ROWS, {"a": "a"}, limit=1)
        self.assertEqual([r["slug"] for r in keep], ["b"])
        whys = {s["slug"]: s["why"] for s in skip}
        self.assertIn("already cached", whys["a"])
        self.assertIn("past --limit 1", whys["c"])

    def test_no_limit_keeps_everything_new(self):
        keep, skip = FM.plan_fetch(self.ROWS, {}, limit=None)
        self.assertEqual(len(keep), 3)
        self.assertEqual(skip, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
