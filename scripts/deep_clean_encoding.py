import glob, os

d = r'c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System\docs\interview-guide'

# Map of 3-byte UTF-8 sequences to ASCII replacements
TRIPLE_MAP = {
    b'\xe2\x80\x93': b'-', b'\xe2\x80\x94': b'--',
    b'\xe2\x80\x99': b"'", b'\xe2\x80\x98': b"'",
    b'\xe2\x80\x9c': b'"', b'\xe2\x80\x9d': b'"',
    b'\xe2\x86\x92': b'->', b'\xe2\x86\x90': b'<-',
    b'\xe2\x86\x93': b'v', b'\xe2\x86\x91': b'^',
    b'\xe2\x86\x94': b'<->', b'\xe2\x86\x95': b'<->',
    b'\xe2\x80\xa6': b'...',
    b'\xe2\x89\xa0': b'!=', b'\xe2\x89\xa5': b'>=', b'\xe2\x89\xa4': b'<=',
    b'\xe2\x9c\x93': b'Y', b'\xe2\x9c\x97': b'N',
    b'\xe2\x80\xa2': b'*', b'\xe2\x80\xb2': b"'",
    # Box-drawing
    b'\xe2\x94\x80': b'-', b'\xe2\x94\x82': b'|',
    b'\xe2\x94\x9c': b'|', b'\xe2\x94\x94': b'|',
    b'\xe2\x94\x90': b'+', b'\xe2\x94\x98': b'+',
    b'\xe2\x94\x8c': b'+', b'\xe2\x94\xac': b'+',
    b'\xe2\x94\xb4': b'+', b'\xe2\x94\xbc': b'+',
    b'\xe2\x94\xa4': b'|', b'\xe2\x94\xa0': b'|',
    b'\xe2\x94\x9c': b'|', b'\xe2\x95\x90': b'=',
    # Block elements
    b'\xe2\x96\x88': b'#', b'\xe2\x96\x91': b'.',
    b'\xe2\x96\x92': b'=', b'\xe2\x96\x93': b'#',
    # Zero-width
    b'\xe2\x80\x8b': b'', b'\xef\xbb\xbf': b'',
    # Greek
    b'\xce\xbb': b'lambda',
}

DOUBLE_MAP = {
    b'\xc2\xa0': b' ',
    b'\xc3\xa9': b'e', b'\xc3\xa0': b'a',
    b'\xc3\xb1': b'n', b'\xc3\xbc': b'u',
}

for f in sorted(glob.glob(os.path.join(d, '*.md'))):
    with open(f, 'rb') as fh:
        raw = fh.read()
    
    result = bytearray()
    i = 0
    while i < len(raw):
        b = raw[i]
        if b < 0x80:
            result.append(b)
            i += 1
        elif b < 0xC0:
            i += 1  # orphaned continuation byte
        elif b < 0xE0:
            pair = raw[i:i+2] if i+1 < len(raw) else b''
            if pair in DOUBLE_MAP:
                result.extend(DOUBLE_MAP[pair])
            i += 2
        elif b < 0xF0:
            triple = raw[i:i+3] if i+2 < len(raw) else b''
            if triple in TRIPLE_MAP:
                result.extend(TRIPLE_MAP[triple])
            i += 3
        else:
            i += 4  # 4-byte sequence, skip
    
    with open(f, 'wb') as fh:
        fh.write(bytes(result))
    
    basename = os.path.basename(f)
    print(f'Deep cleaned: {basename} ({len(raw)} -> {len(result)} bytes)')
