import re

with open('docs/multi-agent-extension-report.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find all slides
slides = list(re.finditer(r'<div class="slide[^"]*" id="slide-\d+">', html))
print(f'Total slides found: {len(slides)}')
for s in slides:
    print(f'  {s.group()} at offset {s.start()}')

# Find h2 headings
h2s = re.findall(r'<h2>(.*?)</h2>', html)
print(f'\nAll h2 headings ({len(h2s)}):')
for i, h in enumerate(h2s):
    print(f'  [{i}] {h[:80]}')

# Find pre blocks with box-drawing chars
pre_blocks = list(re.finditer(r'<pre[^>]*>.*?</pre>', html, re.DOTALL))
box_draw_count = 0
for pb in pre_blocks:
    if '┌' in pb.group() or '├' in pb.group() or '│' in pb.group():
        box_draw_count += 1
print(f'\nPre blocks with box-drawing chars: {box_draw_count}')

# Check which slides have these
print('\nChecking slides for diagram headings...')
slide_pattern = re.compile(r'(<div class="slide[^"]*" id="slide-\d+">.*?</div>\s*</div>)', re.DOTALL)
slide_matches = slide_pattern.findall(html)
print(f'Slide matches via pattern: {len(slide_matches)}')

for i, slide in enumerate(slide_matches):
    h2_match = re.search(r'<h2>(.*?)</h2>', slide)
    if h2_match:
        heading = h2_match.group(1)
        has_pre = '<pre' in slide
        has_box = '┌' in slide or '├' in slide or '│' in slide
        pre_count = len(re.findall(r'<pre[^>]*>', slide))
        print(f'  Slide {i}: heading="{heading[:50]}" pre={pre_count} box_draw={has_box}')
