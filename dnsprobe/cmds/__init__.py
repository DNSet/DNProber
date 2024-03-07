# coding:utf-8

from typing import Optional
from typing import Sequence

from xarg import add_command
from xarg import argp
from xarg import commands
from xarg import run_command

from ..utils import __description__
from ..utils import __name__
from ..utils import __url_home__
from ..utils import __version__
from .config import add_cmd_config
from .config import add_opt_config_file
from .config import get_config
from .nameservers import add_cmd_export_databases
from .nameservers import add_cmd_import_databases
from .nameservers import add_cmd_update_databases


@add_command(__name__)
def add_cmd(_arg: argp):
    add_opt_config_file(_arg)


@run_command(add_cmd, add_cmd_config,
             add_cmd_import_databases,
             add_cmd_export_databases,
             add_cmd_update_databases)
def run_cmd(cmds: commands) -> int:
    cmds.args.config = get_config(cmds)
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    cmds = commands()
    cmds.version = __version__
    return cmds.run(root=add_cmd, argv=argv, description=__description__,
                    epilog=f"For more, please visit {__url_home__}.")
