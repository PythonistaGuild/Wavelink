"""Copyright 2026 Evie. P. <evieepy@gmail.com>, PythonistaGuild

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import argparse
import platform
import subprocess
import sys

import wavelink


parser = argparse.ArgumentParser(prog="wavelink")
parser.add_argument("--version", action="store_true", help="Get version and debug information for wavelink.")


args = parser.parse_args()


def get_debug_info() -> None:
    python_info = "\n".join(sys.version.split("\n"))
    java_version = subprocess.check_output(["java", "-version"], stderr=subprocess.STDOUT)
    java_version = f"\n{' ' * 8}- ".join(v for v in java_version.decode().split("\r\n") if v)

    info: str = f"""
    wavelink: {wavelink.__version__}

    Python:
        - {python_info}
    System:
        - {platform.platform()}
    Java:
        - {java_version or "Version Not Found"}
    """

    print(info)


if args.version:
    get_debug_info()
