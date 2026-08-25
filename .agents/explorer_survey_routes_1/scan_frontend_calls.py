import os
import re
import json

frontend_src = "frontend/src"

api_fetch_calls = []
pattern = re.compile(r"apiFetch(?:<[^>]+>)?\(\s*[`'\"]([^`'\"]+)[`'\"]")
pattern_fetch = re.compile(r"fetch\(\s*[`'\"]([^`'\"]+)[`'\"]")
pattern_template = re.compile(r"apiFetch(?:<[^>]+>)?\(\s*`([^`]+)`")

for root, dirs, files in os.walk(frontend_src):
    for f in files:
        if f.endswith((".ts", ".tsx", ".js", ".jsx")):
            fpath = os.path.join(root, f).replace("\\", "/")
            with open(fpath, "r", encoding="utf-8", errors="ignore") as file:
                content = file.read()
                for m in pattern.findall(content):
                    api_fetch_calls.append({"file": fpath, "endpoint": m, "type": "apiFetch"})
                for m in pattern_fetch.findall(content):
                    api_fetch_calls.append({"file": fpath, "endpoint": m, "type": "fetch"})
                for m in pattern_template.findall(content):
                    api_fetch_calls.append({"file": fpath, "endpoint": m, "type": "template"})

print(f"Total frontend API call instances found: {len(api_fetch_calls)}")
unique_calls = sorted(list(set(c["endpoint"] for c in api_fetch_calls)))
print(f"Unique endpoints called in frontend: {len(unique_calls)}")
for ep in unique_calls:
    print(f"  {ep}")

with open(".agents/explorer_survey_routes_1/frontend_api_calls.json", "w", encoding="utf-8") as f:
    json.dump({"total": len(api_fetch_calls), "unique": unique_calls, "calls": api_fetch_calls}, f, indent=2)
