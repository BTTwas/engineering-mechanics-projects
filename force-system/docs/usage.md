# 使用说明

程序提供窗口和命令行两种入口，使用同一套力系简化计算。长度、力和力矩分别使用 m、N、N·m。

## 启动窗口

需要 Python 3.10 或以上版本及 Tkinter。在 `force-system` 目录中首次安装绘图依赖，然后启动：

```bash
python -m pip install -r requirements.txt
python gui.py
```

Windows 配置了 Python 文件关联时，也可以双击 `launch.pyw` 打开窗口，运行过程在窗口内查看。命令行计算内核不依赖 Matplotlib。

## 输入与计算

左侧是载荷输入区，窗口默认加载课堂立方体算例。点击“+ 添加”可增加作用力或独立力偶，点击已有卡片可修改，卡片右上角的“×”用于删除。作用力默认按大小、方向向量和作用点输入，也可以切换为分量输入；力偶只需填写矩的三个分量。

窗口数值框支持 `√2`、`sqrt(2)`、`1/6` 和简单四则运算。方向向量只表示比例，不必先求单位向量。输入简化点 O 的坐标后，点击“计算并生成图像”。修改简化点时会提示当前显示的是上一次结果，重新计算后才允许导出。

右侧主区域显示主矢和主矩的大小、分量与方向角，下方给出最终简化类型、合力作用线或中央轴。点击右上角“运行细节”展开逐项力矩和计算过程，再次点击可收起。

## 三维图与图片导出

图中并排显示原力系和最终简化结果，可按住鼠标左键拖动旋转，点击“重置视角”恢复默认视角。不同颜色区分各力，虚线表示合力作用线或中央轴，环形箭头按右手法则表示力偶矩方向。

点击“导出图片”，可保存高清 PNG 或矢量 SVG。导出的图片包含原力系图、最终简化图、简化点、主矢与主矩的大小和分量、方向角，以及中央轴、轴向力偶矩和螺距。示意箭头按共同显示比例绘制，力和力矩各用一种比例，图上的投影长度不能直接代替物理量大小。

课堂算例的结果图保存在 `examples/cube_output.png` 与 `examples/cube_output.svg`。课堂算例保留立方体参考线框；新算例只按实际作用点和力绘制，不自动添加立方体。

## 读取与保存

窗口顶部的“打开算例”读取 JSON，“保存输入”保存当前载荷和简化点。JSON 的 `origin` 为简化点，`forces` 为各力，`couples` 为独立力偶矩。每个力只使用分量或大小加方向中的一种写法：

```json
{
  "origin": [0, 0, 0],
  "forces": [
    {"name": "F1", "point": [1, 0, 0], "components": [0, 0, 1]},
    {"name": "F2", "point": [1, 1, 0], "magnitude": 2, "direction": [0, -1, 1]}
  ],
  "couples": []
}
```

JSON 文件中使用数值，算式写法只用于窗口输入框。示例中的 F₂ 大小为 2 N，用于说明输入格式；课堂立方体算例使用 `examples/cube.json` 中的 √2 N。可选的 `geometry` 字段仅控制参考线框，不参与力学计算。

## 命令行

在 `force-system` 目录运行：

```bash
python main.py
python main.py --example
python main.py --input examples/cube.json
python main.py --example --output result.json
python main.py --example --image result.png
```

第一条命令逐项询问简化点、各力和力偶，其余命令分别运行课堂算例、读取文件、保存数值结果和生成结果图片。`--image` 支持 PNG 和 SVG，需要安装绘图依赖。命令行逐项输入使用十进制数值。

## 检查与报告

运行 `python -m unittest discover -s tests -v` 可检查计算、数值输入和图片输出。数值内核使用绝对和相对容差判断零值，具体判据随计算结果输出，接近容差时应按该精度理解分类。

`docs/report.md` 与 `docs/report.html` 为报告正文及打印版。报告打印版不依赖网络；需要重新排版时，另安装 `markdown-it-py`，运行 `python build_report.py`。
