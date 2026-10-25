"""生成报告图和可打印 HTML。仅重新生成报告时需要 matplotlib、markdown-it-py。"""

from pathlib import Path
import html
import io
import re

HERE = Path(__file__).resolve().parent
DOCS = HERE / "docs"


def svg_document(width, height, content):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">'
            '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" '
            'orient="auto"><path d="M0,0 L8,4 L0,8Z" fill="#364653"/></marker>'
            '<marker id="blue" markerWidth="8" markerHeight="8" refX="7" refY="4" '
            'orient="auto"><path d="M0,0 L8,4 L0,8Z" fill="#245e83"/></marker></defs>'
            '<rect width="100%" height="100%" fill="white"/>'
            '<g font-family="Microsoft YaHei, SimSun, sans-serif" font-size="17" '
            'fill="#25333d">' + content + '</g></svg>')


def flowchart():
    shapes, links = [], []
    def box(x, y, w, text, decision=False):
        if decision:
            shapes.append(f'<polygon points="{x+w/2},{y} {x+w},{y+38} '
                          f'{x+w/2},{y+76} {x},{y+38}" fill="#edf3f5" stroke="#627b89"/>')
            cy = y+38
        else:
            shapes.append(f'<rect x="{x}" y="{y}" width="{w}" height="54" rx="7" '
                          'fill="#f4f7f8" stroke="#627b89"/>')
            cy = y+27
        shapes.append(f'<text x="{x+w/2}" y="{cy+6}" text-anchor="middle">{text}</text>')
    def line(points, label="", lx=0, ly=0):
        links.append(f'<polyline points="{points}" fill="none" stroke="#364653" '
                     'stroke-width="1.7" marker-end="url(#arrow)"/>')
        if label:
            links.append(f'<text x="{lx}" y="{ly}" fill="#51646f">{label}</text>')
    box(305, 20, 290, "输入各力、力偶和简化点")
    box(305, 110, 290, "检查输入与方向归一化")
    box(305, 200, 290, "计算 R 与 Mₒ")
    box(330, 295, 240, "R 是否为零？", True)
    box(65, 425, 230, "Mₒ 是否为零？", True)
    box(500, 425, 315, "求中央轴与轴向力偶矩")
    box(530, 540, 255, "轴向力偶矩为零？", True)
    box(25, 665, 155, "平衡力系")
    box(210, 665, 155, "力偶")
    box(475, 665, 155, "合力及作用线")
    box(675, 665, 195, "力螺旋及中央轴")
    box(305, 800, 290, "输出大小、方向与简化结果")
    for a, b in [(74,110),(164,200),(254,295)]:
        line(f"450,{a} 450,{b}")
    line("330,333 180,333 180,425", "是", 240, 323)
    line("570,333 658,333 658,425", "否", 610, 323)
    line("180,501 180,560 102,560 102,665", "是", 124, 548)
    line("295,463 350,463 350,600 287,600 287,665", "否", 310, 450)
    line("658,479 658,540")
    line("530,578 552,578 552,665", "是", 503, 638)
    line("785,578 795,578 795,665", "否", 809, 638)
    for x in (102, 287, 552, 772):
        line(f"{x},719 {x},765 450,765 450,800")
    return svg_document(900, 885, "".join(links+shapes))


def cube():
    def point(p):
        x, y, z = p
        return (205-110*x+230*y, 290+78*x-185*z)
    def line(a, b, color="#58636b", dashed=False, arrow=False, width=1.8):
        x1, y1 = point(a)
        x2, y2 = point(b)
        return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                f'stroke="{color}" stroke-width="{width}" '
                + ('stroke-dasharray="5 4" ' if dashed else '')
                + ('marker-end="url(#blue)" ' if arrow else '') + '/>')
    def text(p, value, dx=0, dy=0, color="#25333d"):
        x, y = point(p)
        return f'<text x="{x+dx}" y="{y+dy}" fill="{color}">{value}</text>'
    output = []
    for dim in range(3):
        for a in range(2):
            for b in range(2):
                p = [0, 0, 0]
                other = [i for i in range(3) if i != dim]
                p[other[0]], p[other[1]] = a, b
                q = p.copy()
                q[dim] = 1
                output.append(line(p, q, dashed=a == 0 and b == 0))
    for end, label, dx, dy in (((1.25,0,0),"x",-10,20),
                               ((0,1.2,0),"y",8,5),((0,0,1.23),"z",-16,-6)):
        output.append(line((0,0,0),end,color="#83919b",dashed=True))
        output.append(text(end,label,dx,dy))
    output.append(text((0,0,0),"O",-25,2))
    # F2 沿前侧面对角线；F4 沿顶面对角线。
    arrows = [((1,0,0),(1,0,.67),"F₁",-30,-2),
              ((1,1,0),(1,.45,.55),"F₂",-25,28),
              ((0,1,0),(0,.55,0),"F₃",15,-15),
              ((0,0,1),(.60,.60,1),"F₄",2,-12)]
    for a,b,label,dx,dy in arrows:
        output.append(line(a,b,color="#245e83",arrow=True,width=3))
        output.append(text(b,label,dx,dy,color="#245e83"))
    output.append('<text x="30" y="435" font-size="15">边长 1 m；F₁ = F₃ = 1 N；F₂ = F₄ = √2 N</text>')
    return svg_document(560, 465, "".join(output))


