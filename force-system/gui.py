"""简洁桌面界面：载荷输入、结果图和可展开的运行细节。"""

import json
import math
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from plotting import preview_figure, export_result, compact, COLORS
except ImportError:
    raise SystemExit("请先运行：python -m pip install -r requirements.txt")

from mechanics import Force, KINDS, load_case, reduce_system, format_result, norm
from numbers_input import number

HERE = Path(__file__).resolve().parent
BG = "#f3f6f3"
WHITE = "#ffffff"
INK = "#233f39"
MUTED = "#82928a"
GREEN = "#357e69"
SOFT = "#eaf2eb"
BORDER = "#e1e9e2"
FONT = "Microsoft YaHei UI"


def label(parent, text="", size=10, color=INK, bold=False, **kwargs):
    return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=color,
                    font=(FONT, size, "bold" if bold else "normal"), **kwargs)


def button(parent, text, command, *, primary=False, small=False):
    bg, fg = (GREEN, WHITE) if primary else (WHITE, INK)
    result = tk.Button(parent, text=text, command=command, bg=bg, fg=fg,
                       activebackground="#2b6a58" if primary else SOFT,
                       activeforeground=WHITE if primary else INK,
                       font=(FONT, 9 if small else 10), relief="flat",
                       borderwidth=0, cursor="hand2", padx=12, pady=7,
                       highlightthickness=0, takefocus=True)
    return result


def field(parent, variable, width=8):
    box = tk.Frame(parent, bg="#f8faf8", highlightbackground=BORDER, highlightthickness=1)
    entry = tk.Entry(box, textvariable=variable, bg="#f8faf8", fg=INK,
                     insertbackground=GREEN, font=(FONT, 10), relief="flat", width=width)
    entry.pack(fill="both", expand=True, padx=9, pady=8)
    return box, entry


