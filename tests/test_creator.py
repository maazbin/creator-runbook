import copy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/creator-runbook/scripts"
sys.path.insert(0, str(SCRIPTS))
import channels
import episode


def fixture(name, kind):
    return json.loads((ROOT / "examples" / name / (kind + ".json")).read_text(encoding="utf-8"))


class CreatorTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = channels.connect(self.root)
        self.addCleanup(self.db.close)
        self.cfg = fixture("motion-notes", "profile")
        channels.configure(self.db, self.cfg)

    def test_parallel_claim_and_reclaim(self):
        now = datetime.now(timezone.utc)
        other = channels.connect(self.root)
        self.addCleanup(other.close)
        job = channels.claim(self.db, "motion-notes", "launch", now)
        second = channels.claim(other, "motion-notes", "launch", now)
        self.assertEqual(second["status"], "working")
        replacement = channels.claim(other, "motion-notes", "launch", now + timedelta(hours=3))
        self.assertEqual(replacement["job"], job["job"])
        self.assertNotEqual(replacement["token"], job["token"])
        with self.assertRaises(ValueError):
            channels.own(self.db, job["job"], job["token"])

    def test_profiles_and_assets_are_isolated(self):
        channels.configure(self.db, fixture("last-light", "profile"))
        for item in ["last-light/secret.png", "motion-notes/diagram.png"]:
            dest = self.root / "assets" / item
            dest.parent.mkdir(parents=True)
            dest.write_bytes(b"fixture")
        job = channels.claim(self.db, "motion-notes", "first")
        packet = channels.writing_packet(job, self.root)
        self.assertEqual(packet["available_assets"], ["diagram.png"])
        with self.assertRaises(ValueError):
            episode.asset(self.root / "assets/motion-notes", "../last-light/secret.png")
        channels.configure(self.db, {**self.cfg, "audience": "Another audience"})
        self.assertEqual(
            channels.own(self.db, job["job"], job["token"])["profile"],
            json.dumps(self.cfg, ensure_ascii=False),
        )

    def test_evidence_and_destination(self):
        draft = fixture("motion-notes", "episode")
        episode.validate(draft, self.cfg)
        for edit in ("evidence", "channel", "runtime"):
            with self.subTest(edit=edit):
                bad = copy.deepcopy(draft)
                if edit == "evidence":
                    bad["scenes"][0]["evidence"] = ["invented"]
                if edit == "channel":
                    bad["channel"] = "last-light"
                if edit == "runtime":
                    bad["scenes"][0]["seconds"] = 20
                with self.assertRaises(ValueError):
                    episode.validate(bad, self.cfg)

    def test_cli_delivers_and_replays_once(self):
        ff = shutil.which(os.getenv("CREATOR_FFMPEG", "ffmpeg"))
        if not ff:
            self.skipTest("needs FFmpeg")

        def run(*args, data=None):
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "channels.py"),
                    "--desk",
                    str(self.root),
                    "--ffmpeg",
                    ff,
                    *map(str, args),
                ],
                input=json.dumps(data) if data else None,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )
            return json.loads(result.stdout)

        cfg = {**self.cfg, "id": "test", "seconds": 1, "size": [960, 540], "fps": 30}
        run("configure", data=cfg)
        job = run("claim", "test", "one")
        draft = fixture("motion-notes", "episode")
        draft["channel"] = "test"
        draft["scenes"] = [
            {**draft["scenes"][0], "layout": "compare", "points": ["Left", "Right"], "seconds": 1}
        ]
        for key in ("file", "audio", "in"):
            draft["scenes"][0].pop(key)
        final = Path(run("finish", job["job"], job["token"], data=draft)["ready"])
        self.assertTrue((final / "video.mp4").stat().st_size > 1000)
        info = subprocess.run(
            [ff, "-hide_banner", "-i", str(final / "video.mp4")], capture_output=True, text=True
        ).stderr
        self.assertIn("960x540", info)
        self.assertIn("30 fps", info)
        self.assertIn("00:00:01,000", (final / "captions.srt").read_text(encoding="utf-8"))
        self.assertEqual(run("claim", "test", "one")["path"], str(final))
        self.assertEqual(run("claim", "test", "two")["recent"][0]["angle"], draft["angle"])
        self.assertEqual(run("claim", "motion-notes", "two")["recent"], [])


if __name__ == "__main__":
    unittest.main()
