from easy_bot_manager.command import MultipleArgument
from easy_bot_manager.easy_bot_manager import BotManager
from easy_bot_manager.lang_utils import *
from mcdreforged.api.command import Literal, Text, GreedyText
from mcdreforged.api.decorator import new_thread
from mcdreforged.command.builder.nodes.arguments import Enumeration


botmgr: BotManager = None

@new_thread('EasyBotMgr-Refresh')
def refresh_source(source):
    global botmgr
    server = source.get_server()
    botmgr.refresh(server)

@new_thread('EasyBotMgr-Refresh')
def refresh_server(server):
    global botmgr
    botmgr.refresh(server)
    
@new_thread('EasyBotMgr-List')
def list(source, cmd):
    global botmgr
    return botmgr.list(source, cmd)

@new_thread('EasyBotMgr-Add')
def add(source, cmd):
    global botmgr
    ret = botmgr.add_bot(source, cmd)
    if ret:
        refresh_source(source)
    return ret
    
def remove(source, cmd):
    global botmgr
    return botmgr.remove_bot(source, cmd)
    
@new_thread('EasyBotMgr-Set')
def set(source, cmd):
    global botmgr
    return botmgr.set_bot(source, cmd)
    
@new_thread('EasyBotMgr-Spawn')
def spawn(source, cmd):
    global botmgr
    return botmgr.spawn_bot(source, cmd)
    
@new_thread('EasyBotMgr-Kick')
def kick(source, cmd):
    global botmgr
    return botmgr.kill_bot(source, cmd)

def name_suggest(filt = 'all'):
    global botmgr
    return botmgr.bot_name_list(filt)

def dim_suggest():
    return ['minecraft:overworld', 'minecraft:the_nether', 'minecraft:the_end']

def usage(source):
    subcommand_list = [
        'help',
        'list',
        'add',
        'remove',
        'set',
        'spawn',
        'kill',
        'refresh'
    ]
    with source.preferred_language_context():
        for subcommand in subcommand_list:
            raw = RTextList(
                RText(
                    '!!bot' + ' {}'.format(subcommand) + tr('usage.args.{}'.format(subcommand)) + ': ',
                    color = RColor.gray
                ),
                RText(
                    tr('usage.{}'.format(subcommand)),
                    color = RColor.white
                )
            )
            if subcommand == 'list':
                raw = raw.h(
                    tr('ebm.usage.list.hover')
                ).c(
                    RAction.run_command, '!!bot list all'
                )
            elif subcommand == 'refresh':
                raw = raw.h(
                    tr('ebm.usage.refresh.hover')
                ).c(
                    RAction.run_command, '!!bot refresh'
                )
            source.reply(raw)


def register_command(server):
    from enum import Enum
    class ListArg(Enum):
        all = 'all'
        online = 'online'
        offline = 'offline'

    server.register_command(
        Literal('!!bot').runs(usage).then(
            Literal('help').runs(usage)
        ).then(
            Literal('list').runs(list).then(
                Enumeration('filter', ListArg).runs(list)
            )
        ).then(
            Literal('add').then(
                Text('name').runs(add).then(
                    MultipleArgument('pos', 3, [float, float, float]).runs(add).then(
                        MultipleArgument('view', 2, [float, float]).runs(add).then(
                            Text('dim').suggests(dim_suggest).runs(add).then(
                                GreedyText('comment').runs(add)
                            )
                        )
                    )
                ).then(
                    Literal('here').runs(add).then(
                        GreedyText('comment').runs(add)
                    )
                )
            )
        ).then(
            Literal('remove').then(
                Text('name').suggests(lambda: name_suggest()).runs(remove)
            )
        ).then(
            Literal('set').then(
                Text('name').suggests(lambda: name_suggest()).then(
                    Literal('here').runs(set).then(
                        GreedyText('comment').runs(set)
                    )
                ).then(
                    MultipleArgument('pos', 3, [float, float, float]).runs(set).then(
                        MultipleArgument('view', 2, [float, float]).runs(set).then(
                            Text('dim').suggests(dim_suggest).runs(set).then(
                                GreedyText('comment').runs(set)
                            )
                        )
                    )
                )
            )
        ).then(
            Literal('spawn').then(
                Text('name').suggests(lambda: name_suggest('offline')).runs(spawn)
            ).then(
                Literal('all').runs(spawn)
            )
        ).then(
            Literal('kill').then(
                Text('name').suggests(lambda: name_suggest('online')).runs(kick)
            ).then(
                Literal('all').runs(kick)
            )
        ).then(
            Literal('refresh').runs(refresh_source)
        )
    )

def on_load(server, old):
    global botmgr
    botmgr = BotManager()
    botmgr.load(server)
    register_command(server)
    server.register_help_message('!!bot', 'Manage Carpet Bots')
    if server.is_server_startup():
        refresh_server(server)

def on_unload(server):
    global botmgr
    botmgr.save(server)

def on_server_startup(server):
    refresh_server(server)

def on_server_stop(server, server_ret_code):
    refresh_server(server)
