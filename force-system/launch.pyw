"""双击启动窗口；运行细节在窗口右侧展开。"""

import tkinter as tk
from tkinter import messagebox

root = tk.Tk()
root.withdraw()
try:
    from gui import App
    root.deiconify()
    App(root)
    root.mainloop()
except (ImportError, SystemExit) as exc:
    messagebox.showerror("启动提示", str(exc)+"\n\n请在本目录运行：\npython -m pip install -r requirements.txt", parent=root)
    root.destroy()
