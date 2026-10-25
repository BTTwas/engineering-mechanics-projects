"""三维图与结果图片。箭头共用显示比例，力和力矩分别缩放。"""

import math
from pathlib import Path
import matplotlib
from matplotlib.figure import Figure
from matplotlib import font_manager, ticker
import numpy as np

from mechanics import KINDS, norm, unit

from theme import (INK, SECONDARY as MUTED, BLUE, MOMENT_BLUE,
                   FORCE_COLORS as COLORS, SOFT, BORDER)


def configure_fonts():
    choices = ("Microsoft YaHei", "Noto Sans CJK SC", "PingFang SC", "SimHei", "DejaVu Sans")
    available = {f.name for f in font_manager.fontManager.ttflist}
    matplotlib.rcParams["font.family"] = [next((x for x in choices if x in available), "DejaVu Sans")]
    matplotlib.rcParams["axes.unicode_minus"] = False
    matplotlib.rcParams["svg.fonttype"] = "path"


configure_fonts()


def compact(v):
    return "(" + ", ".join(f"{x:.5g}" if abs(x) > 1e-10 else "0" for x in v) + ")"


def _geometry_points(geometry):
    if not geometry or geometry.get("type") != "cube":
        return []
    side = float(geometry.get("side", 1))
    start = np.asarray(geometry.get("origin", [0, 0, 0]), dtype=float)
    if not math.isfinite(side) or side <= 0 or not np.isfinite(start).all() or start.shape != (3,):
        raise ValueError("立方体参考几何数据有误")
    return [start + np.array([x, y, z])*side
            for x in (0, 1) for y in (0, 1) for z in (0, 1)]


def _wireframe(ax, points):
    for i, p in enumerate(points):
        for j, q in enumerate(points):
            if j > i and sum(abs(p-q) > 1e-10) == 1:
                ax.plot(*np.array([p, q]).T, color="#b7c9e1", linewidth=1.0, alpha=.9)


def _base_axes(ax):
    ax.set_facecolor("white")
    ax.view_init(elev=23, azim=-53)
    ax.set_proj_type("ortho")
    ax.set_box_aspect((1, 1, 1))
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.set_pane_color((.974, .983, .997, .65))
        axis.line.set_color("#c6d3e5")
        axis._axinfo["grid"]["color"] = "#e4ebf5"
        axis._axinfo["grid"]["linewidth"] = .55
        axis.set_major_locator(ticker.MaxNLocator(3))
    ax.set_xlabel("x / m", fontsize=10, labelpad=0, color=MUTED)
    ax.set_ylabel("y / m", fontsize=10, labelpad=0, color=MUTED)
    ax.set_zlabel("z / m", fontsize=10, labelpad=0, color=MUTED)
    ax.tick_params(labelsize=9, colors=MUTED, pad=0)
    ax.mouse_init(rotate_btn=1, zoom_btn=3)


def _arrow(ax, start, value, factor, color, label):
    start, value = np.array(start), np.array(value)
    if norm(value) <= 1e-15:
        return start
    delta = value * factor
    ax.quiver(*start, *delta, color=color, linewidth=2.5,
              arrow_length_ratio=.19, normalize=False)
    tip = start + delta
    ax.text(*tip, " "+label, color=color, fontsize=12,
            bbox=dict(facecolor="white", edgecolor="none", pad=.3, alpha=.8))
    return tip


def _moment_loop(ax, point, moment, radius, label):
    direction = unit(moment)
    if direction is None:
        return []
    d = np.array(direction)
    reference = np.array([0, 0, 1] if abs(d[2]) < .85 else [0, 1, 0])
    u = np.cross(d, reference)
    u /= np.linalg.norm(u)
    v = np.cross(d, u)
    point = np.array(point)
    theta = np.linspace(.2, math.pi*1.7, 50)
    ring = [point + radius*(math.cos(t)*u+math.sin(t)*v) for t in theta]
    ax.plot(*np.array(ring).T, color=MOMENT_BLUE, linewidth=2.2)
    tip = ring[-1]
    tangent = -math.sin(theta[-1])*u+math.cos(theta[-1])*v
    ax.quiver(*tip, *(tangent*radius*.25), color=MOMENT_BLUE,
              linewidth=1.8, arrow_length_ratio=.65)
    ax.text(*(point + radius*1.4*u), " "+label, color=MOMENT_BLUE, fontsize=11)
    return ring


