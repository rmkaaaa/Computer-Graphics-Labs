from app.model.color_math import cmyk_to_rgb, hsv_to_rgb, rgb_to_hex
from app.model.color_state import ColorState
from app.view.main_window import MainWindow


class ColorController:
    def __init__(self):
        self.model = ColorState()
        self.view = MainWindow(self)
        self.updating = False
        self.refresh_view()

    def run(self):
        self.view.run()

    def component_changed(self, model_name, component, value):
        if self.updating:
            return

        try:
            if model_name == "rgb":
                values = list(self.model.rgb)
                index = {"r": 0, "g": 1, "b": 2}[component]
                values[index] = value
                self.model.set_rgb(*values)

            elif model_name == "cmyk":
                values = list(self.model.cmyk)
                index = {"c": 0, "m": 1, "y": 2, "k": 3}[component]
                values[index] = value
                if value < 0 or value > 100:
                    fixed = max(0.0, min(100.0, value))
                    self.model.set_cmyk(*values)
                    self.model.warning = f"Значение {component.upper()} вне допустимого диапазона 0–100. Применено ограничение: {value:g} → {fixed:g}"
                else:
                    self.model.set_cmyk(*values)

            elif model_name == "hsv":
                values = list(self.model.hsv)
                index = {"h": 0, "s": 1, "v": 2}[component]
                values[index] = value
                low, high = (0, 360) if component == "h" else (0, 100)
                if value < low or value > high:
                    fixed = max(low, min(high, value))
                    values[index] = fixed
                    self.model.set_hsv(*values)
                    self.model.warning = f"Значение {component.upper()} вне допустимого диапазона {low}–{high}. Применено ограничение: {value:g} → {fixed:g}"
                else:
                    self.model.set_hsv(*values)

            self.refresh_view()
        except (ValueError, KeyError):
            self.refresh_view()

    def palette_changed(self, r, g, b):
        if self.updating:
            return
        self.model.set_rgb(r, g, b)
        self.refresh_view()

    def settings_changed(self, illuminant, algorithm, strength, threshold, gamut):
        if self.updating:
            return
        self.model.update_settings(
            illuminant,
            algorithm,
            strength,
            threshold,
            gamut,
        )
        self.refresh_view()

    def refresh_view(self):
        self.updating = True
        snapshot = self.model.snapshot()
        self.view.set_values(snapshot)
        self.view.set_ucr_enabled(self.model.settings.cmyk_algorithm == "UCR")
        self.view.set_gradients(self.make_gradients())
        self.updating = False

    def make_gradients(self):
        rgb = self.model.rgb
        cmyk = self.model.cmyk
        hsv = self.model.hsv

        gradients = {}

        for index, component in enumerate(("r", "g", "b")):
            colors = []
            for step in range(9):
                values = list(rgb)
                values[index] = 255.0 * step / 8.0
                colors.append(rgb_to_hex(*values))
            gradients[f"rgb_{component}"] = colors

        for index, component in enumerate(("c", "m", "y", "k")):
            colors = []
            for step in range(9):
                values = list(cmyk)
                values[index] = 100.0 * step / 8.0
                converted = cmyk_to_rgb(*values)
                colors.append(rgb_to_hex(*converted))
            gradients[f"cmyk_{component}"] = colors

        ranges = [360.0, 100.0, 100.0]
        for index, component in enumerate(("h", "s", "v")):
            colors = []
            for step in range(9):
                values = list(hsv)
                values[index] = ranges[index] * step / 8.0
                converted = hsv_to_rgb(*values)
                colors.append(rgb_to_hex(*converted))
            gradients[f"hsv_{component}"] = colors

        return gradients
