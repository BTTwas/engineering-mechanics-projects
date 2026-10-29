"""窗口与结果图共用的颜色和字号。"""

import sys

BACKGROUND = "#f3f6fc"
SURFACE = "#ffffff"
INK = "#19385e"
SECONDARY = "#536b8a"
BLUE = "#285fae"
BLUE_DARK = "#19488c"
SOFT = "#eaf1fc"
BORDER = "#d8e2f0"
FIELD = "#f7faff"
LOAD_CARD = "#f2f6fd"
DETAILS = "#eef3fb"
WARNING = "#96621c"
ERROR = "#b24650"
FORCE_COLORS = ("#244f91", "#3976bd", "#5889bd", "#465e91", "#347594", "#607da9")
MOMENT_BLUE = "#5479ac"
FONT = "PingFang SC" if sys.platform == "darwin" else "Microsoft YaHei UI"

# 格式优化：主数值和标题加大，说明文字保留较轻的字重。（便于阅读）
SIZES = {8: 10, 9: 10, 10: 11, 11: 12, 14: 16, 15: 17, 18: 20, 20: 22, 24: 28}
