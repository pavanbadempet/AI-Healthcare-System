import os
import sys
import json

# Ensure python path
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///./healthcare.db"
sys.path.insert(0, os.path.abspath("."))

from backend.main import app

def generate_manifest():
    with open(".agents/explorer_survey_routes_1/openapi.json", "r", encoding="utf-8") as f:
        openapi = json.load(f)

    paths = openapi.get("paths", {})
    schemas = openapi.get("components", {}).get("schemas", {})

    manifest = {
        "summary": {
            "total_paths": len(paths),
            "total_schemas": len(schemas),
        },
        "endpoints": []
    }

    for path_str, path_item in paths.items():
        for method_str, op in path_item.items():
            if method_str.lower() not in ["get", "post", "put", "delete", "patch", "options", "head"]:
                continue
            
            method = method_str.upper()
            op_id = op.get("operationId", "")
            tags = op.get("tags", [])
            summary = op.get("summary", "")
            description = op.get("description", "")
            params = op.get("parameters", [])
            req_body = op.get("requestBody", {})
            responses = op.get("responses", {})
            security = op.get("security", [])

            # Parse request body schema
            req_schema_ref = None
            req_schema_details = None
            if req_body:
                content = req_body.get("content", {})
                for ctype, cobj in content.items():
                    schema = cobj.get("schema", {})
                    if "$ref" in schema:
                        req_schema_ref = schema["$ref"].split("/")[-1]
                    elif "items" in schema and "$ref" in schema["items"]:
                        req_schema_ref = "List[" + schema["items"]["$ref"].split("/")[-1] + "]"
                    else:
                        req_schema_ref = schema.get("type", "custom")
            
            # Parse responses
            res_details = {}
            for status_code, res_obj in responses.items():
                res_desc = res_obj.get("description", "")
                res_schema_ref = None
                content = res_obj.get("content", {})
                for ctype, cobj in content.items():
                    schema = cobj.get("schema", {})
                    if "$ref" in schema:
                        res_schema_ref = schema["$ref"].split("/")[-1]
                    elif "items" in schema and "$ref" in schema["items"]:
                        res_schema_ref = "List[" + schema["items"]["$ref"].split("/")[-1] + "]"
                    else:
                        res_schema_ref = schema.get("type", "object")
                res_details[status_code] = {
                    "description": res_desc,
                    "schema": res_schema_ref
                }

            manifest["endpoints"].append({
                "path": path_str,
                "method": method,
                "operation_id": op_id,
                "tags": tags,
                "summary": summary,
                "description": description,
                "parameters": params,
                "request_body_schema": req_schema_ref,
                "responses": res_details,
                "security": security
            })

    with open(".agents/explorer_survey_routes_1/route_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Generated route_manifest.json with {len(manifest['endpoints'])} operations.")

if __name__ == "__main__":
    generate_manifest()
