# coding:utf-8

from collections import namedtuple
from configparser import ConfigParser
from enum import Enum
import os

from .attribute import DEFAULT_CONFIG_FILE
from .attribute import DEFAULT_SERVERS_DIR

DEFAULT_ITEM = namedtuple("dnsprobe_default_config_item",
                          ("section", "option", "default"))


class dnsprobe_config():

    class defaults(Enum):
        SERVERS = DEFAULT_ITEM("main", "nameservers_dir", DEFAULT_SERVERS_DIR)

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

    def dump(self, file: str = DEFAULT_CONFIG_FILE):
        os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, "w") as hdl:
            self.__parser.write(hdl)

    @classmethod
    def from_file(cls, file: str = DEFAULT_CONFIG_FILE) -> "dnsprobe_config":
        assert not os.path.exists(file) or os.path.isfile(file), \
            f"'{file}' is not a regular file."
        parser: ConfigParser = ConfigParser()
        string: str = open(file).read() if os.path.exists(file) else "\n"
        parser.optionxform = lambda option: option  # type: ignore
        parser.read_string(string)
        config = dnsprobe_config(parser)
        config.dump(file)
        return config
