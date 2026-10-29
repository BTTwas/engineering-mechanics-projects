"""检查载荷编辑和输入变更后的计算状态。"""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock

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
