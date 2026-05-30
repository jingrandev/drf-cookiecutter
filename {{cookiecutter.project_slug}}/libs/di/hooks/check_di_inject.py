import ast
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[3]
    errors: list[str] = []

    container_classes, wired_packages = _scan_containers(repo_root)

    for py_file in _iter_python_files(repo_root):
        source = py_file.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError:
            continue

        module = _path_to_module(py_file, repo_root)
        if not module:
            continue

        rel = py_file.relative_to(repo_root)

        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue

            provide_refs = _extract_provide_refs(node)

            if not provide_refs and not _has_inject(node):
                continue

            if provide_refs and not _has_inject(node):
                errors.append(
                    f"{rel}:{node.lineno}: {node.name}: "
                    f"has Provide[...] default but missing @inject"
                )
                continue

            if not provide_refs:
                continue

            if not _module_in_wired_package(module, wired_packages):
                errors.append(
                    f"{rel}:{node.lineno}: {node.name}: "
                    f"uses @inject + Provide but module is not under a wired package "
                    f"(no di_containers.py found in any parent app)"
                )
                continue

            aliases = _extract_import_aliases(tree, module_name=module)
            for ref in provide_refs:
                if not _ref_resolves_to_container(ref, aliases, container_classes, module):
                    errors.append(
                        f"{rel}:{node.lineno}: {node.name}: "
                        f"Provide[{ref}] does not reference a known Container class"
                    )

    for e in errors:
        print(e)

    return 1 if errors else 0


def _scan_containers(
    repo_root: Path,
) -> tuple[set[str], set[str]]:
    container_classes: set[str] = set()
    wired_packages: set[str] = set()

    for di_file in repo_root.rglob("di_containers.py"):
        if _is_excluded(di_file, repo_root):
            continue

        pkg_module = _path_to_module(di_file.parent, repo_root)
        if pkg_module:
            wired_packages.add(pkg_module)

        source = di_file.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue

        aliases = _extract_import_aliases(tree, module_name=pkg_module or "")
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for base in node.bases:
                tokens = _extract_dotted_name(base)
                if not tokens:
                    continue
                resolved = aliases.get(tokens[0], tokens[0])
                if resolved.endswith("DeclarativeContainer") or tokens[-1] == "DeclarativeContainer":
                    if pkg_module:
                        container_classes.add(f"{pkg_module}.{node.name}")
                    break

    return container_classes, wired_packages


def _extract_provide_refs(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    refs: list[str] = []
    all_defaults = list(node.args.defaults) + [
        d for d in node.args.kw_defaults if d is not None
    ]
    for default in all_defaults:
        for child in ast.walk(default):
            if not isinstance(child, ast.Subscript):
                continue
            if not _is_provide(child.value):
                continue
            tokens = _extract_dotted_name(child.slice)
            if tokens:
                refs.append(".".join(tokens))
    return refs


def _is_provide(expr: ast.AST) -> bool:
    if isinstance(expr, ast.Name) and expr.id == "Provide":
        return True
    if isinstance(expr, ast.Attribute) and expr.attr == "Provide":
        return True
    return False


def _has_inject(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for dec in node.decorator_list:
        func = dec.func if isinstance(dec, ast.Call) else dec
        if isinstance(func, ast.Name) and func.id == "inject":
            return True
        if isinstance(func, ast.Attribute) and func.attr == "inject":
            return True
    return False


def _module_in_wired_package(module: str, wired_packages: set[str]) -> bool:
    for pkg in wired_packages:
        if module == pkg or module.startswith(f"{pkg}."):
            return True
    return False


def _ref_resolves_to_container(
    ref: str,
    aliases: dict[str, str],
    container_classes: set[str],
    module: str,
) -> bool:
    parts = ref.split(".")
    if len(parts) < 2:
        return False

    container_symbol = parts[0]
    fq = aliases.get(container_symbol)
    if fq is None:
        fq = f"{module.rsplit('.', 1)[0]}.{container_symbol}" if "." in module else container_symbol
    return fq in container_classes


def _extract_import_aliases(tree: ast.AST, *, module_name: str) -> dict[str, str]:
    aliases: dict[str, str] = {}

    parts = module_name.split(".") if module_name else []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name.split(".")[-1]
                aliases[name] = alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0 and parts:
                base = parts[: max(0, len(parts) - node.level)]
                if node.module:
                    base.extend(node.module.split("."))
                mod = ".".join(base)
            else:
                mod = node.module or ""
            if not mod:
                continue
            for alias in (node.names or []):
                if alias.name == "*":
                    continue
                name = alias.asname or alias.name
                aliases[name] = f"{mod}.{alias.name}"
    return aliases


def _extract_dotted_name(expr: ast.AST) -> list[str] | None:
    tokens: list[str] = []
    cur = expr
    while True:
        if isinstance(cur, ast.Attribute):
            tokens.append(cur.attr)
            cur = cur.value
        elif isinstance(cur, ast.Name):
            tokens.append(cur.id)
            break
        else:
            return None
    tokens.reverse()
    return tokens


def _path_to_module(path: Path, repo_root: Path) -> str | None:
    try:
        rel = path.relative_to(repo_root)
    except ValueError:
        return None
    if rel.suffix != ".py":
        return None
    parts = list(rel.with_suffix("").parts)
    return ".".join(parts) if parts else None


_EXCLUDED_DIRS = frozenset({
    ".git", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    ".venv", "__pycache__", "node_modules", "staticfiles",
})


def _is_excluded(path: Path, repo_root: Path) -> bool:
    try:
        rel = path.relative_to(repo_root)
    except ValueError:
        return True
    return any(part in _EXCLUDED_DIRS for part in rel.parts)


def _iter_python_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for p in repo_root.rglob("*.py"):
        if _is_excluded(p, repo_root):
            continue
        if "migrations" in p.parts:
            continue
        files.append(p)
    return sorted(files)


if __name__ == "__main__":
    raise SystemExit(main())
