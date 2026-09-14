import tkinter as tk
from tkinter import colorchooser, ttk

from app.model.color_math import rgb_to_hex


class GradientSlider(tk.Frame):
    def __init__(self, master, label, minimum, maximum, step, command):
        super().__init__(master)
        self.minimum = minimum
        self.maximum = maximum
        self.step = step
        self.command = command
        self._internal = False
        self.value = minimum

        self.columnconfigure(1, weight=1)

        self.label = ttk.Label(self, text=label, width=3)
        self.label.grid(row=0, column=0, padx=(0, 8))

        self.canvas = tk.Canvas(self, height=22, highlightthickness=1, highlightbackground="#B8B8B8")
        self.canvas.grid(row=0, column=1, sticky="ew")
        self.canvas.bind("<Configure>", self._redraw)
        self.canvas.bind("<Button-1>", self._mouse_set)
        self.canvas.bind("<B1-Motion>", self._mouse_set)

        self.entry_var = tk.StringVar(value="0")
        self.entry = ttk.Entry(self, width=8, textvariable=self.entry_var)
        self.entry.grid(row=0, column=2, padx=(8, 0))
        self.entry.bind("<Return>", self._entry_changed)
        self.entry.bind("<FocusOut>", self._entry_changed)

        self.gradient = ["#000000", "#FFFFFF"]

    def _mouse_set(self, event):
        if self._internal:
            return
        width = max(self.canvas.winfo_width() - 1, 1)
        ratio = max(0.0, min(1.0, event.x / width))
        raw = self.minimum + ratio * (self.maximum - self.minimum)
        value = round(raw / self.step) * self.step
        self.set_value(value, notify=True)

    def _entry_changed(self, event=None):
        if self._internal:
            return
        try:
            value = float(self.entry_var.get().replace(",", "."))
        except ValueError:
            self._show_value()
            return
        self.command(value)

    def set_value(self, value, notify=False):
        value = max(self.minimum, min(self.maximum, float(value)))
        if self.step >= 1:
            value = round(value)
        else:
            value = round(value / self.step) * self.step

        self.value = value
        self._internal = True
        self._show_value()
        self._redraw()
        self._internal = False

        if notify:
            self.command(self.value)

    def _show_value(self):
        if abs(self.value - round(self.value)) < 1e-10:
            text = str(int(round(self.value)))
        else:
            text = f"{self.value:.3f}".rstrip("0").rstrip(".")
        self.entry_var.set(text)

    def set_gradient(self, colors):
        self.gradient = list(colors)
        self._redraw()

    def _redraw(self, event=None):
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        if width <= 1 or height <= 1:
            return

        self.canvas.delete("all")

        if len(self.gradient) < 2:
            self.gradient = ["#000000", "#FFFFFF"]

        segments = max(width, 2)
        stops = [self._hex_to_rgb(color) for color in self.gradient]

        for x in range(segments):
            pos = x / max(segments - 1, 1)
            scaled = pos * (len(stops) - 1)
            index = min(int(scaled), len(stops) - 2)
            local = scaled - index
            a = stops[index]
            b = stops[index + 1]
            color = (
                int(a[0] + (b[0] - a[0]) * local),
                int(a[1] + (b[1] - a[1]) * local),
                int(a[2] + (b[2] - a[2]) * local),
            )
            self.canvas.create_line(x, 0, x, height, fill=rgb_to_hex(*color))

        ratio = (self.value - self.minimum) / (self.maximum - self.minimum)
        x = ratio * width
        self.canvas.create_line(x, 1, x, height - 1, fill="#000000", width=3)
        self.canvas.create_line(x + 1, 1, x + 1, height - 1, fill="#FFFFFF", width=1)

    def _hex_to_rgb(self, value):
        value = value.lstrip("#")
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


