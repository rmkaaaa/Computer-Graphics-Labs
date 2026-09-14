import math

SRGB_PRIMARIES = {
    "R": (0.6400, 0.3300),
    "G": (0.3000, 0.6000),
    "B": (0.1500, 0.0600),
}

ILLUMINANTS = {
    "D65": (0.31270, 0.32900),
    "D50": (0.34567, 0.35850),
    "E": (1.0 / 3.0, 1.0 / 3.0),
}

_EPSILON = 216.0 / 24389.0
_KAPPA = 24389.0 / 27.0


def clamp(value, low, high):
    return max(low, min(high, value))


def round_tuple(values, digits=6):
    return tuple(round(v, digits) for v in values)


def rgb_to_hsv(r, g, b):
    r = clamp(r, 0, 255) / 255.0
    g = clamp(g, 0, 255) / 255.0
    b = clamp(b, 0, 255) / 255.0

    maximum = max(r, g, b)
    minimum = min(r, g, b)
    delta = maximum - minimum

    if delta == 0:
        h = 0.0
    elif maximum == r:
        h = 60.0 * (((g - b) / delta) % 6.0)
    elif maximum == g:
        h = 60.0 * (((b - r) / delta) + 2.0)
    else:
        h = 60.0 * (((r - g) / delta) + 4.0)

    s = 0.0 if maximum == 0 else delta / maximum
    v = maximum
    return round_tuple((h, s * 100.0, v * 100.0), 6)


def hsv_to_rgb(h, s, v):
    h = h % 360.0
    s = clamp(s, 0, 100) / 100.0
    v = clamp(v, 0, 100) / 100.0

    c = v * s
    x = c * (1.0 - abs((h / 60.0) % 2.0 - 1.0))
    m = v - c

    if h < 60:
        rp, gp, bp = c, x, 0.0
    elif h < 120:
        rp, gp, bp = x, c, 0.0
    elif h < 180:
        rp, gp, bp = 0.0, c, x
    elif h < 240:
        rp, gp, bp = 0.0, x, c
    elif h < 300:
        rp, gp, bp = x, 0.0, c
    else:
        rp, gp, bp = c, 0.0, x

    return round_tuple(((rp + m) * 255.0, (gp + m) * 255.0, (bp + m) * 255.0), 6)


def rgb_to_cmyk(r, g, b, algorithm="GCR", strength=100.0, ucr_threshold=55.0):
    r = clamp(r, 0, 255) / 255.0
    g = clamp(g, 0, 255) / 255.0
    b = clamp(b, 0, 255) / 255.0

    c0 = 1.0 - r
    m0 = 1.0 - g
    y0 = 1.0 - b
    gray = min(c0, m0, y0)
    amount = clamp(strength, 0, 100) / 100.0

    if algorithm.upper() == "UCR":
        threshold = clamp(ucr_threshold, 0, 99.999999) / 100.0
        if gray <= threshold:
            k = 0.0
        else:
            shadow_factor = (gray - threshold) / (1.0 - threshold)
            k = gray * amount * shadow_factor
    else:
        k = gray * amount

    k = clamp(k, 0.0, 1.0)

    if k >= 1.0 - 1e-12:
        return 0.0, 0.0, 0.0, 100.0

    denominator = 1.0 - k
    c = clamp((c0 - k) / denominator, 0.0, 1.0)
    m = clamp((m0 - k) / denominator, 0.0, 1.0)
    y = clamp((y0 - k) / denominator, 0.0, 1.0)

    return round_tuple((c * 100.0, m * 100.0, y * 100.0, k * 100.0), 6)


def cmyk_to_rgb(c, m, y, k):
    c = clamp(c, 0, 100) / 100.0
    m = clamp(m, 0, 100) / 100.0
    y = clamp(y, 0, 100) / 100.0
    k = clamp(k, 0, 100) / 100.0

    r = 255.0 * (1.0 - c) * (1.0 - k)
    g = 255.0 * (1.0 - m) * (1.0 - k)
    b = 255.0 * (1.0 - y) * (1.0 - k)

    return round_tuple((r, g, b), 6)


def mat_vec_mul(matrix, vector):
    return [
        matrix[0][0] * vector[0] + matrix[0][1] * vector[1] + matrix[0][2] * vector[2],
        matrix[1][0] * vector[0] + matrix[1][1] * vector[1] + matrix[1][2] * vector[2],
        matrix[2][0] * vector[0] + matrix[2][1] * vector[1] + matrix[2][2] * vector[2],
    ]


