with open('docs/multi-agent-extension-report.html', 'rb') as f:
    raw = f.read()

# 分析框架 in UTF-8
target = '分析框架'.encode('utf-8')
pos = raw.find(target)
print(f'分析框架 found at offset: {pos}')
if pos >= 0:
    print(f'Context: {raw[max(0,pos-5):pos+20]}')

# 三医联动
target2 = '三医联动'.encode('utf-8')
pos2 = raw.find(target2)
print(f'三医联动 found at offset: {pos2}')

# 实施开发计划
target3 = '实施开发计划'.encode('utf-8')
pos3 = raw.find(target3)
print(f'实施开发计划 found at offset: {pos3}')

# Check total Chinese characters
import re
text = raw.decode('utf-8')
zh = len(re.findall(r'[\u4e00-\u9fff]', text))
print(f'\nTotal Chinese chars: {zh}')
print(f'File size: {len(raw)} bytes ({len(raw)/1024:.1f} KB)')
print(f'\nFirst h2 after slide-0 check:')
import re
h2s = re.findall(r'<h2>(.*?)</h2>', text)
for i, h in enumerate(h2s[:5]):
    print(f'  h2 #{i}: {h[:60]}')
