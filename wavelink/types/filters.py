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
from typing import TYPE_CHECKING, Any, Optional, TypedDict

if TYPE_CHECKING:
    from typing_extensions import NotRequired


class Equalizer(TypedDict):
    band: int
    gain: float


class Karaoke(TypedDict):
    level: NotRequired[Optional[float]]
    monoLevel: NotRequired[Optional[float]]
    filterBand: NotRequired[Optional[float]]
    filterWidth: NotRequired[Optional[float]]


class Timescale(TypedDict):
    speed: NotRequired[Optional[float]]
    pitch: NotRequired[Optional[float]]
    rate: NotRequired[Optional[float]]


class Tremolo(TypedDict):
    frequency: NotRequired[Optional[float]]
    depth: NotRequired[Optional[float]]


class Vibrato(TypedDict):
    frequency: NotRequired[Optional[float]]
    depth: NotRequired[Optional[float]]


class Rotation(TypedDict):
    rotationHz: NotRequired[Optional[float]]


class Distortion(TypedDict):
    sinOffset: NotRequired[Optional[float]]
    sinScale: NotRequired[Optional[float]]
    cosOffset: NotRequired[Optional[float]]
    cosScale: NotRequired[Optional[float]]
    tanOffset: NotRequired[Optional[float]]
    tanScale: NotRequired[Optional[float]]
    offset: NotRequired[Optional[float]]
    scale: NotRequired[Optional[float]]


class ChannelMix(TypedDict):
    leftToLeft: NotRequired[Optional[float]]
    leftToRight: NotRequired[Optional[float]]
    rightToLeft: NotRequired[Optional[float]]
    rightToRight: NotRequired[Optional[float]]


class LowPass(TypedDict):
    smoothing: NotRequired[Optional[float]]


class FilterPayload(TypedDict):
    volume: NotRequired[Optional[float]]
    equalizer: NotRequired[Optional[list[Equalizer]]]
    karaoke: NotRequired[Karaoke]
    timescale: NotRequired[Timescale]
    tremolo: NotRequired[Tremolo]
    vibrato: NotRequired[Vibrato]
    rotation: NotRequired[Rotation]
    distortion: NotRequired[Distortion]
    channelMix: NotRequired[ChannelMix]
    lowPass: NotRequired[LowPass]
    pluginFilters: NotRequired[dict[str, Any]]
