import json

with open(".agents/explorer_survey_routes_1/openapi.json", "r", encoding="utf-8") as f:
    openapi = json.load(f)

paths = openapi.get("paths", {})

untagged = []
for path, methods in paths.items():
    for method, op in methods.items():
        if method.lower() not in ["get", "post", "put", "delete", "patch", "options", "head"]:
            continue
        tags = op.get("tags", [])
        if not tags or tags == ["Untagged"]:
            untagged.append((method.upper(), path, op.get("summary", ""), op.get("operationId", "")))

print(f"Untagged endpoints ({len(untagged)}):")
for m, p, s, opid in untagged:
    print(f"  {m} {p} -> {opid} ({s})")
