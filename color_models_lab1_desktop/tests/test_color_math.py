import unittest

from app.model.color_math import (
    cmyk_to_rgb,
    get_rgb_xyz_matrices,
    hsv_to_rgb,
    rgb_to_cmyk,
    rgb_to_hsv,
    rgb_to_xyz,
    xyz_to_lab,
    xyz_to_rgb,
)
from app.model.color_state import ColorState


class ColorMathTests(unittest.TestCase):
    def assertTupleAlmostEqual(self, actual, expected, places=4):
        self.assertEqual(len(actual), len(expected))
        for a, e in zip(actual, expected):
            self.assertAlmostEqual(a, e, places=places)

    def test_black_rgb_to_cmyk_gcr(self):
        self.assertTupleAlmostEqual(
            rgb_to_cmyk(0, 0, 0, "GCR", 100, 55),
            (0, 0, 0, 100),
            5,
        )

    def test_black_cmyk_to_rgb(self):
        self.assertTupleAlmostEqual(
            cmyk_to_rgb(0, 0, 0, 100),
            (0, 0, 0),
            5,
        )

    def test_black_rgb_to_hsv(self):
        self.assertTupleAlmostEqual(
            rgb_to_hsv(0, 0, 0),
            (0, 0, 0),
            5,
        )

    def test_black_hsv_to_rgb(self):
        self.assertTupleAlmostEqual(
            hsv_to_rgb(0, 0, 0),
            (0, 0, 0),
            5,
        )

    def test_white_rgb_to_cmyk(self):
        self.assertTupleAlmostEqual(
            rgb_to_cmyk(255, 255, 255, "GCR", 100, 55),
            (0, 0, 0, 0),
            5,
        )

    def test_red_rgb_to_hsv(self):
        self.assertTupleAlmostEqual(
            rgb_to_hsv(255, 0, 0),
            (0, 100, 100),
            5,
        )

    def test_red_hsv_to_rgb(self):
        self.assertTupleAlmostEqual(
            hsv_to_rgb(0, 100, 100),
            (255, 0, 0),
            5,
        )

    def test_red_rgb_to_cmyk(self):
        self.assertTupleAlmostEqual(
            rgb_to_cmyk(255, 0, 0, "GCR", 100, 55),
            (0, 100, 100, 0),
            5,
        )

    def test_red_xyz_d65(self):
        xyz = rgb_to_xyz(255, 0, 0, "D65")
        self.assertTupleAlmostEqual(
            xyz,
            (41.23908, 21.26390, 1.93308),
            4,
        )

    def test_red_lab_d65(self):
        xyz = rgb_to_xyz(255, 0, 0, "D65")
        lab = xyz_to_lab(*xyz, "D65")
        self.assertTupleAlmostEqual(
            lab,
            (53.2408, 80.0925, 67.2032),
            2,
        )

    def test_rgb_xyz_rgb_round_trip(self):
        source = (74, 125, 255)
        xyz = rgb_to_xyz(*source, "D65")
        rgb, warning = xyz_to_rgb(*xyz, "D65", "Clipping")
        self.assertFalse(warning)
        self.assertTupleAlmostEqual(rgb, source, 3)

    def test_matrix_changes_with_illuminant(self):
        d65, _ = get_rgb_xyz_matrices("D65")
        d50, _ = get_rgb_xyz_matrices("D50")
        self.assertNotEqual(
            tuple(round(value, 8) for row in d65 for value in row),
            tuple(round(value, 8) for row in d50 for value in row),
        )

    def test_scaling_keeps_rgb_in_range(self):
        rgb, warning = xyz_to_rgb(150, 20, 180, "D65", "Scaling")
        self.assertTrue(warning)
        self.assertTrue(all(0 <= value <= 255 for value in rgb))

    def test_ucr_below_threshold_has_no_black(self):
        cmyk = rgb_to_cmyk(128, 128, 128, "UCR", 100, 55)
        self.assertAlmostEqual(cmyk[3], 0.0, places=5)

    def test_ucr_black_uses_black(self):
        cmyk = rgb_to_cmyk(0, 0, 0, "UCR", 100, 55)
        self.assertAlmostEqual(cmyk[3], 100.0, places=5)

    def test_state_black_stays_black_after_recalculation(self):
        state = ColorState()
        state.set_rgb(0, 0, 0)
        self.assertTupleAlmostEqual(state.rgb, (0, 0, 0), 5)
        self.assertTupleAlmostEqual(state.cmyk, (0, 0, 0, 100), 5)
        self.assertTupleAlmostEqual(state.hsv, (0, 0, 0), 5)
        state.set_cmyk(*state.cmyk)
        self.assertTupleAlmostEqual(state.rgb, (0, 0, 0), 5)


    def test_rgb_negative_input_warns_and_clamps(self):
        state = ColorState()
        state.set_rgb(-40, 125, 255)
        self.assertEqual(state.rgb[0], 0)
        self.assertIn("0–255", state.warning)
        self.assertIn("-40", state.warning)

    def test_rgb_overflow_input_warns_and_clamps(self):
        state = ColorState()
        state.set_rgb(270, 125, 255)
        self.assertEqual(state.rgb[0], 255)
        self.assertIn("0–255", state.warning)
        self.assertIn("270", state.warning)


if __name__ == "__main__":
    unittest.main()
