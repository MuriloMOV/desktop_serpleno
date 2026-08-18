import subprocess
import sys
import os

ROOT = os.path.abspath(".")
PYTHON = sys.executable

UI_TEST_FILES = [
    "tests/test_views.py",
    "tests/test_qa_interacoes.py",
    "tests/test_pedidos_ajuda_views.py",
]


def collect_test_nodeids(path: str) -> list[str]:
    """Collect all test nodeids from a test file."""
    cmd = [PYTHON, "-m", "pytest", path, "--collect-only", "-q"]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"Failed to collect tests from {path}:")
        print(proc.stdout)
        print(proc.stderr)
        return []

    nodeids = []
    module = None
    cls = None

    for line in proc.stdout.split('\n'):
        line = line.strip()
        if line.startswith('<Module '):
            module = line[8:-1]
            # Add tests/ prefix if not present
            if not module.startswith('tests/'):
                module = 'tests/' + module
            cls = None
        elif line.startswith('<Class '):
            cls = line[7:-1]
        elif line.startswith('<Function '):
            func = line[10:-1]
            if module and cls:
                nodeids.append(f"{module}::{cls}::{func}")
            elif module:
                nodeids.append(f"{module}::{func}")
            else:
                nodeids.append(func)

    return nodeids


def run_test_isolated(nodeid: str) -> tuple[bool, str]:
    """Run a single test in isolated subprocess."""
    cmd = [PYTHON, "-m", "pytest", nodeid, "-v", "--tb=short"]
    try:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=180)
        out = proc.stdout + "\n" + proc.stderr
        return proc.returncode == 0, out
    except subprocess.TimeoutExpired as e:
        return False, f"TIMEOUT (180s): {e}"


def main():
    all_tests = []
    for path in UI_TEST_FILES:
        full_path = os.path.join(ROOT, path)
        if not os.path.exists(full_path):
            print(f"File not found: {path}")
            continue

        print(f"\n=== Coletando testes de {path} ===")
        tests = collect_test_nodeids(path)
        print(f"Encontrados {len(tests)} testes")
        all_tests.extend(tests)

    print(f"\n=== Total de {len(all_tests)} testes de UI para executar isoladamente ===\n")

    failed = []
    for i, nodeid in enumerate(all_tests, 1):
        print(f"[{i}/{len(all_tests)}] {nodeid}")
        success, output = run_test_isolated(nodeid)
        if success:
            print("  [OK] PASSOU")
        else:
            print("  [FAIL] FALHOU")
            print(output[:500])
            failed.append((nodeid, output))

    print(f"\n=== Resumo ===")
    print(f"Total: {len(all_tests)}")
    print(f"Passaram: {len(all_tests) - len(failed)}")
    print(f"Falharam: {len(failed)}")

    if failed:
        print("\nFalhas:")
        for nodeid, output in failed:
            print(f"  - {nodeid}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()