# coding:utf-8

import os
from typing import Set

from xarg import add_command
from xarg import argp
from xarg import commands
from xarg import run_command

from ..utils import dnsprobe_config
from ..utils import dnsprobe_nameservers
from ..utils import import_databases
from .config import pre_opt_config_file


def add_opt_nameserver_databases(_arg: argp):
    databases: Set[str] = pre_opt_config_file(_arg).all_nameserver_databases
    _arg.add_argument(dest="nameserver_databases", type=str, nargs="+",
                      metavar="NS", action="extend", choices=databases,
                      help=f"nameservers database, choice from {databases}")


@add_command("import-databases", help="Import public DNS databases")
def add_cmd_import_databases(_arg: argp):
    add_opt_nameserver_databases(_arg)


@run_command(add_cmd_import_databases)
def run_cmd_import_databases(cmds: commands) -> int:
    config: dnsprobe_config = cmds.args.config
    for database in cmds.args.nameserver_databases:
        db = config.get_nameserver_database(database)
        import_databases(config.nameservers_dir, db.database_name, db.url)
    return 0


@add_command("export-databases", help="Export public DNS databases")
def add_cmd_export_databases(_arg: argp):
    current_directory = os.path.abspath(".")
    _arg.add_argument("-d", "--output", dest="output_directory", type=str,
                      nargs=1, metavar="DIR", default=[current_directory],
                      help=f"default output directory is {current_directory}")
    add_opt_nameserver_databases(_arg)


@run_command(add_cmd_export_databases)
def run_cmd_export_databases(cmds: commands) -> int:
    output: str = cmds.args.output_directory[0]
    if not os.path.exists(output):
        os.makedirs(output)
    assert os.path.isdir(output), f"'{output}' is not an existing directory"
    config: dnsprobe_config = cmds.args.config
    for database in cmds.args.nameserver_databases:
        db = config.get_nameserver_database(database)
        path = os.path.join(output, db.database_name)
        nameservers = dnsprobe_nameservers(config.nameservers_dir,
                                           db.database_name)
        nameservers.load_temp()
        nameservers.dump(path)
    return 0


@add_command("update-databases", help="Update nameservers databases")
def add_cmd_update_databases(_arg: argp):
    add_opt_nameserver_databases(_arg)


@run_command(add_cmd_update_databases)
def run_cmd_update_databases(cmds: commands) -> int:
    config: dnsprobe_config = cmds.args.config
    for database in cmds.args.nameserver_databases:
        db = config.get_nameserver_database(database)
        nameservers = dnsprobe_nameservers(config.nameservers_dir,
                                           db.database_name)
        nameservers.load_temp()
        nameservers.dump()
    return 0
