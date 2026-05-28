#!/usr/bin/env python3
"""
v2: Direct HTML generation with embedded visual diagrams.
Reads the original markdown, builds visual SVGs for known sections,
and produces the final HTML in one pass.
"""

import re
import math

# ─── SVG builders (from visualize_diagrams.py) ────────────────────────────────

def svg_wrapper(w, h, content):
    return f'''<svg class="diagram" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">
<style>
  .d-text {{ font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; font-size: 13px; fill: #2F2E2A; }}
  .d-text-sm {{ font-size: 11px; fill: #7F7D74; }}
  .d-title {{ font-size: 14px; font-weight: bold; fill: #FFFFFF; }}
  .d-box {{ rx: 8; ry: 8; }}
  .d-arr {{ stroke: #7F7D74; stroke-width: 2; fill: none; marker-end: url(#arrow); }}
  .d-arr-thick {{ stroke: #5E8B5A; stroke-width: 3; fill: none; marker-end: url(#arrow-green); }}
</style>
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#7F7D74"/></marker>
  <marker id="arrow-green" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#5E8B5A"/></marker>
  <filter id="shadow"><feDropShadow dx="1" dy="2" stdDeviation="2" flood-opacity="0.12"/></filter>
</defs>
{content}
</svg>'''


def rect_box(x, y, w, h, color, label, sub="", fill_class="d-box"):
    extra = ""
    if sub:
        sub_escaped = sub.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '&#10;')
        # Use multiple tspan for multi-line sub
        sub_lines = sub.split('\n')
        tspans = ""
        for li, line in enumerate(sub_lines):
            tspans += f'<tspan x="{x+w/2}" dy="{18 if li > 0 else 0}">{line}</tspan>'
        extra = f'<text x="{x+w/2}" y="{y+h-12}" text-anchor="middle" class="d-text-sm" fill="#FFFFFF" opacity="0.9">{tspans}</text>'
    return f'''<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" class="{fill_class}" filter="url(#shadow)"/>
<text x="{x+w/2}" y="{y+h/2+5}" text-anchor="middle" class="d-title" dominant-baseline="middle">{label}</text>
{extra}'''


def arrow_line(x1, y1, x2, y2, cls="d-arr"):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{cls}"/>'


def arrow_h(x1, x2, y, cls="d-arr"):
    return arrow_line(x1, y, x2, y, cls)


def arrow_v(x, y1, y2, cls="d-arr"):
    return arrow_line(x, y1, x, y2, cls)


# ─── §2: 延伸方向一览 ──────────────────────────────────────────────────────
def diagram_overview():
    w, h = 860, 580
    cx, cy = 430, 290

    dirs = [
        ("被动→主动", "#5E8B5A", [("预警监控", "用药依从", "异常检测")]),
        ("单次→长期", "#7BA7B9", [("健康计划", "康复跟踪", "目标管理")]),
        ("个体→家庭", "#CD8B5B", [("家庭关怀", "代际沟通", "紧急联动")]),
        ("文本→多模态", "#E7B83E", [("影像分析", "语音交互", "可穿戴")]),
        ("通用→专业", "#1565C0", [("循证医学", "临床试验", "知识发现")]),
        ("单一→平台", "#795548", [("SaaS平台", "诊所版", "保险版")]),
        ("自我进化", "#4C7048", [("评估评分", "Prompt优化", "LLM路由")]),
        ("三级预防", "#5A9E87", [("风险评估", "筛查推荐", "并发症阻断")]),
    ]

    items = []
    items.append(f'<rect x="{cx-70}" y="{cy-35}" width="140" height="70" fill="#5E8B5A" class="d-box" filter="url(#shadow)"/>')
    items.append(f'<text x="{cx}" y="{cy-7}" text-anchor="middle" class="d-title" font-size="16">WellHealth</text>')
    items.append(f'<text x="{cx}" y="{cy+15}" text-anchor="middle" class="d-text-sm" fill="#FFFFFF">多Agent基座</text>')

    for i, (name, color, subs) in enumerate(dirs):
        angle = i * 45 - 90
        rad = math.pi * angle / 180
        r1, r2 = 100, 185
        x1 = cx + r1 * math.cos(rad)
        y1 = cy + r1 * math.sin(rad)
        x2 = cx + r2 * math.cos(rad)
        y2 = cy + r2 * math.sin(rad)

        dx = x2 - x1
        dy = y2 - y1
        length = (dx*dx + dy*dy) ** 0.5
        if length > 0:
            nx, ny = dx/length, dy/length
            items.append(f'<line x1="{cx+70*nx}" y1="{cy+35*ny}" x2="{x2-45*nx}" y2="{y2-20*ny}" class="d-arr-thick" stroke="{color}"/>')

        items.append(f'<rect x="{x2-40}" y="{y2-15}" width="80" height="30" rx="15" ry="15" fill="{color}" filter="url(#shadow)"/>')
        items.append(f'<text x="{x2}" y="{y2+5}" text-anchor="middle" class="d-title" font-size="12">{name}</text>')

        for j, (s1, s2, s3) in enumerate(subs):
            r3 = 245
            x3 = cx + r3 * math.cos(rad + (j-1)*0.15)
            y3 = cy + r3 * math.sin(rad + (j-1)*0.15)
            items.append(f'<line x1="{x2}" y1="{y2}" x2="{x3}" y2="{y3}" stroke="{color}" stroke-width="1.5" stroke-dasharray="3,3"/>')
            items.append(f'<rect x="{x3-28}" y="{y3-8}" width="56" height="20" rx="10" ry="10" fill="{color}" opacity="0.2"/>')
            items.append(f'<text x="{x3}" y="{y3+4}" text-anchor="middle" class="d-text-sm" fill="{color}" font-size="10">{s1}</text>')

    return svg_wrapper(w, h, '\n'.join(items))


