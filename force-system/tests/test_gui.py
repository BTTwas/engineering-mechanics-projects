"""检查载荷编辑和输入变更后的计算状态。"""

import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

try:
    import tkinter as tk
    from gui import App, LoadDialog, next_load_name
except ImportError:
    tk = None


@unittest.skipIf(tk is None, "未安装窗口依赖")
class LoadModeTests(unittest.TestCase):
    def setUp(self):
        self.interpreter = tk.Tcl()
        self.dialog = SimpleNamespace(
            couple=False, input_mode="大小与方向",
            mode=tk.StringVar(self.interpreter, "大小与方向"),
            magnitude=tk.StringVar(self.interpreter, "10"),
            direction=[tk.StringVar(self.interpreter, x) for x in ("3", "4", "0")],
            vector_title=Mock(), mag_frame=Mock(), error=Mock(),
        )
        self.dialog.mag_frame.winfo_children.return_value = []

    def components(self):
        from mechanics import Force
        from numbers_input import number
        values = tuple(number(v.get()) for v in self.dialog.direction)
        if self.dialog.mode.get() == "分量":
            return Force((0, 0, 0), values).components
        return Force.from_direction(
            (0, 0, 0), number(self.dialog.magnitude.get()), values).components

    def test_switch_modes_keeps_the_same_force(self):
        before = self.components()
        for mode in ("分量", "大小与方向", "分量", "大小与方向"):
            self.dialog.mode.set(mode)
            LoadDialog.update_mode(self.dialog)
            for old, new in zip(before, self.components()):
                self.assertAlmostEqual(old, new, places=12)

    def test_zero_force_can_switch_back(self):
        self.dialog.input_mode = "分量"
        self.dialog.mode.set("大小与方向")
        for variable in self.dialog.direction:
            variable.set("0")
        LoadDialog.update_mode(self.dialog)
        self.assertEqual(self.components(), (0, 0, 0))

    def test_invalid_input_keeps_previous_mode_and_values(self):
        self.dialog.magnitude.set("1/0")
        self.dialog.mode.set("分量")
        LoadDialog.update_mode(self.dialog)
        self.assertEqual(self.dialog.mode.get(), "大小与方向")
        self.assertEqual([v.get() for v in self.dialog.direction], ["3", "4", "0"])
        self.assertTrue(self.dialog.error.config.called)


@unittest.skipIf(tk is None, "未安装窗口依赖")
class InputTests(unittest.TestCase):
    def make_app(self):
        from mechanics import reduce_system
        interpreter = tk.Tcl()
        app = SimpleNamespace(
            items=[], geometry_data=None, root=None,
            origin=[tk.StringVar(interpreter, "0") for _ in range(3)],
            render_loads=Mock(),
        )
        app.get_inputs = lambda: App.get_inputs(app)
        app.load = lambda data: App.load(app, data)
        def calculate():
            app.result = reduce_system(*app.get_inputs())
            return True
        app.calculate = calculate
        return app

    def test_couple_names_survive_json_save_and_open(self):
        from mechanics import Force
        app = self.make_app()
        app.items = [
            {"name": "F1", "force": Force((1, 0, 0), (0, 2, 0), "F1")},
            {"name": "底座力偶", "couple": (1, -2, 3)},
            {"name": "另一力偶", "couple": (1.0000000000004, 1e-15, 0)},
        ]
        app.calculate()
        before, result = list(app.items), app.result
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "case.json"
            with patch("gui.filedialog.asksaveasfilename", return_value=str(path)):
                App.save_case(app)
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved["couples"][0],
                             {"name": "底座力偶", "moment": [1, -2, 3]})
            app.items = []
            app.result = None
            with patch("gui.filedialog.askopenfilename", return_value=str(path)):
                App.open_case(app)
        self.assertEqual(app.items, before)
        self.assertEqual(app.result, result)

    def test_legacy_and_mixed_couple_names(self):
        app = self.make_app()
        cases = [
            ([[1, -2, 3]], ["C1"]),
            ([{"name": "底座力偶", "moment": [1, -2, 3]},
              [0, 0, 2], {"moment": [0, 1, 0]}], ["底座力偶", "C2", "C3"]),
        ]
        for couples, names in cases:
            with self.subTest(couples=couples):
                app.load({"couples": couples})
                self.assertEqual([row["name"] for row in app.items], names)
                self.assertEqual(app.items[0]["couple"], (1, -2, 3))

    def test_invalid_case_does_not_replace_current_inputs(self):
        app = SimpleNamespace(items=[{"name": "F1"}], snapshot=object())
        before = list(app.items)
        with self.assertRaises(ValueError):
            App.load(app, {"forces": [
                {"point": [1e308, 0, 0], "components": [0, 1e308, 0]}]})
        self.assertEqual(app.items, before)
        self.assertIsNotNone(app.snapshot)

    def test_scrolling_on_each_platform(self):
        cases = [
            ("aqua", {"delta": 1}, -1),
            ("aqua", {"delta": -2}, 2),
            ("win32", {"delta": 120}, -1),
            ("win32", {"delta": -30}, 1),
            ("x11", {"num": 4}, -1),
            ("x11", {"num": 5}, 1),
        ]
        for system, event, steps in cases:
            with self.subTest(system=system, event=event):
                app = SimpleNamespace(window_system=system, load_canvas=Mock())
                self.assertEqual(App.scroll_loads(app, SimpleNamespace(**event)), "break")
                app.load_canvas.yview_scroll.assert_called_once_with(steps, "units")


