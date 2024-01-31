# coding:utf-8

from typing import List
from typing import Optional
from typing import Sequence

from xarg import add_command
from xarg import argp
from xarg import commands
from xarg import run_command

from ..utils import USER_CONFIG_FILE
from ..utils import __deamon_description__
from ..utils import __deamon_name__
from ..utils import __url_home__
from ..utils import __version__
from ..utils import dnsprobe_config

subs: List[add_command] = list()


@add_command(__deamon_name__)
def add_cmd(_arg: argp):
    _arg.add_argument("-c", "--config-file", nargs=1, type=str,
                      metavar="FILE", default=[USER_CONFIG_FILE],
                      help=f"default config file is {USER_CONFIG_FILE}")


@run_command(add_cmd, *subs)
def run_cmd(cmds: commands) -> int:
    config_file = cmds.args.config_file[0]
    assert isinstance(config_file, str), \
        f"unexpected type: {type(config_file)}"
    config = dnsprobe_config.from_file(file=config_file)
    config.dump(file=config_file)
    cmds.args.config = config
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    cmds = commands()
    cmds.version = __version__
    return cmds.run(root=add_cmd, argv=argv,
                    description=__deamon_description__,
                    epilog=f"For more, please visit {__url_home__}.")
