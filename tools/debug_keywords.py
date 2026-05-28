with open('docs/multi-agent-extension-report.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

keywords = ["3.2.1", "4.2.1", "5.2.1", "11.1", "12.3.1", "12.3.5", "16.1", "14.1", "17.1", "11.", "延伸方向一览"]

for kw in keywords:
    matches = [i for i, l in enumerate(lines) if kw in l and l.startswith('###')]
    if matches:
        for m in matches:
            print(f'  [{kw}] found in h3 line {m}: {lines[m].strip()[:70]}')
    else:
        # Check in h2 as well
        h2_matches = [i for i, l in enumerate(lines) if kw in l and l.startswith('##') and not l.startswith('###')]
        if h2_matches:
            for m in h2_matches:
                print(f'  [{kw}] found in h2 line {m}: {lines[m].strip()[:70]}')
        else:
            # Search anywhere
            any_matches = [i for i, l in enumerate(lines) if kw in l]
            if any_matches:
                print(f'  [{kw}] found in {len(any_matches)} lines (not in heading)')
            else:
                print(f'  [{kw}] NOT FOUND in file')
