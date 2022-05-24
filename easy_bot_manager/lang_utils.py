from mcdreforged.translation.translation_text import RTextMCDRTranslation
from mcdreforged.plugin.server_interface import ServerInterface
from mcdreforged.api.rtext import *

def tr(translation_key: str, *args) -> RTextMCDRTranslation:
    return ServerInterface.get_instance().rtr(translation_key, *args)

def tr_coord(pos, dim):
    color_map = {
        'minecraft:the_end': RColor.light_purple,
        'minecraft:overworld': RColor.green,
        'minecraft:the_nether': RColor.red
    }
    ID_DIM = {
        -1: 'minecraft:the_nether',
        0: 'minecraft:overworld',
        1: 'minecraft:the_end'
    }
    try:
        int_dim = int(dim)
        sdim = ID_DIM.get(int_dim, str(dim))
    except ValueError:
        sdim = str(dim)
    
    color = color_map.get(sdim, RColor.gray)

    text = RText(
        (tr('dim.{}'.format(sdim)) if sdim in color_map else sdim) +
        ': [{:.1f}, {:.1f}, {:.1f}]'.format(pos[0], pos[1], pos[2]),
        color = color
    ).h(
        tr('coord.hover.click_to_teleport') +
        (tr('dim.{}'.format(sdim)) if sdim in color_map else sdim) +
        '[{:.1f}, {:.1f}, {:.1f}]'.format(pos[0], pos[1], pos[2])
    ).c(
        RAction.suggest_command,
        '/execute in {} run tp {:.1f} {:.1f} {:.1f}'.format(
            sdim, pos[0], pos[1], pos[2]
        )
    )

    return text
