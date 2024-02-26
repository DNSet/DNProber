# coding:utf-8

from binascii import hexlify
from ipaddress import IPv4Address
from ipaddress import IPv6Address
from ipaddress import ip_address
from random import randint
import time
from typing import Union

from dns.resolver import LifetimeTimeout
from dns.resolver import NXDOMAIN
from dns.resolver import NoAnswer
from dns.resolver import NoNameservers
from dns.resolver import Resolver
import ping3

ping3.EXCEPTIONS = True
IPAddress = Union[IPv4Address, IPv6Address]


class dnsprobe():
    '''DNS Prober
    '''

    PING_MIN_TO = 1
    PING_MAX_TO = 8
    TEST_MIN_TO = 0.1
    TEST_MAX_TO = 8.0
    EXAMPLE_DOMAIN = "example.com"

    def __init__(self, address: IPAddress):
        assert isinstance(address, IPAddress), \
            f"unexpected type: {type(address)}"
        resolver = Resolver(configure=False)
        resolver.nameservers = [str(address)]
        self.__addr: IPAddress = address
        self.__resolver = resolver

    @property
    def name(self) -> str:
        return hexlify(data=self.__addr.packed).decode()

    @property
    def address(self) -> str:
        return str(self.__addr)

    @classmethod
    def from_string(cls, address: str) -> "dnsprobe":
        assert isinstance(address, str), f"unexpected type: {type(address)}"
        return dnsprobe(ip_address(address))

    def ping(self, timeout: int = PING_MIN_TO) -> float:
        assert isinstance(timeout, int), f"unexpected type: {type(timeout)}"
        _timeout = min(max(self.PING_MIN_TO, timeout), self.PING_MAX_TO)
        try:
            return ping3.ping(self.address, timeout=_timeout,
                              seq=randint(8192, 32767))
        except ping3.errors.Timeout:
            return -float(_timeout)

    def test(self, domain: str = EXAMPLE_DOMAIN,
             timeout: float = TEST_MIN_TO) -> float:
        assert isinstance(domain, str), f"unexpected type: {type(domain)}"
        assert isinstance(timeout, float), f"unexpected type: {type(timeout)}"
        _timeout = min(max(self.TEST_MIN_TO, timeout), self.TEST_MAX_TO)
        _start = time.perf_counter()

        def ok():
            return time.perf_counter() - _start

        try:
            self.__resolver.resolve(domain, lifetime=_timeout)
            return ok()
        except NXDOMAIN:
            return ok()
        except (NoAnswer, NoNameservers):
            return ok()
        except LifetimeTimeout:
            return -_timeout
