"""MIT License

Copyright (c) 2019-2022 PythonistaGuild

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import argparse
import asyncio
import pathlib
import sys
import typing

import aiohttp


parser = argparse.ArgumentParser()
parser.add_argument('--java', action='store_true')

args = parser.parse_args()
get_java = args.java


RELEASES = 'https://api.github.com/repos/freyacodes/Lavalink/releases/latest'
JAVA = 'https://download.oracle.com/java/17/archive/jdk-17.0.3.1_windows-x64_bin.exe'


if get_java and sys.platform != 'win32':
    raise RuntimeError('Downloading and installing Java is only supported on Windows.')

if get_java:
    import ctypes
    import os

    try:
        is_admin = os.getuid() == 0
    except AttributeError:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0

    if not is_admin:
        raise RuntimeError('This script requires administrator privileges to install Java.\n'
                           'Please restart the script in Command Prompt or Powershell as an administrator.')


_application_yml = """
server: # REST and WS server
  port: {port}
  address: {address}
lavalink:
  server:
    password: "{password}"
    sources:
      youtube: true
      bandcamp: true
      soundcloud: true
      twitch: true
      vimeo: true
      http: true
      local: false
    bufferDurationMs: 400 # The duration of the NAS buffer. Higher values fare better against longer GC pauses
    frameBufferDurationMs: 5000 # How many milliseconds of audio to keep buffered
    youtubePlaylistLoadLimit: 6 # Number of pages at 100 each
    playerUpdateInterval: 5 # How frequently to send player updates to clients, in seconds
    youtubeSearchEnabled: true
    soundcloudSearchEnabled: true
    gc-warnings: true
    #ratelimit:
      #ipBlocks: ["1.0.0.0/8", "..."] # list of ip blocks
      #excludedIps: ["...", "..."] # ips which should be explicit excluded from usage by lavalink
      #strategy: "RotateOnBan" # RotateOnBan | LoadBalance | NanoSwitch | RotatingNanoSwitch
      #searchTriggersFail: true # Whether a search 429 should trigger marking the ip as failing
      #retryLimit: -1 # -1 = use default lavaplayer value | 0 = infinity | >0 = retry will happen this numbers times

metrics:
  prometheus:
    enabled: false
    endpoint: /metrics

sentry:
  dsn: ""
  environment: ""
#  tags:
#    some_key: some_value
#    another_key: another_value

logging:
  file:
    max-history: 30
    max-size: 1GB
  path: ./logs/

  level:
    root: INFO
    lavalink: INFO
"""


async def download(location: pathlib.Path, *, url: str) -> None:
    lavalink = None

    async with aiohttp.ClientSession() as session:
        async with session.get(url=url) as head_resp:
            if url == RELEASES:

                data = await head_resp.json()
                assets = data['assets']

                for asset in assets:
                    if asset['name'] == 'Lavalink.jar':

                        length = asset['size']
                        lavalink = asset['browser_download_url']
                        chunks = round(length / 1024)
                        break
            else:
                length = head_resp.content_length
                chunks = round(length / 1024)

        if lavalink:
            file = 'Lavalink.jar'
            url = lavalink
        else:
            file = 'java17.exe'

        async with session.get(url=url) as resp:
            with open(f'{location.absolute()}/{file}', 'wb') as fp:
                count = 1

                async for chunk in resp.content.iter_chunked(1024):
                    x = int(40 * count / chunks)

                    print(f"\rDownloading {file}: [{u'█' * x}{('.' * (40 - x))}] "
                          f"{count / 1024:.2f}/{chunks / 1024:.2f} MB",
                          end='',
                          file=sys.stdout,
                          flush=True)

                    fp.write(chunk)
                    count += 1

        print("\n", flush=True, file=sys.stdout)


def parse_input(value: str, type_: typing.Any) -> typing.Union[str, int, bool, None]:
    value = str(value)

    quits = ('q', 'quit', 'exit')
    if value.lower() in quits:
        print('Exiting installer...')
        sys.exit(0)

    if type_ is bool:

        bools = {'y': True, 'yes': True, 'true': True, 'n': False, 'no': False, 'false': False}
        result = bools.get(value.lower(), None)

        return result

    try:
        result = type_(value.lower())
    except ValueError:
        return None

    return result


async def main():
    cwd = pathlib.Path.cwd()

    print('\nEnter Q at anytime to quit the installer...\n')

    while True:
        while True:

            port = parse_input(input('Please enter the port number for Lavalink (Enter to use default: 2333): ')
                               or 2333, int)

            if not port:
                print('Invalid port specified. Please enter a number for your port. Enter Q to quit.')
                continue

            break

        while True:

            address = parse_input(input('Please enter the address to star Lavalink (Enter to use default: 0.0.0.0): ')
                                  or '0.0.0.0', str)

            if not address:
                print('Invalid address specified. Please enter a valid binding IP address. Enter Q to quit.')
                continue

            break

        while True:

            password = parse_input(input('Please enter a password for Lavalink (Enter to use default:'
                                         ' "youshallnotpass"): ')
                                   or 'youshallnotpass', str)

            if not password:
                print('Invalid password specified. Please enter a valid password. Enter Q to quit.')
                continue

            break

        while True:

            location = parse_input(input('Please enter a install directory. '
                                         'An attempt to create the directory will be made if it does not not exist. '
                                         f'(Enter to use the current directory: {cwd}): ')
                                   or cwd, str)

            if not location:
                print('Invalid location specified. Please enter a valid directory. Enter Q to quit.')
                continue

            location = pathlib.Path(location)

            break

        while True:
            confirmed_ = parse_input(input('\nPlease confirm the following information:\n\n'
                                           f'Port: {port}\nAddress:'
                                           f' {address}\nPassword:'
                                           f' "{password}"\nLocation:'
                                           f' {location.absolute()}\n\n'
                                           f'(Y: Confirm, N: Re-Enter, Q: Quit): '),
                                     bool)

            if confirmed_ is None:
                print('Invalid response...')
                continue

            break

        if confirmed_ is True:
            break

    if not location.exists():
        try:
            location.mkdir(parents=True, exist_ok=False)
        except Exception as e:
            print(f'Could not make directory: "{location.absolute()}". {e}\nExiting the installer...')

    await download(location=location, url=RELEASES)
    print('Lavalink successfully downloaded...')

    with open(f'{location.absolute()}/application.yml', 'w') as fp:
        fp.write(_application_yml.format(port=port, address=address, password=password))

    if get_java:
        await download(location=location, url=JAVA)

        proc = await asyncio.subprocess.create_subprocess_exec(f'{location.absolute()}/java17.exe')
        await proc.wait()

    print(f'\nSuccess!\n\nDownload Location: {location.absolute()}\n\nInstructions:\n'
          f'- Open a Powershell or Command Prompt\n'
          f'- cd {location.absolute()}\n'
          f'- java -jar Lavalink.jar\n\n'
          f'To connect use the following details:\n'
          f'Port     : {port}\n'
          f'Password : "{password}"\n\n'
          f'You may change these values by editing the application.yml\n')


if __name__ == '__main__':
    asyncio.run(main())
