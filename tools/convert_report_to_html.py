#!/usr/bin/env python3
"""Convert multi-agent-extension-report.md to self-contained HTML with PPT-style tab navigation."""

import re
import json

def parse_markdown(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Split into sections by ## headers (top-level sections)
    sections = []
    current_section = None
    current_lines = []

    def flush_section():
        nonlocal current_section, current_lines
        if current_section is not None:
            sections.append({
                'title': current_section,
                'content': ''.join(current_lines)
            })
        current_lines = []

    for line in lines:
        if line.startswith('## ') and not line.startswith('### '):
            flush_section()
            current_section = line[3:].strip()
        else:
            current_lines.append(line)
    flush_section()

    return sections


def md_to_html(md_text):
    """Convert markdown text block to HTML, handling code blocks, tables, lists, etc."""
    lines = md_text.split('\n')
    html_parts = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        # Horizontal rule
        if line.strip() == '---':
            html_parts.append('<hr>')
            i += 1
            continue

        # Fenced code block
        if line.strip().startswith('```'):
            lang = line.strip()[3:].strip()
            code_lines = []
            i += 1
            while i < n and not lines[i].strip().startswith('```'):
                # Escape HTML entities
                cl = lines[i].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                code_lines.append(cl)
                i += 1
            i += 1  # skip closing ```
            code_content = ''.join(code_lines)
            # Remove trailing newline for cleaner display
            if code_content.endswith('\n'):
                code_content = code_content[:-1]
            lang_attr = f' class="language-{lang}"' if lang else ''
            html_parts.append(f'<pre><code{lang_attr}>{code_content}</code></pre>')
            continue

        # Empty line
        if not line.strip():
            html_parts.append('')
            i += 1
            continue

        # Tables: starting with |---|
        if line.strip().startswith('|') and i + 1 < n and re.match(r'^\|[-:| ]+\|$', lines[i+1].strip()):
            table_html = ['<table>']
            # Header row
            cells = [c.strip() for c in line.strip().split('|')[1:-1]]
            table_html.append('  <thead><tr>' + ''.join(f'<th>{escape_html(c)}</th>' for c in cells) + '</tr></thead>')
            i += 2  # skip separator
            table_html.append('  <tbody>')
            while i < n and lines[i].strip().startswith('|'):
                cells = [c.strip() for c in lines[i].strip().split('|')[1:-1]]
                table_html.append('    <tr>' + ''.join(f'<td>{inline_to_html(c)}</td>' for c in cells) + '</tr>')
                i += 1
            table_html.append('  </tbody>')
            table_html.append('</table>')
            html_parts.append('\n'.join(table_html))
            continue

        # ### headers
        if line.startswith('### '):
            title = inline_to_html(line[4:].strip())
            html_parts.append(f'<h3>{title}</h3>')
            i += 1
            continue

        # #### headers
        if line.startswith('#### '):
            title = inline_to_html(line[5:].strip())
            html_parts.append(f'<h4>{title}</h4>')
            i += 1
            continue

        # Blockquote
        if line.strip().startswith('> '):
            bq_lines = []
            while i < n and lines[i].strip().startswith('> '):
                bq_lines.append(lines[i].strip()[2:])
                i += 1
            html_parts.append(f'<blockquote>{"<br>".join(bq_lines)}</blockquote>')
            continue

        # Unordered list (starts with - or ├ or └ or ┌ or │ or └)
        stripped = line.strip()
        if stripped.startswith('- ') or stripped.startswith('├') or stripped.startswith('└') or stripped.startswith('│') or stripped.startswith('┌') or stripped.startswith('┬') or stripped.startswith('┐'):
            # These are ASCII diagrams or tree structures — treat as pre
            pre_lines = []
            while i < n and lines[i].strip():
                pre_lines.append(lines[i].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
                i += 1
            html_parts.append(f'<pre class="tree">{chr(10).join(pre_lines)}</pre>')
            continue

        # Regular paragraph (with inline formatting)
        html_parts.append(f'<p>{inline_to_html(line.strip())}</p>')
        i += 1

    return '\n'.join(html_parts)


def escape_html(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def inline_to_html(text):
    """Convert inline markdown: **bold**, *italic*, `code`, and escape HTML entities."""
    # Escape HTML first
    text = escape_html(text)
    # Bold: **text** or __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
    # Italic: *text* (but not inside words)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    # Inline code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # Line breaks
    text = text.replace('  \n', '<br>')
    return text


def generate_html(sections):
    # Build tab content for each section
    tab_contents = []
    tab_labels = []

    # Manual mapping for section names to short tab labels
    title_map = {
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

    for sec in sections:
        title = sec['title']
        # Clean title for display
        tab_label = title_map.get(title, title)
        tab_labels.append(tab_label)

        # Determine section number for data attribute
        sec_num = title.split('.')[0] if '.' in title else '0'

        # Convert content
        html_content = md_to_html(sec['content'])
        tab_contents.append({
            'num': sec_num,
            'label': tab_label,
            'title': title,
            'content': html_content
        })

    return build_full_html(tab_contents)


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

/* Sidebar */
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

.tab-list {
  list-style: none;
  padding: 8px 0;
}
.tab-item {
  padding: 10px 16px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary);
  border-left: 3px solid transparent;
  transition: all 0.2s;
  line-height: 1.4;
}
.tab-item:hover { background: var(--bg); color: var(--text); }
.tab-item.active {
  color: var(--primary);
  background: #E8F0E6;
  border-left-color: var(--primary);
  font-weight: 600;
}
.tab-item .tab-num {
  display: inline-block;
  width: 22px;
  height: 22px;
  line-height: 22px;
  text-align: center;
  background: var(--border-light);
  border-radius: 50%;
  font-size: 11px;
  margin-right: 8px;
  color: var(--text-secondary);
}
.tab-item.active .tab-num {
  background: var(--primary);
  color: #fff;
}

/* Main content */
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-light);
  flex-shrink: 0;
}
.toolbar .page-info {
  font-size: 14px;
  color: var(--text-secondary);
}
.toolbar .page-info strong { color: var(--text); }
.nav-buttons { display: flex; gap: 8px; }
.nav-btn {
  padding: 6px 16px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg-card);
  cursor: pointer;
  font-size: 13px;
  color: var(--text);
  transition: all 0.2s;
}
.nav-btn:hover { background: var(--bg); border-color: var(--primary); color: var(--primary); }
.nav-btn:disabled { opacity: 0.4; cursor: default; }
.nav-btn:disabled:hover { background: var(--bg-card); border-color: var(--border); color: var(--text); }

