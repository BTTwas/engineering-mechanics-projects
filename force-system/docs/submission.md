# 课程作业提交说明

本次作业为《空间力系的简化与计算》，提交内容分为程序代码和报告，指定立方体算例及输出图片随程序一同提供。

## 程序代码

提交 `force-system` 文件夹，保留各文件的目录关系：

| 文件 | 内容 |
| --- | --- |
| [mechanics.py](../mechanics.py) | 主矢、主矩及最终简化的计算 |
| [gui.py](../gui.py)、[launch.pyw](../launch.pyw) | 窗口界面及双击启动入口 |
| [plotting.py](../plotting.py)、[theme.py](../theme.py) | 三维绘图、图片导出与共用配色 |
| [numbers_input.py](../numbers_input.py) | 窗口中的数值和简单算式输入 |
| [main.py](../main.py) | 命令行交互及数据读写 |
| [requirements.txt](../requirements.txt) | 窗口绘图依赖 |
| [examples/cube.json](../examples/cube.json) | 指定立方体算例 |
| [examples/cube_result.txt](../examples/cube_result.txt) | 算例完整运行输出 |
| [examples/cube_result.json](../examples/cube_result.json) | 算例数值结果 |
| [examples/cube_output.png](../examples/cube_output.png)、[examples/cube_output.svg](../examples/cube_output.svg) | 程序生成的结果图 |
| `tests/` | 计算、输入和图片输出检查 |

程序需要 Python 3.10 或以上版本及 Tkinter。窗口和图片输出需要安装 `requirements.txt` 中的绘图依赖，具体操作见[使用说明](usage.md)。

## 报告与图像

报告包括力系简化原理、程序流程图、使用说明、指定算例的坐标与载荷定义、计算推导、程序输出和等效关系验算。

[report.html](report.html) 是含公式和图表的完整打印版，需要 PDF 时可下载后通过浏览器打印为 PDF。正文另存为 [report.md](report.md)，其中引用的图为 [flowchart.svg](flowchart.svg) 与 [cube.svg](cube.svg)，提交 Markdown 时需一并保留。

`examples/cube_output.png` 可直接作为运行实例图片使用，其中包含原力系、最终简化、主矢与主矩以及中央轴等数值。`examples/cube_output.svg` 是相同内容的矢量版本。

## 现场演示

运行 `python gui.py` 或双击 `launch.pyw`。窗口默认加载课堂算例，主区域直接展示主矢、主矩、原力系及简化结果，右上角“运行细节”可展开逐项力矩和计算过程。根据现场题目编辑载荷和简化点后，点击“计算并生成图像”，需要保留结果时点击“导出图片”。

命令行可运行 `python main.py --example`，也可用 `python main.py` 逐项输入新题。指定算例的主矢为 (1,-1,2) N，主矩为 (0,-1,-1) N·m，最终为力螺旋，螺距为 -1/6 m。
