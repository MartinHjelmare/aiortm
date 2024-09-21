"""Test the CLI can be run as a Python module."""

import subprocess
import sys


def test_can_run_as_python_module() -> None:
    """Run the CLI as a Python module."""
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "aiortm", "--help"],
        check=True,
        capture_output=True,
    )
    assert result.returncode == 0
    assert b"aiortm [OPTIONS]" in result.stdout
