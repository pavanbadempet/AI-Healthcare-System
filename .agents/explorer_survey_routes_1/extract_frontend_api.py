import os
import re
import json

frontend_src = "frontend/src"

api_calls = []

# Regex patterns for apiFetch, fetch, axios, endpoints
url_pattern = re.compile(r"['\"`](/(?:v1|api|healthz|generate_report|metrics|telemetry)[^'\"`\s]*)['\"`]")

for root, dirs, files in os.walk(frontend_src):
    for f in files:
        if f.endswith((".ts", ".tsx", ".js", ".jsx")):
            fpath = os.path.join(root, f).replace("\\", "/")
            with open(fpath, "r", encoding="utf-8", errors="ignore") as file:
                content = file.read()
                matches = url_pattern.findall(content)
                for m in matches:
                    api_calls.append({
                        "file": fpath,
                        "endpoint": m
                    })

print(f"Total frontend endpoint references found: {len(api_calls)}")
unique_endpoints = sorted(list(set(c["endpoint"] for c in api_calls)))
print(f"Unique endpoints referenced in frontend: {len(unique_endpoints)}")
for ep in unique_endpoints:
    print(f"  {ep}")

with open(".agents/explorer_survey_routes_1/frontend_api_map.json", "w", encoding="utf-8") as f:
    json.dump({"total": len(api_calls), "unique": unique_endpoints, "calls": api_calls}, f, indent=2)
