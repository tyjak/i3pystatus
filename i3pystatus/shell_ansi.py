import re
import subprocess
from i3pystatus import Status, IntervalModule
from i3pystatus.core.command import run_through_shell


class AnsiShell(IntervalModule):
    """
    Runs a shell command that outputs ANSI color codes,
    converts them to i3bar-compatible colors,
    optionally loads colors from Xresources, allows manual overrides,
    supports ignore_empty_stdout and custom formatting like the shell module.
    """

    settings = (
        ("command", "Command to execute as a list or string"),
        ("ansi_color_map", "Optional dict mapping ANSI codes to hex colors"),
        ("default_color", "Fallback color if no ANSI code found"),
        ("interval", "Update interval in seconds"),
        ("ignore_empty_stdout", "Let the block be empty"),
        ("format", "Format string for output, e.g., 'Price: {output}'"),
    )

    required = ("command",)
    interval = 5
    default_color = "#FFFFFF"
    ignore_empty_stdout = False
    ansi_color_map = None
    format = "{output}"

    def _load_xresources(self):
        """
        Load ANSI color codes from Xresources via xrdb.
        Returns dict mapping ANSI code to hex color, or None if failed.
        """
        try:
            xres = subprocess.check_output(["/usr/bin/xrdb", "-query"], text=True)
            color_map = {}
            for line in xres.splitlines():
                if line.startswith("*.color"):
                    key, val = line.split(":", 1)
                    key = key.strip()        # *.color0 .. *.color15
                    val = val.strip()        # e.g. #ff0000
                    try:
                        num = int(key.replace("*.color", ""))
                    except ValueError:
                        continue
                    if 0 <= num <= 7:
                        ansi_code = str(30 + num)
                    elif 8 <= num <= 15:
                        ansi_code = str(90 + (num - 8))
                    else:
                        continue
                    color_map[ansi_code] = val
            return color_map or None
        except Exception:
            return None

    def parse_ansi_to_i3bar(self, output):
        """
        Convert ANSI-colored string to i3bar-compatible dict.
        Only the first ANSI code is considered.
        """
        match = re.search(r'\033\[(\d+)m', output)
        color = self.ansi_color_map.get(match.group(1), self.default_color) if match else self.default_color
        clean_text = re.sub(r'\033\[[0-9;]*m', '', output).strip()
        return clean_text, color

    def run(self):
        # initialize ANSI color map if not set
        if self.ansi_color_map is None:
            self.ansi_color_map = self._load_xresources()
            if self.ansi_color_map is None:
                # fallback to default ANSI → hex mapping
                self.ansi_color_map = {
                    '30': '#000000', '31': '#FF0000', '32': '#00FF00',
                    '33': '#FFFF00', '34': '#0000FF', '35': '#FF00FF',
                    '36': '#00FFFF', '37': '#FFFFFF',
                }

        try:
            retvalue, out, stderr = run_through_shell(self.command, enable_shell=True)

            if retvalue != 0:
                self.logger.error(stderr if stderr else "Unknown error")

            if out:
                out = out.replace("\n", " ").strip()
            elif stderr:
                out = stderr

            text, color = self.parse_ansi_to_i3bar(out)
            full_text = self.format.format(output=text)
            self.output = {"full_text": full_text, "color": color}

        except subprocess.CalledProcessError as e:
            if not text and not self.ignore_empty_stdout:
                self.output = {"full_text": f"Error: {e}", "color": "#FF0000"}


