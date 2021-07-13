Frequently Asked Questions
==================================
Frequently asked questions for WaveLink and Lavalink.

.. contents:: Questions
    :local:


Lavalink
--------

What Java version is needed to run Lavalink.jar?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Java version 11+. The latest version of Java is preferable in most cases.


How do I run Lavalink.jar?
~~~~~~~~~~~~~~~~~~~~~~~~~~
Firstly you need to download and install Java 11+(Preferably the latest version) for your desired OS.

After Java has been successfully installed, open a new terminal for PATH variables to be set.

- Create a Folder/Directory for storing Lavalink.jar and application.yml
- Download the latest `Lavalink.jar` from `CI Server <https://ci.fredboat.com/viewLog.html?buildId=lastSuccessful&buildTypeId=Lavalink_Build&tab=artifacts&guest=1>`_
- Create an application.yml. `Example <https://github.com/freyacodes/Lavalink/blob/master/LavalinkServer/application.yml.example>`_
- In your terminal, run: `cd DIRECTORY_OF_LAVALINK && java -jar Lavalink.jar`

That's it your server should now be running and ready to be connected to.


General
-------

How do I connect to my Lavalink server?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Connecting to Lavalink Nodes is simple in wavelink. For example:

.. code:: python3

    import wavelink

    ...

    node = await wavelink.NodePool.create_node(bot=bot,
                                               host='0.0.0.0',
                                               port=2333,
                                               password='youshallnotpass')


Run the above code from an async environment, usually created as a task in your Cogs `__init__`.
Replace the fields appropriate to what you have set in your `application.yml`

See `Examples and Recipes` or `GitHub Examples <https://github.com/PythonistaGuild/Wavelink/tree/1.0/examples>`_ for more info.


How do I search YouTube for a track in 1.0?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Searching Wavelink for Tracks is simpler in 1.0.

After connecting to a node, simply:

.. code:: python3

    ...

    track = await wavelink.YouTubeTrack.search(query="Ocean Drive", return_first=True)


What is PartialTrack and how do I use it?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
`PartialTrack` is a new feature to 1.0. Instead of searching for and retrieving a track immediately,
`PartialTrack` allows you to queue a song and search at playtime. This allows large amounts of track data to be stored,
and processed without querying the REST API continuously. See `Examples and Recipes` for more info, for a basic example see below:

.. code:: python3

    ...

    partial = wavelink.PartialTrack(query="Ocean Drive", cls=wavelink.YouTubeTrack)

    track = await player.play(partial)
    await ctx.send(f"**Now playing:** `{track.title}`.")

