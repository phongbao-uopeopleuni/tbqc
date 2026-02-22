import sys
with open('d:/tbqc/app.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if '@app.route' in line:
            print(f"L{i+1}: {line.strip()}")
