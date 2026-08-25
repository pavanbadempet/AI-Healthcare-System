import os
import sys
import json

# Set environment
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///./healthcare.db"
sys.path.insert(0, os.path.abspath("."))

from backend.main import app
from fastapi.routing import APIRoute, APIWebSocketRoute
from starlette.routing import WebSocketRoute

def extract_all():
    openapi_schema = app.openapi()
    
    # Save openapi schema
    with open(".agents/explorer_survey_routes_1/openapi.json", "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2)
    
    routes_data = []
    ws_routes = []
    
    for r in app.routes:
        if isinstance(r, APIRoute):
            # Extract dependencies
            deps = []
            for d in r.dependant.dependencies:
                dep_fn = d.call
                dep_name = getattr(dep_fn, '__name__', str(dep_fn))
                deps.append(dep_name)
            
            routes_data.append({
                "path": r.path,
                "name": r.name,
                "methods": list(r.methods),
                "tags": r.tags,
                "summary": r.summary,
                "description": r.description,
                "status_code": r.status_code,
                "response_model": str(r.response_model) if r.response_model else None,
                "dependencies": deps,
                "endpoint_name": r.endpoint.__name__ if hasattr(r.endpoint, '__name__') else str(r.endpoint),
                "endpoint_module": getattr(r.endpoint, '__module__', '')
            })
        elif isinstance(r, (APIWebSocketRoute, WebSocketRoute)):
            endpoint = getattr(r, "endpoint", None)
            ws_routes.append({
                "path": r.path,
                "name": r.name,
                "endpoint": endpoint.__name__ if hasattr(endpoint, '__name__') else str(endpoint),
                "endpoint_module": getattr(endpoint, '__module__', ''),
                "summary": getattr(r, "summary", None),
                "description": getattr(r, "description", None),
            })
        else:
            pass

    output = {
        "total_http_routes": len(routes_data),
        "total_ws_routes": len(ws_routes),
        "routes": routes_data,
        "ws_routes": ws_routes
    }

    with open(".agents/explorer_survey_routes_1/routes_summary.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"Extracted {len(routes_data)} HTTP routes and {len(ws_routes)} WS routes.")
    print(f"OpenAPI paths count: {len(openapi_schema.get('paths', {}))}")

if __name__ == "__main__":
    extract_all()
