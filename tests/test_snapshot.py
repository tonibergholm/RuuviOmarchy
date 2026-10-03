import importlib.util
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

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


if __name__ == '__main__': unittest.main()