class LoadDialog(tk.Toplevel):
    def __init__(self, app, index=None, couple=False):
        super().__init__(app.root)
        self.app, self.index = app, index
        self.payload = None
        self.couple = couple
        self.title("修改载荷" if index is not None else ("添加力偶" if couple else "添加力"))
        self.configure(bg=WHITE)
        self.resizable(False, False)
        self.transient(app.root)
        self.grab_set()
        self.name = tk.StringVar(value=("C" if couple else "F")+str(len(app.items)+1))
        self.mode = tk.StringVar(value="大小与方向")
        self.magnitude = tk.StringVar(value="1")
        self.point = [tk.StringVar(value="0") for _ in range(3)]
        self.direction = [tk.StringVar(value=x) for x in ("0", "0", "1")]
        if index is not None:
            item = app.items[index]
            self.name.set(item["name"])
            self.couple = "couple" in item
            if self.couple:
                values = item["couple"]
            else:
                f = item["force"]
                for v, x in zip(self.point, f.point):
                    v.set(f"{x:.12g}")
                values = f.components
                self.mode.set("分量")
            for v, x in zip(self.direction, values):
                v.set(f"{x:.12g}")

        shell = tk.Frame(self, bg=WHITE, padx=28, pady=24)
        shell.pack(fill="both", expand=True)
        label(shell, "力偶矩" if self.couple else "作用力", 18, bold=True).pack(anchor="w")
        label(shell, "填写载荷后，结果会自动更新。", color=MUTED).pack(anchor="w", pady=(5, 20))
        label(shell, "名称", color=MUTED).pack(anchor="w")
        box, entry = field(shell, self.name)
        box.pack(fill="x", pady=(5, 15))
        entry.focus_set()
        if not self.couple:
            mode_bar = tk.Frame(shell, bg=WHITE)
            mode_bar.pack(fill="x", pady=(0, 15))
            for mode in ("大小与方向", "分量"):
                tk.Radiobutton(mode_bar, text=mode, value=mode, variable=self.mode,
                               command=self.update_mode, bg=WHITE, fg=INK,
                               activebackground=WHITE, selectcolor=SOFT,
                               font=(FONT, 10)).pack(side="left", padx=(0, 18))
            label(shell, "作用点 / m", color=MUTED).pack(anchor="w")
            self.triplet(shell, self.point)
            self.mag_frame = tk.Frame(shell, bg=WHITE)
            self.mag_frame.pack(fill="x", pady=(0, 15))
            label(self.mag_frame, "力的大小 / N", color=MUTED).pack(anchor="w")
            box, _ = field(self.mag_frame, self.magnitude)
            box.pack(fill="x", pady=(5, 0))
        self.vector_title = label(shell, "", color=MUTED)
        self.vector_title.pack(anchor="w")
        self.triplet(shell, self.direction)
        self.hint = label(shell, "支持 √2、sqrt(2)、1/6；方向向量不必归一化。",
                          size=9, color=MUTED)
        self.hint.pack(anchor="w", pady=(0, 8))
        self.error = label(shell, "", size=9, color="#b26d58", wraplength=390, justify="left")
        self.error.pack(anchor="w", pady=(0, 12))
        actions = tk.Frame(shell, bg=WHITE)
        actions.pack(fill="x")
        button(actions, "保存载荷", self.save, primary=True).pack(side="right")
        button(actions, "取消", self.destroy).pack(side="right", padx=8)
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Return>", lambda e: self.save())
        self.update_mode()
        self.update_idletasks()
        self.geometry(f"470x{self.winfo_reqheight()}+{app.root.winfo_rootx()+90}+{app.root.winfo_rooty()+80}")

    def triplet(self, parent, variables):
        row = tk.Frame(parent, bg=WHITE)
        row.pack(fill="x", pady=(5, 16))
        for i, (axis, variable) in enumerate(zip("xyz", variables)):
            group = tk.Frame(row, bg=WHITE)
            group.pack(side="left", expand=True, fill="x", padx=(0, 8 if i < 2 else 0))
            label(group, axis, size=9, color=MUTED).pack(anchor="w")
            box, _ = field(group, variable, width=8)
            box.pack(fill="x", pady=(3, 0))

    def update_mode(self):
        if self.couple:
            self.vector_title.config(text="力偶矩分量 / N·m")
        else:
            self.vector_title.config(text="方向向量" if self.mode.get() == "大小与方向" else "力的分量 / N")
            # 保持布局稳定，分量模式下仅禁用大小框。
            for widget in self.mag_frame.winfo_children():
                if isinstance(widget, tk.Frame):
                    for child in widget.winfo_children():
                        child.configure(state="normal" if self.mode.get() == "大小与方向" else "disabled")

    def save(self):
        try:
            name = self.name.get().strip() or ("C" if self.couple else "F")
            values = tuple(number(v.get()) for v in self.direction)
            if self.couple:
                self.payload = {"name": name, "couple": values}
            else:
                point = tuple(number(v.get()) for v in self.point)
                f = (Force.from_direction(point, number(self.magnitude.get()), values, name)
                     if self.mode.get() == "大小与方向" else Force(point, values, name))
                self.payload = {"name": name, "force": f}
            self.app.apply_load(self.payload, self.index)
            self.destroy()
        except ValueError as exc:
            self.error.config(text=str(exc))


