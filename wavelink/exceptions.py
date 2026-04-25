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

from .types_.rest import ErrorRespT


__all__ = ("HTTPException", "LavalinkError", "WavelinkException")


class WavelinkException(Exception): ...


class HTTPException(Exception):
    def __init__(self, msg: str | None = None, /, *, status: int) -> None:
        super().__init__(msg or "")
        self.status = status


class LavalinkError(Exception):
    def __init__(self, msg: str | None = None, /, *, data: ErrorRespT) -> None:
        super().__init__(f"{msg or data['error']}: {data}")
        self.timestamp = data["timestamp"]
        self.status = data["status"]
        self.error = data["error"]
        self.trace = data.get("trace")
        self.message = data["message"]
        self.path = data["path"]
