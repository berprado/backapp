import os
import ast


def _module_path_from_file(file_path, project_root):
    """Obtiene la ruta de módulo (dot notation) a partir de un archivo."""
    rel_path = os.path.relpath(file_path, project_root)
    parts = rel_path.split(os.sep)

    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1][:-3]  # quitar ".py"

    return ".".join(part for part in parts if part and part != "__pycache__")


def extract_imports(file_path, project_root):
    """Extrae módulos importados desde un archivo y resuelve importaciones relativas."""
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=file_path)
        except Exception:
            return set()

    current_module = _module_path_from_file(file_path, project_root)
    package_parts = current_module.split(".") if current_module else []
    imports = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            level = getattr(node, "level", 0) or 0
            if level:
                base_parts = package_parts[:-level]
            else:
                base_parts = []

            if node.module:
                base_parts.extend(node.module.split("."))

            base_module = ".".join(part for part in base_parts if part)

            if node.names:
                for alias in node.names:
                    if alias.name == "*":
                        if base_module:
                            imports.add(base_module)
                        continue

                    if base_module:
                        imports.add(f"{base_module}.{alias.name}")
                    else:
                        imports.add(alias.name)
            elif base_module:
                imports.add(base_module)

    return imports


def resolve_module_path(module_name, project_root):
    """Resuelve un nombre de módulo a un archivo .py dentro del paquete."""
    if not module_name:
        return None

    parts = module_name.split(".")
    project_package = os.path.basename(project_root)

    # Permitir referencias del tipo "facturador.shared_utils"
    if parts[0] == project_package:
        parts = parts[1:]

    if not parts:
        return None

    for length in range(len(parts), 0, -1):
        candidate = os.path.join(project_root, *parts[:length]) + ".py"
        if os.path.isfile(candidate):
            return os.path.abspath(candidate)

        init_candidate = os.path.join(project_root, *parts[:length], "__init__.py")
        if os.path.isfile(init_candidate):
            return os.path.abspath(init_candidate)

    return None


def crawl_imports(entry_points, project_root):
    """Recorre las dependencias a partir de múltiples entry points."""
    used_modules = set()
    to_process = [os.path.abspath(path) for path in entry_points if os.path.isfile(path)]
    seen = set()

    while to_process:
        current = to_process.pop()
        if current in seen:
            continue
        seen.add(current)
        used_modules.add(current)

        for module_name in extract_imports(current, project_root):
            module_path = resolve_module_path(module_name, project_root)
            if module_path and module_path not in seen:
                to_process.append(module_path)

    return used_modules


def list_all_py_files(project_root):
    """Lista archivos .py en la raíz y subdirectorios relevantes."""
    target_dirs = [project_root]

    for subdir in ("tabs", "pages"):
        candidate = os.path.join(project_root, subdir)
        if os.path.isdir(candidate):
            target_dirs.append(candidate)

    py_files = set()
    for directory in target_dirs:
        for root, _, files in os.walk(directory):
            if "__pycache__" in root:
                continue
            for filename in files:
                if filename.endswith(".py"):
                    py_files.add(os.path.abspath(os.path.join(root, filename)))

    return py_files


def main():
    project_root = os.path.abspath("facturador")

    if not os.path.isdir(project_root):
        print("❌ No se encontró la carpeta facturador en el directorio actual.")
        return

    entry_points = [
        os.path.join(project_root, "main.py"),
        os.path.join(project_root, "ui_copy.py"),
        os.path.join(project_root, "zeeper.py"),
    ]

    for directory, filename in (
        ("tabs", "__init__.py"),
    ):
        candidate = os.path.join(project_root, directory, filename)
        entry_points.append(candidate)

    pages_dir = os.path.join(project_root, "pages")
    if os.path.isdir(pages_dir):
        for filename in os.listdir(pages_dir):
            if filename.endswith(".py"):
                entry_points.append(os.path.join(pages_dir, filename))

    for tab_filename in (
        "facturacion_tab.py",
        "anular_revertir_tab.py",
        "verificar_factura_tab.py",
        "validar_nit_tab.py",
    ):
        entry_points.append(os.path.join(project_root, "tabs", tab_filename))

    existing_entry_points = [path for path in entry_points if os.path.isfile(path)]
    if not existing_entry_points:
        print("❌ No se encontró ningún punto de entrada válido para el análisis.")
        return

    print("🔍 Analizando puntos de entrada:")
    for path in existing_entry_points:
        print("   •", os.path.relpath(path, project_root))

    used = crawl_imports(existing_entry_points, project_root)
    all_files = list_all_py_files(project_root)
    unused = all_files - used

    print("\n✅ Módulos usados:")
    for path in sorted(used):
        print("   ", os.path.relpath(path, project_root))

    print("\n❌ Módulos NO utilizados:")
    for path in sorted(unused):
        print("   ", os.path.relpath(path, project_root))

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
