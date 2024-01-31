# coding:utf-8

from xarg import add_command
from xarg import argp
from xarg import commands
from xarg import run_command

from ..utils import DEFAULT_CONFIG_FILE
from ..utils import dnsprobe_config


@add_command("config", help="Get and set config options")
def add_cmd_config(_arg: argp):
    pass


@run_command(add_cmd_config)
def run_cmd_config(cmds: commands) -> int:
    config_file = DEFAULT_CONFIG_FILE
    config = dnsprobe_config.from_file(file=config_file)
    config.dump(file=config_file)
    return 0
