import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from systems import runtime
from systems.progress import Progress


class DemoRuntimeTests(unittest.TestCase):
    def test_resource_path_stays_inside_project_or_bundle(self):
        path = runtime.resource_path("missao_estoque", "assets")
        self.assertTrue(path.is_absolute())
        self.assertEqual(path.name, "assets")

    def test_demo_save_name_and_round_trip(self):
        with tempfile.TemporaryDirectory() as folder:
            save = Path(folder) / "save_demo.json"
            with patch("systems.progress.IS_FROZEN", True), patch("systems.progress.user_data_dir", return_value=Path(folder)):
                progress = Progress()
                self.assertEqual(progress.path, save)
                progress.select_character("luiza")
                self.assertTrue(save.is_file())
                self.assertEqual(json.loads(save.read_text(encoding="utf-8"))["selected_character"], "luiza")


if __name__ == "__main__":
    unittest.main()
