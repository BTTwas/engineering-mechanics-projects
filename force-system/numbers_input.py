"""输入框支持四则运算、乘方、sqrt 和 π。"""

import ast
import math
import re


def number(text):
    source = str(text).strip().replace("π", "pi").replace("×", "*").replace("÷", "/")
    source = re.sub(r"√\s*(\d+(?:\.\d+)?)", r"sqrt(\1)", source).replace("√(", "sqrt(")
    if not source or len(source) > 100:
        raise ValueError("请填写数值，例如 1、√2 或 1/6")
    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return float(node.value)
        if isinstance(node, ast.Name) and node.id == "pi":
            return math.pi
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp):
            a, b = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Add):
                return a + b
            if isinstance(node.op, ast.Sub):
                return a - b
            if isinstance(node.op, ast.Mult):
                return a * b
            if isinstance(node.op, ast.Div):
                return a / b
            if isinstance(node.op, ast.Pow) and abs(b) <= 12:
                return a ** b
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "sqrt" and len(node.args) == 1 and not node.keywords):
            return math.sqrt(visit(node.args[0]))
        raise ValueError
    try:
        value = visit(ast.parse(source, mode="eval").body)
        if isinstance(value, complex) or not math.isfinite(value):
            raise ValueError
        return float(value)
    except (SyntaxError, TypeError, ValueError, ZeroDivisionError, OverflowError, RecursionError):
        raise ValueError("数值无效，请使用 1、√2、1/6 这类写法") from None
