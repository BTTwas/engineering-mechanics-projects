"""检查载荷编辑和输入变更后的计算状态。"""

import unittest

try:
    import tkinter as tk
    from gui import App, LoadDialog, next_load_name
except ImportError:
    tk = None


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
