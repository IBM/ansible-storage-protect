import subprocess

class CommandExecutor:
    """Executes commands and returns the output and the return code."""

    @staticmethod
    def execute(command):
        """Executes a command and returns its output and return code."""
        try:
            result = subprocess.run(command, shell=True, text=True, capture_output=True)

            # Return both the command output and the return code
            return result.stdout.strip(), result.returncode, result.stderr.strip()
        except FileNotFoundError as e:
            return f"FileNotFoundError: {str(e)}", 1  # Non-zero return code on error
