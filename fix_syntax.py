
with open('backend/prediction.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('\\"', '"')

with open('backend/prediction.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed syntax errors in backend/prediction.py")
