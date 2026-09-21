"""Tests for tools/merge_live.py.

Run them with:

    python3 -m unittest discover -s tools -p 'test_*.py' -v
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from merge_live import merge_zone  # noqa: E402

ZONE = "witcc.dev."

REPO_FILE = """---

# Wentworth Coding Club, witcc.dev.

api: # mayonej@wit.edu
  - ttl: 600
    type: CNAME
    value: api.example.com.

zeta: # lambertl@wit.edu
  - ttl: 600
    type: A
    value: 192.0.2.1
"""


class MergeZoneTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.live_dir = self.root / "live"
        self.repo_dir = self.root / "repo"
        self.live_dir.mkdir()
        self.repo_dir.mkdir()
        (self.repo_dir / "witcc.dev.yaml").write_text(REPO_FILE)

    def write_live(self, body):
        (self.live_dir / "witcc.dev.yaml").write_text(body)

    def merge(self, keep_root_ns=False):
        return merge_zone(
            ZONE,
            self.live_dir,
            self.repo_dir,
            {"octodns-meta"},
            "2026-09-21",
            keep_root_ns,
        )

    def result(self):
        return (self.repo_dir / "witcc.dev.yaml").read_text()

    def test_no_drift_leaves_the_file_alone(self):
        self.write_live(REPO_FILE)
        added, updated, removed = self.merge()
        self.assertEqual(([], [], []), (added, updated, removed))
        self.assertEqual(REPO_FILE, self.result())

    def test_new_record_is_added_and_flagged_for_an_owner(self):
        self.write_live(
            REPO_FILE
            + """
blog:
  - ttl: 300
    type: CNAME
    value: blog.example.com.
"""
        )
        added, updated, removed = self.merge()
        self.assertEqual((["blog"], [], []), (added, updated, removed))
        result = self.result()
        self.assertIn("blog: # TODO owner unknown, added from Cloudflare on 2026-09-21", result)
        self.assertIn("value: blog.example.com.", result)

    def test_changed_record_keeps_its_owner_comment(self):
        self.write_live(REPO_FILE.replace("192.0.2.1", "192.0.2.99"))
        added, updated, removed = self.merge()
        self.assertEqual(([], ["zeta"], []), (added, updated, removed))
        result = self.result()
        self.assertIn("zeta: # lambertl@wit.edu", result)
        self.assertIn("192.0.2.99", result)
        self.assertNotIn("192.0.2.1\n", result)
        # An untouched record keeps its comment too.
        self.assertIn("api: # mayonej@wit.edu", result)

    def test_record_missing_from_cloudflare_is_removed(self):
        self.write_live(
            """---
api: # mayonej@wit.edu
  - ttl: 600
    type: CNAME
    value: api.example.com.
"""
        )
        added, updated, removed = self.merge()
        self.assertEqual(([], [], ["zeta"]), (added, updated, removed))
        self.assertNotIn("zeta", self.result())

    def test_octodns_meta_is_ignored(self):
        self.write_live(
            REPO_FILE
            + """
octodns-meta:
  - ttl: 60
    type: TXT
    value: time=2026-09-21T00:00:00
"""
        )
        added, updated, removed = self.merge()
        self.assertEqual(([], [], []), (added, updated, removed))
        self.assertNotIn("octodns-meta", self.result())

    def test_records_are_sorted_with_the_root_first(self):
        self.write_live(
            """---
zeta: # lambertl@wit.edu
  - ttl: 600
    type: A
    value: 192.0.2.1
"": # eboard
  - ttl: 300
    type: A
    value: 192.0.2.5
api: # mayonej@wit.edu
  - ttl: 600
    type: CNAME
    value: api.example.com.
"""
        )
        self.merge()
        result = self.result()
        order = [result.index(k) for k in ('""', "api:", "zeta:")]
        self.assertEqual(sorted(order), order)

    def test_output_is_still_valid_yaml(self):
        self.write_live(
            REPO_FILE
            + """
blog:
  - ttl: 300
    type: CNAME
    value: blog.example.com.
"""
        )
        self.merge()
        from ruamel.yaml import YAML

        parsed = YAML(typ="safe").load(self.result())
        self.assertEqual({"api", "zeta", "blog"}, set(parsed))
        self.assertEqual("blog.example.com.", parsed["blog"][0]["value"])

    def test_root_ns_from_cloudflare_is_left_out(self):
        # Cloudflare owns the apex nameservers. Pulling them into the zone file
        # makes every later deploy fail on octoDNS's root NS safety check.
        self.write_live(
            REPO_FILE
            + """
"":
  - ttl: 3600
    type: NS
    values:
      - ns1.cloudflare.com.
      - ns2.cloudflare.com.
"""
        )
        added, updated, removed = self.merge()
        self.assertEqual(([], [], []), (added, updated, removed))
        self.assertNotIn("cloudflare.com.", self.result())

    def test_root_ns_is_kept_when_asked_for(self):
        self.write_live(
            REPO_FILE
            + """
"":
  - ttl: 3600
    type: NS
    values:
      - ns1.cloudflare.com.
"""
        )
        added, _, _ = self.merge(keep_root_ns=True)
        self.assertEqual([""], added)

    def test_other_root_records_survive_the_ns_filter(self):
        self.write_live(
            REPO_FILE
            + """
"":
  - ttl: 3600
    type: NS
    values:
      - ns1.cloudflare.com.
  - ttl: 300
    type: A
    value: 192.0.2.7
"""
        )
        added, _, _ = self.merge()
        self.assertEqual([""], added)
        result = self.result()
        self.assertIn("192.0.2.7", result)
        self.assertNotIn("ns1.cloudflare.com.", result)

    def test_missing_dump_is_an_error(self):
        with self.assertRaises(FileNotFoundError):
            self.merge()


if __name__ == "__main__":
    unittest.main()