class MainWindow:
    def __init__(self, listener):
        self.listener = listener
        self.root = tk.Tk()
        self.root.title("Лабораторная работа 1 — CMYK ↔ RGB ↔ HSV")
        self.root.geometry("1120x820")
        self.root.minsize(950, 720)

        self.sliders = {}
        self.value_labels = {}

        self._build()

    def _build(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        top = ttk.Frame(main)
        top.pack(fill="x")

        preview_frame = ttk.LabelFrame(top, text="Цвет", padding=10)
        preview_frame.pack(side="left", fill="y")

        self.preview = tk.Canvas(preview_frame, width=160, height=90, highlightthickness=1, highlightbackground="#AAAAAA")
        self.preview.pack()

        self.hex_label = ttk.Label(preview_frame, text="#000000", font=("Arial", 12, "bold"))
        self.hex_label.pack(pady=(8, 4))

        ttk.Button(preview_frame, text="Выбрать из палитры", command=self._choose_color).pack(fill="x")

        settings = ttk.LabelFrame(top, text="Настройки", padding=10)
        settings.pack(side="left", fill="both", expand=True, padx=(12, 0))

        self.illuminant = tk.StringVar(value="D65")
        self.algorithm = tk.StringVar(value="GCR")
        self.gamut = tk.StringVar(value="Clipping")
        self.strength = tk.DoubleVar(value=100)
        self.ucr_threshold = tk.DoubleVar(value=55)

        self._setting_row(settings, 0, "Белая точка", self.illuminant, ["D65", "D50", "E"])
        self._setting_row(settings, 1, "CMYK", self.algorithm, ["GCR", "UCR"])
        self._setting_row(settings, 2, "RGB-гамма", self.gamut, ["Clipping", "Scaling"])

        ttk.Label(settings, text="Сила K").grid(row=3, column=0, sticky="w", pady=4)
        strength_scale = ttk.Scale(settings, from_=0, to=100, variable=self.strength, command=lambda value: self._settings_changed())
        strength_scale.grid(row=3, column=1, sticky="ew", pady=4)

        ttk.Label(settings, text="Порог UCR").grid(row=4, column=0, sticky="w", pady=4)
        self.ucr_scale = ttk.Scale(settings, from_=0, to=100, variable=self.ucr_threshold, command=lambda value: self._settings_changed())
        self.ucr_scale.grid(row=4, column=1, sticky="ew", pady=4)

        settings.columnconfigure(1, weight=1)

        self.warning = ttk.Label(main, text="", foreground="#9A5200")
        self.warning.pack(fill="x", pady=(8, 0))

        models = ttk.Frame(main)
        models.pack(fill="both", expand=True, pady=(8, 0))
        models.columnconfigure(0, weight=1)
        models.columnconfigure(1, weight=1)
        models.columnconfigure(2, weight=1)

        self._build_model(models, "rgb", "RGB", [("R", 0, 255, 1), ("G", 0, 255, 1), ("B", 0, 255, 1)], 0)
        self._build_model(models, "cmyk", "CMYK", [("C", 0, 100, 0.1), ("M", 0, 100, 0.1), ("Y", 0, 100, 0.1), ("K", 0, 100, 0.1)], 1)
        self._build_model(models, "hsv", "HSV", [("H", 0, 360, 0.1), ("S", 0, 100, 0.1), ("V", 0, 100, 0.1)], 2)

        extra = ttk.Frame(main)
        extra.pack(fill="x", pady=(10, 0))
        extra.columnconfigure(0, weight=1)
        extra.columnconfigure(1, weight=1)
        extra.columnconfigure(2, weight=2)

        xyz_frame = ttk.LabelFrame(extra, text="XYZ", padding=10)
        xyz_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        lab_frame = ttk.LabelFrame(extra, text="LAB", padding=10)
        lab_frame.grid(row=0, column=1, sticky="nsew", padx=6)
        matrix_frame = ttk.LabelFrame(extra, text="Матрица RGB → XYZ", padding=10)
        matrix_frame.grid(row=0, column=2, sticky="nsew", padx=(6, 0))

        for index, name in enumerate(("X", "Y", "Z")):
            label = ttk.Label(xyz_frame, text=f"{name}: 0")
            label.pack(anchor="w", pady=2)
            self.value_labels[f"xyz_{name.lower()}"] = label

        for index, name in enumerate(("L", "a", "b")):
            label = ttk.Label(lab_frame, text=f"{name}: 0")
            label.pack(anchor="w", pady=2)
            self.value_labels[f"lab_{name.lower()}"] = label

        self.white_label = ttk.Label(matrix_frame, text="")
        self.white_label.pack(anchor="w")
        self.matrix_label = ttk.Label(matrix_frame, text="", font=("Courier New", 10), justify="left")
        self.matrix_label.pack(anchor="w", pady=(6, 0))

    def _setting_row(self, parent, row, title, variable, values):
        ttk.Label(parent, text=title).grid(row=row, column=0, sticky="w", pady=4)
        box = ttk.Combobox(parent, textvariable=variable, values=values, state="readonly")
        box.grid(row=row, column=1, sticky="ew", pady=4)
        box.bind("<<ComboboxSelected>>", lambda event: self._settings_changed())

    def _build_model(self, parent, key, title, definitions, column):
        frame = ttk.LabelFrame(parent, text=title, padding=10)
        frame.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 6, 0 if column == 2 else 6))

        for label, minimum, maximum, step in definitions:
            slider = GradientSlider(
                frame,
                label,
                minimum,
                maximum,
                step,
                lambda value, model=key, component=label.lower(): self.listener.component_changed(model, component, value),
            )
            slider.pack(fill="x", pady=7)
            self.sliders[f"{key}_{label.lower()}"] = slider

        ttk.Button(frame, text="Выбрать из палитры", command=self._choose_color).pack(fill="x", pady=(8, 0))

    def _choose_color(self):
        initial = self.hex_label.cget("text")
        result = colorchooser.askcolor(color=initial, parent=self.root)
        if result[0] is not None:
            r, g, b = result[0]
            self.listener.palette_changed(r, g, b)

    def _settings_changed(self):
        self.listener.settings_changed(
            self.illuminant.get(),
            self.algorithm.get(),
            self.strength.get(),
            self.ucr_threshold.get(),
            self.gamut.get(),
        )

    def set_ucr_enabled(self, enabled):
        self.ucr_scale.state(["!disabled"] if enabled else ["disabled"])

    def set_values(self, snapshot):
        r, g, b = snapshot["rgb"]
        c, m, y, k = snapshot["cmyk"]
        h, s, v = snapshot["hsv"]

        values = {
            "rgb_r": r,
            "rgb_g": g,
            "rgb_b": b,
            "cmyk_c": c,
            "cmyk_m": m,
            "cmyk_y": y,
            "cmyk_k": k,
            "hsv_h": h,
            "hsv_s": s,
            "hsv_v": v,
        }

        for key, value in values.items():
            self.sliders[key].set_value(value, notify=False)

        self.hex_label.configure(text=snapshot["hex"])
        self.preview.configure(bg=snapshot["hex"])
        self.warning.configure(text=snapshot["warning"])

        x, yy, z = snapshot["xyz"]
        l, a, bb = snapshot["lab"]
        self.value_labels["xyz_x"].configure(text=f"X: {x:.4f}")
        self.value_labels["xyz_y"].configure(text=f"Y: {yy:.4f}")
        self.value_labels["xyz_z"].configure(text=f"Z: {z:.4f}")
        self.value_labels["lab_l"].configure(text=f"L: {l:.4f}")
        self.value_labels["lab_a"].configure(text=f"a: {a:.4f}")
        self.value_labels["lab_b"].configure(text=f"b: {bb:.4f}")

        xn, yn, zn = snapshot["white_point"]
        self.white_label.configure(text=f"Xn={xn:.3f}, Yn={yn:.3f}, Zn={zn:.3f}")
        matrix = snapshot["matrix"]
        text = "\n".join("  ".join(f"{value: .6f}" for value in row) for row in matrix)
        self.matrix_label.configure(text=text)

    def set_gradients(self, gradients):
        for key, colors in gradients.items():
            if key in self.sliders:
                self.sliders[key].set_gradient(colors)

    def run(self):
        self.root.mainloop()
