with open('docs/multi-agent-extension-report.html', 'r', encoding='utf-8') as f:
    content = f.read()

checks = [
    'WellHealth 多 Agent 架构应用延伸分析报告',
    '1. 分析框架',
    '三医联动',
    '实施开发计划',
    'PrescriptionReviewAgent',
    'PatientProfileAgent',
    'class ClosedLoopRecord',
    'Phase 0',
    'Week 1-2',
    'InsurancePolicyAgent',
    'ComorbidityNegotiator',
    'PopulationAnalysisAgent',
    'PRESCRIPTION_REVIEW',
    'PrescriptionReviewCoordinator',
    '17.8 风险与缓解措施',
    '42 个',
    '63 个',
    '40 周',
]
all_ok = True
for c in checks:
    found = c in content
    if not found:
        all_ok = False
    print(f'  {"[OK]" if found else "[FAIL]"} "{c}"')

# Check structure
print()
print(f'Total length: {len(content)} chars')
print(f'h2 tags: {content.count("<h2")}')
print(f'h3 tags: {content.count("<h3")}')
print(f'table tags: {content.count("<table")}')
print(f'pre tags: {content.count("<pre")}')
print(f'tab-item count: {content.count("tab-item")}')
print(f'slide IDs: {content.count("slide-")}')

# Try to find issues
import re
zh = len(re.findall(r'[\u4e00-\u9fff]', content))  # noqa
print(f'Chinese characters: {zh}')

print()
if all_ok:
    print('ALL CHECKS PASSED')
else:
    print('SOME CHECKS FAILED')
