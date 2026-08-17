from __future__ import annotations
import os
import sys


def get_project_root() -> str:
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
        )
    )


def get_assets_dir() -> str:
    return os.path.join(get_project_root(), "assets")


def get_config_dir() -> str:
    return os.path.join(get_project_root(), "config")


def get_sql_dir() -> str:
    return os.path.join(get_project_root(), "sql")


def get_docs_dir() -> str:
    return os.path.join(get_project_root(), "docs")
