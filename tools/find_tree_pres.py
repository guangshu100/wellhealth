import re

with open('docs/multi-agent-extension-report.html', 'r', encoding='utf-8') as f:
    html = f.read()

pres = list(re.finditer(r'<pre[^>]*>(.*?)</pre>', html, re.DOTALL))
print(f'Total pre blocks: {len(pres)}')

tree_count = 0
code_count = 0
for i, p in enumerate(pres):
    content = p.group(1)
    is_tree = any(c in content for c in ['├', '└', '│', '┌', '┬', '┐', '─'])
    if is_tree:
        tree_count += 1
        # Show context: what heading is near this pre block?
        pos = p.start()
        before = html[max(0,pos-300):pos]
        h_match = re.search(r'<(h[234])>(.*?)</\1>', before)
        if h_match:
            print(f'  TREE #{i}: near <{h_match.group(1)}>{h_match.group(2)[:50]}')
        else:
            print(f'  TREE #{i}: (no nearby heading, pos={pos})')
    else:
        lang_match = re.search(r'<(?:yaml|python|code)', content)
        if lang_match:
            code_count += 1

print(f'\nOf {len(pres)} pre blocks:')
print(f'  Tree-style (diagrams): {tree_count}')
print(f'  Code-style: likely {code_count}+')
