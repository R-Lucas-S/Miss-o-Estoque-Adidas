"""Gera a demo Windows one-folder e seu ZIP reproduzível."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


VERSION = "0.5.0-demo.1"
ROOT = Path(__file__).resolve().parent
DIST_ROOT = ROOT / "dist"
RELEASE_DIR = DIST_ROOT / f"MissaoEstoque_Demo_v{VERSION}"


def run(debug: bool, skip_zip: bool) -> None:
    mode = "debug" if debug else "final"
    build_id = f"{int(time.time())}_{os.getpid()}"
    staging_root = DIST_ROOT / f"staging_{mode}_{build_id}"
    pyinstaller_output = staging_root / "MissaoEstoque_Demo"
    env = os.environ.copy()
    env["MISSAO_DEMO_CONSOLE"] = "1" if debug else "0"
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--workpath",
        str(ROOT / "build" / f"demo_work_{mode}_{build_id}"),
        "--distpath",
        str(staging_root),
        "MissaoEstoque_Demo.spec",
    ]
    subprocess.run(command, cwd=ROOT, env=env, check=True)

    # Copy incremental evita falhas de bloqueio do OneDrive/antivírus em
    # diretórios que acabaram de ser examinados. Uma nova versão sempre cria
    # outra pasta, portanto arquivos antigos não contaminam releases futuras.
    shutil.copytree(pyinstaller_output, RELEASE_DIR, dirs_exist_ok=True)
    shutil.copy2(ROOT / "README_DEMO.txt", RELEASE_DIR / "README.txt")

    if skip_zip:
        return
    archive_base = DIST_ROOT / f"MissaoEstoque_Demo_v{VERSION}_Windows"
    zip_path = Path(shutil.make_archive(str(archive_base), "zip", DIST_ROOT, RELEASE_DIR.name))
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    zip_path.with_suffix(".sha256.txt").write_text(
        f"{digest}  {zip_path.name}\n", encoding="ascii"
    )
    print(f"BUILD: {RELEASE_DIR}")
    print(f"ZIP:   {zip_path}")
    print(f"SHA-256: {digest}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="mantém o console para diagnóstico")
    parser.add_argument("--skip-zip", action="store_true", help="gera somente a pasta")
    args = parser.parse_args()
    run(args.debug, args.skip_zip)