# ─── §3.2.1: MonitorAgent ─────────────────────────────────────────────────
def diagram_monitor():
    w, h = 800, 320
    cx = 400
    items = []

    items.append(rect_box(cx-70, 100, 140, 60, "#5E8B5A", "MonitorAgent", "协调者"))

    agents = [
        (cx-200, 30, "#E7B83E", "DataAnalyzer", "数据分析"),
        (cx+60, 30, "#CD8B5B", "AlertAssessor", "风险判定"),
        (cx-200, 200, "#7BA7B9", "Intervention", "干预执行"),
        (cx+60, 200, "#795548", "Notification", "通知推送"),
    ]
    for x, y, color, name, sub in agents:
        items.append(rect_box(x, y, 130, 44, color, name, sub))
        if y < 100:
            items.append(arrow_v(x+65, y+44, 100))
        else:
            items.append(arrow_v(cx, 160, y))

    items.append(rect_box(cx-60, 0, 120, 30, "#4C7048", "定时触发"))
    items.append(arrow_v(cx, 30, 100))
    items.append(rect_box(cx-60, h-30, 120, 30, "#4C7048", "分发行动指令"))
    items.append(arrow_v(cx, h-60, h-30))
    items.append(arrow_h(cx-70, cx-200, 130))
    items.append(arrow_h(cx+70, cx+60, 130))
    items.append(arrow_h(cx-70, cx-200, 222))
    items.append(arrow_h(cx+70, cx+60, 222))

    return svg_wrapper(w, h, '\n'.join(items))


# ─── §4.2.1: PlanCoordinator ──────────────────────────────────────────────
def diagram_plan_coordinator():
    w, h = 820, 460
    cx = 410
    items = []

    items.append(rect_box(cx-130, 0, 260, 36, "#4C7048", "患者档案+历史+偏好"))
    items.append(arrow_v(cx, 36, 70))
    items.append(rect_box(cx-80, 70, 160, 50, "#5E8B5A", "PlanCoordinator", "接收+分发"))
    items.append(arrow_v(cx-60, 120, 170))
    items.append(arrow_v(cx-20, 120, 170))
    items.append(arrow_v(cx+20, 120, 170))
    items.append(arrow_v(cx+60, 120, 170))

    agents = [
        (cx-220, 170, "#CD8B5B", "临床目标\nAgent"),
        (cx-70, 170, "#E7B83E", "营养方案\nAgent"),
        (cx+80, 170, "#7BA7B9", "运动方案\nAgent"),
        (cx+230, 170, "#795548", "心理支持\nAgent"),
    ]
    for x, y, color, label in agents:
        items.append(rect_box(x, y, 110, 50, color, label))
        items.append(arrow_v(x+55, y+50, 250))

    items.append(rect_box(cx-100, 250, 200, 50, "#5A9E87", "PlanValidator", "冲突检测"))
    items.append(arrow_v(cx, 300, 360))
    items.append(rect_box(cx-140, 360, 280, 50, "#1565C0", "综合健康计划", "3月目标+每周计划+评估指标"))

    return svg_wrapper(w, h, '\n'.join(items))


