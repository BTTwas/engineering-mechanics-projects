# 工程力学课程作业

这里放工程力学课的编程作业和计算记录。

## 空间力系的简化与计算

根据各力的大小、方向、作用点和简化点，计算主矢、主矩，并判断最终简化为平衡、合力、力偶还是力螺旋。程序使用 Python，包含命令行输入和窗口界面。

进入 `force-system` 文件夹后运行：

```bash
python gui.py
```

也可以直接运行老师给出的立方体算例：

```bash
python main.py --example
```

Python 3.10 及以上即可，计算部分只用标准库。窗口界面需要 Tkinter，Windows 官方 Python 安装包通常自带。

[作业说明](force-system/README.md) · [课程报告](force-system/docs/report.md) · [可打印报告](force-system/docs/report.html)
