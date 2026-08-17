import argparse
import logging
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPEC_FILE = PROJECT_ROOT / "SerPleno.spec"


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Automatiza a geracao do executavel desktop do SerPleno."
    )
    parser.add_argument(
        "--name",
        default="SerPleno",
        help="Nome do executavel final (sem extensao). Default: SerPleno",
    )
    parser.add_argument(
        "--onefile",
        action="store_true",
        default=True,
        help="Gera executavel em arquivo unico (default).",
    )
    parser.add_argument(
        "--no-onefile",
        action="store_false",
        dest="onefile",
        help="Gera executavel em pasta.",
    )
    parser.add_argument(
        "--windowed",
        action="store_true",
        default=True,
        help="Executavel sem console (default).",
    )
    parser.add_argument(
        "--console",
        action="store_false",
        dest="windowed",
        help="Executavel com console visivel.",
    )
    return parser.parse_args()


def clean_build_artifacts() -> None:
    logging.info("Limpando builds anteriores...")
    dirs_to_remove = [PROJECT_ROOT / "dist", PROJECT_ROOT / "build"]
    for directory in dirs_to_remove:
        if directory.exists():
            shutil.rmtree(directory)
            logging.info("Removido: %s", directory)

    spec_files = list(PROJECT_ROOT.glob("*.spec"))
    for spec_file in spec_files:
        spec_file.unlink()
        logging.info("Removido: %s", spec_file)


def ensure_spec_exists(name: str, onefile: bool, windowed: bool) -> Path:
    if SPEC_FILE.exists():
        try:
            existing_content = SPEC_FILE.read_text(encoding="utf-8")
            if f'name="{name}"' in existing_content:
                logging.info("Usando spec existente: %s", SPEC_FILE)
                return SPEC_FILE
            else:
                logging.info("Nome diferente detectado, regenerando spec...")
        except Exception:
            pass

    logging.info("Gerando %s dinamicamente...", SPEC_FILE)
    entry_point = PROJECT_ROOT / "src" / "ser_pleno" / "app.py"

    datas_lines = []
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        datas_lines.append(f'    (r"{env_path}", "."),')

    config_dir = PROJECT_ROOT / "config"
    if config_dir.exists():
        for item in config_dir.iterdir():
            if item.is_file():
                datas_lines.append(f'    (r"{item}", "config"),')

    assets_dir = PROJECT_ROOT / "src" / "ser_pleno" / "assets"
    if assets_dir.exists():
        datas_lines.append(f'    (r"{assets_dir}", "ser_pleno/assets"),')

    sql_dir = PROJECT_ROOT / "src" / "ser_pleno" / "sql"
    if sql_dir.exists():
        datas_lines.append(f'    (r"{sql_dir}", "ser_pleno/sql"),')

    datas_block = "\n".join(datas_lines) if datas_lines else ""

    hidden_imports = [
        "customtkinter",
        "PIL",
        "PIL._tkinter_finder",
        "PIL.ImageTk",
        "darkdetect",
        "matplotlib",
        "matplotlib.backends.backend_tkagg",
        "numpy",
        "mysql.connector",
    ]
    hidden_block = ",\n        ".join(f'"{imp}"' for imp in hidden_imports)

    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
import os

base_dir = r"{PROJECT_ROOT}"
entry_point = r"{entry_point}"

datas = [
{datas_block}
]

a = Analysis(
    [entry_point],
    pathex=["src", base_dir],
    binaries=[],
    datas=datas,
    hiddenimports=[
        {hidden_block}
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    exclude_binaries=False,
    name="{name}",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console={str(not windowed).capitalize()},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile={str(onefile).capitalize()},
)
"""
    SPEC_FILE.write_text(spec_content, encoding="utf-8")
    logging.info("Spec gerado: %s", SPEC_FILE)
    return SPEC_FILE


def build(spec_path: Path, name: str) -> None:
    logging.info("Executando PyInstaller...")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_path),
    ]
    logging.info("Comando: %s", " ".join(cmd))
    result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        logging.error("PyInstaller falhou:\n%s\n%s", result.stdout, result.stderr)
        raise SystemExit(1)

    logging.info("Build concluido.")
    dist_dir = PROJECT_ROOT / "dist"
    if not dist_dir.exists():
        logging.error("Pasta dist/ nao encontrada apos build.")
        raise SystemExit(1)

    logging.info("Arquivos em dist/:")
    for item in dist_dir.iterdir():
        logging.info("  %s", item.name)


def main() -> None:
    args = parse_args()
    setup_logging()
    logging.info("Build iniciado em: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logging.info("Nome: %s | OneFile: %s | Windowed: %s", args.name, args.onefile, args.windowed)

    clean_build_artifacts()
    spec_path = ensure_spec_exists(args.name, args.onefile, args.windowed)
    build(spec_path, args.name)
    logging.info("Build finalizado com sucesso.")


if __name__ == "__main__":
    main()
