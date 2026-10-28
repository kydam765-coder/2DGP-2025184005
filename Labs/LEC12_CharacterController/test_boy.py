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

    def test_autorun_reverses_at_the_right_edge(self):
        self.character.x = 749
        self.character.begin_autorun()
        self.set_time(1.0)
        self.character.update()
        self.assertEqual(self.character.face_dir, -1)
        self.assertLessEqual(self.character.x, 800 - 50 * self.character.scale)

    def test_autorun_reverses_at_the_left_edge(self):
        self.character.x = 51
        self.character.face_dir = -1
        self.character.begin_autorun()
        self.set_time(1.0)
        self.character.update()
        self.assertEqual(self.character.face_dir, 1)
        self.assertGreaterEqual(self.character.x, 50 * self.character.scale)

    def test_autorun_returns_to_idle_after_five_seconds(self):
        self.character.begin_autorun()
        self.set_time(5.0)
        self.character.update()
        self.assertEqual(self.character.state, 'IDLE')
        self.assertEqual(self.character.scale, 1.0)

    def test_direction_key_cancels_autorun_into_manual_run(self):
        for direction in (-1, 1):
            self.character.begin_autorun()
            self.set_time(self.clock[0] + 0.1)
            self.character.update()
            self.character.update_direction_keys([direction])
            self.assertEqual(self.character.state, 'RUN')
            self.assertEqual(self.character.face_dir, direction)
            self.assertEqual(self.character.scale, 1.0)
            self.character.update_direction_keys([])
            self.assertEqual(self.character.state, 'IDLE')

    def test_interrupted_autorun_uses_manual_run_movement(self):
        self.character.begin_autorun()
        self.set_time(0.1)
        self.character.update()
        self.character.update_direction_keys([-1])
        start_x = self.character.x
        self.character.update()
        self.assertLess(self.character.x, start_x)
        self.character.update_direction_keys([])
        self.assertEqual(self.character.state, 'IDLE')

    def test_idle_timer_restarts_after_autorun(self):
        self.character.begin_autorun()
        self.set_time(5.0)
        self.character.update()
        self.set_time(9.9)
        self.character.update()
        self.assertEqual(self.character.state, 'IDLE')
        self.set_time(10.0)
        self.character.update()
        self.assertEqual(self.character.state, 'SLEEP')


if __name__ == '__main__':
    unittest.main()
