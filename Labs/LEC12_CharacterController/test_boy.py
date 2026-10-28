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

    def test_autorun_starts_without_an_initial_position_jump(self):
        start_x = self.character.x
        self.character.begin_autorun()
        self.character.update()
        self.assertEqual(self.character.x, start_x)

    def test_autorun_moves_in_its_facing_direction(self):
        self.character.begin_autorun()
        self.set_time(1.0)
        self.character.update()
        self.assertGreater(self.character.x, 400)

    def test_autorun_accelerates_over_time(self):
        self.character.begin_autorun()
        self.set_time(1.0)
        self.character.update()
        first_distance = self.character.x - 400
        self.set_time(2.0)
        self.character.update()
        self.assertGreater(self.character.x - 400 - first_distance, first_distance)

    def test_autorun_speed_has_a_cap(self):
        with patch.object(boy.Autorun, 'DURATION', 100.0):
            self.character.begin_autorun()
            self.set_time(5.9)
            self.character.update()
            start_x = self.character.x
            self.set_time(6.0)
            self.character.update()
            first_distance = abs(self.character.x - start_x)
            start_x = self.character.x
            self.set_time(6.1)
            self.character.update()
            self.assertAlmostEqual(abs(self.character.x - start_x), first_distance)

    def test_autorun_scales_up_over_time(self):
        self.character.begin_autorun()
        self.set_time(2.0)
        self.character.update()
        self.assertAlmostEqual(self.character.scale, 1.4)

    def test_autorun_scale_has_a_cap(self):
        with patch.object(boy.Autorun, 'DURATION', 100.0):
            self.character.begin_autorun()
            self.set_time(6.0)
            self.character.update()
            self.assertEqual(self.character.scale, boy.Autorun.MAX_SCALE)


if __name__ == '__main__':
    unittest.main()