# ─── §5.2.1: FamilyHealth ────────────────────────────────────────────────
def diagram_family():
    w, h = 780, 380
    cx = 390
    items = []

    items.append(rect_box(cx-150, 0, 300, 50, "#5E8B5A", "FamilyHealth Agent", "家庭的健康管家"))
    items.append(arrow_v(cx, 50, 90))

    members = [
        (cx-240, 90, "#CD8B5B", "父亲-糖尿病", "Diabetes Agent"),
        (cx-20, 90, "#7BA7B9", "母亲-高血压", "Hypertension Agent"),
        (cx+200, 90, "#5A9E87", "子女-健康管理", "General Agent"),
    ]
    for x, y, color, title, sub in members:
        items.append(rect_box(x, y, 200, 70, color, title, sub))

    items.append(arrow_v(cx-140, 160, 200))
    items.append(arrow_v(cx, 160, 200))
    items.append(arrow_v(cx+140, 160, 200))

    items.append(f'<rect x="{cx-240}" y="200" width="620" height="120" rx="10" ry="10" fill="#E8F0E6" filter="url(#shadow)"/>')
    items.append(f'<text x="{cx}" y="225" text-anchor="middle" class="d-text" font-size="13" font-weight="bold" fill="#4C7048">家庭共享资源</text>')

    resources = ["家庭食谱库", "家庭活动计划", "家庭关怀消息", "健康报告"]
    for i, res in enumerate(resources):
        x = cx - 190 + i * 120
        items.append(f'<rect x="{x}" y="240" width="100" height="40" rx="20" fill="#FFFFFF" stroke="#DDCFB0" stroke-width="1"/>')
        items.append(f'<text x="{x+50}" y="265" text-anchor="middle" class="d-text-sm" font-size="12">{res}</text>')

    return svg_wrapper(w, h, '\n'.join(items))


# ─── §12.3.1: 处方审核三层架构 ────────────────────────────────────────────
def diagram_prescription_review():
    w, h = 740, 520
    cx = 370
    items = []

    items.append(rect_box(60, 0, 120, 36, "#4C7048", "患者"))
    items.append(rect_box(240, 0, 120, 36, "#7BA7B9", "医生开方"))
    items.append(rect_box(420, 0, 120, 36, "#E7B83E", "处方提交"))
    items.append(arrow_h(180, 240, 18))
    items.append(arrow_h(360, 420, 18))

    items.append(arrow_v(cx+90, 36, 80))
    items.append(rect_box(cx-130, 80, 260, 46, "#5E8B5A", "PrescriptionReviewCoordinator", "编排器-协调3层审核"))
    items.append(arrow_v(cx-60, 126, 170))
    items.append(arrow_v(cx, 126, 170))
    items.append(arrow_v(cx+60, 126, 170))

    layers = [
        (cx-240, 170, "#CD8B5B", "Layer 1: 规则引擎", "相互作用·禁忌·重复·剂量"),
        (cx-20, 170, "#1565C0", "Layer 2: 医保政策", "目录匹配·报销·限制·替代"),
        (cx+200, 170, "#5A9E87", "Layer 3: AI个体化", "年龄/体重/肾功·SHAP解释"),
    ]
    for x, y, color, title, sub in layers:
        items.append(rect_box(x, y, 200, 110, color, title))
        sub_escaped = sub
        items.append(f'<text x="{x+100}" y="{y+75}" text-anchor="middle" class="d-text-sm" fill="#FFFFFF" opacity="0.9">{sub_escaped}</text>')

    for xpos in [cx-140, cx+100, cx+340]:
        items.append(arrow_v(xpos+30, 280, 350))

    items.append(rect_box(cx-200, 370, 400, 80, "#5E8B5A", "审核结果汇总", "通过 | 警告(可开) | 拦截(需修改)"))

    return svg_wrapper(w, h, '\n'.join(items))


# ─── §12.3.5: 闭环管理 ─────────────────────────────────────────────────
def diagram_closed_loop():
    w, h = 820, 300
    items = []

    steps = [
        ("预问诊", "#7BA7B9", "TriageAgent\n症状→科室"),
        ("线上问诊", "#5E8B5A", "BridgeAgent\n对接互联网医院"),
        ("处方流转", "#CD8B5B", "ReviewAgent\n3层审核"),
        ("用药管理", "#E7B83E", "AdherenceAgent\n提醒→打卡"),
        ("随访", "#795548", "FollowUpAgent\n复诊→评价"),
        ("效果评估", "#1565C0", "HealthPlanAgent\n指标追踪→调整"),
    ]

    for i, (title, color, sub) in enumerate(steps):
        x = 20 + i * 135
        items.append(rect_box(x, 20, 115, 80, color, f"Step {i+1}\n{title}"))
        sub_escaped = sub.replace('<', '&lt;').replace('>', '&gt;')
        items.append(f'<text x="{x+57}" y="75" text-anchor="middle" class="d-text-sm" fill="#FFFFFF" opacity="0.9" font-size="10">{sub_escaped}</text>')
        if i < len(steps) - 1:
            items.append(arrow_h(x+115, x+135, 60))

    items.append(rect_box(100, 200, 620, 40, "#4C7048", "完整闭环: 症状→分诊→问诊→处方→购药→用药→随访→评估→调整"))
    items.append(rect_box(240, 0, 340, 26, "#5E8B5A", "Closed-Loop 全流程 Agent 协作"))

    return svg_wrapper(w, h, '\n'.join(items))


