# coding:utf-8

from xarg import add_command
from xarg import argp
from xarg import commands
from xarg import run_command

from ..utils import dnsprobe_config
from ..utils import update_nameservers


@add_command("update-nameservers", help="Update public DNS Servers database")
def add_cmd_update_nameservers(_arg: argp):
    args = _arg.preparse_from_sys_argv()
    conf = dnsprobe_config.from_file(file=args.config_file[0])
    databases = conf.all_nameserver_databases
    _arg.add_argument(dest="nameserver_databases", type=str, nargs="+",
                      metavar="NS", action="extend", choices=databases,
                      help=f"nameservers database, choice from {databases}")


@run_command(add_cmd_update_nameservers)
def run_cmd_update_nameservers(cmds: commands) -> int:
    config: dnsprobe_config = cmds.args.config
    for database in cmds.args.nameserver_databases:
        db = config.get_nameserver_database(database)
        update_nameservers(config.nameservers_dir, db.database_name, db.url)
    return 0
