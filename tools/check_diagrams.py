import re

with open('docs/multi-agent-extension-report.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find all SVG diagrams
svgs = list(re.finditer(r'<svg class="diagram".*?</svg>', html, re.DOTALL))
print(f'Total SVGs found: {len(svgs)}')

for i, svg in enumerate(svgs):
    # Find what's near the SVG (look for preceding h3/h2)
    pos = svg.start()
    before = html[max(0,pos-500):pos]
    h_match = re.findall(r'<(h[234])>(.*?)</\1>', before)
    if h_match:
        nearest = h_match[-1]
        print(f'  Diagram {i+1}: near <{nearest[0]}>{nearest[1][:60]}</{nearest[0]}>')
    else:
        print(f'  Diagram {i+1}: position {pos}')

# Check the SVG for content to identify which diagram it is
for i, svg in enumerate(svgs):
    content = svg.group()
    if 'MonitorAgent' in content:
        print(f'  Diagram {i+1}: MonitorAgent')
    elif 'PlanCoordinator' in content:
        print(f'  Diagram {i+1}: PlanCoordinator')
    elif 'FamilyHealth' in content:
        print(f'  Diagram {i+1}: FamilyHealth')
    elif 'PrescriptionReviewCoordinator' in content:
        print(f'  Diagram {i+1}: PrescriptionReview')
    elif 'P0 -' in content or 'P1 -' in content:
        print(f'  Diagram {i+1}: Priority Matrix')
    elif 'Closed-Loop' in content:
        print(f'  Diagram {i+1}: Closed Loop')
    elif 'WellHealth' in content and 'Phase' in content:
        print(f'  Diagram {i+1}: Roadmap')
    elif 'WellHealth' in content and ('医疗端' in content or '医保端' in content):
        print(f'  Diagram {i+1}: Ecosystem')
    elif 'WellHealth' in content:
        print(f'  Diagram {i+1}: Overview')

print(f'\nTotal HTML size: {len(html)} chars')
