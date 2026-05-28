#!/usr/bin/env python3
"""Enhance the HTML report by replacing ASCII diagrams with visual SVG/HTML components."""

import re
import os

# ─── SVG / visual component builders ───────────────────────────────────────────

def svg_wrapper(width, height, content):
    return f'''<svg class="diagram" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
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

def rect_box(x, y, w, h, color, label, sub="", cls="d-box"):
    extra = ""
    if sub:
        extra = f'<text x="{x+w/2}" y="{y+h-10}" text-anchor="middle" class="d-text-sm">{sub}</text>'
    return f'''<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" class="{cls}" filter="url(#shadow)"/>
<text x="{x+w/2}" y="{y+h/2+5}" text-anchor="middle" class="d-title" dominant-baseline="middle">{label}</text>
{extra}'''

def arrow(x1, y1, x2, y2, cls="d-arr"):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{cls}"/>'

def arrow_h(x1, x2, y, cls="d-arr"):
    return arrow(x1, y, x2, y, cls)

def arrow_v(x, y1, y2, cls="d-arr"):
    return arrow(x, y1, x, y2, cls)

# ─── §2: 延伸方向一览 ──────────────────────────────────────────────────────
def diagram_overview():
    """WellHealth center hub + 8 direction branches with 3 sub-items each"""
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
    # Central hub
    items.append(f'<rect x="{cx-70}" y="{cy-35}" width="140" height="70" fill="#5E8B5A" class="d-box" filter="url(#shadow)"/>')
    items.append(f'<text x="{cx}" y="{cy-7}" text-anchor="middle" class="d-title" font-size="16">WellHealth</text>')
    items.append(f'<text x="{cx}" y="{cy+15}" text-anchor="middle" class="d-text-sm" fill="#FFFFFF">多Agent基座</text>')

    for i, (name, color, subs) in enumerate(dirs):
        angle = i * 45 - 90  # start from top
        rad = 3.14159 * angle / 180
        r1, r2 = 100, 185
        x1 = cx + r1 * __import__('math').cos(rad) if abs(__import__('math').cos(rad)) > 0.01 else cx
        y1 = cy + r1 * __import__('math').sin(rad) if abs(__import__('math').sin(rad)) > 0.01 else cy
        x2 = cx + r2 * __import__('math').cos(rad)
        y2 = cy + r2 * __import__('math').sin(rad)

        # Arrow from center to direction
        dx = (x2 - x1)
        dy = (y2 - y1)
        length = (dx*dx + dy*dy) ** 0.5
        if length > 0:
            nx, ny = dx/length, dy/length
            items.append(f'<line x1="{x1+70*nx}" y1="{y1+35*ny}" x2="{x2-45*nx}" y2="{y2-20*ny}" class="d-arr-thick" stroke="{color}"/>')

        # Direction label
        items.append(f'<rect x="{x2-40}" y="{y2-15}" width="80" height="30" rx="15" ry="15" fill="{color}" filter="url(#shadow)"/>')
        items.append(f'<text x="{x2}" y="{y2+5}" text-anchor="middle" class="d-title" font-size="12">{name}</text>')

        # Sub-items (smaller, further out)
        for j, (s1, s2, s3) in enumerate(subs):
            r3 = 245
            x3 = cx + r3 * __import__('math').cos(rad + (j-1)*0.15)
            y3 = cy + r3 * __import__('math').sin(rad + (j-1)*0.15)
            items.append(f'<line x1="{x2}" y1="{y2}" x2="{x3}" y2="{y3}" stroke="{color}" stroke-width="1.5" stroke-dasharray="3,3"/>')
            items.append(f'<rect x="{x3-28}" y="{y3-8}" width="56" height="20" rx="10" ry="10" fill="{color}" opacity="0.2"/>')
            items.append(f'<text x="{x3}" y="{y3+4}" text-anchor="middle" class="d-text-sm" fill="{color}" font-size="10">{s1}</text>')

    return svg_wrapper(w, h, '\n'.join(items))


# ─── §3.2.1: MonitorAgent 协作 ─────────────────────────────────────────────
def diagram_monitor():
    w, h = 800, 320
    cx = 400
    items = []

    # Center: MonitorAgent
    items.append(rect_box(cx-70, 100, 140, 60, "#5E8B5A", "MonitorAgent", "协调者"))
    
    # 4 sub-agents around
    agents = [
        (cx-200, 30, "#E7B83E", "DataAnalyzer", "数据分析"),
        (cx+60, 30, "#CD8B5B", "AlertAssessor", "风险判定"),
        (cx-200, 200, "#7BA7B9", "Intervention", "干预执行"),
        (cx+60, 200, "#795548", "Notification", "通知推送"),
    ]
    for x, y, color, name, sub in agents:
        items.append(rect_box(x, y, 130, 44, color, name, sub))
        # Arrow to/from center
        if y < 100:  # top
            items.append(arrow_v(x+65, y+44, 100))
        else:  # bottom
            items.append(arrow_v(cx, 160, y))

    # Top: 定时触发
    items.append(rect_box(cx-60, 0, 120, 30, "#4C7048", "⏰ 定时触发"))
    items.append(arrow_v(cx, 30, 100))

    # Bottom: 行动指令
    items.append(rect_box(cx-60, h-30, 120, 30, "#4C7048", "📤 分发行动指令"))
    items.append(arrow_v(cx, h-60, h-30))
    
    # Left/right arrows
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

    # Input
    items.append(rect_box(cx-130, 0, 260, 36, "#4C7048", "📋 患者健康档案 + 历史数据 + 个人偏好"))
    items.append(arrow_v(cx, 36, 70))

    # PlanCoordinator
    items.append(rect_box(cx-80, 70, 160, 50, "#5E8B5A", "PlanCoordinator", "接收+分发"))
    items.append(arrow_v(cx-60, 120, 170))
    items.append(arrow_v(cx-20, 120, 170))
    items.append(arrow_v(cx+20, 120, 170))
    items.append(arrow_v(cx+60, 120, 170))

    # 4 specialist agents in a row
    agents = [
        (cx-220, 170, "#CD8B5B", "临床目标\nAgent"),
        (cx-70, 170, "#E7B83E", "营养方案\nAgent"),
        (cx+80, 170, "#7BA7B9", "运动方案\nAgent"),
        (cx+230, 170, "#795548", "心理支持\nAgent"),
    ]
    for x, y, color, label in agents:
        items.append(rect_box(x, y, 110, 50, color, label))
        items.append(arrow_v(x+55, y+50, 250))

    # PlanValidator
    items.append(rect_box(cx-100, 250, 200, 50, "#5A9E87", "PlanValidator", "质量门控 - 冲突检测"))
    items.append(arrow_v(cx, 300, 360))

    # Output
    items.append(rect_box(cx-140, 360, 280, 50, "#1565C0", "📄 综合健康计划", "3个月目标 + 每周计划 + 评估指标"))
    
    return svg_wrapper(w, h, '\n'.join(items))


# ─── §5.2.1: FamilyHealth ────────────────────────────────────────────────
def diagram_family():
    w, h = 780, 380
    cx = 390
    items = []

    # Header
    items.append(rect_box(cx-150, 0, 300, 50, "#5E8B5A", "👨‍👩‍👧‍👦 FamilyHealth Agent", "家庭的健康管家"))
    items.append(arrow_v(cx, 50, 90))

    # 3 family members
    members = [
        (cx-240, 90, "#CD8B5B", "父亲 - 糖尿病", "Diabetes Agent"),
        (cx-20, 90, "#7BA7B9", "母亲 - 高血压", "Hypertension Agent"),
        (cx+200, 90, "#5A9E87", "子女 - 健康管理", "General Agent"),
    ]
    for x, y, color, title, sub in members:
        items.append(rect_box(x, y, 200, 70, color, title, sub))

    items.append(arrow_v(cx-140, 160, 200))
    items.append(arrow_v(cx, 160, 200))
    items.append(arrow_v(cx+140, 160, 200))

    # Shared resources
    items.append(rect_box(cx-240, 200, 620, 120, "#E8F0E6", "家庭共享资源", "", "#F5F8F4"))
    # Change the box to be a frame
    items[-1] = items[-1].replace('class="d-box"', 'rx="10" ry="10"')
    
    resources = ["🍽️ 家庭食谱库", "🏃 家庭活动计划", "💬 家庭关怀消息", "📊 家庭健康报告"]
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

    # Top: Patient → Doctor → Prescription
    items.append(rect_box(60, 0, 120, 36, "#4C7048", "患者"))
    items.append(rect_box(240, 0, 120, 36, "#7BA7B9", "医生开方"))
    items.append(rect_box(420, 0, 120, 36, "#E7B83E", "处方提交"))
    items.append(arrow_h(180, 240, 18))
    items.append(arrow_h(360, 420, 18))

    # Coordinator
    items.append(arrow_v(cx+90, 36, 80))
    items.append(rect_box(cx-130, 80, 260, 46, "#5E8B5A", "PrescriptionReviewCoordinator", "编排器 - 协调3层审核"))
    items.append(arrow_v(cx-60, 126, 170))
    items.append(arrow_v(cx, 126, 170))
    items.append(arrow_v(cx+60, 126, 170))

    # 3 layers
    layers = [
        (cx-240, 170, "#CD8B5B", "Layer 1: 规则引擎", "相互作用 · 禁忌症 · 重复用药 · 剂量范围"),
        (cx-20, 170, "#1565C0", "Layer 2: 医保政策", "目录匹配 · 报销比例 · 限制条件 · 替代推荐"),
        (cx+200, 170, "#5A9E87", "Layer 3: AI个体化", "年龄/体重/肾功能 · 剂量调整 · SHAP解释"),
    ]
    for x, y, color, title, sub in layers:
        items.append(rect_box(x, y, 200, 110, color, title))
        items.append(f'<text x="{x+100}" y="{y+75}" text-anchor="middle" class="d-text-sm" fill="#FFFFFF" opacity="0.9">{sub}</text>')

    # Merge arrows down
    for x in [cx-140, cx+100, cx+340]:
        items.append(arrow_v(x+30, 280, 350))

    # Result
    items.append(rect_box(cx-200, 370, 400, 80, "#5E8B5A", "审核结果汇总", "✅ 通过  |  ⚠️ 警告(可开)  |  ❌ 拦截(需修改)"))

    return svg_wrapper(w, h, '\n'.join(items))


# ─── §12.3.5: 闭环管理流程 ─────────────────────────────────────────────────
def diagram_closed_loop():
    w, h = 820, 300
    items = []

    steps = [
        ("Step 1\n预问诊", "#7BA7B9", "TriageAgent\n症状→科室"),
        ("Step 2\n线上问诊", "#5E8B5A", "BridgeAgent\n对接互联网医院"),
        ("Step 3\n处方流转", "#CD8B5B", "ReviewAgent\n3层审核"),
        ("Step 4\n用药管理", "#E7B83E", "AdherenceAgent\n用药提醒→打卡"),
        ("Step 5\n随访", "#795548", "FollowUpAgent\n复诊提醒→评价"),
        ("Step 6\n效果评估", "#1565C0", "HealthPlanAgent\n指标追踪→调整"),
    ]

    for i, (title, color, sub) in enumerate(steps):
        x = 20 + i * 135
        # Step box
        items.append(rect_box(x, 20, 115, 80, color, title))
        items.append(f'<text x="{x+57}" y="{y+55}" text-anchor="middle" class="d-text-sm" fill="#FFFFFF" opacity="0.9" font-size="10">{sub.replace(chr(10), chr(10))}</text>')
        # Arrow between steps
        if i < len(steps) - 1:
            items.append(arrow_h(x+115, x+135, 60))

    # Bottom: full loop label
    items.append(rect_box(100, 200, 620, 40, "#4C7048", "完整闭环: 症状→分诊→问诊→处方→购药→用药→随访→评估→调整"))

    # Top label
    items.append(rect_box(240, 0, 340, 26, "#5E8B5A", "🔄 Closed-Loop 全流程 Agent 协作"))
    
    return svg_wrapper(w, h, '\n'.join(items))


# ─── §11.1: 优先级矩阵 ────────────────────────────────────────────────────
def diagram_priority_matrix():
    w, h = 780, 540
    items = []

    # Title
    items.append(f'<text x="390" y="30" text-anchor="middle" class="d-text" font-size="16" font-weight="bold">延伸实施优先级矩阵</text>')
    items.append(f'<text x="700" y="30" text-anchor="end" class="d-text-sm">用户/商业价值 →</text>')
    items.append(f'<text x="20" y="280" text-anchor="middle" class="d-text-sm" transform="rotate(-90,20,280)">技术可行性 →</text>')

    # P0 - top left (high value, high feasibility)
    items.append(rect_box(50, 50, 320, 190, "#D32F2F", "P0 — 立即启动"))
    p0_items = [
        "★ 处方前置审核", "★ 患者全景画像", "★ 历史数据挖掘",
        "★ 管理视角报表", "异常检测Agent", "用药依从性", "健康计划"
    ]
    for j, item in enumerate(p0_items):
        y = 95 + j * 25
        items.append(f'<text x="70" y="{y}" class="d-text-sm" fill="#FFFFFF" font-size="12">{item}</text>')

    # P1 - top right (high feasibility, lower value)
    items.append(rect_box(410, 50, 320, 190, "#E65100", "P1 — 短期"))
    p1_items = [
        "★ 智能预问诊闭环", "★ 群体差异分析", "★ 数据质量治理",
        "★ 多病共治增强", "药物相互作用", "语音交互", "循证医学"
    ]
    for j, item in enumerate(p1_items):
        y = 95 + j * 25
        items.append(f'<text x="430" y="{y}" class="d-text-sm" fill="#FFFFFF" font-size="12">{item}</text>')

    # P2 - bottom left
    items.append(rect_box(50, 280, 320, 190, "#E7B83E", "P2 — 中期"))
    p2_items = [
        "★ 一老一小健康", "影像分析Agent", "家庭健康管家",
        "医生Copilot", "可穿戴集成"
    ]
    for j, item in enumerate(p2_items):
        y = 325 + j * 25
        items.append(f'<text x="70" y="{y}" class="d-text-sm" fill="#2F2E2A" font-size="12">{item}</text>')

    # P3 - bottom right
    items.append(rect_box(410, 280, 320, 190, "#7BA7B9", "P3 — 长期"))
    p3_items = [
        "临床试验匹配", "自我进化系统", "SaaS平台", "保险版"
    ]
    for j, item in enumerate(p3_items):
        y = 325 + j * 25
        items.append(f'<text x="430" y="{y}" class="d-text-sm" fill="#2F2E2A" font-size="12">{item}</text>')

    # Legend
    items.append(f'<text x="390" y="510" text-anchor="middle" class="d-text-sm" fill="#D32F2F">★ = 医生反馈直接驱动项</text>')
    items.append(f'<text x="390" y="530" text-anchor="middle" class="d-text-sm" fill="#7F7D74">高技术可行性 ← 矩阵 → 低技术可行性</text>')

    return svg_wrapper(w, h, '\n'.join(items))


# ─── §16.1 / §14.1: 生态 / 用户全景 ─────────────────────────────────
def diagram_ecosystem():
    w, h = 780, 480
    cx, cy = 390, 240
    items = []

    # Center hub
    items.append(rect_box(cx-100, cy-35, 200, 70, "#5E8B5A", "WellHealth", "多Agent平台"))

    # 6 sectors around
    sectors = [
        ("医疗端", "#1565C0", (cx, cy-160), ["互联网医院", "HIS/EMR", "体检中心"]),
        ("医保端", "#D32F2F", (cx+170, cy-100), ["国家医保", "省市医保", "商保公司"]),
        ("药房端", "#E7B83E", (cx+170, cy+80), ["连锁药店", "单体药店", "药企"]),
        ("设备端", "#7BA7B9", (cx, cy+170), ["血糖仪", "血压计", "智能手环"]),
        ("第三方", "#795548", (cx-170, cy+80), ["LLM厂商", "地图/短信", "语音服务"]),
        ("监管端", "#5A9E87", (cx-170, cy-100), ["卫健委", "疾控中心", "食药监"]),
    ]

    for name, color, (sx, sy), subs in sectors:
        # Connection line
        dx, dy = sx - cx, sy - cy
        length = (dx*dx + dy*dy)**0.5
        nx, ny = dx/length, dy/length
        items.append(f'<line x1="{cx+100*nx}" y1="{cy+35*ny}" x2="{sx}" y2="{sy}" class="d-arr-thick" stroke="{color}"/>')

        # Sector box
        items.append(rect_box(sx-60, sy-40, 120, 80, color, name))
        for j, sub in enumerate(subs):
            items.append(f'<text x="{sx}" y="{sy+5+j*18}" text-anchor="middle" class="d-text-sm" fill="#FFFFFF" opacity="0.85" font-size="10">{sub}</text>')

    return svg_wrapper(w, h, '\n'.join(items))


# ─── §17.1: 路线图 ──────────────────────────────────────────────────────
def diagram_roadmap():
    w, h = 820, 300
    items = []

    # Timeline bar
    items.append(f'<rect x="40" y="100" width="740" height="8" rx="4" fill="#DDCFB0"/>')

    phases = [
        ("Phase 0-1", "Week 1-8", "#D32F2F", [
            "基础设施",
            "处方前置审核",
            "患者全景画像",
            "数据挖掘看板",
            "异常检测",
            "用药依从性",
            "健康计划",
        ]),
        ("Phase 2", "Week 9-16", "#E65100", [
            "预问诊闭环",
            "群体差异分析",
            "数据质量治理",
            "语音接入",
            "医保API",
            "互联网医院",
            "共病协商",
        ]),
        ("Phase 3", "Week 17-24", "#E7B83E", [
            "老年健康",
            "儿童健康",
            "影像分析",
            "可穿戴集成",
            "医生Copilot",
            "家庭健康管家",
            "移动App启动",
        ]),
        ("Phase 4", "Week 25-40", "#5E8B5A", [
            "自我进化",
            "多租户SaaS",
            "保险版",
            "临床试验",
            "持续优化",
        ]),
    ]

    for i, (title, period, color, items_list) in enumerate(phases):
        x = 60 + i * 185

        # Phase marker on timeline
        items.append(f'<circle cx="{x+70}" cy="104" r="10" fill="{color}" filter="url(#shadow)"/>')
        items.append(f'<text x="{x+70}" y="108" text-anchor="middle" class="d-text-sm" fill="#FFFFFF" font-size="9">{i+1}</text>')

        # Phase title
        items.append(rect_box(x, 20, 140, 30, color, f"{title} ({period})"))

        # Vertical connection
        items.append(arrow_v(x+70, 50, 100))

        # Items below
        for j, item in enumerate(items_list):
            y = 130 + j * 22
            items.append(f'<rect x="{x+10}" y="{y}" width="160" height="18" rx="9" fill="#FFFFFF" stroke="{color}" stroke-width="1" opacity="0.8"/>')
            items.append(f'<text x="{x+90}" y="{y+13}" text-anchor="middle" class="d-text-sm" fill="#2F2E2A" font-size="10">{item}</text>')

    # Time axis labels
    times = ["2026.06", "2026.09", "2026.12", "2027.03"]
    for i, t in enumerate(times):
        x = 60 + i * 185
        items.append(f'<text x="{x+70}" y="90" text-anchor="middle" class="d-text-sm" font-size="10" fill="#7F7D74">{t}</text>')

    return svg_wrapper(w, h, '\n'.join(items))


# ─── HTML Enhancement ──────────────────────────────────────────────────────────

DIAGRAM_MAP = {
    # (heading_substring, diagram_func, position)
    "延伸方向一览": ("overview", diagram_overview),
    "3.2.1 健康预警监控": ("monitor", diagram_monitor),
    "4.2.1 个性化健康计划": ("plan_coordinator", diagram_plan_coordinator),
    "5.2.1 家庭健康管家": ("family", diagram_family),
    "12.3.1 处方前置审核": ("prescription_review", diagram_prescription_review),
    "12.3.5 智能预问诊与闭环": ("closed_loop", diagram_closed_loop),
    "延伸实施优先级矩阵": ("priority_matrix", diagram_priority_matrix),
    "外部生态接入规划": ("ecosystem", diagram_ecosystem),
    "实施开发计划": ("roadmap", diagram_roadmap),
    "用户生态全景图": ("ecosystem", diagram_ecosystem),
    "用户画像全景": ("ecosystem", diagram_ecosystem),
    "目标用户群与服务矩阵": ("ecosystem", diagram_ecosystem),
    "生态全景图": ("ecosystem", diagram_ecosystem),
    "14.1 用户画像全景": ("ecosystem", diagram_ecosystem),
    "16.1 生态全景图": ("ecosystem", diagram_ecosystem),
    "17.1 总体路线图": ("roadmap", diagram_roadmap),
}

def enhance_html(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Add diagram CSS
    diagram_css = '''
/* Diagram styles */
.diagram {
  display: block;
  max-width: 100%;
  height: auto;
  margin: 16px auto;
  border-radius: 12px;
  background: #FFFFFF;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
'''
    # Inject CSS before </style>
    html = html.replace('</style>', diagram_css + '\n</style>')

    # For each known diagram, find the slide containing the heading and replace
    # the first major pre block after that heading with the SVG
    
    # Strategy: split slides, process each one
    slides_pattern = re.compile(r'(<div class="slide[^"]*" id="slide-\d+">.*?</div>\s*</div>)', re.DOTALL)
    
    def process_slide(match):
        slide = match.group(1)
        # Extract heading
        h2_match = re.search(r'<h2>(.*?)</h2>', slide)
        if not h2_match:
            return slide
        
        heading = h2_match.group(1)
        
        # Check if this slide matches any known diagram
        diagram_key = None
        for key, (name, func) in DIAGRAM_MAP.items():
            if key in heading:
                diagram_key = key
                diagram_func = func
                break
        
        if diagram_key is None:
            return slide
        
        # Generate the SVG
        svg = diagram_func()
        
        # Find the first major pre block (diagram/code block) and replace it
        # Look for patterns: large pre blocks, tree pre blocks
        # Replace the largest pre block (likely the main diagram)
        pre_blocks = list(re.finditer(r'<pre[^>]*>.*?</pre>', slide, re.DOTALL))
        
        if not pre_blocks:
            return slide
        
        # For diagrams, replace the first major pre block (usually the biggest in the slide)
        # Actually, let's replace the first pre block that has box-drawing chars or is large
        replaced = False
        new_slide = slide
        
        for pre_match in pre_blocks:
            pre_content = pre_match.group()
            # Only replace if it contains box-drawing characters or is a large block
            if ('┌' in pre_content or '├' in pre_content or '│' in pre_content) and len(pre_content) > 200:
                # Replace this pre block with the SVG
                start = pre_match.start()
                end = pre_match.end()
                
                # Also remove any adjacent empty lines / paragraphs
                # The SVG replaces the pre block plus any surrounding whitespace/br/p
                before = new_slide[:start]
                after = new_slide[end:]
                
                new_slide = before + '\n' + svg + '\n' + after
                replaced = True
                break
        
        if not replaced and pre_blocks:
            # Fallback: replace the first pre block
            pre_match = pre_blocks[0]
            start = pre_match.start()
            end = pre_match.end()
            before = new_slide[:start]
            after = new_slide[end:]
            new_slide = before + '\n' + svg + '\n' + after
        
        return new_slide
    
    # Process all slides
    html = slides_pattern.sub(process_slide, html)
    
    # Also handle the user panorama (section 14) which uses a different pattern
    # The ASCII user panorama in section 14 is inside a regular flow
    # Let's replace it specifically
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Enhanced HTML written to {output_path}")

    # Count replacements
    svg_count = html.count('<svg class="diagram"')
    print(f"Total diagrams inserted: {svg_count}")

def main():
    input_path = r'E:\workspace-llm\wellhealth\docs\multi-agent-extension-report.html'
    output_path = r'E:\workspace-llm\wellhealth\docs\multi-agent-extension-report.html'
    
    enhance_html(input_path, output_path)

if __name__ == '__main__':
    main()
