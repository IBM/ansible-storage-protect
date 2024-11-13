import subprocess
class CommandExecutor:
    """Executes commands and returns the output."""

    @staticmethod
    def execute(command):
        """Executes a command and returns its output."""
        try:
            result = subprocess.run(command, shell=True, text=True, capture_output=True)

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error: {result.stderr.strip() or 'Command failed with no stderr output.'}"
        except FileNotFoundError as e:
            return f"FileNotFoundError: {str(e)}"