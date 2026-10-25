"""Tkinter 窗口入口。运行 python gui.py。"""

import json
import math
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from mechanics import (Force, load_case, reduce_system, format_result, fmt_vec,
                       add, scale, norm)

HERE = Path(__file__).resolve().parent


class App:
    def __init__(self, root):
        self.root = root
        self.rows = []
        self.result = None
        root.title("空间力系的简化与计算")
        root.geometry("1160x820")
        root.minsize(1020, 730)
        style = ttk.Style()
        style.configure(".", font=("Microsoft YaHei UI", 10))
        style.configure("Treeview", rowheight=27)
        shell = ttk.Frame(root, padding=16)
        shell.pack(fill="both", expand=True)

        head = ttk.Frame(shell)
        head.pack(fill="x")
        ttk.Label(head, text="空间力系的简化与计算",
                  font=("Microsoft YaHei UI", 17, "bold")).pack(side="left")
        for text, command in (("课堂算例", self.example), ("打开 JSON", self.open_case),
                              ("保存输入", self.save_case)):
            ttk.Button(head, text=text, command=command).pack(side="right", padx=4)
        ttk.Label(shell, text="长度 m · 力 N · 力矩 N·m；方向向量只需填写比例。").pack(
            anchor="w", pady=(5, 10))

        origin_bar = ttk.Frame(shell)
        origin_bar.pack(fill="x")
        ttk.Label(origin_bar, text="简化点 O：").pack(side="left")
        self.origin = [tk.StringVar(value="0") for _ in range(3)]
        for axis, value in zip("xyz", self.origin):
            ttk.Label(origin_bar, text=axis).pack(side="left", padx=(10, 4))
            ttk.Entry(origin_bar, textvariable=value, width=10).pack(side="left")
        ttk.Button(origin_bar, text="计算", command=self.calculate).pack(side="right")

        editor = ttk.LabelFrame(shell, text="输入 / 修改载荷", padding=10)
        editor.pack(fill="x", pady=10)
        self.kind = tk.StringVar(value="力")
        self.mode = tk.StringVar(value="分量")
        self.name = tk.StringVar(value="F1")
        self.magnitude = tk.StringVar(value="1")
        self.point = [tk.StringVar(value="0") for _ in range(3)]
        self.direction = [tk.StringVar(value="0") for _ in range(3)]
        ttk.Combobox(editor, textvariable=self.kind, values=("力", "力偶"),
                     state="readonly", width=6).grid(row=0, column=0, padx=4)
        ttk.Entry(editor, textvariable=self.name, width=10).grid(row=0, column=1, padx=4)
        ttk.Combobox(editor, textvariable=self.mode, values=("分量", "大小和方向"),
                     state="readonly", width=11).grid(row=0, column=2, padx=4)
        ttk.Label(editor, text="大小").grid(row=0, column=3)
        ttk.Entry(editor, textvariable=self.magnitude, width=12).grid(row=0, column=4)
        ttk.Label(editor, text="力偶直接填矩分量；作用点和大小不参与计算。").grid(
            row=0, column=5, columnspan=3, padx=8, sticky="w")
        ttk.Label(editor, text="作用点 x, y, z").grid(row=1, column=0, columnspan=2, pady=8)
        for j, value in enumerate(self.point):
            ttk.Entry(editor, textvariable=value, width=12).grid(row=1, column=j+2, padx=4)
        ttk.Label(editor, text="分量 / 方向 x, y, z").grid(row=2, column=0, columnspan=2)
        for j, value in enumerate(self.direction):
            ttk.Entry(editor, textvariable=value, width=12).grid(row=2, column=j+2, padx=4)
        for j, (text, cmd) in enumerate((("添加", self.add_row),
                                        ("更新选中项", self.update_row),
                                        ("删除选中项", self.remove_rows))):
            ttk.Button(editor, text=text, command=cmd).grid(row=2, column=j+5, padx=5)

        columns = ("name", "type", "point", "components")
        self.table = ttk.Treeview(shell, columns=columns, show="headings", height=5)
        for column, text, width in zip(columns, ("名称", "类型", "作用点 / m", "力 / 力偶矩分量"),
                                        (95, 65, 300, 450)):
            self.table.heading(column, text=text)
            self.table.column(column, width=width)
        self.table.pack(fill="x")
        self.table.bind("<<TreeviewSelect>>", self.select_row)

        tabs = ttk.Notebook(shell)
        tabs.pack(fill="both", expand=True, pady=(10, 0))
        result_frame = ttk.Frame(tabs)
        diagram_frame = ttk.Frame(tabs)
        tabs.add(result_frame, text="计算结果")
        tabs.add(diagram_frame, text="力系示意")
        self.output = tk.Text(result_frame, font=("Consolas", 11), wrap="word",
                              padx=12, pady=10)
        scroll = ttk.Scrollbar(result_frame, command=self.output.yview)
        self.output.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.output.pack(fill="both", expand=True)
        self.output.configure(state="disabled")
        self.canvas = tk.Canvas(diagram_frame, background="#fafafa", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda event: self.draw())
        self.status = tk.StringVar(value="")
        ttk.Label(shell, textvariable=self.status).pack(anchor="w", pady=(6, 0))
        self.example()

    def set_output(self, text):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", text)
        self.output.configure(state="disabled")

    def read_origin(self):
        from mechanics import vector
        return vector([v.get() for v in self.origin], "简化点")

    def read_editor(self):
        from mechanics import vector
        name = self.name.get().strip() or "F"
        values = vector([v.get() for v in self.direction], "分量或方向")
        if self.kind.get() == "力偶":
            return {"name": name, "couple": values}
        point = vector([v.get() for v in self.point], "作用点")
        if self.mode.get() == "大小和方向":
            force = Force.from_direction(point, self.magnitude.get(), values, name)
        else:
            force = Force(point, values, name)
        return {"name": name, "force": force}

    def refresh(self):
        self.table.delete(*self.table.get_children())
        for i, row in enumerate(self.rows):
            if "force" in row:
                f = row["force"]
                values = (f.name, "力", fmt_vec(f.point), fmt_vec(f.components))
            else:
                values = (row["name"], "力偶", "—", fmt_vec(row["couple"]))
            self.table.insert("", "end", iid=str(i), values=values)
        self.name.set(f"F{sum('force' in r for r in self.rows)+1}")
        self.calculate()

    def add_row(self):
        try:
            self.rows.append(self.read_editor())
            self.refresh()
        except ValueError as exc:
            messagebox.showerror("输入有误", str(exc))

    def update_row(self):
        selected = self.table.selection()
        if len(selected) != 1:
            messagebox.showinfo("选择载荷", "请选中一行后更新。")
            return
        try:
            row = self.read_editor()
            self.rows[int(selected[0])] = row
            self.refresh()
        except ValueError as exc:
            messagebox.showerror("输入有误", str(exc))

    def remove_rows(self):
        for i in sorted((int(x) for x in self.table.selection()), reverse=True):
            self.rows.pop(i)
        self.refresh()

    def select_row(self, event=None):
        selected = self.table.selection()
        if len(selected) != 1:
            return
        row = self.rows[int(selected[0])]
        self.name.set(row["name"])
        self.mode.set("分量")
        is_force = "force" in row
        self.kind.set("力" if is_force else "力偶")
        point = row["force"].point if is_force else (0, 0, 0)
        values = row["force"].components if is_force else row["couple"]
        for field, value in zip(self.point, point):
            field.set(f"{value:.12g}")
        for field, value in zip(self.direction, values):
            field.set(f"{value:.12g}")

    def load(self, data):
        # 所有数据验证通过后再替换窗口中的输入。
        forces, origin, couples = load_case(data)
        rows = [{"name": f.name, "force": f} for f in forces]
        rows += [{"name": f"M{i+1}", "couple": c} for i, c in enumerate(couples)]
        self.rows = rows
        for field, value in zip(self.origin, origin):
            field.set(str(value))
        self.refresh()

    def example(self):
        self.load(json.loads((HERE / "examples" / "cube.json").read_text(encoding="utf-8")))

    def open_case(self):
        path = filedialog.askopenfilename(filetypes=[("JSON 算例", "*.json")])
        if path:
            try:
                self.load(json.loads(Path(path).read_text(encoding="utf-8")))
            except (OSError, ValueError, TypeError) as exc:
                messagebox.showerror("无法打开算例", str(exc))

    def save_case(self):
        try:
            data = {"origin": self.read_origin(),
                    "forces": [{"name": r["force"].name, "point": r["force"].point,
                                "components": r["force"].components}
                               for r in self.rows if "force" in r],
                    "couples": [r["couple"] for r in self.rows if "couple" in r]}
            path = filedialog.asksaveasfilename(defaultextension=".json",
                                               filetypes=[("JSON 算例", "*.json")])
            if path:
                Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2,
                                                allow_nan=False)+"\n", encoding="utf-8")
        except (OSError, ValueError) as exc:
            messagebox.showerror("无法保存", str(exc))

    def calculate(self):
        try:
            forces = [r["force"] for r in self.rows if "force" in r]
            couples = [r["couple"] for r in self.rows if "couple" in r]
            self.result = reduce_system(forces, self.read_origin(), couples)
            self.set_output(format_result(self.result, forces))
            self.status.set(f"{len(forces)} 个力，{len(couples)} 个独立力偶")
            self.draw()
        except ValueError as exc:
            self.result = None
            self.set_output("输入有误：" + str(exc))
            self.canvas.delete("all")

    def draw(self):
        c = self.canvas
        c.delete("all")
        if self.result is None:
            return
        forces = [r["force"] for r in self.rows if "force" in r]
        origin = self.result["origin"]
        extent = max([1.0] + [norm(tuple(p-o for p, o in zip(f.point, origin)))
                              for f in forces])
        force_max = max([1e-30] + [norm(f.components) for f in forces])
        arrows = [(f.point, add(f.point, scale(f.components, extent*.45/force_max)), f.name)
                  for f in forces]
        points = [origin, (0, 0, 0)]
        for a, b, _ in arrows:
            points.extend((a, b))
        axis = None
        if self.result["central_point"] is not None:
            a, d = self.result["central_point"], self.result["axis_direction"]
            axis = (add(a, scale(d, -extent)), add(a, scale(d, extent)))
            points.extend(axis)
        def project(p):
            x, y, z = p
            return (y-.65*x, .45*x-z)
        projected = [project(p) for p in points]
        lo = [min(p[i] for p in projected) for i in range(2)]
        hi = [max(p[i] for p in projected) for i in range(2)]
        width, height = max(100, c.winfo_width()), max(100, c.winfo_height())
        zoom = min((width-100)/max(1, hi[0]-lo[0]),
                   (height-90)/max(1, hi[1]-lo[1]))
        def screen(p):
            x, y = project(p)
            return (width/2+(x-(lo[0]+hi[0])/2)*zoom,
                    height/2+(y-(lo[1]+hi[1])/2)*zoom)
        c.create_text(12, 12, anchor="nw", text="蓝色：各力　红色虚线：合力作用线 / 中央轴",
                      fill="#333333")
        c.create_text(12, height-12, anchor="sw",
                      text="固定斜投影；力箭头共用显示比例；力偶见计算结果。", fill="#666666")
        for i, label in enumerate("xyz"):
            tip = [0, 0, 0]
            tip[i] = extent*.45
            c.create_line(*screen((0, 0, 0)), *screen(tip), arrow="last", fill="#999999")
            c.create_text(*screen(tip), text=label, anchor="sw", fill="#555555")
        if axis:
            c.create_line(*screen(axis[0]), *screen(axis[1]), dash=(6, 4),
                          fill="#b4483f", width=2)
        ox, oy = screen(origin)
        c.create_oval(ox-4, oy-4, ox+4, oy+4, fill="#222222")
        c.create_text(ox+8, oy+8, text="O", anchor="nw")
        for a, b, label in arrows:
            c.create_line(*screen(a), *screen(b), arrow="last", width=2, fill="#235d8d")
            c.create_text(*screen(b), text=label, anchor="sw", fill="#235d8d")


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
