import os
import ast

used_modules = set()

def extract_imports(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=file_path)
        except Exception:
            return []
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports

def resolve_module_path(module_name, project_root):
    parts = module_name.split(".")
    py_path = os.path.join(project_root, *parts) + ".py"
    if os.path.isfile(py_path):
        return os.path.abspath(py_path)
    init_path = os.path.join(project_root, *parts, "__init__.py")
    if os.path.isfile(init_path):
        return os.path.abspath(init_path)
    return None

def crawl_imports(entry_point, project_root):
    to_process = [os.path.abspath(entry_point)]
    seen = set()
    while to_process:
        current = to_process.pop()
        if current in seen:
            continue
        seen.add(current)
        used_modules.add(current)
        imports = extract_imports(current)
        for imp in imports:
            imp_path = resolve_module_path(imp, project_root)
            if imp_path and imp_path not in seen:
                to_process.append(imp_path)
    return used_modules

def list_all_py_files(project_root):
    py_files = set()
    for root, _, files in os.walk(project_root):
        for f in files:
            if f.endswith(".py"):
                py_files.add(os.path.abspath(os.path.join(root, f)))
    return py_files

def main():
    project_root = os.path.abspath("facturador")
    entry_file = os.path.join(project_root, "main.py")

    if not os.path.isfile(entry_file):
        print("❌ No se encontró main.py en la carpeta facturador.")
        return

    print(f"🔍 Analizando desde: {entry_file}")
    used = crawl_imports(entry_file, project_root)
    all_files = list_all_py_files(project_root)
    unused = all_files - used

    print("\n✅ Módulos usados:")
    for path in sorted(used):
        print("   ", os.path.relpath(path, project_root))

    print("\n❌ Módulos NO utilizados:")
    for path in sorted(unused):
        print("   ", os.path.relpath(path, project_root))

    # Guardar reporte
    report_path = os.path.join(project_root, "report.txt")
    with open(report_path, "w", encoding="utf-8") as out:
        out.write("✅ Módulos usados:\n")
        for path in sorted(used):
            out.write(f"{os.path.relpath(path, project_root)}\n")
        out.write("\n❌ Módulos NO utilizados:\n")
        for path in sorted(unused):
            out.write(f"{os.path.relpath(path, project_root)}\n")

    print(f"\n📄 Reporte guardado en: {report_path}")

if __name__ == "__main__":
    main()
