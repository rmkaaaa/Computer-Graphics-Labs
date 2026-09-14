from dataclasses import dataclass

from .color_math import (
    clamp,
    cmyk_to_rgb,
    get_rgb_xyz_matrices,
    get_white_point_xyz,
    hsv_to_rgb,
    lab_to_xyz,
    rgb_to_cmyk,
    rgb_to_hex,
    rgb_to_hsv,
    rgb_to_xyz,
    xyz_to_lab,
    xyz_to_rgb,
)


@dataclass
class ColorSettings:
    illuminant: str = "D65"
    cmyk_algorithm: str = "GCR"
    black_strength: float = 100.0
    ucr_threshold: float = 55.0
    gamut_strategy: str = "Clipping"


class ColorState:
    def __init__(self):
        self.settings = ColorSettings()
        self.rgb = (74.0, 125.0, 255.0)
        self.warning = ""
        self.recalculate()

    def set_rgb(self, r, g, b):
        values = (float(r), float(g), float(b))
        names = ("R", "G", "B")
        fixed = tuple(clamp(value, 0, 255) for value in values)
        changed = [
            f"{name}: {value:g} → {new_value:g}"
            for name, value, new_value in zip(names, values, fixed)
            if value != new_value
        ]
        self.rgb = fixed
        self.warning = (
            "Значение вне допустимого диапазона 0–255. Применено ограничение: "
            + ", ".join(changed)
            if changed else ""
        )
        self.recalculate()

    def set_cmyk(self, c, m, y, k):
        self.rgb = cmyk_to_rgb(c, m, y, k)
        self.warning = ""
        self.recalculate()

    def set_hsv(self, h, s, v):
        self.rgb = hsv_to_rgb(h, s, v)
        self.warning = ""
        self.recalculate()

    def set_xyz(self, x, y, z):
        self.rgb, warning = xyz_to_rgb(
            x,
            y,
            z,
            self.settings.illuminant,
            self.settings.gamut_strategy,
        )
        self.warning = "Цвет вышел за RGB-гамму. Применена обработка диапазона." if warning else ""
        self.recalculate()

    def set_lab(self, l, a, b):
        xyz = lab_to_xyz(l, a, b, self.settings.illuminant)
        self.rgb, warning = xyz_to_rgb(
            *xyz,
            self.settings.illuminant,
            self.settings.gamut_strategy,
        )
        self.warning = "Цвет вышел за RGB-гамму. Применена обработка диапазона." if warning else ""
        self.recalculate()

    def update_settings(
        self,
        illuminant,
        cmyk_algorithm,
        black_strength,
        ucr_threshold,
        gamut_strategy,
    ):
        self.settings.illuminant = illuminant
        self.settings.cmyk_algorithm = cmyk_algorithm
        self.settings.black_strength = clamp(float(black_strength), 0, 100)
        self.settings.ucr_threshold = clamp(float(ucr_threshold), 0, 100)
        self.settings.gamut_strategy = gamut_strategy
        self.warning = ""
        self.recalculate()

    def recalculate(self):
        r, g, b = self.rgb

        self.cmyk = rgb_to_cmyk(
            r,
            g,
            b,
            self.settings.cmyk_algorithm,
            self.settings.black_strength,
            self.settings.ucr_threshold,
        )
        self.hsv = rgb_to_hsv(r, g, b)
        self.xyz = rgb_to_xyz(r, g, b, self.settings.illuminant)
        self.lab = xyz_to_lab(*self.xyz, self.settings.illuminant)
        self.hex_value = rgb_to_hex(r, g, b)
        self.rgb_to_xyz_matrix, self.xyz_to_rgb_matrix = get_rgb_xyz_matrices(
            self.settings.illuminant
        )
        self.white_point = get_white_point_xyz(self.settings.illuminant)

    def snapshot(self):
        return {
            "rgb": self.rgb,
            "cmyk": self.cmyk,
            "hsv": self.hsv,
            "xyz": self.xyz,
            "lab": self.lab,
            "hex": self.hex_value,
            "warning": self.warning,
            "matrix": self.rgb_to_xyz_matrix,
            "white_point": self.white_point,
        }