.content-area {
  flex: 1;
  overflow-y: auto;
  padding: 32px 40px;
}

.slide {
  display: none;
  max-width: 960px;
  margin: 0 auto;
}
.slide.active { display: block; }

/* Typography */
.slide h2 {
  font-size: 28px;
  color: var(--primary-dark);
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 2px solid var(--primary-light);
}
.slide h3 {
  font-size: 20px;
  color: var(--text);
  margin: 24px 0 12px;
}
.slide h4 {
  font-size: 17px;
  color: var(--text);
  margin: 20px 0 10px;
}
.slide p {
  font-size: 15px;
  line-height: 1.7;
  margin: 8px 0;
  color: var(--text);
}
.slide p code, .slide li code {
  background: #E8F0E6;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  font-family: "SF Mono", "Fira Code", "Consolas", monospace;
}

/* Code blocks */
.slide pre {
  background: #1E1E2E;
  color: #CDD6F4;
  padding: 16px 20px;
  border-radius: 10px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.5;
  font-family: "SF Mono", "Fira Code", "Consolas", monospace;
  margin: 12px 0;
  tab-size: 2;
}
.slide pre code {
  background: none;
  padding: 0;
  color: inherit;
  font-size: inherit;
}
.slide pre.tree {
  background: #F5F0E8;
  color: var(--text);
  border: 1px solid var(--border-light);
  line-height: 1.4;
}

