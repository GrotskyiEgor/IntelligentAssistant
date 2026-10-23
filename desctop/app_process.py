import os
import sys

from PyQt6.QtCore import QProcess, QProcessEnvironment


class AssistantProcessMixin:
    def start_assintant(self):
        if self.assistant_process is not None:
            return

        self.assistant_process = QProcess(self)

        env = QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONIOENCODING", "utf-8")
        self.assistant_process.setProcessEnvironment(env)

        self.assistant_process.readyReadStandardOutput.connect(
            self.read_output
        )

        self.assistant_process.readyReadStandardError.connect(
            self.read_output
        )

        self.assistant_process.finished.connect(
            self.assistant_fineshed
        )

        self.assistant_process.setProcessChannelMode(
            QProcess.ProcessChannelMode.MergedChannels
        )

        python = sys.executable

        base_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

        manage_py = os.path.join(
            base_dir,
            "assistant",
            "manage.py"
        )

        self.assistant_process.start(
            python,
            [manage_py, "run_assistant"]
        )

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.restart_btn.setEnabled(True)

    def stop_assintant(self, on_stopped=None):
        process = self.assistant_process

        if process is None:
            if on_stopped:
                on_stopped()
            return

        def _handle_finished(*args):
            try:
                process.finished.disconnect(_handle_finished)
            except (TypeError, RuntimeError):
                pass

            if on_stopped:
                on_stopped()

        process.finished.connect(_handle_finished)
        process.kill()

    def restart_assintant(self):
        if self.assistant_process is None:
            self.start_assintant()
            return

        self.restart_btn.setEnabled(False)

        self.stop_assintant(
            on_stopped=self.start_assintant
        )

    def read_output(self):
        data = self.assistant_process.readAllStandardOutput()

        text = bytes(data).decode(
            "utf-8",
            errors="replace"
        )

        if not text:
            return

        print(text, end="")

        for line in text.splitlines():
            line = line.strip()

            if line.startswith("ANSWER:"):
                answer = line[len("ANSWER:"):].strip()

                if answer:
                    self.add_message(self.assistant_display_name(), answer)

    def read_error(self):
        data = self.assistant_process.readAllStandardError()

        text = bytes(data).decode(
            "utf-8",
            errors="replace"
        )

        if text:
            print("ERROR:", text, end="")

    def assistant_fineshed(self, *args):
        print("Помічник завершив роботу.")

        if self.assistant_process is not None:
            self.assistant_process.deleteLater()
            self.assistant_process = None

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.restart_btn.setEnabled(False)
