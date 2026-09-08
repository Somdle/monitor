import ast
from pathlib import Path


def test_imports_follow_documented_ownership():
    allowed = {
        "__init__": set(),
        "theme": set(),
        "device": set(),
        "power": set(),
        "icon": set(),
        "instance": set(),
        "startup": set(),
        "tray": {"icon"},
        "logging_setup": set(),
        "session": set(),
        "gpu": set(),
        "cpu_temperature": set(),
        "sensors": {"gpu", "cpu_temperature"},
        "render": {"theme", "sensors"},
        "runtime": {"device", "render", "session", "theme", "sensors"},
        "app": {
            "power",
            "render",
            "runtime",
            "theme",
            "sensors",
            "tray",
            "icon",
            "instance",
            "startup",
        },
        "__main__": {"device", "logging_setup", "runtime", "theme", "app", "instance"},
    }
    root = Path(__file__).parents[1] / "src" / "monitor35"
    for path in root.glob("*.py"):
        imports = set()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("monitor35."):
                imports.add(node.module.split(".")[1])
            if isinstance(node, ast.Import):
                imports.update(
                    alias.name.split(".")[1]
                    for alias in node.names
                    if alias.name.startswith("monitor35.")
                )
        assert imports <= allowed[path.stem], (path, imports)