class App:
    def __init__(self, root):
        self.root = root
        self.items, self.result, self.geometry_data = [], None, None
        self.snapshot = None
        self.figure, self.figure_canvas = None, None
        self.drawer_open = False
        self.origin = [tk.StringVar(value="0") for _ in range(3)]
        root.title("力系计算 · 工程力学")
        root.geometry("1380x900")
        root.minsize(1160, 790)
        root.configure(bg=BG)
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("Vertical.TScrollbar", background=BORDER, troughcolor=WHITE,
                        bordercolor=WHITE, arrowcolor=MUTED, width=9)

        header = tk.Frame(root, bg=WHITE, padx=26, pady=17)
        header.pack(fill="x")
        mark = tk.Label(header, text="R", bg=SOFT, fg=GREEN, font=("Georgia", 25, "italic"),
                        padx=15, pady=2)
        mark.pack(side="left", padx=(0, 14))
        heading = tk.Frame(header, bg=WHITE)
        heading.pack(side="left")
        label(heading, "力系计算", 20, bold=True).pack(anchor="w")
        label(heading, "空间力系的简化与计算", 9, MUTED).pack(anchor="w", pady=(2, 0))
        self.details_button = button(header, "运行细节  ›", self.toggle_details)
        self.details_button.pack(side="right", padx=(12, 0))
        for text, command in (("保存输入", self.save_case), ("打开算例", self.open_case),
                              ("课堂算例", self.example)):
            button(header, text, command, small=True).pack(side="right", padx=3)
        self.body = tk.Frame(root, bg=BG, padx=22, pady=22)
        self.body.pack(fill="both", expand=True)
        self.body.columnconfigure(1, weight=1, minsize=610)
        self.body.rowconfigure(0, weight=1)

        sidebar = tk.Frame(self.body, bg=WHITE, width=300, highlightbackground=BORDER,
                           highlightthickness=1)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        sidebar.grid_propagate(False)
        inside = tk.Frame(sidebar, bg=WHITE, padx=20, pady=20)
        inside.pack(fill="both", expand=True)
        label(inside, "载荷输入", 15, bold=True).pack(anchor="w")
        label(inside, "长度 m · 力 N · 力矩 N·m", 9, MUTED).pack(anchor="w", pady=(5, 21))
        line = tk.Frame(inside, bg=WHITE)
        line.pack(fill="x", pady=(0, 10))
        self.count = label(line, "作用力", 10, MUTED)
        self.count.pack(side="left")
        menu_button = button(line, "+ 添加", self.add_menu, small=True)
        menu_button.pack(side="right")
        self.add_button = menu_button
        list_area = tk.Frame(inside, bg=WHITE)
        list_area.pack(fill="both", expand=True)
        self.load_canvas = tk.Canvas(list_area, bg=WHITE, highlightthickness=0)
        scroll = ttk.Scrollbar(list_area, orient="vertical", command=self.load_canvas.yview)
        self.load_canvas.configure(yscrollcommand=scroll.set)
        self.load_canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.load_list = tk.Frame(self.load_canvas, bg=WHITE)
        self.list_window = self.load_canvas.create_window((0, 0), window=self.load_list, anchor="nw")
        self.load_list.bind("<Configure>", lambda e: self.load_canvas.configure(
            scrollregion=self.load_canvas.bbox("all")))
        self.load_canvas.bind("<Configure>", lambda e: self.load_canvas.itemconfigure(
            self.list_window, width=e.width))
        self.load_canvas.bind("<MouseWheel>", self.scroll_loads)

        tk.Frame(inside, bg=BORDER, height=1).pack(fill="x", pady=(16, 17))
        label(inside, "简化点 O", 11, bold=True).pack(anchor="w")
        origin_row = tk.Frame(inside, bg=WHITE)
        origin_row.pack(fill="x", pady=(9, 17))
        for i, (axis, variable) in enumerate(zip("xyz", self.origin)):
            group = tk.Frame(origin_row, bg=WHITE)
            group.pack(side="left", expand=True, fill="x", padx=(0, 6 if i < 2 else 0))
            label(group, axis, 9, MUTED).pack(anchor="w")
            box, entry = field(group, variable, width=5)
            box.pack(fill="x", pady=(3, 0))
            entry.bind("<Return>", lambda e: self.calculate())
            variable.trace_add("write", self.mark_dirty)
        button(inside, "计算并生成图像", self.calculate, primary=True).pack(fill="x", ipady=4)
        self.status = label(inside, "", 9, MUTED, wraplength=250, justify="left")
        self.status.pack(anchor="w", pady=(12, 0))

        self.main = tk.Frame(self.body, bg=BG)
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.columnconfigure(0, weight=1)
        self.main.rowconfigure(2, weight=1)
        top = tk.Frame(self.main, bg=BG)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        title = tk.Frame(top, bg=BG)
        title.pack(side="left")
        label(title, "计算结果", 18, bold=True).pack(anchor="w")
        self.summary_note = label(title, "给定简化点处的主矢与主矩", 9, MUTED)
        self.summary_note.pack(anchor="w", pady=(4, 0))
        self.export_button = button(top, "导出图片  ↗", self.export_image)
        self.export_button.pack(side="right", pady=4)

        metric_row = tk.Frame(self.main, bg=BG)
        metric_row.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        metric_row.columnconfigure((0, 1), weight=1)
        self.metrics = {}
        for i, (key, title_text, units) in enumerate((("resultant", "主矢 R", "N"),
                                                     ("moment", "主矩 M_O", "N·m"))):
            card = tk.Frame(metric_row, bg=WHITE, padx=18, pady=14,
                            highlightbackground=BORDER, highlightthickness=1)
            card.grid(row=0, column=i, sticky="nsew", padx=(0, 7) if i == 0 else (7, 0))
            label(card, title_text, 10, MUTED).pack(anchor="w")
            value = label(card, "—", 24, bold=True)
            value.pack(anchor="w", pady=(5, 3))
            components = label(card, "", 10)
            components.pack(anchor="w")
            angle = label(card, "", 9, MUTED)
            angle.pack(anchor="w", pady=(5, 0))
            self.metrics[key] = (value, components, angle, units)

        chart_card = tk.Frame(self.main, bg=WHITE, padx=14, pady=12,
                              highlightbackground=BORDER, highlightthickness=1)
        chart_card.grid(row=2, column=0, sticky="nsew", pady=(0, 15))
        chart_card.rowconfigure(1, weight=1)
        chart_card.columnconfigure(0, weight=1)
        chart_top = tk.Frame(chart_card, bg=WHITE)
        chart_top.grid(row=0, column=0, sticky="ew")
        label(chart_top, "力系与简化结果", 11, bold=True).pack(side="left")
        button(chart_top, "重置视角", self.reset_view, small=True).pack(side="right")
        self.plot_host = tk.Frame(chart_card, bg=WHITE)
        self.plot_host.grid(row=1, column=0, sticky="nsew")
        label(chart_card, "拖动旋转查看 · 环形箭头表示力偶矩 · 箭头按显示比例绘制",
              8, MUTED).grid(row=2, column=0, sticky="w", pady=(3, 0))
        final = tk.Frame(self.main, bg=SOFT, padx=19, pady=16)
        final.grid(row=3, column=0, sticky="ew")
        self.kind_label = label(final, "最终简化", 14, GREEN, True)
        self.kind_label.pack(anchor="w")
        self.axis_label = label(final, "", 10, wraplength=700, justify="left")
        self.axis_label.pack(anchor="w", pady=(7, 0))
        self.couple_label = label(final, "", 10, wraplength=700, justify="left", color=GREEN)
        self.couple_label.pack(anchor="w", pady=(5, 0))

        self.drawer = tk.Frame(self.body, bg="#edf2ed", width=310, padx=18, pady=20,
                               highlightbackground=BORDER, highlightthickness=1)
        self.drawer.grid_propagate(False)
        label(self.drawer, "运行细节", 15, bold=True).pack(anchor="w")
        label(self.drawer, "输入 → 分解 → 求和 → 简化", 9, MUTED).pack(anchor="w", pady=(6, 15))
        self.log = tk.Text(self.drawer, bg="#edf2ed", fg="#526b60", relief="flat",
                           font=(FONT, 9), wrap="word", padx=0, pady=0, spacing3=5)
        self.log.pack(fill="both", expand=True)
        self.log.configure(state="disabled")
        self.example()

    def scroll_loads(self, event):
        self.load_canvas.yview_scroll(-int(event.delta/120), "units")
        return "break"

    def add_menu(self):
        menu = tk.Menu(self.root, tearoff=0, font=(FONT, 10), bg=WHITE, fg=INK)
        menu.add_command(label="添加作用力", command=lambda: LoadDialog(self))
        menu.add_command(label="添加独立力偶", command=lambda: LoadDialog(self, couple=True))
        menu.tk_popup(self.add_button.winfo_rootx(), self.add_button.winfo_rooty()+35)

    def apply_load(self, row, index=None):
        if index is None:
            self.items.append(row)
        else:
            self.items[index] = row
        self.render_loads()
        self.calculate()

    def remove_load(self, index):
        self.items.pop(index)
        self.render_loads()
        self.calculate()

    def render_loads(self):
        for widget in self.load_list.winfo_children():
            widget.destroy()
        n = sum("force" in row for row in self.items)
        self.count.config(text=f"{n} 个力 · {len(self.items)-n} 个力偶")
        if not self.items:
            label(self.load_list, "还没有载荷，点击“添加”开始。", 9, MUTED,
                  wraplength=230).pack(anchor="w", pady=20)
        for i, row in enumerate(self.items):
            card = tk.Frame(self.load_list, bg="#f6f9f6", padx=11, pady=10)
            card.pack(fill="x", pady=(0, 8))
            head = tk.Frame(card, bg="#f6f9f6")
            head.pack(fill="x")
            color = COLORS[i % len(COLORS)] if "force" in row else "#bd8267"
            label(head, "●", 8, color).pack(side="left", padx=(0, 6))
            name = label(head, row["name"], 11, bold=True)
            name.pack(side="left")
            remove = button(head, "×", lambda j=i: self.remove_load(j), small=True)
            remove.configure(bg="#f6f9f6", padx=5, pady=0, fg=MUTED)
            remove.pack(side="right")
            if "force" in row:
                f = row["force"]
                label(head, f"{norm(f.components):.5g} N", 9, MUTED).pack(side="right", padx=4)
                label(card, "作用点  "+compact(f.point), 9, MUTED).pack(anchor="w", pady=(6, 2))
                label(card, "分量     "+compact(f.components), 9).pack(anchor="w")
            else:
                label(card, "力偶矩  "+compact(row["couple"])+" N·m", 9, MUTED).pack(anchor="w", pady=(7, 0))
            # 点击卡片编辑；删除按钮保留自身的点击行为。
            def bind_edit(widget, j=i):
                if widget is remove:
                    return
                widget.bind("<Button-1>", lambda e, k=j: LoadDialog(self, k))
                widget.bind("<MouseWheel>", self.scroll_loads)
                if isinstance(widget, tk.Label):
                    widget.configure(cursor="hand2")
                for child in widget.winfo_children():
                    bind_edit(child, j)
            bind_edit(card)

    def mark_dirty(self, *args):
        if self.result is None:
            return
        self.snapshot = None
        self.export_button.configure(state="disabled")
        self.status.configure(text="简化点已修改，点击下方按钮更新结果。", fg="#a27d4d")
        self.summary_note.configure(text="输入已修改 · 当前显示上一次计算结果")

    def get_inputs(self):
        forces = [r["force"] for r in self.items if "force" in r]
        couples = [r["couple"] for r in self.items if "couple" in r]
        origin = tuple(number(v.get()) for v in self.origin)
        return forces, origin, couples

    def calculate(self):
        try:
            forces, origin, couples = self.get_inputs()
            result = reduce_system(forces, origin, couples)
            figure = preview_figure(forces, result, couples, self.geometry_data)
            # 完成计算及绘图后再替换旧结果，避免半成品覆盖。
            self.result = result
            self.snapshot = (forces, couples, self.geometry_data)
            self.show_figure(figure)
            for key, (value, components, angle, units) in self.metrics.items():
                value.config(text=f"{result[key+'_magnitude']:.6g} {units}")
                components.config(text="分量  "+compact(result[key]))
                angles = result[key+"_angles_deg"]
                angle.config(text="方向角  "+("未定义" if angles is None else compact(angles)+"°"))
            kind = result["kind"]
            self.kind_label.config(text="最终简化 · "+KINDS[kind])
            if result["central_point"] is not None:
                text = ("中央轴" if kind == "wrench" else "合力作用线")
                self.axis_label.config(text=f"{text}：A = {compact(result['central_point'])} m\n"
                    f"r = A + t {compact(result['axis_direction'])}")
                self.couple_label.config(text=(f"轴向力偶矩 {compact(result['axial_couple'])} N·m"
                    f"    h = {result['pitch']:.6g} m" if kind == "wrench" else "沿上述作用线作用的单一合力"))
            else:
                self.axis_label.config(text="力偶矩是自由矢量，无唯一作用线。" if kind == "couple"
                                       else "主矢与主矩在给定容差内均为零。")
                self.couple_label.config(text="")
            self.summary_note.config(text="给定简化点处的主矢与主矩 · O = "+compact(origin))
            self.status.config(text="已完成计算，结果可导出为图片。", fg=GREEN)
            self.export_button.configure(state="normal")
            log = "01  读取输入\n"+f"{len(forces)} 个力，{len(couples)} 个力偶\nO = {compact(origin)}\n\n"
            log += "02  计算与简化\n\n"+format_result(result, forces)
            self.log.config(state="normal")
            self.log.delete("1.0", "end")
            self.log.insert("1.0", log)
            self.log.config(state="disabled")
            return True
        except (ValueError, TypeError, OverflowError) as exc:
            self.snapshot = None
            self.export_button.configure(state="disabled")
            self.status.config(text=str(exc), fg="#b26d58")
            self.summary_note.config(text="输入有误 · 当前显示上一次有效结果")
            return False

    def show_figure(self, figure):
        if self.figure_canvas is not None:
            self.figure_canvas.get_tk_widget().destroy()
        if self.figure is not None:
            self.figure.clear()
        self.figure = figure
        self.figure_canvas = FigureCanvasTkAgg(figure, master=self.plot_host)
        self.figure_canvas.get_tk_widget().configure(highlightthickness=0, borderwidth=0)
        self.figure_canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figure_canvas.draw_idle()

    def reset_view(self):
        if self.figure:
            for axis in self.figure.axes:
                axis.view_init(elev=23, azim=-53)
            self.figure_canvas.draw_idle()

    def toggle_details(self):
        self.drawer_open = not self.drawer_open
        if self.drawer_open:
            self.drawer.grid(row=0, column=2, sticky="nsew", padx=(18, 0))
            self.root.geometry(f"{min(1650,self.root.winfo_screenwidth()-50)}x900")
        else:
            self.drawer.grid_remove()
            self.root.geometry("1380x900")
        self.details_button.config(text="收起细节  ‹" if self.drawer_open else "运行细节  ›")

    def load(self, data):
        forces, origin, couples = load_case(data)
        geometry = data.get("geometry")
        from plotting import _geometry_points
        _geometry_points(geometry)
        self.items = [{"name": f.name, "force": f} for f in forces]
        self.items += [{"name": f"C{i+1}", "couple": c} for i, c in enumerate(couples)]
        self.geometry_data = geometry
        for variable, value in zip(self.origin, origin):
            variable.set(f"{value:.12g}")
        self.render_loads()
        self.calculate()

    def example(self):
        self.load(json.loads((HERE/"examples"/"cube.json").read_text(encoding="utf-8")))

    def open_case(self):
        path = filedialog.askopenfilename(filetypes=[("JSON 算例", "*.json")])
        if path:
            try:
                self.load(json.loads(Path(path).read_text(encoding="utf-8")))
            except (OSError, ValueError, TypeError, AttributeError) as exc:
                messagebox.showerror("无法打开算例", str(exc), parent=self.root)

    def save_case(self):
        try:
            forces, origin, couples = self.get_inputs()
            data = {"origin": origin, "forces": [
                {"name": f.name, "point": f.point, "components": f.components} for f in forces],
                "couples": couples}
            if self.geometry_data:
                data["geometry"] = self.geometry_data
            path = filedialog.asksaveasfilename(defaultextension=".json",
                                                filetypes=[("JSON 算例", "*.json")])
            if path:
                Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2,
                                                allow_nan=False)+"\n", encoding="utf-8")
        except (OSError, ValueError) as exc:
            messagebox.showerror("无法保存", str(exc), parent=self.root)

    def export_image(self):
        if self.snapshot is None:
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", initialfile="力系计算结果.png",
                    filetypes=[("高清 PNG 图片", "*.png"), ("矢量 SVG 图片", "*.svg")])
        if path:
            try:
                forces, couples, geometry = self.snapshot
                export_result(path, forces, self.result, couples, geometry)
                self.status.config(text="结果图片已保存。", fg=GREEN)
            except (OSError, ValueError) as exc:
                messagebox.showerror("无法导出图片", str(exc), parent=self.root)


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
