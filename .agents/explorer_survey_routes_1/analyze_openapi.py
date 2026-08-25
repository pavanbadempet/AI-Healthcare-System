import json
import os

with open(".agents/explorer_survey_routes_1/openapi.json", "r", encoding="utf-8") as f:
    spec = json.load(f)

paths = spec.get("paths", {})
components = spec.get("components", {})
schemas = components.get("schemas", {})
security_schemes = components.get("securitySchemes", {})

print(f"Total paths in OpenAPI: {len(paths)}")
print(f"Total schemas in components: {len(schemas)}")
print(f"Security schemes: {list(security_schemes.keys())}")

# Group paths by prefix / tag
tags_count = {}
by_prefix = {}
total_endpoints = 0

all_endpoints = []

for path, methods in paths.items():
    for method, op in methods.items():
        if method.lower() not in ["get", "post", "put", "delete", "patch", "options", "head", "trace"]:
            continue
        total_endpoints += 1
        tags = op.get("tags", ["Untagged"])
        for t in tags:
            tags_count[t] = tags_count.get(t, 0) + 1
        
        # prefix
        parts = path.strip("/").split("/")
        prefix = "/" + parts[0] if parts else "/"
        if len(parts) > 1 and parts[0] == "v1":
            prefix = f"/v1/{parts[1]}"
        by_prefix[prefix] = by_prefix.get(prefix, 0) + 1

        all_endpoints.append({
            "path": path,
            "method": method.upper(),
            "operation_id": op.get("operationId"),
            "summary": op.get("summary"),
            "description": op.get("description"),
            "tags": tags,
            "parameters": op.get("parameters", []),
            "request_body": op.get("requestBody"),
            "responses": op.get("responses", {}),
            "security": op.get("security", []),
        })

print(f"Total operations (HTTP method + path pairs): {total_endpoints}")
print("\nEndpoints by Tag:")
for t, c in sorted(tags_count.items(), key=lambda x: -x[1]):
    print(f"  {t}: {c}")

print("\nEndpoints by Prefix:")
for p, c in sorted(by_prefix.items(), key=lambda x: -x[1]):
    print(f"  {p}: {c}")

with open(".agents/explorer_survey_routes_1/all_endpoints.json", "w", encoding="utf-8") as f:
    json.dump(all_endpoints, f, indent=2)