# ─── §11.1: 优先级矩阵 ────────────────────────────────────────────────────
def diagram_priority_matrix():
    w, h = 780, 540
    items = []

    items.append(f'<text x="390" y="30" text-anchor="middle" class="d-text" font-size="16" font-weight="bold">延伸实施优先级矩阵</text>')
    items.append(f'<text x="700" y="30" text-anchor="end" class="d-text-sm">用户/商业价值 →</text>')

    # P0
    items.append(rect_box(50, 50, 320, 190, "#D32F2F", "P0 - 立即启动"))
    p0 = ["处方前置审核", "患者全景画像", "历史数据挖掘", "管理视角报表", "异常检测Agent", "用药依从性", "健康计划"]
    for j, item in enumerate(p0):
        items.append(f'<text x="70" y="{95+j*25}" class="d-text-sm" fill="#FFFFFF" font-size="12">{item}</text>')

    # P1
    items.append(rect_box(410, 50, 320, 190, "#E65100", "P1 - 短期"))
    p1 = ["智能预问诊闭环", "群体差异分析", "数据质量治理", "多病共治增强", "药物相互作用", "语音交互", "循证医学"]
    for j, item in enumerate(p1):
        items.append(f'<text x="430" y="{95+j*25}" class="d-text-sm" fill="#FFFFFF" font-size="12">{item}</text>')

    # P2
    items.append(rect_box(50, 280, 320, 190, "#E7B83E", "P2 - 中期"))
    p2 = ["一老一小健康", "影像分析Agent", "家庭健康管家", "医生Copilot", "可穿戴集成"]
    for j, item in enumerate(p2):
        items.append(f'<text x="70" y="{325+j*25}" class="d-text-sm" fill="#2F2E2A" font-size="12">{item}</text>')

    # P3
    items.append(rect_box(410, 280, 320, 190, "#7BA7B9", "P3 - 长期"))
    p3 = ["临床试验匹配", "自我进化系统", "SaaS平台", "保险版"]
    for j, item in enumerate(p3):
        items.append(f'<text x="430" y="{325+j*25}" class="d-text-sm" fill="#2F2E2A" font-size="12">{item}</text>')

    return svg_wrapper(w, h, '\n'.join(items))


# ─── §16.1 / §14.1: 生态全景 ──────────────────────────────────────────
def diagram_ecosystem():
    w, h = 780, 480
    cx, cy = 390, 240
    items = []

    items.append(rect_box(cx-100, cy-35, 200, 70, "#5E8B5A", "WellHealth", "多Agent平台"))

    sectors = [
        ("医疗端", "#1565C0", (cx, cy-160), ["互联网医院", "HIS/EMR", "体检中心"]),
        ("医保端", "#D32F2F", (cx+170, cy-100), ["国家医保", "省市医保", "商保公司"]),
        ("药房端", "#E7B83E", (cx+170, cy+80), ["连锁药店", "单体药店", "药企"]),
        ("设备端", "#7BA7B9", (cx, cy+170), ["血糖仪", "血压计", "智能手环"]),
        ("第三方", "#795548", (cx-170, cy+80), ["LLM厂商", "地图/短信", "语音服务"]),
        ("监管端", "#5A9E87", (cx-170, cy-100), ["卫健委", "疾控中心", "食药监"]),
    ]

    for name, color, (sx, sy), subs in sectors:
        dx, dy = sx - cx, sy - cy
        length = (dx*dx + dy*dy)**0.5
        nx, ny = dx/length, dy/length
        items.append(f'<line x1="{cx+100*nx}" y1="{cy+35*ny}" x2="{sx}" y2="{sy}" class="d-arr-thick" stroke="{color}"/>')
        items.append(rect_box(sx-60, sy-40, 120, 80, color, name))
        for j, sub in enumerate(subs):
            items.append(f'<text x="{sx}" y="{sy+5+j*18}" text-anchor="middle" class="d-text-sm" fill="#FFFFFF" opacity="0.85" font-size="10">{sub}</text>')

    return svg_wrapper(w, h, '\n'.join(items))


