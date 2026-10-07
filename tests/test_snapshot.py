import importlib.util
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import socket
import sqlite3
import tempfile
import threading
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location("reader", Path(__file__).parents[1] / "read-sensors.py")
reader = importlib.util.module_from_spec(spec); spec.loader.exec_module(reader)


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "sensors with space #.sqlite3"

    def make_database(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("CREATE TABLE sensors (id TEXT, name TEXT, favorite INTEGER, last_seen REAL, rssi INTEGER, latest TEXT)")
            db.executemany("INSERT INTO sensors VALUES (?,?,?,?,?,?)", [
                ("A", "Kitchen <&>", 0, 1000, -60, json.dumps({"temperature":21.4,"humidity":45,"pressure":1000,"voltage":2.8})),
                ("B", "Fridge", 1, 900, -70, json.dumps({"temperature":-2.4,"humidity":None})),
                ("C", "Bad clock", 0, 2000, -50, json.dumps({"temperature":True,"humidity":float('nan')})),
                ("D", "Bad JSON", 0, 1000, -50, "bad json")])

    def test_favorites_values_freshness_and_read_only(self):
        self.make_database(); before = self.path.read_bytes()
        report = reader.snapshot(self.path, now=1010)
        self.assertEqual(report['error'], '')
        self.assertEqual([s['id'] for s in report['sensors']], ['B','C','A'])
        fridge, future, kitchen = report['sensors']
        self.assertTrue(fridge['favorite']); self.assertTrue(fridge['stale'])
        self.assertEqual(fridge['temperature'], -2.4)
        self.assertTrue(future['stale']); self.assertIsNone(future['temperature']); self.assertIsNone(future['humidity'])
        self.assertFalse(kitchen['stale']); self.assertEqual(kitchen['age'],10)
        self.assertEqual(kitchen['name'],'Kitchen <&>')
        json.dumps(report,allow_nan=False)
        self.assertEqual(self.path.read_bytes(), before)

    def test_missing_database_is_not_created(self):
        report = reader.snapshot(self.path)
        self.assertEqual(report['sensors'], []); self.assertTrue(report['error'])
        self.assertFalse(self.path.exists())

    def test_invalid_database_reports_error(self):
        self.path.write_text('invalid sqlite')
        self.assertTrue(reader.snapshot(self.path)['error'])

    def test_bounded_snapshot(self):
        self.make_database()
        with closing(sqlite3.connect(self.path)) as db, db:
            db.executemany("INSERT INTO sensors VALUES (?,?,?,?,?,?)",[(str(i),'Tag',0,1000,-60,'{}') for i in range(200)])
        # The limit includes one invalid JSON row, which is skipped safely.
        self.assertEqual(len(reader.snapshot(self.path)['sensors']),127)


class CollectorStatusTests(unittest.TestCase):
    def setUp(self):
        # Unix socket paths are short; avoid long temporary directories.
        self.runtime = tempfile.TemporaryDirectory(prefix='ruuvi-', dir='/tmp')
        self.addCleanup(self.runtime.cleanup)
        patcher = mock.patch.dict(os.environ, {'XDG_RUNTIME_DIR': self.runtime.name}); patcher.start(); self.addCleanup(patcher.stop)
        self.database = Path(self.runtime.name) / 'sensors.sqlite3'

    def serve(self, response):
        digest = hashlib.sha256(str(self.database.resolve()).encode()).hexdigest()[:20]
        server = socket.socket(socket.AF_UNIX); server.bind(str(Path(self.runtime.name) / f'ruuvilinux-collector-{digest}.sock')); server.listen(1)
        self.addCleanup(server.close)
        def answer():
            connection, _ = server.accept()
            with connection:
                self.request = connection.recv(4096); connection.sendall(response)
        thread = threading.Thread(target=answer, daemon=True); thread.start(); return thread

    def test_offline_collector(self):
        self.assertEqual(reader.collector_status(self.database), {'running': False, 'status': '', 'homeassistant': ''})

    def test_status_with_home_assistant(self):
        thread = self.serve(json.dumps({'running': True, 'status': 'Background collector · scanning',
            'homeassistant': {'enabled': True, 'status': 'Home Assistant · publishing'}}).encode() + b'\n')
        status = reader.collector_status(self.database); thread.join(2)
        self.assertEqual(json.loads(self.request), {'command': 'status'})
        self.assertEqual(status, {'running': True, 'status': 'Background collector · scanning', 'homeassistant': 'Home Assistant · publishing'})

    def test_older_collector_and_bad_reply(self):
        thread = self.serve(b'{"running": true, "status": "Background collector paused"}\n')
        self.assertEqual(reader.collector_status(self.database)['homeassistant'], ''); thread.join(2)

    def test_garbage_reply_is_offline(self):
        thread = self.serve(b'not json\n')
        self.assertFalse(reader.collector_status(self.database)['running']); thread.join(2)


if __name__ == '__main__': unittest.main()
