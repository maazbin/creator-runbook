"""Private multi-channel production queue. Run with --help for the host interface."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import sys
import tempfile

import episode

UTC = timezone.utc
SKILL = Path(__file__).resolve().parents[1]
ID = re.compile(r"[a-z0-9][a-z0-9_-]{0,62}\Z")


def profile(data):
    if not isinstance(data, dict):
        raise ValueError("Channel profile must be an object")
    for key in ("id", "name", "platform", "niche", "audience", "language", "voice"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError(f"Missing channel field: {key}")
    if not ID.fullmatch(data["id"]) or not ID.fullmatch(data["platform"]):
        raise ValueError("Use a stable lowercase channel ID and platform name")
    if data.get("format", "portrait") not in ("portrait", "landscape", "square"):
        raise ValueError("format must be portrait, landscape or square")
    episode.master_settings(data)
    if data.get("delivery", "captioned") not in ("captioned", "voiced"):
        raise ValueError("delivery must be captioned or voiced")
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", str(data.get("accent", "#C3E690"))):
        raise ValueError("Use a six-digit channel accent color, for example #C3E690")
    duration = data.get("seconds", 45)
    if type(duration) is not int or duration < 1:
        raise ValueError("seconds must be a positive integer")
    if not isinstance(data.get("sources", {}), dict) or any(
        not isinstance(v, str) or not v.strip() for v in data.get("sources", {}).values()
    ):
        raise ValueError("sources must map evidence IDs to verified facts, locators and links")
    return data


def connect(root):
    root.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(root / "channels.sqlite", isolation_level=None, timeout=30)
    db.row_factory = sqlite3.Row
    db.executescript("""
        CREATE TABLE IF NOT EXISTS channels (
            id TEXT PRIMARY KEY, profile TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY, channel TEXT NOT NULL, request_id TEXT NOT NULL, profile TEXT NOT NULL,
            token TEXT, available INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL,
            title TEXT, angle TEXT, path TEXT, issue TEXT, UNIQUE(channel,request_id));
        CREATE INDEX IF NOT EXISTS recent ON jobs(channel,status,id);
    """)
    return db


@contextmanager
def transaction(db):
    db.execute("BEGIN IMMEDIATE")
    try:
        yield
        db.commit()
    except BaseException:
        db.rollback()
        raise


def configure(db, data):
    data = profile(data)
    with transaction(db):
        db.execute(
            "INSERT INTO channels(id,profile) VALUES(?,?) "
            "ON CONFLICT(id) DO UPDATE SET profile=excluded.profile",
            (data["id"], json.dumps(data, ensure_ascii=False)),
        )
    return {"channel": data["id"]}


def claim(db, channel, request_id, now=None):
    if not ID.fullmatch(request_id):
        raise ValueError("Choose a stable lowercase request ID")
    now = now or datetime.now(UTC)
    ts = int(now.timestamp())
    with transaction(db):
        row = db.execute("SELECT profile FROM channels WHERE id=?", (channel,)).fetchone()
        if row is None:
            raise ValueError("Unknown channel")
        db.execute(
            "INSERT OR IGNORE INTO jobs(channel,request_id,profile,status) VALUES(?,?,?,'queued')",
            (channel, request_id, row["profile"]),
        )
        job = db.execute(
            "SELECT * FROM jobs WHERE channel=? AND request_id=?", (channel, request_id)
        ).fetchone()
        if job["status"] in ("ready", "blocked") or (
            job["status"] == "working" and job["available"] > ts
        ):
            return {key: job[key] for key in ("id", "status", "path", "issue")}
        token = secrets.token_hex(16)
        db.execute(
            "UPDATE jobs SET status='working',token=?,available=?,issue=NULL WHERE id=?",
            (token, ts + 7200, job["id"]),
        )
        history = db.execute(
            "SELECT title,angle FROM jobs WHERE channel=? AND status='ready' "
            "ORDER BY id DESC LIMIT 16",
            (channel,),
        ).fetchall()
        return {
            "job": job["id"],
            "token": token,
            "request": request_id,
            "channel": json.loads(job["profile"]),
            "recent": [dict(r) for r in history],
        }


def own(db, job, token):
    row = db.execute(
        "SELECT * FROM jobs WHERE id=? AND token=? AND status='working'", (job, token)
    ).fetchone()
    if row is None:
        raise ValueError("The job was already completed or reclaimed")
    return row


def fail(db, job, token, message):
    with transaction(db):
        own(db, job, token)
        db.execute(
            "UPDATE jobs SET token=NULL,status='blocked',issue=? WHERE id=?", (message[:800], job)
        )


def deliver(db, root, job, token, draft, ff):
    row = own(db, job, token)
    cfg = json.loads(row["profile"])
    episode.validate(draft, cfg)
    angle = draft["angle"].strip()
    dest = root / "deliveries" / cfg["id"]
    dest.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=dest) as tmp:
        stage = Path(tmp) / "episode"
        stage.mkdir()
        episode.build(stage, root / "assets" / cfg["id"], cfg, draft, ff)
        final = dest / f"{job:06d}-{token[:8]}"
        with transaction(db):
            own(db, job, token)
            stage.rename(final)
            db.execute(
                """UPDATE jobs SET status='ready',token=NULL,title=?,angle=?,path=?,issue=NULL WHERE id=?""",
                (draft["title"], angle, str(final), job),
            )
    return str(final)


def writing_packet(job, root):
    skill = (SKILL / "references/script-desk.md").read_text(encoding="utf-8")
    contract = (SKILL / "references/episode-contract.md").read_text(encoding="utf-8")
    assets = root / "assets" / job["channel"]["id"]
    names = [
        f.relative_to(assets).as_posix()
        for f in sorted(assets.rglob("*"))
        if f.is_file() and f.resolve().is_relative_to(assets.resolve())
    ]
    posting = (SKILL / "references/posting.md").read_text(encoding="utf-8")
    return {
        "directions": contract,
        "script_desk": skill,
        "publishing": posting,
        "channel": job["channel"],
        "available_assets": names,
        "recent": job["recent"],
    }


def read_json():
    return json.load(sys.stdin.buffer, strict=True)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--desk", type=Path, default=Path.home() / ".creator-runbook")
    ap.add_argument("--ffmpeg", default=os.environ.get("CREATOR_FFMPEG", "ffmpeg"))
    sub = ap.add_subparsers(dest="cmd", required=True)
    for k in ("configure", "list", "status"):
        sub.add_parser(k)
    c = sub.add_parser("claim")
    c.add_argument("channel")
    c.add_argument("request_id")
    for k in ("finish", "block"):
        c = sub.add_parser(k)
        c.add_argument("job", type=int)
        c.add_argument("token")
        if k == "block":
            c.add_argument("reason")
    sub.add_parser("retry").add_argument("job", type=int)
    args = ap.parse_args()
    root = args.desk.expanduser().resolve()
    db = connect(root)
    try:
        if args.cmd == "configure":
            out = configure(db, read_json())
        elif args.cmd == "list":
            out = [
                json.loads(row["profile"])
                for row in db.execute("SELECT profile FROM channels ORDER BY id")
            ]
        elif args.cmd == "status":
            out = [
                dict(row)
                for row in db.execute(
                    "SELECT id,channel,request_id,status,title,path,issue FROM jobs ORDER BY id DESC LIMIT 100"
                )
            ]
        elif args.cmd == "retry":
            cur = db.execute(
                "UPDATE jobs SET status='retry',available=0,issue=NULL,profile=(SELECT profile FROM channels WHERE channels.id=jobs.channel) WHERE id=? AND status='blocked'",
                (args.job,),
            )
            if not cur.rowcount:
                raise ValueError("Retry needs a blocked job")
            out = {"queued": args.job}
        elif args.cmd == "claim":
            out = claim(db, args.channel, args.request_id)
            if "token" in out:
                out["brief"] = writing_packet(out, root)
        elif args.cmd == "finish":
            out = {"ready": deliver(db, root, args.job, args.token, read_json(), args.ffmpeg)}
        elif args.cmd == "block":
            fail(db, args.job, args.token, args.reason)
            out = {"blocked": args.job}
        print(json.dumps(out, ensure_ascii=False, indent=2))
    except (OSError, ValueError, RuntimeError, sqlite3.Error) as exc:
        ap.exit(1, f"creator-runbook: {exc}\n")
    finally:
        db.close()


if __name__ == "__main__":
    main()
