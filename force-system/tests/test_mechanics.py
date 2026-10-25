"""核对四种简化结果、课堂算例、等效关系及输入检查。"""

import json
import math
from pathlib import Path
import unittest

from mechanics import (Force, add, sub, cross, scale, norm, reduce_system,
                       load_case)

HERE = Path(__file__).resolve().parents[1]


class ReductionTests(unittest.TestCase):
    def assertVector(self, a, b, places=9):
        for x, y in zip(a, b):
            self.assertAlmostEqual(x, y, places=places)

    def test_cube(self):
        forces, origin, couples = load_case(json.loads(
            (HERE/"examples"/"cube.json").read_text(encoding="utf-8")))
        r = reduce_system(forces, origin, couples)
        self.assertVector(r["resultant"], (1, -1, 2))
        self.assertVector(r["moment"], (0, -1, -1))
        self.assertVector(r["central_point"], (1/2, 1/6, -1/6))
        self.assertVector(r["axial_couple"], (-1/6, 1/6, -1/3))
        self.assertAlmostEqual(r["pitch"], -1/6)
        self.assertEqual(r["kind"], "wrench")

    def test_equilibrium(self):
        forces = [Force((2, 0, 0), (1, 0, 0)), Force((-1, 0, 0), (-1, 0, 0))]
        self.assertEqual(reduce_system(forces)["kind"], "equilibrium")
        self.assertEqual(reduce_system([])["kind"], "equilibrium")

    def test_couple(self):
        r = reduce_system([Force((0, 1, 0), (1, 0, 0)),
                           Force((0, 0, 0), (-1, 0, 0))])
        self.assertEqual(r["kind"], "couple")
        self.assertVector(r["moment"], (0, 0, -1))
        self.assertIsNone(r["central_point"])
        self.assertEqual(reduce_system([], couples=[(1, 2, 3)])["kind"], "couple")

    def test_single_resultant(self):
        r = reduce_system([Force((0, 2, 0), (3, 0, 0))])
        self.assertEqual(r["kind"], "resultant")
        self.assertVector(r["central_point"], (0, 2, 0))
        self.assertVector(r["axial_couple"], (0, 0, 0))

    def test_wrench_at_origin(self):
        r = reduce_system([Force((0, 0, 0), (0, 0, 2))], couples=[(0, 0, 6)])
        self.assertEqual(r["kind"], "wrench")
        self.assertVector(r["central_point"], (0, 0, 0))
        self.assertAlmostEqual(r["pitch"], 3)

    def test_direction_is_normalized(self):
        force = Force.from_direction((0, 0, 0), 5, (3, 4, 0))
        self.assertVector(force.components, (3, 4, 0))

    def test_moment_transfer_and_reconstruction(self):
        forces = [Force((1, 3, -2), (2, -1, 4)),
                  Force((-1, 2, 5), (-3, 2, 1))]
        origin, shifted = (0, 0, 0), (3, -2, 1)
        a = reduce_system(forces, origin, [(1, -1, 2)])
        b = reduce_system(forces, shifted, [(1, -1, 2)])
        expected = sub(a["moment"], cross(sub(shifted, origin), a["resultant"]))
        self.assertVector(b["moment"], expected)
        self.assertAlmostEqual(a["pitch"], b["pitch"])
        # 任意选取中央轴上的点，重构原力系在 O 点的矩。
        for r in (a, b):
            for t in (-3, 0, 4):
                p = add(r["central_point"], scale(r["axis_direction"], t))
                reconstructed = add(cross(sub(p, r["origin"]), r["resultant"]),
                                    r["axial_couple"])
                self.assertVector(reconstructed, r["moment"])
        # 改换简化点只会改变中央轴代表点，不会改变中央轴本身。
        self.assertAlmostEqual(norm(cross(sub(a["central_point"], b["central_point"]),
                                          a["axis_direction"])), 0)

    def test_small_numerical_noise(self):
        forces = [Force((0, 0, 0), (1, 0, 0)),
                  Force((0, 0, 0), (-1+1e-12, 0, 0))]
        self.assertEqual(reduce_system(forces)["kind"], "equilibrium")
        self.assertEqual(reduce_system([Force((0, 0, 0), (1e-6, 0, 0))])["kind"],
                         "resultant")

    def test_invalid_inputs(self):
        for args in (((0, 0, 0), -1, (1, 0, 0)),
                     ((0, 0, 0), 1, (0, 0, 0)),
                     ((0, 0, 0), float("nan"), (1, 0, 0))):
            with self.assertRaises(ValueError):
                Force.from_direction(*args)
        for point, components in (((1, 2), (1, 2, 3)),
                                  ((0, 0, 0), (float("inf"), 0, 0))):
            with self.assertRaises(ValueError):
                Force(point, components)
        for case in ({"forces": [{}]}, {"forces": [
                {"point": [0, 0, 0], "components": [1, 0, 0], "magnitude": 1}]}):
            with self.assertRaises(ValueError):
                load_case(case)


if __name__ == "__main__":
    unittest.main()
