import os
import sys
import json
from collections import defaultdict

with open(".agents/explorer_survey_routes_1/openapi.json", "r", encoding="utf-8") as f:
    openapi = json.load(f)

paths = openapi.get("paths", {})
schemas = openapi.get("components", {}).get("schemas", {})

# Group operations by Tag
tag_groups = defaultdict(list)

for path_str, path_item in paths.items():
    for method_str, op in path_item.items():
        if method_str.lower() not in ["get", "post", "put", "delete", "patch", "options", "head"]:
            continue
        method = method_str.upper()
        tags = op.get("tags", ["Top-Level & System"])
        tag = tags[0] if tags else "Top-Level & System"
        tag_groups[tag].append({
            "path": path_str,
            "method": method,
            "op_id": op.get("operationId", ""),
            "summary": op.get("summary", ""),
            "description": op.get("description", ""),
            "parameters": op.get("parameters", []),
            "request_body": op.get("requestBody", {}),
            "responses": op.get("responses", {}),
            "security": op.get("security", [])
        })

print(f"Total tag groups: {len(tag_groups)}")
for tag, ops in tag_groups.items():
    print(f"Tag: {tag} -> {len(ops)} operations")
