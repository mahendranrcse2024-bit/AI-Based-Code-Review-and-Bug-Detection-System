import ast
from dataclasses import dataclass
from pathlib import Path
from app.config import MAX_FILE_SIZE, SUPPORTED_EXTENSIONS

@dataclass
class SourceUnit:
    filename: str
    code: str
    language: str
    project: str = "Untitled"
    version: str = "1.0"

class ValidationError(ValueError):
    pass

def validate_source(filename: str, code: str) -> SourceUnit:
    name = Path(filename or "untitled.py").name
    suffix = Path(name).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValidationError(f"Unsupported extension '{suffix or '[none]'}'. Supported: {', '.join(SUPPORTED_EXTENSIONS)}")
    if not code or not code.strip():
        raise ValidationError("Source code cannot be empty.")
    if len(code.encode("utf-8")) > MAX_FILE_SIZE:
        raise ValidationError(f"Source exceeds the {MAX_FILE_SIZE} byte limit.")
    if "\x00" in code:
        raise ValidationError("Binary or NUL-containing input is not accepted.")
    return SourceUnit(name, code.replace("\r\n", "\n").replace("\r", "\n"), SUPPORTED_EXTENSIONS[suffix])

def python_summary(code: str) -> dict:
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return {"parse_error": str(exc), "functions": [], "classes": [], "imports": []}
    functions, classes, imports = [], [], []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append({"name": node.name, "line": node.lineno})
        elif isinstance(node, ast.ClassDef):
            classes.append({"name": node.name, "line": node.lineno})
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append({"name": ast.unparse(node), "line": node.lineno})
    return {"parse_error": None, "functions": functions, "classes": classes, "imports": imports}
