# coding:utf-8

from typing import Generic
from typing import List
from typing import TypeVar

MVT = TypeVar("MVT")  # Value type.
SVT = TypeVar("SVT")  # Value type.


class EmptySlot(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class multislot(Generic[MVT]):

    class singleslot(Generic[SVT]):

        def __init__(self, no: int):
            assert isinstance(no, int), f"unexpected type: {type(no)}"
            self.__slot_data: List[SVT] = list()
            self.__slot_no: int = no

        @property
        def no(self) -> int:
            return self.__slot_no

        def pop(self) -> SVT:
            try:
                return self.__slot_data.pop(0)
            except IndexError:
                raise EmptySlot("pop from empty slot")

        def push(self, *args: SVT) -> None:
            self.__slot_data.extend(args)

    def __init__(self, layer: int):
        assert isinstance(layer, int), f"unexpected type: {type(layer)}"
        self.__slots: List[multislot.singleslot[MVT]] = [
            self.singleslot(i) for i in range(layer)]
        self.__layer: int = layer
        self.__order: int = 0

    def slide(self, delta: int = 1) -> None:
        self.__order = (self.__order + delta) % self.layer

    def slot(self, no: int = -1) -> "singleslot[MVT]":
        order: int = no if no >= 0 and no < self.layer else self.__order
        return self.__slots[order]

    def pop(self) -> MVT:
        return self.slot().pop()

    def push(self, *args: MVT) -> None:
        self.slot().push(*args)

    def delta_slot(self, delta: int = 0) -> "singleslot[MVT]":
        return self.__slots[(self.__order + delta) % self.layer]

    def delta_pop(self, delta: int = 0) -> MVT:
        return self.delta_slot(delta).pop()

    def delta_push(self, *args: MVT, delta: int = 0) -> None:
        self.delta_slot(delta).push(*args)

    @property
    def layer(self) -> int:
        return self.__layer

    @property
    def order(self) -> int:
        return self.__order
