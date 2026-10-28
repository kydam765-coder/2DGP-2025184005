import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import boy


class AutorunTests(unittest.TestCase):
    def setUp(self):
        self.clock = [0.0]
        self.time_patch = patch.object(boy, 'get_time', lambda: self.clock[0])
        self.image_patch = patch.object(boy, 'load_image', lambda _: object())
        self.time_patch.start()
        self.image_patch.start()
        self.character = boy.Boy()

    def tearDown(self):
        self.time_patch.stop()
        self.image_patch.stop()

    def set_time(self, value):
        self.clock[0] = value

    def test_autorun_state_class_is_attached_to_boy(self):
        self.assertIsInstance(self.character.autorun, boy.Autorun)

    def test_idle_enters_autorun_when_started(self):
        self.character.begin_autorun()
        self.assertEqual(self.character.state, 'AUTORUN')

    def test_autorun_can_only_start_from_idle(self):
        self.character.start_running()
        self.character.begin_autorun()
        self.assertEqual(self.character.state, 'RUN')


if __name__ == '__main__':
    unittest.main()
