"""Desktop GUI for MiR control. Thin UI over mir.MirClient."""

__all__ = ["main"]


def main() -> int:
    from gui.app import run_app

    return run_app()