# ─── §17.1: 路线图 ──────────────────────────────────────────────────────
def diagram_roadmap():
    w, h = 820, 300
    items = []

    items.append(f'<rect x="40" y="100" width="740" height="8" rx="4" fill="#DDCFB0"/>')

    phases = [
        ("Phase 0-1", "Week 1-8", "#D32F2F", ["基础设施", "处方前置审核", "患者全景画像", "数据挖掘看板", "异常检测", "用药依从性", "健康计划"]),
        ("Phase 2", "Week 9-16", "#E65100", ["预问诊闭环", "群体差异分析", "数据质量治理", "语音接入", "互联网医院", "共病协商"]),
        ("Phase 3", "Week 17-24", "#E7B83E", ["老年健康", "儿童健康", "影像分析", "可穿戴集成", "医生Copilot", "家庭健康管家"]),
        ("Phase 4", "Week 25-40", "#5E8B5A", ["自我进化", "多租户SaaS", "保险版", "临床试验", "持续优化"]),
    ]

    for i, (title, period, color, items_list) in enumerate(phases):
        x = 60 + i * 185
        items.append(f'<circle cx="{x+70}" cy="104" r="10" fill="{color}" filter="url(#shadow)"/>')
        items.append(f'<text x="{x+70}" y="108" text-anchor="middle" class="d-text-sm" fill="#FFFFFF" font-size="9">{i+1}</text>')
        items.append(rect_box(x, 20, 140, 30, color, f"{title} ({period})"))
        items.append(arrow_v(x+70, 50, 100))
        for j, item in enumerate(items_list):
            ypos = 130 + j * 22
            items.append(f'<rect x="{x+10}" y="{ypos}" width="160" height="18" rx="9" fill="#FFFFFF" stroke="{color}" stroke-width="1" opacity="0.8"/>')
            items.append(f'<text x="{x+90}" y="{ypos+13}" text-anchor="middle" class="d-text-sm" fill="#2F2E2A" font-size="10">{item}</text>')

    times = ["2026.06", "2026.09", "2026.12", "2027.03"]
    for i, t in enumerate(times):
        x = 60 + i * 185
        items.append(f'<text x="{x+70}" y="90" text-anchor="middle" class="d-text-sm" font-size="10" fill="#7F7D74">{t}</text>')

    return svg_wrapper(w, h, '\n'.join(items))


# ─── Markdown → HTML with diagram injection ──────────────────────────────────

DIAGRAM_KEYWORDS = {
    "延伸方向一览": diagram_overview,
    "3.2.1": diagram_monitor,
    "4.2.1": diagram_plan_coordinator,
    "5.2.1": diagram_family,
    "11.1": diagram_priority_matrix,
    "12.3.1": diagram_prescription_review,
    "12.3.5": diagram_closed_loop,
    "12.3.2": None,  # will use ASCII
    "16.1": diagram_ecosystem,
    "14.1": diagram_ecosystem,
    "17.1": diagram_roadmap,
}

# Track which diagram has been injected per section content
_diagram_injected_for = set()


