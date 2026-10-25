"""检查输入算式与四种简化结果的图像输出。"""

import json
import math
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from PIL import Image

from mechanics import Force, load_case, reduce_system
from numbers_input import number
from plotting import result_figure, export_result

HERE = Path(__file__).resolve().parents[1]


class NumberTests(unittest.TestCase):
    def test_classroom_expressions(self):
        self.assertAlmostEqual(number("√2"), math.sqrt(2))
        self.assertAlmostEqual(number("sqrt(2)"), math.sqrt(2))
        self.assertAlmostEqual(number("1/6"), 1/6)
        self.assertAlmostEqual(number("-(2+1)/2"), -1.5)
        self.assertAlmostEqual(number("√(1+3)"), 2)

    def test_reject_invalid_and_nonfinite(self):
        for value in ("1/0", "sqrt(-1)", "1e999", "", "2**9999", "True",
                      "__import__('os')", "sqrt(x)", "[1,2]", "sqrt(x=2)"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                number(value)


class ImageTests(unittest.TestCase):
    def test_all_reduction_types_are_drawn(self):
        cases = [
            ([], [], "equilibrium"),
            ([], [(0, 0, 2)], "couple"),
            ([Force((1, 0, 0), (0, 1, 0))], [], "resultant"),
            ([Force((0, 0, 0), (0, 0, 1))], [(0, 0, -2)], "wrench"),
        ]
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            self.assertEqual(Path(tmp).resolve().parent, HERE.resolve())
            for i, (forces, couples, kind) in enumerate(cases):
                result = reduce_system(forces, couples=couples)
                self.assertEqual(result["kind"], kind)
                figure = result_figure(forces, result, couples)
                self.assertEqual(len(figure.axes), 2)
                self.assertTrue(all(ax.name == "3d" for ax in figure.axes))
                text = "\n".join(t.get_text() for t in figure.texts)
                self.assertIn("方向角", text)
                if kind in ("resultant", "wrench"):
                    self.assertIn("r = A", text)
                figure.clear()
                path = Path(tmp)/f"case{i}.svg"
                export_result(path, forces, result, couples)
                self.assertTrue(ET.parse(path).getroot().tag.endswith("svg"))

    def test_cube_png_has_print_resolution(self):
        data = json.loads((HERE/"examples"/"cube.json").read_text(encoding="utf-8"))
        forces, origin, couples = load_case(data)
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            self.assertEqual(Path(tmp).resolve().parent, HERE.resolve())
            path = Path(tmp)/"result.png"
            export_result(path, forces, reduce_system(forces, origin, couples),
                          couples, data.get("geometry"))
            with Image.open(path) as image:
                self.assertEqual(image.size, (3120, 2340))
                self.assertEqual(image.format, "PNG")
                self.assertLess(min(image.convert("RGB").getextrema()[0]), 100)


if __name__ == "__main__":
    unittest.main()
