from easy_bot_manager.command import *
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
def list_bot(source, cmd):
    global botmgr
    return botmgr.list(source, cmd)

@new_thread('EasyBotMgr-Add')
def add_bot(source, cmd):
    global botmgr
    ret = botmgr.add_bot(source, cmd)
    if ret:
        refresh_source(source)
    return ret
    
def remove_bot(source, cmd):
    global botmgr
    return botmgr.remove_bot(source, cmd)
    
@new_thread('EasyBotMgr-Set')
def set_bot(source, cmd):
    global botmgr
    return botmgr.set_bot(source, cmd)

@new_thread('EasyBotMgr-Set')
def remove_bot_comment(source, cmd):
    global botmgr
    return botmgr.remove_bot_comment(source, cmd)
    
@new_thread('EasyBotMgr-Spawn')
def spawn_bot(source, cmd):
    global botmgr
    return botmgr.spawn_bot(source, cmd)
    
@new_thread('EasyBotMgr-Kick')
def kick_bot(source, cmd):
    global botmgr
    return botmgr.kill_bot(source, cmd)

def name_suggest(filt = 'all'):
    global botmgr
    return botmgr.bot_name_list(filt)

def dim_suggest():
    return ['minecraft:overworld', 'minecraft:the_nether', 'minecraft:the_end']

def list_filter_suggest():
    return [e.name for e in BotManager.ListArg]

def usage(source):
    subcommand_list = [
        'help',
        'list',
        'add',
        'remove1',
        'remove2',
        'set1',
        'set2',
        'spawn',
        'kill',
        'refresh'
    ]
    with source.preferred_language_context():
        for subcommand in subcommand_list:
            raw = RTextList(
                RText(
                    '!!bot ' + tr('usage.args.{}'.format(subcommand)) + ': ',
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
    add_comment_node = GreedyText('comment').runs(add_bot)

    add_dim_node = DumbNode('dim').then(
        Literal('here').runs(add_bot).then(
            add_comment_node
        )
    ).then(
        Text('dim').suggests(dim_suggest).runs(add_bot).then(
            add_comment_node
        )
    )

    add_view_node = DumbNode('view').then(
        Literal('here').runs(add_bot).then(
            add_dim_node
        )
    ).then(
        MultipleArguments('view', 2, float).runs(add_bot).then(
            add_dim_node
        )
    )

    add_pos_node = DumbNode('pos').then(
        Literal('here').runs(add_bot).then(
            add_view_node
        )
    ).then(
        MultipleArguments('pos', 3, float).runs(add_bot).then(
            add_view_node
        )
    )

    set_comment_node = GreedyText('comment').runs(set_bot)

    set_dim_node = DumbNode('dim').then(
        NLRA(
            'dim',
            ['keep', 'here'],
            Text('dim').suggests(dim_suggest)
        ).runs(set_bot).then(
            set_comment_node
        )
    )

    set_view_node = DumbNode('view').then(
        NLRA(
            'view',
            ['keep', 'here'],
            MultipleArguments('view', 2, float)
        ).runs(set_bot).then(
            set_dim_node
        )
    )

    set_pos_node = DumbNode('pos').then(
        NLRA(
            'pos',
            ['keep', 'here'],
            MultipleArguments('pos', 3, float)
        ).runs(set_bot).then(
            set_view_node
        )
    )

    server.register_command(
        Literal('!!bot').runs(usage).then(
            Literal('help').runs(usage)
        ).then(
            Literal('list').runs(list_bot).then(
                Enumeration('filter', BotManager.ListArg).runs(list_bot).suggests(list_filter_suggest)
            )
        ).then(
            Literal('add').then(
                Text('name').runs(add_bot).then(
                    add_pos_node
                ).then(
                    add_comment_node
                )
            )
        ).then(
            Literal('remove').then(
                Text('name').suggests(lambda: name_suggest()).runs(remove_bot).then(
                    Literal('comment').runs(remove_bot_comment)
                )
            )
        ).then(
            Literal('set').then(
                Text('name').suggests(lambda: name_suggest()).then(
                    set_pos_node
                ).then(
                    Literal('comment').then(
                        GreedyText('comment').runs(set_bot)
                    )
                )
            )
        ).then(
            Literal('spawn').then(
                Text('name').suggests(lambda: name_suggest('offline')).runs(spawn_bot)
            ).then(
                Literal('all').runs(spawn_bot)
            )
        ).then(
            Literal('kill').then(
                Text('name').suggests(lambda: name_suggest('online')).runs(kick_bot)
            ).then(
                Literal('all').runs(kick_bot)
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
    server.register_help_message('!!bot', tr('help_message'))
    if server.is_server_startup():
        refresh_server(server)

def on_unload(server):
    global botmgr
    botmgr.save(server)

def on_server_startup(server):
    refresh_server(server)

def on_server_stop(server, server_ret_code):
    refresh_server(server)