def build():
    from markdown_it import MarkdownIt
    from matplotlib.mathtext import math_to_image
    import matplotlib
    matplotlib.use("Agg")

    DOCS.mkdir(exist_ok=True)
    for name, drawing in (("flowchart",flowchart()),("cube",cube())):
        (DOCS/f"{name}.svg").write_text(drawing, encoding="utf-8")
    source = (DOCS/"report.md").read_text(encoding="utf-8")
    for name, caption in (("flowchart","程序流程"),("cube","课堂算例：坐标与各力方向")):
        source = re.sub(r"!\[[^\]]*\]\("+name+r"\.svg\)",
                        '<figure>'+ (DOCS/f"{name}.svg").read_text(encoding="utf-8")+
                        '<figcaption>'+caption+'</figcaption></figure>', source)
    def equation(match):
        buffer = io.BytesIO()
        formula = re.sub(r"\s+", " ", match.group(1)).replace(r"\ne", r"\neq")
        formula = re.sub(r"\\(mathbf|mathbb|mathrm)\s+([A-Za-z])", r"\\\1{\2}", formula)
        math_to_image("$"+formula+"$", buffer, format="svg", dpi=160, color="#172b3a")
        svg = buffer.getvalue().decode("utf-8")
        svg = svg[svg.index("<svg"):]
        return '\n<div class="equation">'+svg+'</div>\n'
    source = re.sub(r"\$\$(.*?)\$\$", equation, source, flags=re.S)
    body = MarkdownIt("default", {"html":True}).enable("table").render(source)
    page = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>空间力系的简化与计算</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#eee;font:16px/1.85 "Microsoft YaHei","SimSun",serif;color:#202b32}
main{max-width:950px;margin:32px auto;padding:52px 66px;background:white}
h1{font-size:29px;letter-spacing:.06em;margin:0 0 10px;text-align:center}
h1+p{text-align:center;color:#69757d;margin-bottom:44px}
h2{font-size:21px;margin:34px 0 16px;border-bottom:1px solid #b6c2ca;padding-bottom:6px}
h3{font-size:17px;margin:25px 0 12px}
p{margin:12px 0;text-align:justify}
table{width:100%;border-collapse:collapse;font-size:14px;line-height:1.7;margin:20px 0}
th,td{border:1px solid #bcc8cf;padding:9px 10px;text-align:left}
th{background:#f0f4f6}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f5f6;padding:14px 18px;font-size:13px;line-height:1.75}
code{font-family:Consolas,"Microsoft YaHei",monospace;font-size:.9em}
.equation{text-align:center;margin:22px 0;break-inside:avoid}
.equation svg{max-width:100%;height:auto}
figure{text-align:center;margin:26px 0;break-inside:avoid}
figure svg{max-width:100%;height:auto}
figure:first-of-type svg{max-height:750px;width:auto;max-width:100%}
figcaption{color:#66737c;font-size:13px}
@media print{
@page{size:A4;margin:18mm 17mm}
body{background:white;font-size:11pt;line-height:1.75}
main{max-width:none;margin:0;padding:0}
h1{font-size:22pt}h2{font-size:15pt;break-after:avoid}h3{font-size:12pt;break-after:avoid}
table{font-size:9pt;break-inside:avoid}pre{font-size:9pt}
figure:first-of-type svg{max-height:205mm}
p{orphans:3;widows:3}
}
@media(max-width:650px){main{margin:0;padding:26px 18px}table{font-size:12px}th,td{padding:5px}}
</style></head><body><main>"""
    (DOCS/"report.html").write_text(page+body+"</main></body></html>\n", encoding="utf-8")
    print("报告与两张示意图已生成。")


if __name__ == "__main__":
    build()