def parse_and_convert(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    sections = []
    current_sec_lines = []
    current_sec_title = ""
    in_code_block = False

    def flush():
        nonlocal current_sec_title
        if current_sec_title:
            content = ''.join(current_sec_lines)
            sections.append({'title': current_sec_title, 'content': content})
            current_sec_lines.clear()

    for line in lines:
        if line.startswith('## ') and not line.startswith('### '):
            flush()
            current_sec_title = line[3:].strip()
        else:
            current_sec_lines.append(line)
    flush()

    return sections


def markdown_to_html(text, section_title=""):
    """Convert markdown text block to HTML."""
    global _diagram_injected_for
    lines = text.split('\n')
    html_parts = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        if line.strip() == '---':
            html_parts.append('<hr>')
            i += 1
            continue

        if line.strip().startswith('```'):
            lang = line.strip()[3:].strip()
            code_lines = []
            i += 1
            while i < n and not lines[i].strip().startswith('```'):
                cl = lines[i].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                code_lines.append(cl)
                i += 1
            i += 1
            code_content = ''.join(code_lines).rstrip('\n')
            lang_attr = f' class="language-{lang}"' if lang else ''
            html_parts.append(f'<pre><code{lang_attr}>{code_content}</code></pre>')
            continue

        if not line.strip():
            html_parts.append('')
            i += 1
            continue

        if line.strip().startswith('|') and i + 1 < n and re.match(r'^\|[-:| ]+\|$', lines[i+1].strip()):
            table_html = ['<table>']
            cells = [c.strip() for c in line.strip().split('|')[1:-1]]
            table_html.append('<thead><tr>' + ''.join(f'<th>{inline_html(c)}</th>' for c in cells) + '</tr></thead>')
            i += 2
            table_html.append('<tbody>')
            while i < n and lines[i].strip().startswith('|'):
                cells = [c.strip() for c in lines[i].strip().split('|')[1:-1]]
                table_html.append('<tr>' + ''.join(f'<td>{inline_html(c)}</td>' for c in cells) + '</tr>')
                i += 1
            table_html.append('</tbody></table>')
            html_parts.append('\n'.join(table_html))
            continue

        if line.startswith('### ') or line.startswith('#### '):
            prefix = '#### ' if line.startswith('#### ') else '### '
            title_text = line[len(prefix):].strip()
            title_html = inline_html(title_text)
            tag = 'h4' if line.startswith('#### ') else 'h3'
            html_parts.append(f'<{tag}>{title_html}</{tag}>')
            i += 1

            # Check if this heading matches a diagram keyword (longest match first)
            diagram_key = None
            sorted_kw = sorted(DIAGRAM_KEYWORDS.keys(), key=len, reverse=True)
            for kw in sorted_kw:
                if kw in title_text:
                    diagram_key = kw
                    break

            if diagram_key and diagram_key not in _diagram_injected_for:
                _diagram_injected_for.add(diagram_key)
                func = DIAGRAM_KEYWORDS[diagram_key]
                if func is None:
                    continue
                svg = func()
                html_parts.append(svg)

                # Skip ASCII diagram blocks that follow
                skip_count = 0
                while i < n:
                    s = lines[i].strip()
                    if not s:
                        i += 1
                        continue
                    if any(s.startswith(c) for c in ['├', '└', '│', '┌', '┬', '┐', '─', '`']):
                        i += 1
                        skip_count += 1
                        continue
                    if s.startswith('—') or s == '---':
                        i += 1
                        continue
                    if s.startswith('```'):
                        i += 1
                        while i < n and not lines[i].strip().startswith('```'):
                            i += 1
                        i += 1
                        skip_count += 1
                        continue
                    if s.startswith('### ') or s.startswith('#### ') or s.startswith('- ') or s.startswith('|') or s.startswith('>'):
                        break
                    if skip_count > 0 and not any(c in s for c in ['┌', '─', '┐', '│', '└', '├', '┤']):
                        break
                    i += 1
                    skip_count += 1
                continue
            continue

        if line.startswith('#### '):
            title = inline_html(line[5:].strip())
            html_parts.append(f'<h4>{title}</h4>')
            i += 1
            continue

        if line.strip().startswith('> '):
            bq_lines = []
            while i < n and lines[i].strip().startswith('> '):
                bq_lines.append(lines[i].strip()[2:])
                i += 1
            html_parts.append(f'<blockquote>{"<br>".join(bq_lines)}</blockquote>')
            continue

        stripped = line.strip()
        if any(stripped.startswith(c) for c in ['├', '└', '│', '┌', '┬', '┐', '─']):
            pre_lines = []
            while i < n and lines[i].strip():
                pre_lines.append(lines[i].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
                i += 1
            html_parts.append('<pre class="tree">' + '\n'.join(pre_lines) + '</pre>')
            continue

        # Check for pipe-style list items (|-- AgentName | Desc |)
        if stripped.startswith('|') and stripped.endswith('|') and stripped.count('|') >= 3:
            # Could be a table that wasn't caught above, or a description list
            # Simple fix: treat as paragraph
            pass

        if stripped.startswith('- '):
            ul_lines = []
            while i < n and lines[i].strip().startswith('- '):
                ul_lines.append(lines[i].strip()[2:])
                i += 1
            html_parts.append('<ul>\n' + '\n'.join(f'<li>{inline_html(l)}</li>' for l in ul_lines) + '\n</ul>')
            continue

        html_parts.append(f'<p>{inline_html(line.strip())}</p>')
        i += 1

    return '\n'.join(html_parts)


def inline_html(text):
    """Convert inline markdown: **bold**, *italic*, `code`"""
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    return text


TITLE_MAP = {
    '1. 分析框架': '1. 分析框架',
    '2. 延伸方向一览': '2. 方向一览',
    '3. 方向一：从被动应答到主动干预': '3. 被动→主动',
    '4. 方向二：从单次咨询到长期健康管理': '4. 单次→长期',
    '5. 方向三：从患者个体到家庭生态': '5. 个体→家庭',
    '6. 方向四：从文本对话到多模态交互': '6. 文本→多模态',
    '7. 方向五：从通用 LLM 到专业医学推理': '7. 通用→专业',
    '8. 方向六：从单一应用到平台生态': '8. 单一→平台',
    '9. 方向七：从人工反馈到自我进化': '9. 自我进化',
    '10. 方向八：从治疗到预防的三级预防体系': '10. 三级预防',
    '11. 延伸实施优先级矩阵（含医生反馈驱动项）': '11. 优先级矩阵',
    '12. 方向九：从健康管理到"三医联动"生态（医生反馈驱动）': '12. 三医联动',
    '13. 附录：Agent 扩展全景图 (含医生反馈驱动项)': '13. Agent全景图',
    '14. 目标用户群与服务矩阵': '14. 用户矩阵',
    '15. 应用终端规划': '15. 终端规划',
    '16. 外部生态接入规划': '16. 生态接入',
    '17. 实施开发计划': '17. 实施计划',
}


CSS = """
:root {
  --primary: #5E8B5A;
  --primary-light: #7CA878;
  --primary-dark: #4C7048;
  --bg: #FCF8F0;
  --bg-card: #FFFFFF;
  --text: #2F2E2A;
  --text-secondary: #7F7D74;
  --border: #DDCFB0;
  --border-light: #E8DFD0;
  --accent: #E7B83E;
  --header-bg: #5E8B5A;
  --sidebar-width: 220px;
  --shadow: 0 2px 12px rgba(0,0,0,0.08);
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  background: var(--bg);
  color: var(--text);
  display: flex;
  height: 100vh;
  overflow: hidden;
}
.sidebar {
  width: var(--sidebar-width);
  background: var(--bg-card);
  border-right: 1px solid var(--border-light);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow-y: auto;
}
.sidebar-header {
  padding: 20px 16px;
  background: var(--header-bg);
  color: #fff;
  text-align: center;
}
.sidebar-header h1 { font-size: 18px; font-weight: 600; }
.sidebar-header .subtitle { font-size: 12px; opacity: 0.85; margin-top: 4px; }
.tab-list { list-style: none; padding: 8px 0; }
.tab-item {
  padding: 10px 16px; cursor: pointer; font-size: 13px; color: var(--text-secondary);
  border-left: 3px solid transparent; transition: all 0.2s; line-height: 1.4;
}
.tab-item:hover { background: var(--bg); color: var(--text); }
.tab-item.active {
  color: var(--primary); background: #E8F0E6; border-left-color: var(--primary); font-weight: 600;
}
.tab-item .tab-num {
  display: inline-block; width: 22px; height: 22px; line-height: 22px; text-align: center;
  background: var(--border-light); border-radius: 50%; font-size: 11px; margin-right: 8px;
  color: var(--text-secondary);
}
.tab-item.active .tab-num { background: var(--primary); color: #fff; }
.main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.toolbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 24px; background: var(--bg-card); border-bottom: 1px solid var(--border-light);
  flex-shrink: 0;
}
.toolbar .page-info { font-size: 14px; color: var(--text-secondary); }
.toolbar .page-info strong { color: var(--text); }
.nav-buttons { display: flex; gap: 8px; }
.nav-btn {
  padding: 6px 16px; border: 1px solid var(--border); border-radius: 6px;
  background: var(--bg-card); cursor: pointer; font-size: 13px; color: var(--text);
  transition: all 0.2s;
}
.nav-btn:hover { background: var(--bg); border-color: var(--primary); color: var(--primary); }
.nav-btn:disabled { opacity: 0.4; cursor: default; }
.content-area { flex: 1; overflow-y: auto; padding: 32px 40px; }
.slide { display: none; max-width: 960px; margin: 0 auto; }
.slide.active { display: block; }
.slide h2 {
  font-size: 28px; color: var(--primary-dark); margin-bottom: 24px;
  padding-bottom: 12px; border-bottom: 2px solid var(--primary-light);
}
.slide h3 { font-size: 20px; color: var(--text); margin: 24px 0 12px; }
.slide h4 { font-size: 17px; color: var(--text); margin: 20px 0 10px; }
.slide p { font-size: 15px; line-height: 1.7; margin: 8px 0; color: var(--text); }
.slide p code, .slide li code {
  background: #E8F0E6; padding: 2px 6px; border-radius: 4px; font-size: 13px;
  font-family: "SF Mono", "Fira Code", "Consolas", monospace;
}
.slide pre {
  background: #1E1E2E; color: #CDD6F4; padding: 16px 20px; border-radius: 10px;
  overflow-x: auto; font-size: 13px; line-height: 1.5;
  font-family: "SF Mono", "Fira Code", "Consolas", monospace; margin: 12px 0; tab-size: 2;
}
.slide pre code { background: none; padding: 0; color: inherit; font-size: inherit; }
.slide pre.tree { background: #F5F0E8; color: var(--text); border: 1px solid var(--border-light); line-height: 1.4; }
.slide table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 14px; }
.slide th, .slide td { padding: 10px 14px; border: 1px solid var(--border-light); text-align: left; }
.slide th { background: var(--primary); color: #fff; font-weight: 600; white-space: nowrap; }
.slide tr:nth-child(even) { background: #FAF8F3; }
.slide tr:hover { background: #E8F0E6; }
.slide blockquote {
  border-left: 4px solid var(--primary-light); padding: 12px 16px; margin: 12px 0;
  background: #F5F8F4; border-radius: 0 8px 8px 0; font-size: 14px; color: var(--text-secondary);
}
.slide ul, .slide ol { margin: 8px 0; padding-left: 24px; }
.slide li { font-size: 15px; line-height: 1.6; margin: 4px 0; }
.slide hr { border: none; border-top: 2px solid var(--border-light); margin: 32px 0; }
.slide .toc-list { columns: 2; column-gap: 32px; list-style: none; padding: 0; }
.slide .toc-list li { break-inside: avoid; padding: 6px 0; border-bottom: 1px dotted var(--border-light); }
.slide .toc-list a { color: var(--primary); text-decoration: none; font-size: 14px; }
.slide .toc-list a:hover { text-decoration: underline; }

/* Diagram styles */
.diagram {
  display: block; max-width: 100%; height: auto; margin: 16px auto;
  border-radius: 12px; background: #FFFFFF; box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
@media (max-width: 768px) {
  .sidebar { width: 60px; }
  .sidebar-header h1, .sidebar-header .subtitle, .tab-item span:not(.tab-num) { display: none; }
  .tab-item { text-align: center; padding: 12px 8px; }
  .tab-item .tab-num { margin-right: 0; }
  .content-area { padding: 16px; }
  .slide .toc-list { columns: 1; }
}
"""


def build_html(sections):
    global _diagram_injected_for
    _diagram_injected_for = set()
    tabs_html = ""
    slides_html = ""

    for idx, sec in enumerate(sections):
        title = sec['title']
        tab_label = TITLE_MAP.get(title, title)
        active = " active" if idx == 0 else ""

        tabs_html += f'''<li class="tab-item{active}" data-tab="{idx}" onclick="goTo({idx})"><span class="tab-num">{idx}</span><span>{tab_label}</span></li>\n'''

        slides_html += f'<div class="slide{active}" id="slide-{idx}">\n<div class="slide-inner">\n'

        if idx == 0:
            slides_html += f'<h2>{title}</h2>\n<ul class="toc-list">\n'
            for j, tab in enumerate(sections):
                if j == 0:
                    continue
                t = tab['title']
                slides_html += f'<li><a href="javascript:goTo({j})">{t}</a></li>\n'
            slides_html += '</ul>\n'
        else:
            slides_html += f'<h2>{title}</h2>\n'
            # Check h2-level diagram match (overview in section 2)
            h2_svg = ""
            for kw, func in DIAGRAM_KEYWORDS.items():
                if kw in title and func is not None:
                    h2_svg = func()
                    break
            if h2_svg:
                slides_html += h2_svg + '\n'
            slides_html += markdown_to_html(sec['content'], title)

        slides_html += '</div></div>\n'

    # Build full HTML
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WellHealth 多 Agent 架构应用延伸分析报告</title>
<style>
{CSS}
</style>
</head>
<body>

<div class="sidebar">
  <div class="sidebar-header">
    <h1>WellHealth</h1>
    <div class="subtitle">多Agent延伸分析 v2.0</div>
  </div>
  <ul class="tab-list" id="tabList">
    {tabs_html}
  </ul>
</div>

<div class="main">
  <div class="toolbar">
    <div class="page-info">第 <strong id="currentPage">1</strong> / <span id="totalPages">{len(sections)}</span> 页</div>
    <div class="nav-buttons">
      <button class="nav-btn" onclick="prevSlide()" id="prevBtn">‹ 上一页</button>
      <button class="nav-btn" onclick="nextSlide()" id="nextBtn">下一页 ›</button>
    </div>
  </div>
  <div class="content-area">
    {slides_html}
  </div>
</div>

<script>
let currentSlide = 0;
const totalSlides = {len(sections)};

function goTo(idx) {{
  if (idx < 0 || idx >= totalSlides) return;
  document.querySelectorAll('.slide').forEach(s => s.classList.remove('active'));
  document.getElementById('slide-' + idx).classList.add('active');
  document.querySelectorAll('.tab-item').forEach(t => t.classList.remove('active'));
  const tab = document.querySelectorAll('.tab-item[data-tab="' + idx + '"]');
  if (tab.length) {{ tab[0].classList.add('active'); tab[0].scrollIntoView({{ block: 'nearest' }}); }}
  document.getElementById('currentPage').textContent = idx + 1;
  document.getElementById('prevBtn').disabled = idx === 0;
  document.getElementById('nextBtn').disabled = idx === totalSlides - 1;
  currentSlide = idx;
  document.querySelector('.content-area').scrollTop = 0;
}}
function nextSlide() {{ goTo(currentSlide + 1); }}
function prevSlide() {{ goTo(currentSlide - 1); }}
document.addEventListener('keydown', function(e) {{
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {{ e.preventDefault(); nextSlide(); }}
  if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {{ e.preventDefault(); prevSlide(); }}
  if (e.key === 'Home') {{ e.preventDefault(); goTo(0); }}
  if (e.key === 'End') {{ e.preventDefault(); goTo(totalSlides - 1); }}
}});
goTo(0);
</script>
</body>
</html>'''

    return html


def main():
    md_path = r'E:\workspace-llm\wellhealth\docs\multi-agent-extension-report.md'
    out_path = r'E:\workspace-llm\wellhealth\docs\multi-agent-extension-report.html'

    sections = parse_and_convert(md_path)
    print(f'Parsed {len(sections)} sections')

    html = build_html(sections)

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)

    size = len(html.encode('utf-8'))
    svg_count = html.count('<svg class="diagram"')
    print(f'\nHTML written: {out_path}')
    print(f'Size: {size:,} bytes ({size/1024:.1f} KB)')
    print(f'Visual diagrams embedded: {svg_count}')


if __name__ == '__main__':
    main()
