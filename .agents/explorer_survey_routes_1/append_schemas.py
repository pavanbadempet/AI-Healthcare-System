import json

with open(".agents/explorer_survey_routes_1/openapi.json", "r", encoding="utf-8") as f:
    openapi = json.load(f)

schemas = openapi.get("components", {}).get("schemas", {})

schema_lines = []
schema_lines.append("---")
schema_lines.append("## 7. Component Schemas & Data Transfer Objects (DTOs)")
schema_lines.append("")
schema_lines.append(f"Total Schemas Defined in Components: {len(schemas)}")
schema_lines.append("")

for sname, sdef in sorted(schemas.items()):
    stype = sdef.get("type", "object")
    sdesc = sdef.get("description", "")
    props = sdef.get("properties", {})
    required = set(sdef.get("required", []))
    
    schema_lines.append(f"### 7.{sname} (`{sname}`)")
    if sdesc:
        schema_lines.append(f"> {sdesc}")
    
    if props:
        schema_lines.append("| Field | Type | Required | Description |")
        schema_lines.append("| --- | --- | --- | --- |")
        for pname, pdef in props.items():
            ptype = pdef.get("type", "any")
            if "$ref" in pdef:
                ptype = pdef["$ref"].split("/")[-1]
            elif "items" in pdef and "$ref" in pdef["items"]:
                ptype = "List[" + pdef["items"]["$ref"].split("/")[-1] + "]"
            elif "items" in pdef:
                ptype = f"List[{pdef['items'].get('type', 'any')}]"
            
            p_req = "Yes" if pname in required else "No"
            p_desc = pdef.get("description", pdef.get("title", "")).replace("\n", " ").replace("|", "\\|")
            schema_lines.append(f"| `{pname}` | `{ptype}` | {p_req} | {p_desc} |")
        schema_lines.append("")
    else:
        schema_lines.append(f"Type: `{stype}`")
        schema_lines.append("")

with open(".agents/explorer_survey_routes_1/routes_survey.md", "r", encoding="utf-8") as f:
    content = f.read()

with open(".agents/explorer_survey_routes_1/routes_survey.md", "w", encoding="utf-8") as f:
    f.write(content + "\n" + "\n".join(schema_lines))

print(f"Appended {len(schemas)} component schemas to routes_survey.md")
