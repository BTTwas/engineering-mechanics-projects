"""空间力系的简化。长度用 m，力用 N，力矩用 N·m。"""

from dataclasses import dataclass
import math

Vector = tuple[float, float, float]


def vector(values, name="向量") -> Vector:
    try:
        if isinstance(values, (str, bytes, dict)) or len(values) != 3:
            raise ValueError
        if any(isinstance(x, bool) for x in values):
            raise ValueError
        result = tuple(float(x) for x in values)
    except (TypeError, ValueError, OverflowError):
        raise ValueError(f"{name}必须是三个有限实数") from None
    if not all(math.isfinite(x) for x in result):
        raise ValueError(f"{name}必须是三个有限实数")
    return result


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))

def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))

def scale(a, k):
    return tuple(x * k for x in a)

def dot(a, b):
    return math.fsum(x * y for x, y in zip(a, b))

def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])

def norm(a):
    return math.hypot(*a)

def unit(a):
    size = norm(a)
    return None if size == 0 else scale(a, 1 / size)

def sum_vectors(vectors):
    rows = list(vectors)
    return tuple(math.fsum(row[i] for row in rows) for i in range(3))


@dataclass(frozen=True)
class Force:
    point: Vector
    components: Vector
    name: str = ""

    def __post_init__(self):
        object.__setattr__(self, "point", vector(self.point, "作用点"))
        object.__setattr__(self, "components", vector(self.components, "力的分量"))

    @classmethod
    def from_direction(cls, point, magnitude, direction, name=""):
        if isinstance(magnitude, bool):
            raise ValueError("力的大小应为非负有限数")
        try:
            magnitude = float(magnitude)
        except (TypeError, ValueError, OverflowError):
            raise ValueError("力的大小应为非负有限数") from None
        if not math.isfinite(magnitude) or magnitude < 0:
            raise ValueError("力的大小应为非负有限数")
        direction = vector(direction, "方向向量")
        length = norm(direction)
        if length == 0:
            raise ValueError("方向向量不能为零")
        if not math.isfinite(length):
            raise ValueError("方向向量量级过大，请缩小方向分量")

        # 此方法为先归一化再乘大小，方向分量表示比例，不要求使用者先算单位向量，
        components = tuple(magnitude * (x / length) for x in direction)
        return cls(point, components, name)


KINDS = {
    "equilibrium": "平衡力系",
    "couple": "力偶",
    "resultant": "合力",
    "wrench": "力螺旋",
}


def reduce_system(forces, origin=(0, 0, 0), couples=(), *,
                  force_atol=1e-10, moment_atol=1e-10, rtol=1e-9):
    """central_point 用全局坐标；中央轴方向取主矢的单位向量。"""
    origin = vector(origin, "简化点")
    forces = list(forces)
    couples = [vector(c, "力偶矩") for c in couples]

    tolerances = (force_atol, moment_atol, rtol)
    if any(not math.isfinite(t) or t < 0 for t in tolerances):
        raise ValueError("容差应为非负有限数")
    try:
        moments = [cross(sub(f.point, origin), f.components) for f in forces]
        resultant = sum_vectors(f.components for f in forces)
        moment = sum_vectors(moments + couples)
        force_scale = math.fsum(norm(f.components) for f in forces)
        moment_scale = math.fsum(norm(m) for m in moments + couples)
        force_tol = force_atol + rtol * force_scale
        moment_tol = moment_atol + rtol * moment_scale
        if not all(math.isfinite(x) for x in
                   (*resultant, *moment, force_tol, moment_tol)):
            raise ValueError("数值范围过大，请调整单位或输入量级")
        f_size, m_size = norm(resultant), norm(moment)
        if not math.isfinite(f_size) or not math.isfinite(m_size):
            raise ValueError("数值范围过大，请调整单位或输入量级")

        result = {
            "origin": origin, "resultant": resultant, "moment": moment,
            "resultant_magnitude": f_size, "moment_magnitude": m_size,
            "resultant_direction": unit(resultant),
            "moment_direction": unit(moment),
            "resultant_angles_deg": angles(resultant),
            "moment_angles_deg": angles(moment),
            "force_moments": moments,
            "force_tolerance": force_tol, "moment_tolerance": moment_tol,
            "central_point": None, "axis_direction": None,
            "pitch": None, "axial_couple": None,
        }

        if f_size <= force_tol:
            result["kind"] = "equilibrium" if m_size <= moment_tol else "couple"
        else:
            direction = unit(resultant)
            # r0 = (R × M) / |R|²；用单位方向避免不必要的平方。
            offset = scale(cross(direction, moment), 1 / f_size)
            axial_scalar = dot(moment, direction)
            axial_couple = scale(direction, axial_scalar)
            result.update(
                central_point=add(origin, offset),
                axis_direction=direction,
                pitch=axial_scalar / f_size,
                axial_couple=axial_couple,
                kind="resultant" if abs(axial_scalar) <= moment_tol else "wrench",
            )
        # 检查中间运算溢出，避免把 inf 当成有效结果。
        for key in ("central_point", "axial_couple"):
            if result[key] is not None:
                vector(result[key], "计算结果")
        if result["pitch"] is not None and not math.isfinite(result["pitch"]):
            raise ValueError("数值范围过大，请调整单位或输入量级")
        return result
    except (OverflowError, ZeroDivisionError):
        raise ValueError("数值范围过大，请调整单位或输入量级") from None


