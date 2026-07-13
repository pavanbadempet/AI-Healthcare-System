with open('docs/Healthcare_Retraining_Colab.ipynb', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('        import os\\n",', '        "import os\\n",')
with open('docs/Healthcare_Retraining_Colab.ipynb', 'w', encoding='utf-8') as f:
    f.write(content)
