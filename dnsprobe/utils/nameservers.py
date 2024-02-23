# coding:utf-8

import csv
from datetime import datetime
from datetime import timezone
from enum import Enum
import os
import shutil
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from urllib import request


class dnsprobe_nameservers():

    class item():
        TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

        class fields(Enum):
            IP_ADDRESS = "ip_address"
            NAME = "name"
            AS_NUMBER = "as_number"
            AS_ORG = "as_org"
            COUNTRY_CODE = "country_code"
            CITY = "city"
            VERSION = "version"
            ERROR = "error"
            DNSSEC = "dnssec"
            RELIABILITY = "reliability"
            CHECKED_AT = "checked_at"
            CREATED_AT = "created_at"
        FIELDS: List[str] = [field.value for field in fields]

        def __init__(self, **kwargs: str):
            assert isinstance(kwargs, dict), f"unexpected type: {type(kwargs)}"
            self.__values: Dict[str, str] = dict()
            self.__values.update(**kwargs)

            def __get(key: str) -> str:
                return self.__values[key].strip()

            def __get_checked_at() -> datetime:
                ts: str = __get(self.fields.CHECKED_AT.value)
                dt: datetime = datetime.strptime(ts, self.TIME_FORMAT)
                return dt.replace(tzinfo=timezone.utc)

            self.__ip_address: str = __get(self.fields.IP_ADDRESS.value)
            self.__country_code: str = __get(self.fields.COUNTRY_CODE.value)
            __reliability: float = float(__get(self.fields.RELIABILITY.value))
            self.__reliability: float = __reliability
            self.__checked_at: datetime = __get_checked_at()

        @property
        def ip_address(self) -> str:
            return self.__ip_address

        @property
        def country_code(self) -> str:
            return self.__country_code

        @property
        def reliability(self) -> float:
            return self.__reliability

        @reliability.setter
        def reliability(self, value: float):
            self.__reliability = min(max(0.0, value), 1.0)
            self.__checked_at = datetime.now(timezone.utc)

        @property
        def checked_at(self) -> datetime:
            return self.__checked_at

        @property
        def name(self) -> Optional[str]:
            return self.__values.get(self.fields.NAME.value, None)

        def dump(self) -> Dict[str, str]:
            return self.__values

    def __init__(self, dir: str, name: str, reliability: float = 0.0):
        assert isinstance(dir, str), f"unexpected type: {type(dir)}"
        assert isinstance(name, str), f"unexpected type: {type(name)}"
        assert isinstance(reliability, float), \
            f"unexpected type: {type(reliability)}"
        self.__filter_reliability: float = reliability
        self.__data: Dict[str, dnsprobe_nameservers.item] = dict()
        self.__path: str = os.path.join(dir, name)
        self.__name: str = name
        self.__safe_load(self.__path)

    def __iter__(self):
        return iter(self.__data.keys())

    def __getitem__(self, address: str) -> item:
        return self.__data[address]

    def __safe_load(self, path: str) -> None:
        backup: str = f"{path}.bak"
        if os.path.isfile(backup):
            if os.path.isfile(path):
                os.remove(path)
            assert not os.path.exists(path), f"restore {path} still exists"
            assert shutil.move(src=backup, dst=path) == path
        assert not os.path.exists(backup), f"backup {backup} already exists"
        if os.path.exists(path):
            assert os.path.isfile(path), f"'{path}' is not a regular file."
            with open(path) as rhdl:
                for line in csv.DictReader(rhdl):
                    self.update(self.item(**line))

    def __safe_dump(self, path: str) -> None:
        dir: str = os.path.dirname(path)
        if not os.path.exists(dir):
            os.makedirs(dir)
        backup: str = f"{path}.bak"
        assert not os.path.exists(backup), f"backup {backup} already exists"
        if os.path.isfile(path):
            assert shutil.move(src=path, dst=backup) == backup
        with open(path, "w") as whdl:
            writer = csv.DictWriter(whdl, fieldnames=self.item.FIELDS)
            writer.writeheader()
            for item in self.__data.values():
                writer.writerow(item.dump())
        if os.path.isfile(backup):
            os.remove(backup)

    def dump(self, path: Optional[str] = None) -> None:
        self.__safe_dump(path if isinstance(path, str) else self.__path)

    def update(self, item: item) -> None:
        assert isinstance(item, dnsprobe_nameservers.item), \
            f"unexpected type: {type(item)}"
        self.__data.setdefault(item.ip_address, item)

    def filter(self, item: item) -> bool:
        if item.reliability < self.reliability:
            return False
        return True

    @property
    def name(self) -> str:
        return self.__name

    @property
    def reliability(self) -> float:
        return self.__filter_reliability

    @property
    def filter_address(self) -> Set[str]:
        return {k for k, v in self.__data.items() if self.filter(v)}

    @classmethod
    def download(cls, url: str, filename: Optional[str] = None) -> str:
        return request.urlretrieve(url, filename)[0]


def update_nameservers(dir: str, name: str, url: str) -> None:
    nameservers = dnsprobe_nameservers(dir, name)
    with open(dnsprobe_nameservers.download(url)) as rhdl:
        for line in csv.DictReader(rhdl):
            nameservers.update(dnsprobe_nameservers.item(**line))
    nameservers.dump()
