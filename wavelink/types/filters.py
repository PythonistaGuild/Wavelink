"""
MIT License

Copyright (c) 2019-Current PythonistaGuild, EvieePy

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

from typing import Any, TypedDict


class Equalizer(TypedDict):
    band: int
    gain: float


class Karaoke(TypedDict, total=False):
    level: float | None
    monoLevel: float | None
    filterBand: float | None
    filterWidth: float | None


class Timescale(TypedDict, total=False):
    speed: float | None
    pitch: float | None
    rate: float | None


class Tremolo(TypedDict, total=False):
    frequency: float | None
    depth: float | None


class Vibrato(TypedDict, total=False):
    frequency: float | None
    depth: float | None


class Rotation(TypedDict, total=False):
    rotationHz: float | None


class Distortion(TypedDict, total=False):
    sinOffset: float | None
    sinScale: float | None
    cosOffset: float | None
    cosScale: float | None
    tanOffset: float | None
    tanScale: float | None
    offset: float | None
    scale: float | None


class ChannelMix(TypedDict, total=False):
    leftToLeft: float | None
    leftToRight: float | None
    rightToLeft: float | None
    rightToRight: float | None


class LowPass(TypedDict, total=False):
    smoothing: float | None


class FilterPayload(TypedDict, total=False):
    volume: float | None
    equalizer: list[Equalizer] | None
    karaoke: Karaoke
    timescale: Timescale
    tremolo: Tremolo
    vibrato: Vibrato
    rotation: Rotation
    distortion: Distortion
    channelMix: ChannelMix
    lowPass: LowPass
    pluginFilters: dict[str, Any]
