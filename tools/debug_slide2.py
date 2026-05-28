import re

with open('docs/multi-agent-extension-report.html', 'r', encoding='utf-8') as f:
    html = f.read()

pattern = re.compile(r'(<div class="slide[^"]*" id="slide-\d+">.*?</div>\s*</div>)', re.DOTALL)
slides = pattern.findall(html)
print(f'Total slides: {len(slides)}')

# Slide 2 = index 2
s = slides[2]
print(f'Slide 2 length: {len(s)}')
print(f'Has <pre>: {"<pre" in s}')

h2 = re.search(r'<h2>(.*?)</h2>', s)
if h2:
    print(f'h2: {h2.group(1)[:60]}')

# Check what's inside
pre_blocks = re.findall(r'<pre[^>]*>.*?</pre>', s, re.DOTALL)
print(f'pre blocks count: {len(pre_blocks)}')
for i, p in enumerate(pre_blocks):
    print(f'  Pre {i}: {len(p)} bytes')

# Maybe the content is in a code block?
code_blocks = re.findall(r'<code>.*?</code>', s, re.DOTALL)
print(f'code blocks count: {len(code_blocks)}')

# Print entire slide content (first 500 chars)
print(f'\nFirst 500 chars of slide 2:\n{s[:500]}')
