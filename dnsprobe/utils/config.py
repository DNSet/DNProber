# coding:utf-8

from collections import namedtuple
from configparser import ConfigParser
from enum import Enum
import os

from appdirs import user_config_dir
from appdirs import user_data_dir

from .attribute import __name__

# from appdirs import site_config_dir
# from appdirs import site_data_dir

# GLOBAL_CONFIG_DIR = site_config_dir(appname=__name__)
# GLOBAL_CONFIG_FILE = os.path.join(GLOBAL_CONFIG_DIR, "dnsprobe.conf")
# GLOBAL_SERVERS_DIR = site_data_dir(appname=f"{__name__}.nameservers")

USER_CONFIG_DIR = user_config_dir(appname=__name__)
USER_CONFIG_FILE = os.path.join(USER_CONFIG_DIR, "dnsprobe.conf")
USER_SERVERS_DIR = user_data_dir(appname=f"{__name__}.nameservers")

DEFAULT_ITEM = namedtuple("dnsprobe_default_config_item",
                          ("section", "option", "default"))


class dnsprobe_config():

    class defaults(Enum):
        SERVERS = DEFAULT_ITEM("main", "nameservers_dir", USER_SERVERS_DIR)

    def __init__(self, parser: ConfigParser):
        assert isinstance(parser, ConfigParser), \
            f"unexpected type: {type(parser)}"
        self.__parser: ConfigParser = parser
        self.__setdefault()

    def __setdefault(self):
        for default in self.defaults:
            item = default.value
            assert isinstance(item, DEFAULT_ITEM)
            section: str = item.section if isinstance(item.section, str) else \
                self.__parser.default_section
            option: str = item.option
            if not self.__parser.has_option(section, option):
                if not self.__parser.has_section(section):
                    self.__parser.add_section(section)
                self.__parser.set(section, option, item.default)

    def dump(self, file: str = USER_CONFIG_FILE):
        os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, "w") as hdl:
            self.__parser.write(hdl)

    @classmethod
    def from_file(cls, file: str = USER_CONFIG_FILE) -> "dnsprobe_config":
        assert not os.path.exists(file) or os.path.isfile(file), \
            f"'{file}' is not a regular file."
        parser: ConfigParser = ConfigParser()
        string: str = open(file).read() if os.path.exists(file) else "\n"
        parser.optionxform = lambda option: option  # type: ignore
        parser.read_string(string)
        config = dnsprobe_config(parser)
        config.dump(file)
        return config
