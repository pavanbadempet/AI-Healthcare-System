import glob, os

d = r'c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System\docs\interview-guide'
replacements = {
    b'\xe2\x80\x93': b'-',
    b'\xe2\x80\x94': b'--',
    b'\xe2\x80\x99': b"'",
    b'\xe2\x80\x98': b"'",
    b'\xe2\x80\x9c': b'"',
    b'\xe2\x80\x9d': b'"',
    b'\xe2\x86\x92': b'->',
    b'\xe2\x86\x90': b'<-',
    b'\xe2\x86\x93': b'v',
    b'\xe2\x86\x91': b'^',
    b'\xe2\x80\xa6': b'...',
    b'\xe2\x9c\x93': b'Y',
    b'\xe2\x9c\x97': b'N',
    b'\xc2\xa0': b' ',
}

for f in glob.glob(os.path.join(d, '*.md')):
    with open(f, 'rb') as fh:
        raw = fh.read()
    for old, new in replacements.items():
        raw = raw.replace(old, new)
    with open(f, 'wb') as fh:
        fh.write(raw)
    print(f'Cleaned: {os.path.basename(f)}')
