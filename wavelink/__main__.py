import argparse
import platform
import subprocess
import sys

import aiohttp
import discord

import wavelink


parser = argparse.ArgumentParser(prog='wavelink')
parser.add_argument('--version', action='store_true', help='Get version and debug information for wavelink.')


args = parser.parse_args()


def get_debug_info() -> None:
    python_info = '\n'.join(sys.version.split('\n'))
    java_version = subprocess.check_output(['java', '-version'], stderr=subprocess.STDOUT)
    java_version = f'\n{" " * 8}- '.join(v for v in java_version.decode().split('\r\n') if v)

    info: str = f"""
    Python:
        - {python_info}
    System:
        - {platform.platform()}
    Java:
        - {java_version or "Version Not Found"}
    Libraries:
        - wavelink   : v{wavelink.__version__}
        - discord.py : v{discord.__version__}
        - aiohttp    : v{aiohttp.__version__}
    """

    print(info)


if args.version:
    get_debug_info()

