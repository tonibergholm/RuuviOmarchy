#!/usr/bin/env python3
"""Read a bounded, read-only snapshot of RuuviLinux's SQLite database."""
import argparse
from contextlib import closing
import hashlib
import json
import math
import os
from pathlib import Path
import socket
import sqlite3
import tempfile
import time


def finite(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value if math.isfinite(value) else None


def snapshot(path, now=None):
    now = time.time() if now is None else now
    result = {"version": 1, "sensors": [], "error": ""}
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        result["error"] = "Open RuuviLinux to discover your tags."
        return result
    try:
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=.25)) as db:
            rows = db.execute("SELECT id,name,favorite,last_seen,rssi,latest FROM sensors ORDER BY favorite DESC,name COLLATE NOCASE,id LIMIT 128")
            for identity, name, favorite, stamp, rssi, latest in rows:
                try:
                    values = json.loads(latest)
                    if not isinstance(values, dict): continue
                except (ValueError, TypeError):
                    continue
                stamp = finite(stamp)
                age = max(0, now - stamp) if stamp is not None else None
                result["sensors"].append({
                    "id": str(identity)[:100], "name": str(name)[:80],
                    "favorite": bool(favorite), "age": age,
                    "stale": stamp is None or stamp > now + 5 or age > 30,
                    "rssi": finite(rssi),
                    **{key: finite(values.get(key)) for key in ("temperature", "humidity", "pressure", "voltage")}
                })
    except (sqlite3.Error, OSError):
        result["error"] = "Cannot read saved sensors. Check RuuviLinux and the database setting."
    return result


def collector_status(path, timeout=.25):
    """Ask RuuviLinux's collector for status; mirrors ruuvilinux.collector_client."""
    path = Path(path).expanduser().resolve()
    digest = hashlib.sha256(str(path).encode()).hexdigest()[:20]
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", str(Path(tempfile.gettempdir()) / f"ruuvilinux-{os.getuid()}")))
    result = {"running": False, "status": "", "homeassistant": ""}
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(timeout)
            client.connect(str(runtime / f"ruuvilinux-collector-{digest}.sock"))
            client.sendall(b'{"command":"status"}\n')
            data = bytearray()
            while b"\n" not in data and len(data) <= 16384:
                packet = client.recv(4096)
                if not packet: break
                data.extend(packet)
        report = json.loads(bytes(data).split(b"\n", 1)[0])
    except (OSError, ValueError):
        return result
    if not isinstance(report, dict) or not report.get("running"): return result
    ha = report.get("homeassistant")
    result.update(running=True, status=str(report.get("status", ""))[:200])
    if isinstance(ha, dict) and ha.get("enabled"): result["homeassistant"] = str(ha.get("status", ""))[:200]
    return result


def default_path():
    return Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "ruuvilinux/sensors.sqlite3"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", default="")
    args = parser.parse_args()
    path = args.database or default_path()
    report = snapshot(path)
    report["collector"] = collector_status(path)
    print(json.dumps(report, allow_nan=False))