/* Tables */
.slide table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 14px;
}
.slide th, .slide td {
  padding: 10px 14px;
  border: 1px solid var(--border-light);
  text-align: left;
}
.slide th {
  background: var(--primary);
  color: #fff;
  font-weight: 600;
  white-space: nowrap;
}
.slide tr:nth-child(even) { background: #FAF8F3; }
.slide tr:hover { background: #E8F0E6; }

/* Blockquote */
.slide blockquote {
  border-left: 4px solid var(--primary-light);
  padding: 12px 16px;
  margin: 12px 0;
  background: #F5F8F4;
  border-radius: 0 8px 8px 0;
  font-size: 14px;
  color: var(--text-secondary);
}

/* Lists */
.slide ul, .slide ol {
  margin: 8px 0;
  padding-left: 24px;
}
.slide li {
  font-size: 15px;
  line-height: 1.6;
  margin: 4px 0;
}

/* Horizontal rule */
.slide hr {
  border: none;
  border-top: 2px solid var(--border-light);
  margin: 32px 0;
}

/* Emoji sizing */
.slide .emoji { font-size: 1.2em; }

/* TOC in first slide */
.slide .toc-list {
  columns: 2;
  column-gap: 32px;
  list-style: none;
  padding: 0;
}
.slide .toc-list li {
  break-inside: avoid;
  padding: 6px 0;
  border-bottom: 1px dotted var(--border-light);
}
.slide .toc-list a {
  color: var(--primary);
  text-decoration: none;
  font-size: 14px;
}
.slide .toc-list a:hover { text-decoration: underline; }

/* Responsive */
@media (max-width: 768px) {
  .sidebar { width: 60px; }
  .sidebar-header h1, .sidebar-header .subtitle, .tab-item span:not(.tab-num) { display: none; }
  .tab-item { text-align: center; padding: 12px 8px; }
  .tab-item .tab-num { margin-right: 0; }
  .content-area { padding: 16px; }
  .slide .toc-list { columns: 1; }
}
"""

def build_full_html(tab_contents):
    tabs_html = ''
    slides_html = ''
    toc_items = ''

    for idx, tc in enumerate(tab_contents):
        active = ' active' if idx == 0 else ''
        tabs_html += f'''<li class="tab-item{active}" data-tab="{idx}" onclick="goTo({idx})"><span class="tab-num">{tc['num']}</span><span>{tc['label']}</span></li>\n'''

        slides_html += f'''<div class="slide{active}" id="slide-{idx}">\n<div class="slide-inner">\n'''
        
        # For the first slide (TOC), override
        if idx == 0:
            slides_html += f'<h2>{tc["title"]}</h2>\n'
            # Parse TOC from content
            # Build TOC from tab_contents
            slides_html += '<ul class="toc-list">\n'
            for j, tab in enumerate(tab_contents):
                if j == 0: continue
                slides_html += f'<li><a href="javascript:goTo({j})">{tab["title"]}</a></li>\n'
            slides_html += '</ul>\n'
        else:
            slides_html += f'<h2>{tc["title"]}</h2>\n'
            slides_html += tc['content']
        
        slides_html += '</div></div>\n'

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
    <div class="page-info">第 <strong id="currentPage">1</strong> / <span id="totalPages">{len(tab_contents)}</span> 页</div>
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
const totalSlides = {len(tab_contents)};

function goTo(idx) {{
  if (idx < 0 || idx >= totalSlides) return;
  // Update slides
  document.querySelectorAll('.slide').forEach(s => s.classList.remove('active'));
  document.getElementById('slide-' + idx).classList.add('active');
  // Update tabs
  document.querySelectorAll('.tab-item').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-item[data-tab="' + idx + '"]')[0].classList.add('active');
  // Scroll tab into view
  const tabEl = document.querySelectorAll('.tab-item[data-tab="' + idx + '"]')[0];
  if (tabEl) tabEl.scrollIntoView({{ block: 'nearest' }});
  // Update page number
  document.getElementById('currentPage').textContent = idx + 1;
  // Update buttons
  document.getElementById('prevBtn').disabled = idx === 0;
  document.getElementById('nextBtn').disabled = idx === totalSlides - 1;
  currentSlide = idx;
  // Scroll content to top
  document.querySelector('.content-area').scrollTop = 0;
}}

function nextSlide() {{ goTo(currentSlide + 1); }}
function prevSlide() {{ goTo(currentSlide - 1); }}

// Keyboard navigation
document.addEventListener('keydown', function(e) {{
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {{ e.preventDefault(); nextSlide(); }}
  if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {{ e.preventDefault(); prevSlide(); }}
  if (e.key === 'Home') {{ e.preventDefault(); goTo(0); }}
  if (e.key === 'End') {{ e.preventDefault(); goTo(totalSlides - 1); }}
}});

// Initial state
goTo(0);
</script>
</body>
</html>'''

    return html


def main():
    input_path = r'E:\workspace-llm\wellhealth\docs\multi-agent-extension-report.md'
    output_path = r'E:\workspace-llm\wellhealth\docs\multi-agent-extension-report.html'

    sections = parse_markdown(input_path)
    print(f"Found {len(sections)} sections")

    html = generate_html(sections)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    file_size = len(html.encode('utf-8'))
    print(f"HTML written to {output_path}")
    print(f"File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")


if __name__ == '__main__':
    main()