def inverse_3x3(matrix):
    a, b, c = matrix[0]
    d, e, f = matrix[1]
    g, h, i = matrix[2]

    determinant = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)

    if abs(determinant) < 1e-15:
        raise ValueError("Матрица вырождена")

    inv = 1.0 / determinant

    return [
        [(e * i - f * h) * inv, (c * h - b * i) * inv, (b * f - c * e) * inv],
        [(f * g - d * i) * inv, (a * i - c * g) * inv, (c * d - a * f) * inv],
        [(d * h - e * g) * inv, (b * g - a * h) * inv, (a * e - b * d) * inv],
    ]


def get_white_point_xyz(illuminant):
    x, y = ILLUMINANTS.get(illuminant, ILLUMINANTS["D65"])
    yn = 100.0
    xn = x / y * yn
    zn = (1.0 - x - y) / y * yn
    return round_tuple((xn, yn, zn), 6)


def get_rgb_xyz_matrices(illuminant):
    def primary_xyz(x, y):
        return [x / y, 1.0, (1.0 - x - y) / y]

    red = primary_xyz(*SRGB_PRIMARIES["R"])
    green = primary_xyz(*SRGB_PRIMARIES["G"])
    blue = primary_xyz(*SRGB_PRIMARIES["B"])

    primary_matrix = [
        [red[0], green[0], blue[0]],
        [red[1], green[1], blue[1]],
        [red[2], green[2], blue[2]],
    ]

    xn, yn, zn = get_white_point_xyz(illuminant)
    white = [xn / 100.0, yn / 100.0, zn / 100.0]

    scales = mat_vec_mul(inverse_3x3(primary_matrix), white)

    rgb_to_xyz_matrix = [
        [primary_matrix[row][col] * scales[col] for col in range(3)]
        for row in range(3)
    ]

    xyz_to_rgb_matrix = inverse_3x3(rgb_to_xyz_matrix)

    return rgb_to_xyz_matrix, xyz_to_rgb_matrix


def srgb_to_linear(value):
    value = clamp(value, 0, 255) / 255.0
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def linear_to_srgb(value):
    if value <= 0.0031308:
        return 12.92 * value
    return 1.055 * (max(value, 0.0) ** (1.0 / 2.4)) - 0.055


def rgb_to_xyz(r, g, b, illuminant="D65"):
    matrix, _ = get_rgb_xyz_matrices(illuminant)
    linear = [srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b)]
    xyz = mat_vec_mul(matrix, linear)
    return round_tuple((xyz[0] * 100.0, xyz[1] * 100.0, xyz[2] * 100.0), 6)


def fit_gamut(values, strategy):
    warning = any(value < -1e-8 or value > 1.0 + 1e-8 for value in values)

    if strategy.lower() == "scaling" and warning:
        low = min(0.0, min(values))
        high = max(1.0, max(values))
        if high - low < 1e-15:
            fitted = [0.0, 0.0, 0.0]
        else:
            fitted = [(value - low) / (high - low) for value in values]
    else:
        fitted = [clamp(value, 0.0, 1.0) for value in values]

    return fitted, warning


def xyz_to_rgb(x, y, z, illuminant="D65", gamut_strategy="Clipping"):
    _, matrix = get_rgb_xyz_matrices(illuminant)
    linear = mat_vec_mul(matrix, [x / 100.0, y / 100.0, z / 100.0])
    srgb = [linear_to_srgb(value) for value in linear]
    fitted, warning = fit_gamut(srgb, gamut_strategy)
    rgb = [clamp(value * 255.0, 0.0, 255.0) for value in fitted]
    return round_tuple(rgb, 6), warning


def lab_f(value):
    if value > _EPSILON:
        return value ** (1.0 / 3.0)
    return (_KAPPA * value + 16.0) / 116.0


def lab_f_inv(value):
    cube = value ** 3
    if cube > _EPSILON:
        return cube
    return (116.0 * value - 16.0) / _KAPPA


def xyz_to_lab(x, y, z, illuminant="D65"):
    xn, yn, zn = get_white_point_xyz(illuminant)
    fx = lab_f(x / xn)
    fy = lab_f(y / yn)
    fz = lab_f(z / zn)

    l = 116.0 * fy - 16.0
    a = 500.0 * (fx - fy)
    b = 200.0 * (fy - fz)

    return round_tuple((l, a, b), 6)


def lab_to_xyz(l, a, b, illuminant="D65"):
    xn, yn, zn = get_white_point_xyz(illuminant)

    fy = (l + 16.0) / 116.0
    fx = fy + a / 500.0
    fz = fy - b / 200.0

    x = xn * lab_f_inv(fx)
    y = yn * lab_f_inv(fy)
    z = zn * lab_f_inv(fz)

    return round_tuple((x, y, z), 6)


def rgb_to_hex(r, g, b):
    r = int(round(clamp(r, 0, 255)))
    g = int(round(clamp(g, 0, 255)))
    b = int(round(clamp(b, 0, 255)))
    return f"#{r:02X}{g:02X}{b:02X}"
