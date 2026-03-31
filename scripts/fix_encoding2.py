import glob, os

d = r'c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System\docs\interview-guide'

for f in glob.glob(os.path.join(d, '*.md')):
    with open(f, 'r', encoding='utf-8', errors='replace') as fh:
        t = fh.read()
    
    # Fix double-encoded artifacts
    t = t.replace("??'", "->")
    t = t.replace('??"', "--")
    t = t.replace('??T', "'")
    t = t.replace('??', "")  # Catch remaining
    
    with open(f, 'w', encoding='utf-8') as fh:
        fh.write(t)
    print(f'Fixed: {os.path.basename(f)}')
