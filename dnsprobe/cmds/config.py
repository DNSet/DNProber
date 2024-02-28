# coding:utf-8

from xarg import Namespace
from xarg import add_command
from xarg import argp
from xarg import commands
from xarg import run_command

from ..utils import USER_CONFIG_FILE
from ..utils import dnsprobe_config


def add_opt_config_file(_arg: argp):
    _arg.add_argument("-c", "--config-file", nargs=1, type=str,
                      metavar="FILE", default=[USER_CONFIG_FILE],
                      help=f"default config file is {USER_CONFIG_FILE}")


def pre_opt_config_file(_arg: argp) -> dnsprobe_config:
    args: Namespace = _arg.preparse_from_sys_argv()
    return dnsprobe_config.from_file(file=args.config_file[0])


def get_config(cmds: commands) -> dnsprobe_config:
    config_file = cmds.args.config_file[0]
    assert isinstance(config_file, str), \
        f"unexpected type: {type(config_file)}"
    config = dnsprobe_config.from_file(file=config_file)
    config.dump(file=config_file)
    return config


@add_command("config", help="Get and set config options")
def add_cmd_config(_arg: argp):
    pass


@run_command(add_cmd_config)
def run_cmd_config(cmds: commands) -> int:
    return 0
