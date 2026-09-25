from __future__ import annotations

import re
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


class WindowsLauncherContractTests(unittest.TestCase):
    """Static Windows 11 contracts that also work on the Linux test runner."""

    SETUP_CMD = "Setup-and-Run-VAP-Seaborn-Stack.cmd"
    DEMO_CMD = "VAP-Seaborn-Stack.cmd"
    UI_CMD = "VAP-Seaborn-Stack-UI.cmd"
    SETUP_PS1 = "Setup-VAP-Seaborn-Stack.ps1"
    RUN_PS1 = "Run-VAP-Seaborn-Stack.ps1"

    def test_batch_launchers_are_utf8_decodable_and_use_script_directory(self) -> None:
        for name in (self.SETUP_CMD, self.DEMO_CMD, self.UI_CMD):
            with self.subTest(name=name):
                source = read_text(name)
                self.assertIn("%~dp0", source)
                self.assertRegex(source, r'(?i)set\s+"SCRIPT_DIR=%~dp0"')
                self.assertNotIn("cd %SCRIPT_DIR%", source)

    def test_batch_launchers_preserve_child_exit_code(self) -> None:
        for name in (self.SETUP_CMD, self.DEMO_CMD, self.UI_CMD):
            with self.subTest(name=name):
                source = read_text(name)
                self.assertRegex(source, r'(?i)set\s+"EXIT_CODE=%ERRORLEVEL%"')
                self.assertRegex(source, r'(?i)exit\s+/b\s+%EXIT_CODE%')

    def test_powershell_entrypoints_prefer_pwsh_7_with_legacy_fallback(self) -> None:
        """PS7 correctly reads UTF-8/no-BOM scripts; 5.1 remains a fallback."""
        for name in (self.SETUP_CMD, self.DEMO_CMD):
            with self.subTest(name=name):
                source = read_text(name).lower()
                self.assertIn("pwsh.exe", source)
                self.assertIn("powershell.exe", source)
                self.assertLess(source.index("pwsh.exe"), source.rindex("powershell.exe"))

    def test_legacy_powershell_fallback_can_decode_chinese_messages(self) -> None:
        """Windows PowerShell 5.1 treats a BOM-less script as the ANSI code page."""
        utf8_bom = b"\xef\xbb\xbf"
        for name in (self.SETUP_PS1, self.RUN_PS1):
            with self.subTest(name=name):
                payload = (ROOT / name).read_bytes()
                has_non_ascii = any(byte > 0x7F for byte in payload)
                self.assertTrue(
                    payload.startswith(utf8_bom) or not has_non_ascii,
                    f"{name} contains Chinese UTF-8 text but no BOM for powershell.exe 5.1.",
                )

    def test_batch_powershell_file_paths_are_quoted(self) -> None:
        cases = {
            self.SETUP_CMD: "Setup-VAP-Seaborn-Stack.ps1",
            self.DEMO_CMD: "Run-VAP-Seaborn-Stack.ps1",
        }
        for name, script in cases.items():
            with self.subTest(name=name):
                source = read_text(name)
                self.assertIn(f'"%SCRIPT_DIR%{script}"', source)

    def test_setup_checks_exact_python_312_for_existing_and_new_venv(self) -> None:
        source = read_text(self.SETUP_PS1)
        self.assertIn("sys.version_info[:2] == (3, 12)", source)
        self.assertIn('Join-Path $VenvRoot "Scripts\\python.exe"', source)
        self.assertIn("-m venv $VenvRoot", source)
        self.assertIn("-r $Requirements", source)

    def test_setup_uses_literal_paths_and_restores_callers_location(self) -> None:
        source = read_text(self.SETUP_PS1)
        self.assertGreaterEqual(source.count("Test-Path -LiteralPath"), 2)
        self.assertIn("Push-Location $ScriptRoot", source)
        self.assertRegex(source, r"(?s)try\s*\{.*\}\s*finally\s*\{\s*Pop-Location\s*\}")

    def test_ui_fast_path_validates_python_312_before_pythonw(self) -> None:
        """A stale copied .venv must not make the GUI disappear without a message."""
        source = read_text(self.UI_CMD)
        has_inline_probe = bool(
            re.search(r"(?i)(version_info|python\s+3\.12|-3\.12)", source)
        )
        has_validating_ps1_route = bool(
            re.search(r"(?i)Setup-VAP-Seaborn-Stack\.ps1", source)
        )
        self.assertTrue(
            has_inline_probe or has_validating_ps1_route,
            "UI fast path launches pythonw merely because it exists; validate Python 3.12 first.",
        )

    def test_run_script_passes_values_as_argument_arrays_without_eval(self) -> None:
        source = read_text(self.RUN_PS1)
        self.assertIn("@PythonPrefix @CommandArguments", source)
        self.assertIn('$CommandArguments += @("--source", $Source)', source)
        self.assertNotRegex(source, r"(?i)Invoke-Expression|\biex\b")

    def test_run_script_rejects_missing_required_action_arguments(self) -> None:
        source = read_text(self.RUN_PS1)
        self.assertIn('if (-not $Id) { throw "render-one', source)
        self.assertIn('if (-not $Source) { throw "$Action', source)
        self.assertIn("if ($LASTEXITCODE -ne 0)", source)

    def test_open_output_supports_rooted_output_directories_and_configured_formats(self) -> None:
        source = read_text(self.RUN_PS1)
        self.assertRegex(source, r"(?i)(IsPathRooted|Split-Path\s+-IsAbsolute)")
        self.assertRegex(source, r"(?i)output_formats")
        self.assertNotRegex(
            source,
            r'\$ConfigObject\.project\.output_name\s*\+\s*"\.png"',
            "-OpenOutput must not silently require PNG when HTML/PDF/SVG are configured.",
        )

    def test_powershell_files_parse_when_pwsh_is_available(self) -> None:
        pwsh = shutil.which("pwsh") or shutil.which("pwsh.exe")
        if not pwsh:
            self.skipTest("PowerShell 7 is not installed on this Linux runner")
        parser = (
            "param($p) "
            "$tokens=$null; $errors=$null; "
            "[System.Management.Automation.Language.Parser]::ParseFile("
            "$p,[ref]$tokens,[ref]$errors) | Out-Null; "
            "if($errors.Count){$errors | ForEach-Object {Write-Error $_}; exit 1}"
        )
        for name in (self.SETUP_PS1, self.RUN_PS1):
            with self.subTest(name=name):
                completed = subprocess.run(
                    [pwsh, "-NoLogo", "-NoProfile", "-Command", parser, str(ROOT / name)],
                    text=True,
                    capture_output=True,
                    timeout=30,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
