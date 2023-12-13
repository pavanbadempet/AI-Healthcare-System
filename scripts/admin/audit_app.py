import ast
import builtins

def get_undefined_variables(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()
    
    tree = ast.parse(code)
    
    defined = set(dir(builtins))
    defined.add('st')
    defined.add('pd')
    defined.add('np')
    defined.add('requests')
    defined.add('json')
    defined.add('os')
    defined.add('time')
    defined.add('base64')
    defined.add('option_menu')
    defined.add('st_lottie')
    defined.add('px')
    defined.add('go')
    defined.add('BACKEND_URL')
    
    # Add imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                defined.add(name.asname or name.name)
        elif isinstance(node, ast.ImportFrom):
            for name in node.names:
                defined.add(name.asname or name.name)
                
    undefined = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Add function arguments to defined scope (simplified)
            local_defined = set(defined)
            for arg in node.args.args:
                local_defined.add(arg.arg)
                
            for child in ast.walk(node):
                if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                    local_defined.add(child.id)
                elif isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                    if child.id not in local_defined:
                         undefined.append((child.id, child.lineno))

    return undefined

# Note: This is a simple analyzer and might have false positives due to complex scoping,
# but it's perfect for catching simple typos like 'age_input' vs 'age'
errors = []
try:
    for name, line in get_undefined_variables("app.py"):
        # Filter common non-issues or specific knowns
        if name not in ["load_lottieurl", "fetch_profile", "login", "signup", "save_record", 
                        "render_latest_report", "local_css", "init_session_state",
                        "fetch_records_cached", "update_profile", "delete_record",
                        "render_interactive_trend_chart", "render_radar_chart",
                        "get_pdf_download_link", "fetch_news_feed"]:
            errors.append(f"Line {line}: Undefined variable '{name}'")
except Exception as e:
    print(f"Analyzer Error: {e}")

if errors:
    print("POTENTIAL UNDEFINED VARIABLES:")
    for e in errors:
        print(e)
else:
    print("No obvious undefined variables found.")
