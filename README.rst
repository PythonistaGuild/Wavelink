.. image:: https://raw.githubusercontent.com/PythonistaGuild/Wavelink/master/logo.png


.. image:: https://img.shields.io/badge/Python-3.10%20%7C%203.11-blue.svg
    :target: https://www.python.org


.. image:: https://img.shields.io/github/license/PythonistaGuild/Wavelink.svg
    :target: LICENSE


.. image:: https://img.shields.io/discord/490948346773635102?color=%237289DA&label=Pythonista&logo=discord&logoColor=white
   :target: https://discord.gg/RAKc3HF


.. image:: https://img.shields.io/pypi/dm/Wavelink?color=black
    :target: https://pypi.org/project/Wavelink
    :alt: PyPI - Downloads


.. image:: https://img.shields.io/maintenance/yes/2023?color=pink&style=for-the-badge
    :target: https://github.com/PythonistaGuild/Wavelink/commits/main
    :alt: Maintenance



Wavelink is a robust and powerful Lavalink wrapper for `Discord.py <https://github.com/Rapptz/discord.py>`_.
Wavelink features a fully asynchronous API that's intuitive and easy to use.


Migrating from Version 2 to Version 3:
######################################

`Migrating Guide <https://wavelink.dev/en/latest/migrating.html>`_


**Features:**

- Full asynchronous design.
- Lavalink v4+ Supported with REST API.
- discord.py v2.0.0+ Support.
- Advanced AutoPlay and track recommendations for continuous play.
- Object orientated design with stateful objects and payloads.
- Fully annotated and complies with Pyright strict typing.


Documentation
-------------
`Official Documentation <https://wavelink.dev/en/latest>`_

Support
-------
For support using WaveLink, please join the official `support server
<https://discord.gg/RAKc3HF>`_ on `Discord <https://discordapp.com>`_.

.. image:: https://discordapp.com/api/guilds/490948346773635102/widget.png?style=banner2
    :target: https://discord.gg/RAKc3HF


Installation
------------
**WaveLink 3 requires Python 3.10+**

**Windows**

.. code:: sh

    py -3.10 -m pip install -U wavelink

**Linux**

.. code:: sh

    python3.10 -m pip install -U wavelink

**Virtual Environments**

.. code:: sh

    pip install -U wavelink


Getting Started
---------------

**See Examples:** `Examples <https://github.com/PythonistaGuild/Wavelink/tree/main/examples>`_


Lavalink
--------

Wavelink **3** requires **Lavalink v4**.
See: `Lavalink <https://github.com/lavalink-devs/Lavalink/releases>`_

For spotify support, simply install and use `LavaSrc <https://github.com/topi314/LavaSrc>`_ with your `wavelink.Playable`


Notes
-----

- Wavelink **3** is compatible with Lavalink **v4+**.
- Wavelink has built in support for Lavalink Plugins including LavaSrc and SponsorBlock.
- Wavelink is fully typed in compliance with Pyright Strict, though some nuances remain between discord.py and wavelink.
