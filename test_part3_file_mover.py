#!/usr/bin/env python3
"""test_part3_file_mover.py

Unit‑style tests for **part3_file_mover.py**.  They create a temporary
source tree and JSON descriptors (Parts 1‑1 & 2), invoke the mover
script via *subprocess*, and verify that files are (or are not) moved as
expected.

Run with:
    python test_part3_file_mover.py

or through pytest if preferred.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class MoveFilesTest(unittest.TestCase):
    """End‑to‑end checks using a fresh tmpdir each time."""

    def setUp(self) -> None:  # noqa: D401
        # Create an isolated temp workspace.
        self._tmp = tempfile.TemporaryDirectory()  # cleaned in tearDown
        workspace = Path(self._tmp.name)

        # --- source tree ---
        self.src_root = workspace / "source"
        (self.src_root / "subdir").mkdir(parents=True, exist_ok=True)
        (self.src_root / "file1.txt").write_text("alpha\n")
        (self.src_root / "subdir" / "file2.txt").write_text("bravo\n")

        # --- destination root ---
        self.dest_root = workspace / "dest"
        self.dest_root.mkdir()

        # --- JSON inputs ---
        self.file_list_json = workspace / "file_list.json"
        file_list = [
            {"id": 1, "path": "file1.txt"},
            {"id": 2, "path": "subdir/file2.txt"},
        ]
        self.file_list_json.write_text(json.dumps(file_list, indent=2))

        self.mapping_json = workspace / "mapping.json"
        mapping = [
            {
                "id": 1,
                "new_name": "document1.txt",
                "new_path": "Work",
            },
            {
                "id": 2,
                "new_name": "document2.txt",
                "new_path": "Work/Project",
            },
        ]
        self.mapping_json.write_text(json.dumps(mapping, indent=2))

        # Path to the script under test (assumed to live next to this file)
        self.script = Path(__file__).with_name("part3_file_mover.py")
        if not self.script.exists():
            self.fail(f"Cannot find {self.script}; place tests alongside script.")

    def tearDown(self) -> None:  # noqa: D401
        self._tmp.cleanup()

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _run(self, *extra_args: str) -> subprocess.CompletedProcess[str]:
        """Invoke the script with constructed args; capture output."""
        cmd = [
            sys.executable,
            str(self.script),
            "--file-list",
            str(self.file_list_json),
            "--mapping",
            str(self.mapping_json),
            "--root",
            str(self.src_root),
            "--dest-root",
            str(self.dest_root),
            *extra_args,
        ]
        return subprocess.run(cmd, text=True, capture_output=True)

    # ------------------------------------------------------------------
    # actual tests
    # ------------------------------------------------------------------

    def test_dry_run_does_not_move_files(self):
        """--dry-run should leave original files intact and create nothing."""
        result = self._run("--dry-run")
        self.assertEqual(result.returncode, 0, msg=result.stderr)

        self.assertTrue((self.src_root / "file1.txt").exists())
        self.assertTrue((self.src_root / "subdir" / "file2.txt").exists())
        self.assertFalse((self.dest_root / "Work" / "document1.txt").exists())


    def test_actual_move_relocates_files(self):
        """Without --dry-run, files are moved to the destination tree."""
        result = self._run()
        self.assertEqual(result.returncode, 0, msg=result.stderr)

        self.assertFalse((self.src_root / "file1.txt").exists())
        self.assertFalse((self.src_root / "subdir" / "file2.txt").exists())

        self.assertTrue((self.dest_root / "Work" / "document1.txt").is_file())
        self.assertTrue(
            (self.dest_root / "Work" / "Project" / "document2.txt").is_file()
        )


if __name__ == "__main__":
    print("Start testing!")
    unittest.main(verbosity=2)