def draw_panels(figure, forces, result, couples=(), geometry=None, *, export=False):
    forces, couples = list(forces), list(couples)
    geometry_points = _geometry_points(geometry)
    origin = np.array(result["origin"])
    anchors = [origin, np.zeros(3)] + [np.array(f.point) for f in forces] + geometry_points
    scene = max(1.0, max(np.linalg.norm(p-origin) for p in anchors))
    fmax = max([1e-15]+[norm(f.components) for f in forces]+[result["resultant_magnitude"]])
    factor = scene*.72/fmax
    boxes = ([(.025, .445, .455, .425), (.52, .445, .455, .425)] if export
             else [(.005, .05, .48, .89), (.51, .05, .48, .89)])
    axes = [figure.add_axes(box, projection="3d") for box in boxes]
    for ax in axes:
        _base_axes(ax)
        _wireframe(ax, geometry_points)
        ax.scatter(*origin, color=INK, s=17, depthshade=False)
        ax.text(*origin, " O", fontsize=10, color=INK)
    panel_points = [anchors.copy(), anchors.copy()]
    for i, f in enumerate(forces):
        color = COLORS[i % len(COLORS)]
        axes[0].scatter(*f.point, s=10, color=color, depthshade=False)
        panel_points[0].append(_arrow(axes[0], f.point, f.components, factor, color, f.name or f"F{i+1}"))
    for i, c in enumerate(couples):
        panel_points[0] += _moment_loop(axes[0], origin, c, scene*.17, f"C{i+1}")
    kind = result["kind"]
    if kind in ("resultant", "wrench"):
        point = np.array(result["central_point"])
        d = np.array(result["axis_direction"])
        endpoints = [point - d*scene*.7, point+d*scene*.9]
        axes[1].plot(*np.array(endpoints).T, color=BLUE, linewidth=1.4,
                     linestyle=(0, (4, 4)), alpha=.7)
        axes[1].scatter(*point, s=18, color=BLUE, depthshade=False)
        axes[1].text(*point, " A", color=BLUE, fontsize=11)
        panel_points[1].extend(endpoints)
        panel_points[1].append(_arrow(axes[1], point, result["resultant"], factor, BLUE, "R"))
        if kind == "wrench":
            panel_points[1] += _moment_loop(axes[1], point, result["axial_couple"], scene*.2, "M∥")
    elif kind == "couple":
        panel_points[1] += _moment_loop(axes[1], origin, result["moment"], scene*.23, "M")
    else:
        axes[1].text2D(.5, .5, "R = 0   /   M = 0", ha="center", color=BLUE,
                       transform=axes[1].transAxes, fontsize=12)
    for ax, coordinates in zip(axes, panel_points):
        points = np.array(coordinates)
        low, high = points.min(axis=0), points.max(axis=0)
        center = (low+high)/2
        half = max(.55, max(high-low)*.60)
        ax.set_xlim(center[0]-half, center[0]+half)
        ax.set_ylim(center[1]-half, center[1]+half)
        ax.set_zlim(center[2]-half, center[2]+half)
    axes[0].set_title("原力系", loc="left", color=INK, fontsize=13, fontweight="medium", pad=3)
    axes[1].set_title("最终简化 · "+KINDS[kind], loc="left", color=INK, fontsize=13, fontweight="medium", pad=3)
    return axes


def preview_figure(forces, result, couples=(), geometry=None):
    figure = Figure(figsize=(9.5, 4.1), dpi=100, facecolor="white")
    draw_panels(figure, forces, result, couples, geometry)
    return figure


def result_figure(forces, result, couples=(), geometry=None, *, views=None):
    from matplotlib.patches import FancyBboxPatch
    figure = Figure(figsize=(12, 9), dpi=120, facecolor="white")
    figure.text(.055, .947, "空间力系的简化与计算", fontsize=23, color=INK, fontweight="bold")
    figure.text(.055, .909, f"简化点 O = {compact(result['origin'])} m", fontsize=11, color=MUTED)
    figure.text(.945, .947, KINDS[result["kind"]], ha="right", fontsize=16, color=BLUE)
    axes = draw_panels(figure, forces, result, couples, geometry, export=True)
    if views is not None:
        for ax, (elev, azim, roll) in zip(axes, views):
            ax.view_init(elev=elev, azim=azim, roll=roll)
    for left, key, title, units in ((.055, "resultant", "主矢  R", "N"),
                                    (.515, "moment", "主矩  M_O", "N·m")):
        figure.patches.append(FancyBboxPatch((left-.01, .266), .425, .153,
            boxstyle="round,pad=0.012,rounding_size=0.012", transform=figure.transFigure,
            facecolor=SOFT, edgecolor="none", zorder=-1))
        figure.text(left+.01, .387, title, color=MUTED, fontsize=11)
        figure.text(left+.01, .348, f"{result[key+'_magnitude']:.7g}  {units}",
                    color=INK, fontsize=22)
        figure.text(left+.01, .315, "分量  "+compact(result[key]), color=INK, fontsize=11)
        angles = result[key+"_angles_deg"]
        angle_text = "未定义（零向量）" if angles is None else compact(angles)+" °"
        figure.text(left+.01, .281, "方向角  "+angle_text, color=MUTED, fontsize=11)
    if result["central_point"] is not None:
        label = "合力作用线" if result["kind"] == "resultant" else "中央轴"
        lines = [
            f"{label}上的一点 A = {compact(result['central_point'])} m",
            f"作用线  r = A + t {compact(result['axis_direction'])}，t ∈ R",
        ]
        if result["kind"] == "wrench":
            lines.append(f"轴向力偶矩  {compact(result['axial_couple'])} N·m"
                         f"       螺距 h = {result['pitch']:.7g} m")
    elif result["kind"] == "couple":
        lines = ["最终为力偶，力偶矩是自由矢量，无唯一作用点或作用线。"]
    else:
        lines = ["主矢与主矩在给定容差内均为零，力系处于平衡。"]
    for i, text in enumerate(lines):
        figure.text(.055, .217-i*.037, text, color=INK, fontsize=11)
    figure.text(.055, .056, "方向角为与 x、y、z 正轴的夹角。箭头按显示比例绘制；坐标单位 m。",
                color=MUTED, fontsize=10)
    figure.text(.055, .031, "力与力矩分别使用显示比例，环形箭头表示力偶矩方向。",
                color=MUTED, fontsize=10)
    return figure


def export_result(path, forces, result, couples=(), geometry=None, *, views=None):
    figure = result_figure(forces, result, couples, geometry, views=views)
    path = Path(path)
    if path.suffix.lower() not in (".png", ".svg"):
        raise ValueError("请选择 PNG 或 SVG 格式")
    figure.savefig(path, dpi=260, facecolor="white")
    figure.clear()
