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

from ._lib import Client, Connectable, GuildVoiceStatePayload, VoiceProtocol, VoiceServerUpdatePayload


class Player(VoiceProtocol):
    def __init__(self, client: Client, channel: Connectable) -> None:
        super().__init__(client, channel)

    async def on_voice_server_update(self, data: VoiceServerUpdatePayload) -> None:
        return await super().on_voice_server_update(data)

    async def on_voice_state_update(self, data: GuildVoiceStatePayload) -> None:
        return await super().on_voice_state_update(data)
