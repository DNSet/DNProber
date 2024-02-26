# coding:utf-8

from collections import namedtuple
from configparser import ConfigParser
from configparser import SectionProxy
from enum import Enum
import os
from typing import List
from typing import Set

from appdirs import user_config_dir
from appdirs import user_data_dir

from .attribute import __name__

# from appdirs import site_config_dir
# from appdirs import site_data_dir

# GLOBAL_CONFIG_DIR = site_config_dir(appname=__name__)
# GLOBAL_CONFIG_FILE = os.path.join(GLOBAL_CONFIG_DIR, "dnsprobe.conf")
# GLOBAL_SERVERS_DIR = site_data_dir(appname=f"{__name__}.nameservers")

USER_CONFIG_DIR = user_config_dir(appname=__name__)
assert isinstance(USER_CONFIG_DIR, str), \
    f"unexpected type: {type(USER_CONFIG_DIR)}"

USER_CONFIG_FILE = os.path.join(USER_CONFIG_DIR, "dnsprobe.conf")
assert isinstance(USER_CONFIG_FILE, str), \
    f"unexpected type: {type(USER_CONFIG_FILE)}"

USER_DEAMON_DIR = user_data_dir(appname=f"{__name__}.d")
assert isinstance(USER_DEAMON_DIR, str), \
    f"unexpected type: {type(USER_DEAMON_DIR)}"

USER_SERVERS_DIR = user_data_dir(appname=f"{__name__}.nameservers")
assert isinstance(USER_SERVERS_DIR, str), \
    f"unexpected type: {type(USER_SERVERS_DIR)}"

DEFAULT_CONFIG_ITEM = namedtuple("dnsprobe_default_config_item",
                                 ("section", "option", "default"))
NAMESERVER_DATABASE_ITEM = namedtuple("dnsprobe_nameserver_database_item",
                                      ("name", "url"))


class dnsprobe_config():

    class defaults(Enum):
        THREADS = DEFAULT_CONFIG_ITEM("main", "threads", str(16))
        DEAMON_DIR = DEFAULT_CONFIG_ITEM("main", "deamon_dir", USER_DEAMON_DIR)
        NAMESERVERS_DIR = DEFAULT_CONFIG_ITEM("main", "nameservers_dir",
                                              USER_SERVERS_DIR)

    class nameserver_section():
        PREFIX = "nameserverdb."

        class databases(Enum):
            PUBLIC_DNS = NAMESERVER_DATABASE_ITEM(
                "public-dns", "https://public-dns.info/nameservers-all.csv")

        def __init__(self, section: SectionProxy):
            assert isinstance(section, SectionProxy), \
                f"unexpected type: {type(section)}"
            self.__section: SectionProxy = section

        @property
        def section_name(self) -> str:
            return self.__section.name

        @property
        def database_name(self) -> str:
            return self.format_database_name(self.section_name)

        @property
        def url(self) -> str:
            return self.__section["url"]

        @classmethod
        def format_section_name(cls, database_name: str) -> str:
            return cls.PREFIX + database_name

        @classmethod
        def format_database_name(cls, section_name: str) -> str:
            return section_name.lstrip(cls.PREFIX)

    def __init__(self, parser: ConfigParser):
        assert isinstance(parser, ConfigParser), \
            f"unexpected type: {type(parser)}"
        self.__parser: ConfigParser = parser
        self.__setdefault()

    def __setdefault(self):
        for default in self.defaults:
            item = default.value
            assert isinstance(item, DEFAULT_CONFIG_ITEM), \
                f"unexpected type: {type(item)}"
            section = item.section if isinstance(item.section, str) else \
                self.__parser.default_section
            self.__set_option(section, item.option, item.default)

        for database in self.nameserver_section.databases:
            item = database.value
            assert isinstance(item, NAMESERVER_DATABASE_ITEM), \
                f"unexpected type: {type(item)}"
            section = self.nameserver_section.format_section_name(item.name)
            self.__set_option(section, "url", item.url)

    def __set_option(self, section: str, option: str, value: str):
        if not self.__parser.has_option(section, option):
            if not self.__parser.has_section(section):
                self.__parser.add_section(section)
            self.__parser.set(section, option, value)

    def __get_item(self, item: DEFAULT_CONFIG_ITEM) -> str:
        section = item.section if isinstance(item.section, str) else \
            self.__parser.default_section
        return self.__parser.get(section, item.option)

    def dump(self, file: str = USER_CONFIG_FILE):
        os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, "w") as hdl:
            self.__parser.write(hdl)

    @property
    def threads(self) -> int:
        return int(self.__get_item(self.defaults.THREADS.value))

    @property
    def deamon_dir(self) -> str:
        return self.__get_item(self.defaults.DEAMON_DIR.value)

    @property
    def nameservers_dir(self) -> str:
        return self.__get_item(self.defaults.NAMESERVERS_DIR.value)

    @property
    def all_nameserver_databases(self) -> Set[str]:
        sections: List[str] = self.__parser.sections()
        prefix: str = self.nameserver_section.PREFIX
        length: int = len(prefix)
        return {s[length:] for s in sections if s.startswith(prefix)}

    def get_nameserver_database(self, name: str) -> nameserver_section:
        section_name = self.nameserver_section.format_section_name(name)
        return self.nameserver_section(self.__parser[section_name])

    def get_all_nameserver_databases(self) -> List[nameserver_section]:
        all_databases: Set[str] = self.all_nameserver_databases
        return [self.get_nameserver_database(db) for db in all_databases]

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
