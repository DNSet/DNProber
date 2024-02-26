# coding:utf-8

from collections import namedtuple
from ctypes import Structure
from ctypes import addressof
from ctypes import c_char
from ctypes import c_uint8
from ctypes import c_uint16
from ctypes import c_uint64
from ctypes import memmove
from ctypes import sizeof
from datetime import datetime
from datetime import timezone
import os
from queue import Empty
from queue import Queue
from random import randint
from threading import Thread
import time
from typing import Dict
from typing import Optional
from typing import Sequence
from typing import Set

from strie import ctrie
from strie import testakey
from xarg import add_command
from xarg import argp
from xarg import commands
from xarg import run_command

from ..cmds.config import add_opt_config_file
from ..cmds.config import get_config
from ..utils import __deamon_description__
from ..utils import __deamon_name__
from ..utils import __url_home__
from ..utils import __version__
from ..utils import dnsprobe
from ..utils import dnsprobe_nameservers
from .multislot import EmptySlot
from .multislot import multislot


def checkip(key: str, len: int) -> bool:
    return True


testip46 = testakey(allowed_char=testakey.ip46, inspection=checkip)


class dnsprobe_deamon():
    class item():
        class stat():

            def __init__(self):
                self.__total: int = 0
                self.__fault: int = 0
                self.__retry: int = 0
                self.__cost: float = 0.0
                self.__reliability: float = 1.0

            @property
            def total(self) -> int:
                return self.__total

            @property
            def retry(self) -> int:
                return self.__retry

            @property
            def fault(self) -> int:
                return self.__fault

            @property
            def normal(self) -> int:
                return self.__total - self.__fault

            @property
            def cost(self) -> float:
                return self.__cost

            @property
            def reliability(self) -> float:
                return self.__reliability

            @reliability.setter
            def reliability(self, value: float):
                self.__reliability = min(max(0.0, value), 1.0)

            @property
            def average_cost(self) -> float:
                return self.cost / self.total if self.total > 0 else 1.0

            @property
            def block_time(self) -> float:
                return self.average_cost * 2**self.retry

            def count(self, cost: float) -> None:
                self.__total += 1
                if cost < 0.0:
                    self.__retry += 1
                    self.__fault += 1
                    self.__cost -= cost
                    self.reliability -= 0.0001 * 2**min(self.__retry, 8)
                else:
                    self.__retry = 0
                    self.__cost += cost
                    self.reliability += 0.1 * 2**-cost

        class stor(Structure):

            _fields_ = [
                ("field_checked_at", c_uint64),
                ("field_reliability", c_uint16),
                ("field_average_cost", c_uint16),
                ("field_retry", c_uint8),
            ]

            @property
            def checked_at(self) -> datetime:
                return datetime.fromtimestamp(float(self.field_checked_at),
                                              tz=timezone.utc)

            @property
            def reliability(self) -> float:
                return self.field_reliability / 1000

            @property
            def average_cost(self) -> float:
                return self.field_average_cost / 1000

            @property
            def delta_slot(self) -> int:
                value: int = 2**self.field_retry
                return randint(value - 1, value * 2)

            @classmethod
            def dump(cls, checked_at: int, reliability: int,
                     average_cost: int, retry: int) -> bytes:
                data: dnsprobe_deamon.item.stor = cls()
                data.field_checked_at = checked_at
                data.field_reliability = min(max(0, reliability), 1000)
                data.field_average_cost = min(max(0, average_cost), 30000)
                data.field_retry = min(max(0, retry), 100)
                return bytes(data)

            @classmethod
            def load(cls, data: bytes) -> "dnsprobe_deamon.item.stor":
                len: int = sizeof(cls)
                obj: dnsprobe_deamon.item.stor = cls()
                ptr = (c_char * len).from_buffer(bytearray(data))
                memmove(addressof(obj), ptr, len)
                return obj

        def __init__(self, address: str):
            assert isinstance(address, str), \
                f"unexpected type: {type(address)}"
            self.__checked_at: datetime = datetime.now(timezone.utc)
            self.__prober: dnsprobe = dnsprobe.from_string(address)
            self.__stat: dnsprobe_deamon.item.stat = self.stat()
            self.__nset: Set[str] = set()
            self.__addr: str = address

        @property
        def address(self) -> str:
            return self.__addr

        @property
        def databases(self) -> Set[str]:
            return self.__nset

        @property
        def checked_at(self) -> datetime:
            return self.__checked_at

        @property
        def reliability(self) -> float:
            return round(self.__stat.reliability, 3)

        @property
        def delay(self) -> int:
            min_delay: int = 2**self.__stat.retry - 1
            return randint(min_delay, min_delay * 2)

        def access(self) -> float:
            timeout: float = self.__stat.block_time * 2
            cost: float = self.__prober.test(timeout=timeout)
            self.__checked_at = datetime.now(timezone.utc)
            self.__stat.count(cost)
            return cost

        def update(self, name: str, checked_at: datetime, reliability: float):
            assert isinstance(name, str), f"unexpected type: {type(name)}"
            assert isinstance(checked_at, datetime), \
                f"unexpected type: {type(checked_at)}"
            assert isinstance(reliability, float), \
                f"unexpected type: {type(reliability)}"
            self.__stat.reliability = min(self.reliability, reliability)
            self.__checked_at = checked_at
            self.__nset.add(name)

        def dump(self) -> bytes:
            checked_at: int = int(self.checked_at.timestamp())
            reliability: int = min(max(0, int(self.reliability * 1000)), 1000)
            average_cost: int = int(min(self.__stat.average_cost, 8.0) * 1000)
            return self.stor.dump(checked_at, reliability, average_cost,
                                  self.__stat.retry)

    STAT_ITEM = namedtuple("dnsprobed_stat_item", ("entry", "speed"))
    TASK_ITEM = namedtuple("dnsprobed_task_item", ("entry"))

    def __init__(self, folder: str):
        assert isinstance(folder, str), f"unexpected type: {type(folder)}"
        os.makedirs(folder, exist_ok=True)
        self.__ctrie: ctrie = ctrie(path=folder, word=(1, ), test=testip46,
                                    cachemax=10**6, readonly=False)
        self.__statq: Queue[dnsprobe_deamon.STAT_ITEM] = Queue(maxsize=1024)
        self.__taskq: Queue[dnsprobe_deamon.TASK_ITEM] = Queue(maxsize=1024)
        self.__names: Dict[str, dnsprobe_nameservers] = dict()
        self.__items: Dict[str, dnsprobe_deamon.item] = dict()
        self.__slots: multislot[dnsprobe_deamon.item] = multislot(24 * 6)
        self.__slots.slide(self.__slot_no)
        self.__count: int = 0

    @property
    def __slot_no(self) -> int:
        def minutes(dt: datetime) -> int:
            return dt.hour * 60 + dt.minute
        return int(minutes(datetime.now()) / 10)

    @property
    def count(self) -> int:
        return self.__count

    def __slide(self) -> None:
        while self.__slot_no == self.__slots.order:
            time.sleep(30)
        self.__slots.slide()

    def __update_address(self, ns: dnsprobe_nameservers, addr: str) -> None:
        slot: int = 0
        name: str = ns.name
        checked_at: datetime = ns[addr].checked_at
        reliability: float = ns[addr].reliability
        if addr in self.__ctrie:
            stor = self.item.stor.load(self.__ctrie[addr])
            slot = stor.delta_slot
            checked_at = stor.checked_at
            reliability = stor.reliability
        if addr not in self.__items:
            item: dnsprobe_deamon.item = self.item(addr)
            self.__slots.delta_push(item, delta=slot)
            self.__items[addr] = item
            self.__count += 1
        self.__items[addr].update(name, checked_at, reliability)

    def update_nameservers(self, ns: dnsprobe_nameservers) -> None:
        assert ns.name not in self.__names, f"'{ns.name}' already exists"
        self.__names[ns.name] = ns
        for addr in self.__names[ns.name]:
            self.__update_address(ns, addr)

    def task(self) -> None:
        def handle(task_item: dnsprobe_deamon.TASK_ITEM):
            entry: dnsprobe_deamon.item = task_item.entry
            cost: float = entry.access()
            self.__statq.put(self.STAT_ITEM(entry, cost))

        while self.count > 0:
            try:
                handle(self.__taskq.get())
            except Empty:
                continue

    def stat(self) -> None:
        objects: Set[dnsprobe_deamon.item] = set()

        def requeue(stat_item: dnsprobe_deamon.STAT_ITEM):
            entry: dnsprobe_deamon.item = stat_item.entry
            milli: float = stat_item.speed * 1000
            delay: int = randint(3, 6) if milli > 0 else entry.delay
            delta: int = min(max(1, delay), self.__slots.layer - 1)
            self.__ctrie[entry.address] = self.__items[entry.address].dump()
            self.__slots.delta_push(entry, delta=delta)  # Repush to multislot
            speed = f"{milli:.2f}ms" if milli > 0 else f"timeout({int(milli)})"
            message = f"{entry.address}: {entry.reliability}, {speed}, {delta}"
            commands().logger.info(message)
            objects.add(entry)

        def flush():
            pass

        while self.count > 0:
            try:
                requeue(self.__statq.get(block=False, timeout=15.0))
                if len(objects) < 10000:
                    continue
            except Empty:
                pass
            flush()

    def run(self, threads: int = 8) -> None:
        for i in range(threads):
            Thread(target=self.task, name=f"dnsprobed-{i}").start()
        Thread(target=self.stat, name="dnsprobed-stat").start()

        slot_count: int = 0
        item_count: int = 0
        while self.count > 0:
            try:
                item: dnsprobe_deamon.item = self.__slots.pop()
                self.__taskq.put(self.TASK_ITEM(item))
                slot_count += 1
            except EmptySlot:
                item_count += slot_count
                slot_no: int = self.__slots.order
                message: str = f"SLOT {slot_no}: {slot_count}/{item_count}"
                commands().logger.info(message)
                slot_count = 0
                time.sleep(60)
                self.__slide()


@add_command(__deamon_name__)
def add_cmd(_arg: argp):
    add_opt_config_file(_arg)


@run_command(add_cmd)
def run_cmd(cmds: commands) -> int:
    cmds.args.config = get_config(cmds)
    nameservers_dir = cmds.args.config.nameservers_dir
    dnsprobed = dnsprobe_deamon(cmds.args.config.deamon_dir)
    for database in cmds.args.config.all_nameserver_databases:
        db = cmds.args.config.get_nameserver_database(database)
        ns = dnsprobe_nameservers(nameservers_dir, db.database_name)
        dnsprobed.update_nameservers(ns)
    dnsprobed.run(threads=cmds.args.config.threads)
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    cmds = commands()
    cmds.version = __version__
    return cmds.run(root=add_cmd, argv=argv,
                    description=__deamon_description__,
                    epilog=f"For more, please visit {__url_home__}.")