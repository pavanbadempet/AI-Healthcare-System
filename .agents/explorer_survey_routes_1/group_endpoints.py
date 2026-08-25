import json
from collections import defaultdict

with open(".agents/explorer_survey_routes_1/openapi.json", "r", encoding="utf-8") as f:
    openapi = json.load(f)

paths = openapi.get("paths", {})
components = openapi.get("components", {})
schemas = components.get("schemas", {})

print(f"Total paths: {len(paths)}")
print(f"Total component schemas: {len(schemas)}")

# Group endpoints by tag
by_tag = defaultdict(list)
for path, methods in paths.items():
    for method, op in methods.items():
        if method.lower() not in ["get", "post", "put", "delete", "patch", "options", "head"]:
            continue
        tags = op.get("tags", ["Untagged"])
        for tag in tags:
            by_tag[tag].append((method.upper(), path, op))

print(f"Total tags: {len(by_tag)}")
for tag, eps in sorted(by_tag.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"- {tag}: {len(eps)} endpoints")
