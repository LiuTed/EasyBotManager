from mcdreforged.api.types import CommandSource, PluginServerInterface, ServerInterface
from easy_bot_manager.lang_utils import *
from enum import Enum, auto
from typing import List

class Bot:
    def __init__(
        self,
        name: str,
        pos: List[float],
        view: List[float],
        dim: str,
        comment: str = ''
    ) -> None:
        self.name = name
        self.pos = pos
        self.view = view
        self.dim = dim
        self.comment = comment
        self.online: bool = False

    def serialize(self) -> dict:
        ret = {
            'name': self.name,
            'pos': self.pos,
            'view': self.view,
            'dim': self.dim,
            'comment': self.comment
        }
        return ret

    def deserialize(self, bot: dict) -> None:
        self.name = bot['name']
        self.pos = bot['pos']
        self.view = bot['view']
        self.dim = bot['dim']
        self.comment = bot['comment']

class BotManager:
    class ListArg(Enum):
        all = auto()
        online = auto()
        offline = auto()

    def __init__(self) -> None:
        self.bots: List['Bot'] = []
    
    def save(self, server: PluginServerInterface):
        b = {
            'bots': [bot.serialize() for bot in self.bots]
        }
        server.save_config_simple(b, 'bots.json')
    
    def load(self, server: PluginServerInterface):
        lb = server.load_config_simple('bots.json', {'bots': []})
        for bot in lb['bots']:
            b = Bot(None, None, None, None, '')
            b.deserialize(bot)
            self.bots.append(b)
    
    def refresh(self, server: ServerInterface):
        api = server.get_plugin_instance('minecraft_data_api')
        players = api.get_server_player_list()
        
        if (not server.is_server_startup()) or (players is None):
            for b in self.bots:
                b.online = False
            return
        
        for b in self.bots:
            if b.name in players[2]:
                b.online = True
            else:
                b.online = False
        return
    
    def list(self, source: CommandSource, cmd: dict):
        text = ''
        filt_map = {
            self.ListArg.all: lambda bot: True,
            self.ListArg.online: lambda bot: bot.online,
            self.ListArg.offline: lambda bot: not bot.online
        }
        if 'filter' in cmd:
            filt = filt_map[cmd['filter']]
        else:
            filt = lambda bot: True

        with source.preferred_language_context():
            if len(self.bots) == 0:
                source.reply(tr('ebm.list.no_bot'))
                return
            has_output = False
            for bot in self.bots:
                if filt(bot):
                    text = RTextList(
                        RText(
                            '{}: '.format(bot.name),
                            color=RColor.green if bot.online else RColor.gray
                        ).h(
                            tr('ebm.list.online' if bot.online else 'ebm.list.offline')
                        ),
                        tr_coord(bot.pos, bot.dim),
                        RText(
                            tr('ebm.list.looking') + '[{:.1f}, {:.1f}]'.format(bot.view[0], bot.view[1]),
                            color = RColor.white
                        ),
                        RText(
                            '[△]', color=RColor.yellow
                        ).h(
                            tr('ebm.list.spawn')
                        ).c(
                            RAction.run_command,
                            '!!bot spawn {}'.format(bot.name)
                        ),
                        RText(
                            '[▽]', color=RColor.dark_blue
                        ).h(
                            tr('ebm.list.kick')
                        ).c(
                            RAction.run_command,
                            '!!bot kill {}'.format(bot.name)
                        ),
                        RText(
                            '[☒]', color=RColor.red
                        ).h(
                            tr('ebm.list.remove')
                        ).c(
                            RAction.suggest_command,
                            '!!bot remove {}'.format(bot.name)
                        ),
                        RText(
                            '[▷]', color=RColor.blue
                        ).h(
                            tr('ebm.list.set')
                        ).c(
                            RAction.suggest_command,
                            '!!bot set {} here here here'.format(bot.name)
                        ),
                        RText(
                            '[?]', color=RColor.dark_purple if bot.comment != '' else RColor.gray
                        ).h(
                            tr('ebm.list.comment') + bot.comment
                        )
                    )
                    if not source.is_player and bot.comment != '':
                        text.append(RText(
                            tr('ebm.list.comment') + bot.comment, color=RColor.dark_purple
                        ))
                    source.reply(text)
                    has_output = True
            if not has_output:
                source.reply(tr('ebm.list.no_matching'))
    
    def bot_name_list(self, filt: str):
        if filt == 'all':
            return [bot.name for bot in self.bots]
        elif filt == 'online':
            return [bot.name for bot in self.bots if bot.online]
        elif filt == 'offline':
            return [bot.name for bot in self.bots if not bot.online]
        else:
            return [bot.name for bot in self.bots]
    
    def add_bot(self, source: CommandSource, cmd: dict):
        name = cmd['name']
        with source.preferred_language_context():
            if name == 'all':
                source.reply(tr('ebm.add.invalid_name_all'))
                return False

            for b in self.bots:
                if b.name == name:
                    source.reply(tr('ebm.add.bot_exist', name))
                    return False

        pos = cmd.get('pos', 'here')
        view = cmd.get('view', 'here')
        dim = cmd.get('dim', 'here')
        comment = cmd.get('comment', '')

        if 'here' in [pos, view, dim]:
            with source.preferred_language_context():
                if source.is_player:
                    player = source.player
                    api = source.get_server().get_plugin_instance('minecraft_data_api')
                    info = api.get_player_info(player)
                    if info is None:
                        source.reply(tr('ebm.add.get_info_fail', player))
                        return False
                    if pos == 'here':
                        try:
                            pos = info['Pos']
                        except:
                            source.reply(tr('ebm.add.get_pos_fail', player))
                            return False
                    if view == 'here':
                        try:
                            view = info['Rotation']
                        except:
                            source.reply(tr('ebm.add.get_view_fail', player))
                            return False
                    if dim == 'here':
                        try:
                            dim = info['Dimension']
                        except:
                            source.reply(tr('ebm.add.get_dim_fail', player))
                            return False
                else:
                    source.reply(tr('ebm.add.need_specify'))
                    return False
        
        bot = Bot(name, pos, view, dim, comment)
        self.bots.append(bot)
        with source.preferred_language_context():
            source.reply(tr('ebm.add.succeed', name))
        return True

    def remove_bot(self, source: CommandSource, cmd: dict):
        name = cmd['name']
        with source.preferred_language_context():
            for b in self.bots:
                if b.name == name:
                    if b.online:
                        source.reply(
                            RTextList(
                                RText(
                                    tr('ebm.remove.online_warning', name),
                                    color=RColor.gold
                                ),
                                RText(
                                    tr('ebm.remove.kick_suggest'),
                                    color=RColor.blue
                                ).c(
                                    RAction.suggest_command,
                                    '/player {} kill'.format(name)
                                )
                            )
                        )
                    self.bots.remove(b)
                    source.reply(tr('ebm.remove.succeed', name))
                    return True
            source.reply(tr('ebm.bot_not_found', name))
        return False
    
    def remove_bot_comment(self, source: CommandSource, cmd: dict):
        name = cmd['name']
        for b in self.bots:
            if b.name == name:
                b.comment = ''
                with source.preferred_language_context():
                    source.reply(tr('ebm.set.succeed', name))
                    return True
        
        with source.preferred_language_context():
            source.reply(tr('ebm.bot_not_found', name))
            return False
    
    def set_bot(self, source: CommandSource, cmd: dict):
        name = cmd['name']
        idx = -1
        for i, b in enumerate(self.bots):
            if b.name == name:
                idx = i
                break
        
        if idx == -1:
            with source.preferred_language_context():
                source.reply(tr('ebm.bot_not_found', name))
                return False

        pos = cmd.get('pos', 'keep')
        view = cmd.get('view', 'keep')
        dim = cmd.get('dim', 'keep')
        comment = cmd.get('comment', '')

        if pos == 'keep':
            pos = self.bots[idx].pos
        if view == 'keep':
            view = self.bots[idx].view
        if dim == 'keep':
            dim = self.bots[idx].dim

        if 'here' in [pos, view, dim]:
            with source.preferred_language_context():
                if source.is_player:
                    player = source.player
                    api = source.get_server().get_plugin_instance('minecraft_data_api')
                    info = api.get_player_info(player)
                    if info is None:
                        source.reply(tr('ebm.add.get_info_fail', player))
                        return False
                    if pos == 'here':
                        try:
                            pos = info['Pos']
                        except:
                            source.reply(tr('ebm.add.get_pos_fail', player))
                            return False
                    if view == 'here':
                        try:
                            view = info['Rotation']
                        except:
                            source.reply(tr('ebm.add.get_view_fail', player))
                            return False
                    if dim == 'here':
                        try:
                            dim = info['Dimension']
                        except:
                            source.reply(tr('ebm.add.get_dim_fail', player))
                            return False
                else:
                    source.reply(tr('ebm.add.need_specify'))
                    return False

        self.bots[idx].pos = pos
        self.bots[idx].view = view
        self.bots[idx].dim = dim
        if comment != '':
            self.bots[idx].comment = comment
        with source.preferred_language_context():
            source.reply(tr('ebm.set.succeed', name))
        return True

    def spawn_bot(self, source: CommandSource, cmd: dict):
        server = source.get_server()
        if not server.is_server_startup():
            source.reply(tr('ebm.spawn.server_not_startup'))
            return False

        if 'name' in cmd:
            name = cmd['name']

            for b in self.bots:
                if b.name == name:
                    if b.online:
                        source.reply(tr('ebm.spawn.online', name))
                        return False
                    c = 'player {} spawn at {} {} {} facing {} {} in {}'.format(
                        b.name, b.pos[0], b.pos[1], b.pos[2],
                        b.view[0], b.view[1], b.dim
                    )
                    server.execute(c)
                    b.online = True
                    return True
            source.reply(tr('ebm.bot_not_found', name))
            return False
        
        else:
            for b in self.bots:
                if not b.online:
                    c = 'player {} spawn at {} {} {} facing {} {} in {}'.format(
                        b.name, b.pos[0], b.pos[1], b.pos[2],
                        b.view[0], b.view[1], b.dim
                    )
                    server.execute(c)
                    b.online = True
            return True
    
    def kill_bot(self, source: CommandSource, cmd: dict):
        server = source.get_server()
        if not server.is_server_startup():
            source.reply(tr('ebm.kill.server_not_startup'))
            return False
        if 'name' in cmd:
            name = cmd['name']

            for b in self.bots:
                if b.name == name:
                    if not b.online:
                        source.reply(tr('ebm.kill.offline', name))
                        return False
                    c = 'player {} kill'.format(b.name)
                    server.execute(c)
                    b.online = False
                    return True
            source.reply(tr('ebm.bot_not_found', name))
            return False
        else:
            for b in self.bots:
                if b.online:
                    c = 'player {} kill'.format(b.name)
                    server.execute(c)
                    b.online = False
            return True
