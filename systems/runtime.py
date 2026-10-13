"""Caminhos e diagnóstico seguros para desenvolvimento e builds Windows."""

from __future__ import annotations

import logging
import os
from pathlib import Path
import sys


DEMO_VERSION = "0.5.0-demo.1"
IS_FROZEN = bool(getattr(sys, "frozen", False))
PROJECT_ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))


def resource_path(*parts: str) -> Path:
    """Retorna um recurso tanto no projeto quanto no bundle do PyInstaller."""
    return PROJECT_ROOT.joinpath(*parts)


def user_data_dir() -> Path:
    """Builds usam AppData; desenvolvimento continua isolado no projeto."""
    if not IS_FROZEN:
        return resource_path("missao_estoque")
    base = Path(os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or Path.home())
    return base / "MissaoEstoqueDemo"


def ensure_user_dirs() -> Path:
    root = user_data_dir()
    root.mkdir(parents=True, exist_ok=True)
    (root / "logs").mkdir(exist_ok=True)
    return root


def configure_logging() -> Path:
    log_path = ensure_user_dirs() / "logs" / "game.log"
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        encoding="utf-8",
        force=True,
    )
    logging.info("Iniciando Missão: Estoque Perfeito DEMO %s", DEMO_VERSION)
    return log_path


def write_crash_log(traceback_text: str) -> Path:
    path = ensure_user_dirs() / "logs" / "crash.log"
    path.write_text(traceback_text, encoding="utf-8")
    return path
