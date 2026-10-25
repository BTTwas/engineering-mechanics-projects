# 课程作业提交说明

本次作业为《空间力系的简化与计算》，提交内容分为程序代码和报告，立方体算例随程序一同提供。现场演示使用同一份程序，可以运行指定算例，也可以根据现场题目修改载荷与简化点。

## 程序代码

将 `force-system` 文件夹作为程序部分提交，保留以下文件及原有目录关系：

| 文件 | 内容 |
| --- | --- |
| [mechanics.py](../mechanics.py) | 向量计算、主矢与主矩、力系最终简化 |
| [main.py](../main.py) | 命令行交互及 JSON 数据读写 |
| [gui.py](../gui.py) | 窗口输入、结果显示和力系示意 |
| [examples/cube.json](../examples/cube.json) | 题目指定的立方体算例 |
| [examples/cube_result.txt](../examples/cube_result.txt) | 算例完整运行输出 |
| [examples/cube_result.json](../examples/cube_result.json) | 算例计算结果数据 |
| [tests/test_mechanics.py](../tests/test_mechanics.py) | 数值计算与等效关系检查 |

程序需要 Python 3.10 或以上版本，窗口界面需要 Tkinter。计算和运行不需要安装第三方包，具体操作见[使用说明](usage.md)。

## 报告

报告包括力系简化原理、程序流程图、使用说明、指定立方体算例的坐标与载荷定义、计算推导、程序输出以及结果验算。

[report.html](report.html) 是包含公式和图表的完整打印版，可下载后在浏览器中打开；需要 PDF 时，通过浏览器打印功能另存为 PDF。报告正文另存为 [report.md](report.md)，其中的流程图和算例图分别为 [flowchart.svg](flowchart.svg) 与 [cube.svg](cube.svg)。提交 Markdown 版本时需同时保留这两张图。

## 现场演示

在 `force-system` 目录下运行 `python gui.py`，窗口默认载入立方体算例。先展示各力的作用点和分量，再展示向 O 点简化的主矢与主矩，以及力螺旋的中央轴、轴向力偶矩和螺距。根据现场题目修改载荷或简化点后，点击“计算”查看结果。

也可以运行 `python main.py --example` 直接展示指定算例，或运行 `python main.py` 逐项输入新题目。指定算例的主矢为 (1,-1,2) N，主矩为 (0,-1,-1) N·m，最终简化为力螺旋，螺距为 -1/6 m。
