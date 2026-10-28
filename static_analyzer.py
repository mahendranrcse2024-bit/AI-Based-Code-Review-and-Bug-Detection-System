import ast, json, shutil, subprocess, tempfile
from pathlib import Path
from app.core.preprocessing import SourceUnit, python_summary

CATEGORY = {"F": "Correctness", "E": "Readability", "W": "Readability", "C": "Readability", "B": "Security", "S": "Security", "R": "Performance"}
SEVERITY = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1, "Informational": 0}

def finding(fid, line, rule, category, severity, title, description, evidence, tool, fix):
    return {"id": fid, "line": line or 1, "rule_id": rule, "category": category, "severity": severity, "title": title, "description": description, "evidence": evidence, "tool": tool, "recommended_fix": fix, "status": "Open", "ai_generated": False}

def builtin_python(unit: SourceUnit):
    findings=[]
    try: tree=ast.parse(unit.code)
    except SyntaxError as exc:
        line = getattr(exc, "lineno", 1) or 1
        text = unit.code.splitlines()[line-1] if unit.code.splitlines() and line <= len(unit.code.splitlines()) else ""
        return [finding("PY-SYNTAX", line, "PY-SYNTAX", "Correctness", "High", "Syntax error", str(exc), text, "Python AST", "Fix the syntax error before relying on further analysis.")]
    lines=unit.code.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "eval":
            findings.append(finding(f"PY-EVAL-{node.lineno}", node.lineno, "PY-EVAL", "Security", "High", "Dynamic eval usage", "eval executes dynamically constructed input and can enable code execution.", lines[node.lineno-1].strip(), "Python AST", "Avoid eval; use explicit parsing or a constrained mapping."))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "input":
            findings.append(finding(f"PY-INPUT-{node.lineno}", node.lineno, "PY-INPUT", "Security", "Low", "Unvalidated user input", "Input reaches the program without visible validation in this local context.", lines[node.lineno-1].strip(), "Python AST", "Validate type, length, and allowed values before use."))
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            findings.append(finding(f"PY-BARE-EXCEPT-{node.lineno}", node.lineno, "PY-BARE-EXCEPT", "Correctness", "Medium", "Bare exception handler", "Catching every exception can hide programming errors and make recovery unsafe.", lines[node.lineno-1].strip(), "Python AST", "Catch the narrowest expected exception and log useful context."))
        if isinstance(node, ast.FunctionDef) and len(node.body) > 30:
            findings.append(finding(f"PY-LONG-FUNC-{node.lineno}", node.lineno, "PY-LONG-FUNC", "Readability", "Low", "Long function", "The function has more than 30 top-level statements and may be difficult to test or maintain.", lines[node.lineno-1].strip(), "Python AST", "Split responsibilities into smaller, focused functions."))
    return findings

def external_tools(unit: SourceUnit):
    findings=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/unit.filename
        path.write_text(unit.code, encoding="utf-8")
        if shutil.which("ruff"):
            try:
                out=subprocess.run(["ruff","check","--output-format","json",str(path)],capture_output=True,text=True,timeout=15)
                for item in json.loads(out.stdout or "[]"):
                    code=item.get("code","RUFF"),
                    code=code[0] if isinstance(code, tuple) else code
                    line=item.get("location",{}).get("row",1)
                    msg=item.get("message","Style issue")
                    findings.append(finding(f"{code}-{line}",line,code,"Readability","Low",msg,msg,item.get("fix",""),"Ruff","Apply the reported Ruff fix after reviewing context."))
            except (json.JSONDecodeError, subprocess.TimeoutExpired): pass
    return findings

def analyze(unit: SourceUnit):
    if unit.language != "python":
        return [], {"language": unit.language, "supported": False, "message": "Only Python has implemented AST/static-tool analysis."}
    results = builtin_python(unit) + external_tools(unit)
    return results, {"language": "python", "supported": True, "summary": python_summary(unit.code), "tools": ["Python AST", "Ruff (when installed)"]}
