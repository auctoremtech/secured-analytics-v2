#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def _ensure_virtualenv():
    """Restart script under local .venv Python if not already running there."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    venv_base = os.path.join(project_root, ".venv")
    if os.name == "nt":
        venv_python = os.path.join(venv_base, "Scripts", "python.exe")
    else:
        venv_python = os.path.join(venv_base, "bin", "python")

    if os.path.isfile(venv_python):
        current = os.path.abspath(sys.executable)
        expected = os.path.abspath(venv_python)
        if current != expected:
            os.execv(expected, [expected] + sys.argv)


def main():
    """Run administrative tasks."""
    _ensure_virtualenv()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "securedAnalytics.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
