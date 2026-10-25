"""命令行入口：不带参数时逐项输入，--example 运行课堂算例。"""

import argparse
import json
from pathlib import Path

from mechanics import Force, load_case, reduce_system, format_result

HERE = Path(__file__).resolve().parent


def ask_vector(prompt):
    while True:
        try:
            parts = input(prompt).replace(",", " ").replace("，", " ").split()
            from mechanics import vector
            return vector(parts)
        except ValueError as exc:
            print(exc)


def ask_count(prompt):
    while True:
        try:
            count = int(input(prompt))
            if count >= 0:
                return count
        except ValueError:
            pass
        print("请输入非负整数。")


def interactive():
    print("空间力系的简化与计算")
    print("长度用 m，力用 N。三个分量用空格隔开。")
    origin = ask_vector("简化点 x y z：")
    forces = []
    for i in range(ask_count("力的个数：")):
        print(f"\nF{i+1}")
        point = ask_vector("作用点 x y z：")
        while True:
            mode = input("输入方式：1 分量；2 大小和方向 [1]：").strip() or "1"
            if mode == "1":
                forces.append(Force(point, ask_vector("Fx Fy Fz："), f"F{i+1}"))
                break
            if mode == "2":
                try:
                    magnitude = float(input("力的大小："))
                    direction = ask_vector("方向向量 dx dy dz（不必归一化）：")
                    forces.append(Force.from_direction(point, magnitude, direction, f"F{i+1}"))
                    break
                except ValueError as exc:
                    print(exc)
            else:
                print("请输入 1 或 2。")
    couples = [ask_vector(f"第 {i+1} 个力偶矩 Mx My Mz：")
               for i in range(ask_count("\n独立力偶的个数（没有则填 0）："))]
    return forces, origin, couples


def main():
    parser = argparse.ArgumentParser(description="空间力系的简化与计算")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--example", action="store_true", help="运行课堂立方体算例")
    source.add_argument("--input", type=Path, help="读取 JSON 算例")
    parser.add_argument("--output", type=Path, help="把计算结果另存为 JSON")
    args = parser.parse_args()
    try:
        if args.example or args.input:
            path = HERE / "examples" / "cube.json" if args.example else args.input
            forces, origin, couples = load_case(json.loads(path.read_text(encoding="utf-8")))
        else:
            forces, origin, couples = interactive()
        result = reduce_system(forces, origin, couples)
        print(format_result(result, forces))
        if args.output:
            args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2,
                                              allow_nan=False) + "\n", encoding="utf-8")
            print(f"\n已保存：{args.output}")
        return 0
    except (ValueError, TypeError, OSError) as exc:
        parser.exit(2, f"输入错误：{exc}\n")
    except (EOFError, KeyboardInterrupt):
        print("\n已结束输入。")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