@unittest.skipIf(tk is None, "未安装窗口依赖")
class GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
        except tk.TclError as exc:
            raise unittest.SkipTest(str(exc))
        cls.root.withdraw()
        cls.app = App(cls.root)
        cls.root.update_idletasks()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        self.app.example()

    def test_edit_input_mode_keeps_force_magnitude(self):
        before = self.app.result["resultant"]
        dialog = LoadDialog(self.app, 1)
        dialog.withdraw()
        dialog.mode.set("大小与方向")
        dialog.update_mode()
        dialog.save()
        for old, new in zip(before, self.app.result["resultant"]):
            self.assertAlmostEqual(old, new, places=10)

    def test_names_do_not_repeat_after_removal(self):
        items = [{"name": "F1"}, {"name": "F3"}, {"name": "C1"}]
        self.assertEqual(next_load_name(items), "F2")
        self.assertEqual(next_load_name(items, couple=True), "C2")

    def test_renaming_force_keeps_original_values(self):
        from mechanics import norm
        from numbers_input import number
        cases = [
            {"origin": [1, 0, 0], "forces": [
                {"point": [1.0000000000004, 0, 0], "components": [0, 1e12, 0]},
                {"point": [1, 0, 0], "components": [0, -1e12, 0]}]},
            {"forces": [{"point": [0, 0, 0],
                         "components": [1.0000000000004, -1.2345678901234567, 1e-15]}]},
        ]
        for case in cases:
            with self.subTest(case=case):
                self.app.load(case)
                force = self.app.items[0]["force"]
                before = self.app.result
                dialog = LoadDialog(self.app, 0)
                dialog.withdraw()
                self.addCleanup(lambda d=dialog: d.destroy() if d.winfo_exists() else None)
                self.assertEqual(number(dialog.magnitude.get()), norm(force.components))
                dialog.name.set("重命名的力")
                dialog.save()
                saved = self.app.items[0]["force"]
                self.assertEqual(saved.name, "重命名的力")
                self.assertEqual(saved.point, force.point)
                self.assertEqual(saved.components, force.components)
                self.assertEqual(self.app.result, before)

    def test_renaming_couple_keeps_original_values(self):
        couple = (1.0000000000004, -1.2345678901234567, 1e-15)
        self.app.load({"couples": [couple]})
        before = self.app.result
        dialog = LoadDialog(self.app, 0)
        dialog.withdraw()
        self.addCleanup(lambda: dialog.destroy() if dialog.winfo_exists() else None)
        dialog.name.set("重命名的力偶")
        dialog.save()
        self.assertEqual(self.app.items[0], {"name": "重命名的力偶", "couple": couple})
        self.assertEqual(self.app.result, before)

    def test_cancel_edit_keeps_inputs_and_result(self):
        before = list(self.app.items)
        result = self.app.result
        dialog = LoadDialog(self.app, 0)
        dialog.withdraw()
        dialog.name.set("临时名称")
        dialog.point[0].set("123")
        dialog.direction[1].set("456")
        dialog.destroy()
        self.assertEqual(self.app.items, before)
        self.assertIs(self.app.result, result)

    def test_invalid_origin_disables_export_until_recalculated(self):
        self.app.origin[0].set("sqrt(-1)")
        self.assertIsNone(self.app.snapshot)
        self.assertFalse(self.app.calculate())
        self.assertEqual(str(self.app.export_button.cget("state")), "disabled")
        self.app.origin[0].set("1/2")
        self.assertTrue(self.app.calculate())
        self.assertEqual(str(self.app.export_button.cget("state")), "normal")
        self.assertAlmostEqual(self.app.result["origin"][0], .5)


if __name__ == "__main__":
    unittest.main()
