class Stats:
    def __init__(self, data):

        self.uptime = data['uptime']

        self.players = data['players']
        self.playing_players = data['playingPlayers']

        memory = data['memory']
        self.memory_free = memory['free']
        self.memory_used = memory['used']
        self.memory_allocated = memory['allocated']
        self.memory_reservable = memory['reservable']

        cpu = data['cpu']
        self.cpu_cores = cpu['cores']
        self.system_load = cpu['systemLoad']
        self.lavalink_load = cpu['lavalinkLoad']

        frame_stats = data.get('frameStats', {})
        self.frames_sent = frame_stats.get('sent', -1)
        self.frames_nulled = frame_stats.get('nulled', -1)
        self.frames_deficit = frame_stats.get('deficit', -1)
        self.penalty = Penalty(self)