def angles(a):
    direction = unit(a)
    if direction is None:
        return None
    return tuple(math.degrees(math.acos(max(-1, min(1, x)))) for x in direction)


def load_case(data):
    if not isinstance(data, dict):
        raise ValueError("算例应为 JSON 对象")
    for key in ("forces", "couples"):
        if not isinstance(data.get(key, []), list):
            raise ValueError(f"{key} 应为数组")
    forces = []
    for i, item in enumerate(data.get("forces", []), 1):
        if not isinstance(item, dict):
            raise ValueError(f"第 {i} 个力应为对象")
        name = str(item.get("name", f"F{i}"))
        try:
            point = item["point"]
            if "components" in item:
                if "magnitude" in item or "direction" in item:
                    raise ValueError("分量输入与大小/方向输入不能同时使用")
                forces.append(Force(point, item["components"], name))
            else:
                forces.append(Force.from_direction(
                    point, item["magnitude"], item["direction"], name))
        except KeyError as exc:
            raise ValueError(f"{name} 缺少字段 {exc.args[0]}") from None
    origin = vector(data.get("origin", [0, 0, 0]), "简化点")
    couples = [vector(x, "力偶矩") for x in data.get("couples", [])]
    return forces, origin, couples


def fmt(value):
    return f"{value:.8g}" if abs(value) >= 5e-12 else "0"

def fmt_vec(a):
    return "(" + ", ".join(fmt(x) for x in a) + ")"


def format_result(result, forces=()):
    lines = ["空间力系的简化与计算", "坐标单位 m；力单位 N；力矩单位 N·m",
             f"简化点 O = {fmt_vec(result['origin'])}", ""]
    for i, (force, moment) in enumerate(zip(forces, result["force_moments"]), 1):
        lines.append(f"{force.name or 'F'+str(i)}: F = {fmt_vec(force.components)}, "
                     f"M_O = {fmt_vec(moment)}")
    for prefix, key, size_key in (
        ("主矢 R", "resultant", "resultant_magnitude"),
        ("主矩 M_O", "moment", "moment_magnitude"),
    ):
        lines += ["", f"{prefix} = {fmt_vec(result[key])}",
                  f"大小 = {fmt(result[size_key])}",
                  "单位方向 = " + ("未定义（零向量）" if result[key+"_direction"] is None
                                    else fmt_vec(result[key+"_direction"])),
                  "与 x、y、z 正轴的夹角 / ° = " +
                  ("未定义" if result[key+"_angles_deg"] is None
                   else fmt_vec(result[key+"_angles_deg"]))]
    lines += ["", "最终简化结果：" + KINDS[result["kind"]]]
    if result["central_point"] is not None:
        label = "合力作用线" if result["kind"] == "resultant" else "中央轴"
        lines += [f"{label}上的一点 A = {fmt_vec(result['central_point'])}",
                  f"{label}：r = A + t {fmt_vec(result['axis_direction'])}，t ∈ R",
                  "轴上保留的力偶矩 = " + fmt_vec(result["axial_couple"]),
                  f"螺距 h = {fmt(result['pitch'])} m"]
    elif result["kind"] == "couple":
        lines += ["力偶矩为自由矢量，无唯一作用点或作用线。"]
    else:
        lines += ["主矢和主矩在给定容差内均为零。"]
    lines += ["", f"零值判据：力 {fmt(result['force_tolerance'])} N；"
              f"力矩 {fmt(result['moment_tolerance'])} N·m"]
    return "\n".join(lines)
