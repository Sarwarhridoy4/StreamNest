from __future__ import annotations

import os
import platform
import shutil
import subprocess

import flet as ft


class FfmpegInstallMixin:
    def _on_install_ffmpeg(self, _: ft.ControlEvent) -> None:
        if self.ffmpeg_install_running:
            self._set_status("FFmpeg installation is already running.")
            return
        if not self.ffmpeg_missing:
            self._set_status("FFmpeg is already installed.")
            return
        if not self.ffmpeg_install_supported:
            self._show_popup("Automatic FFmpeg installation is not available on this platform.", ft.Colors.RED_700)
            return

        plan, error_message = self._resolve_ffmpeg_install_plan()
        if error_message:
            self._show_popup(error_message, ft.Colors.RED_700)
            self._set_status(error_message)
            return

        self.pending_ffmpeg_install_plan = plan
        preview_lines = [
            f"{'sudo ' if requires_sudo else ''}{' '.join(command)}"
            for command, requires_sudo in plan
        ]
        needs_password = self._install_plan_requires_password(plan)
        prompt = (
            "Run the following command(s) to install FFmpeg?\n\n"
            + "\n".join(preview_lines)
            + ("\n\nA password prompt will appear for privileged commands." if needs_password else "")
        )
        self.ffmpeg_install_confirm_dialog.content = ft.Text(prompt, selectable=True)
        try:
            self.page.show_dialog(self.ffmpeg_install_confirm_dialog)
        except Exception:
            self._show_popup("Unable to open install confirmation dialog.", ft.Colors.RED_700)

    def _is_ffmpeg_missing(self) -> bool:
        """Backward-compatible wrapper for FFmpeg presence check."""
        try:
            return self.ffmpeg_utils.is_ffmpeg_missing()
        except Exception:
            return True

    def _build_ffmpeg_install_hint(self) -> str:
        """Backward-compatible wrapper for FFmpeg install hint."""
        try:
            return self.ffmpeg_utils.build_ffmpeg_install_hint()
        except Exception:
            return "FFmpeg not found."

    def _on_recheck_ffmpeg(self, _: ft.ControlEvent) -> None:
        # Compatibility: support older environments where _is_ffmpeg_missing may not exist
        try:
            self.ffmpeg_missing = self._is_ffmpeg_missing()
        except AttributeError:
            self.ffmpeg_missing = self.ffmpeg_utils.is_ffmpeg_missing()
        try:
            self.ffmpeg_install_hint = self._build_ffmpeg_install_hint()
        except AttributeError:
            self.ffmpeg_install_hint = self.ffmpeg_utils.build_ffmpeg_install_hint()
        self.ffmpeg_warning_text.value = self.ffmpeg_install_hint
        self.welcome_ffmpeg_warning_text.value = self.ffmpeg_install_hint
        self.ffmpeg_warning_text.visible = self.ffmpeg_missing
        self.welcome_ffmpeg_warning_text.visible = self.ffmpeg_missing
        self.install_ffmpeg_btn.visible = self.ffmpeg_missing and self.ffmpeg_install_supported
        self.welcome_install_ffmpeg_btn.visible = self.ffmpeg_missing and self.ffmpeg_install_supported
        status = "FFmpeg detected." if not self.ffmpeg_missing else "FFmpeg still not detected in PATH."
        self._set_status(status)
        self._show_popup(status, ft.Colors.GREEN_700 if not self.ffmpeg_missing else ft.Colors.RED_700)

    def _on_open_ffmpeg_log(self, _: ft.ControlEvent) -> None:
        if not self.ffmpeg_install_logs:
            self._show_popup("No FFmpeg install log available yet.", ft.Colors.BLUE_GREY_700)
            return
        self._refresh_ffmpeg_log_text()
        try:
            self.page.show_dialog(self.ffmpeg_log_dialog)
        except Exception:
            self._show_popup("Unable to open FFmpeg log dialog.", ft.Colors.RED_700)

    def _on_close_ffmpeg_log_dialog(self, _: ft.ControlEvent) -> None:
        try:
            self.page.pop_dialog()
        except Exception:
            self.ffmpeg_log_dialog.open = False
            self._page_update()

    def _on_open_ytdlp_log(self, _: ft.ControlEvent) -> None:
        if not self.ytdlp_logs:
            self._show_popup("No yt-dlp log available yet.", ft.Colors.BLUE_GREY_700)
            return
        self._refresh_ytdlp_log_text()
        try:
            self.page.show_dialog(self.ytdlp_log_dialog)
        except Exception:
            self._show_popup("Unable to open yt-dlp log dialog.", ft.Colors.RED_700)

    def _on_close_ytdlp_log_dialog(self, _: ft.ControlEvent) -> None:
        try:
            self.page.pop_dialog()
        except Exception:
            self.ytdlp_log_dialog.open = False
            self._page_update()

    def _reset_ffmpeg_install_logs(self) -> None:
        self.ffmpeg_install_logs = []
        self._refresh_ffmpeg_log_text()

    def _append_ffmpeg_install_log(self, line: str) -> None:
        normalized = line.rstrip()
        if not normalized:
            return
        self.ffmpeg_install_logs.append(normalized)
        if len(self.ffmpeg_install_logs) > 600:
            self.ffmpeg_install_logs = self.ffmpeg_install_logs[-600:]
        self._refresh_ffmpeg_log_text()

    def _refresh_ffmpeg_log_text(self) -> None:
        self.ffmpeg_log_text.value = "\n".join(self.ffmpeg_install_logs)
        self._page_update()

    def _reset_ytdlp_logs(self) -> None:
        self.ytdlp_logs = []
        self._refresh_ytdlp_log_text()

    def _append_ytdlp_log(self, line: str) -> None:
        normalized = line.rstrip()
        if not normalized:
            return
        self.ytdlp_logs.append(normalized)
        if len(self.ytdlp_logs) > 1200:
            self.ytdlp_logs = self.ytdlp_logs[-1200:]
        self._refresh_ytdlp_log_text()

    def _refresh_ytdlp_log_text(self) -> None:
        self.ytdlp_log_text.value = "\n".join(self.ytdlp_logs)
        self._page_update()

    def _resolve_ffmpeg_install_plan(self) -> tuple[list[tuple[list[str], bool]], str | None]:
        system = platform.system().lower()
        if system.startswith("windows"):
            if shutil.which("winget") is None:
                return [], "Winget was not found. Install App Installer from Microsoft Store, then retry."
            return [
                (
                    [
                        "winget",
                        "install",
                        "--id",
                        "Gyan.FFmpeg",
                        "-e",
                        "--accept-package-agreements",
                        "--accept-source-agreements",
                    ],
                    False,
                )
            ], None

        if system == "darwin":
            if shutil.which("brew") is None:
                return [], "Homebrew was not found. Install Homebrew first, then run FFmpeg install again."
            return [(["brew", "install", "ffmpeg"], False)], None

        if system.startswith("linux"):
            if os.geteuid() != 0 and shutil.which("sudo") is None:
                return [], "sudo is required for automatic installation. Install FFmpeg manually or run the app as root."
            if shutil.which("apt-get"):
                return [(["apt-get", "update"], True), (["apt-get", "install", "-y", "ffmpeg"], True)], None
            if shutil.which("dnf"):
                return [(["dnf", "install", "-y", "ffmpeg"], True)], None
            if shutil.which("yum"):
                return [(["yum", "install", "-y", "ffmpeg"], True)], None
            if shutil.which("pacman"):
                return [(["pacman", "-S", "--noconfirm", "ffmpeg"], True)], None
            if shutil.which("zypper"):
                return [(["zypper", "--non-interactive", "install", "ffmpeg"], True)], None
            return [], "No supported package manager was detected. Install FFmpeg manually for your distribution."

        return [], "Automatic FFmpeg installation is unsupported on this platform."

    def _install_plan_requires_password(self, plan: list[tuple[list[str], bool]]) -> bool:
        if not any(requires_sudo for _, requires_sudo in plan):
            return False
        if os.geteuid() == 0:
            return False
        try:
            check = subprocess.run(  # noqa: S603
                ["sudo", "-n", "true"],
                capture_output=True,
                text=True,
                check=False,
            )
            return check.returncode != 0
        except Exception:
            return True

    def _on_ffmpeg_install_confirmed(self, _: ft.ControlEvent) -> None:
        try:
            self.page.pop_dialog()
        except Exception:
            self.ffmpeg_install_confirm_dialog.open = False
        if not self.pending_ffmpeg_install_plan:
            self._set_status("No FFmpeg install plan available.")
            return

        if self._install_plan_requires_password(self.pending_ffmpeg_install_plan):
            self.ffmpeg_password_field.value = ""
            try:
                self.page.show_dialog(self.ffmpeg_password_dialog)
            except Exception:
                self._show_popup("Unable to open password dialog.", ft.Colors.RED_700)
            return
        self._start_ffmpeg_install_worker(password=None)

    def _on_ffmpeg_password_submit(self, _: ft.ControlEvent) -> None:
        password = (self.ffmpeg_password_field.value or "").strip()
        try:
            self.page.pop_dialog()
        except Exception:
            self.ffmpeg_password_dialog.open = False
        if not password:
            self._set_status("Installation canceled: password is required for privileged commands.")
            return
        self._start_ffmpeg_install_worker(password=password)

    def _start_ffmpeg_install_worker(self, password: str | None) -> None:
        if self.ffmpeg_install_running:
            return
        self.ffmpeg_install_running = True
        self._reset_ffmpeg_install_logs()
        self._append_ffmpeg_install_log("Starting FFmpeg installation...")
        try:
            self.page.show_dialog(self.ffmpeg_log_dialog)
        except Exception:
            self._show_popup("Unable to open FFmpeg log dialog.", ft.Colors.RED_700)
        self.install_ffmpeg_btn.disabled = True
        self.welcome_install_ffmpeg_btn.disabled = True
        self._refresh_view()
        self.page.run_thread(self._run_ffmpeg_install_worker, list(self.pending_ffmpeg_install_plan), password)

    def _run_ffmpeg_install_worker(self, plan: list[tuple[list[str], bool]], password: str | None) -> None:
        total_steps = len(plan)
        for idx, (command, requires_sudo) in enumerate(plan, start=1):
            self._run_ui(lambda idx=idx, total_steps=total_steps: self._set_status(f"Installing FFmpeg ({idx}/{total_steps})..."))
            cmd_display = f"{'sudo ' if requires_sudo else ''}{' '.join(command)}"
            self._run_ui(lambda cmd_display=cmd_display: self._append_ffmpeg_install_log(f"$ {cmd_display}"))
            success, output = self._run_install_command(command, requires_sudo, password)
            if not success:
                self._run_ui(lambda output=output: self._append_ffmpeg_install_log(f"ERROR: {output}"))
                self._run_ui(lambda output=output: self._set_status(f"FFmpeg install failed: {output}"))
                self._run_ui(lambda output=output: self._show_popup(f"FFmpeg install failed: {output}", ft.Colors.RED_700))
                self._run_ui(self._complete_ffmpeg_install_attempt)
                return
            self._run_ui(lambda: self._append_ffmpeg_install_log("Command finished successfully."))

        self._run_ui(self._finalize_ffmpeg_install)

    def _run_install_command(self, command: list[str], requires_sudo: bool, password: str | None) -> tuple[bool, str]:
        full_command = command
        input_data = None

        if requires_sudo and os.geteuid() != 0:
            full_command = ["sudo", "-S"] + command
            if password:
                input_data = f"{password}\n"

        output_lines: list[str] = []
        try:
            process = subprocess.Popen(  # noqa: S603
                full_command,
                stdin=subprocess.PIPE if input_data is not None else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except Exception as exc:
            return False, str(exc)

        if input_data is not None and process.stdin is not None:
            try:
                process.stdin.write(input_data)
                process.stdin.flush()
            except Exception:
                pass
            finally:
                try:
                    process.stdin.close()
                except Exception:
                    pass

        if process.stdout is not None:
            for raw_line in process.stdout:
                line = raw_line.rstrip()
                if line:
                    output_lines.append(line)
                    self._run_ui(lambda line=line: self._append_ffmpeg_install_log(line))

        return_code = process.wait()
        if return_code == 0:
            return True, (output_lines[-1] if output_lines else "OK")

        error_message = output_lines[-1] if output_lines else "Unknown command failure"
        if "sudo" in " ".join(full_command) and "password" in error_message.lower():
            return False, "Invalid password or sudo denied access."
        return False, error_message

    def _finalize_ffmpeg_install(self) -> None:
        self.ffmpeg_missing = self._is_ffmpeg_missing()
        self.ffmpeg_install_hint = self._build_ffmpeg_install_hint()
        self._complete_ffmpeg_install_attempt()
        if self.ffmpeg_missing:
            self._append_ffmpeg_install_log("Install completed, but ffmpeg was not detected in PATH.")
            self._set_status(
                "Install command completed, but ffmpeg is still not in PATH. Restart the app or add FFmpeg to PATH."
            )
            self._show_popup("FFmpeg not yet detected in PATH.", ft.Colors.RED_700)
            return
        self._append_ffmpeg_install_log("FFmpeg installed and detected in PATH.")
        self._set_status("FFmpeg installed and detected.")
        self._show_popup("FFmpeg installed successfully.", ft.Colors.GREEN_700)

    def _complete_ffmpeg_install_attempt(self) -> None:
        self.ffmpeg_install_running = False
        self.pending_ffmpeg_install_plan = []
        self.ffmpeg_warning_text.value = self.ffmpeg_install_hint
        self.welcome_ffmpeg_warning_text.value = self.ffmpeg_install_hint
        self.ffmpeg_warning_text.visible = self.ffmpeg_missing
        self.welcome_ffmpeg_warning_text.visible = self.ffmpeg_missing
        self.install_ffmpeg_btn.visible = self.ffmpeg_missing and self.ffmpeg_install_supported
        self.welcome_install_ffmpeg_btn.visible = self.ffmpeg_missing and self.ffmpeg_install_supported
        self.install_ffmpeg_btn.disabled = False
        self.welcome_install_ffmpeg_btn.disabled = False
        self._refresh_view()
