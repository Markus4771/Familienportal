from pathlib import Path
import subprocess


SCRIPTS = [
    Path("deploy/install.sh"),
    Path("deploy/release-install.sh"),
    Path("deploy/familienportalctl"),
    Path("deploy/familienportal-release"),
]


def test_deployment_scripts_have_valid_bash_syntax():
    for script in SCRIPTS:
        subprocess.run(["bash", "-n", str(script)], check=True)


def test_lifecycle_manager_contains_required_commands():
    text = Path("deploy/familienportalctl").read_text(encoding="utf-8")
    for command in ("backup", "update", "rollback", "remove", "status", "version"):
        assert command in text


def test_release_installer_verifies_checksum():
    text = Path("deploy/release-install.sh").read_text(encoding="utf-8")
    assert "sha256sum -c" in text
    assert "releases/latest" in text
