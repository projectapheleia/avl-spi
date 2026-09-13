# Copyright 2026 Apheleia
#
# Description:
# Apheleia Verification Library Master Sequence

import random

import avl

from ._item import SequenceItem


class MstSequence(avl.Sequence):

    def __init__(self, name: str, parent: avl.Component) -> None:
        """
        Initialize the sequence

        Sequence of independently randomized transfers

        :param name: Name of the sequence
        :param parent: Parent component of the sequence
        """
        super().__init__(name, parent)

        self.i_f = avl.Factory.get_variable(f"{self.get_full_name()}.i_f", None)
        """Handle to interface - defines capabilities and parameters"""

        self.n_items = avl.Factory.get_variable(f"{self.get_full_name()}.n_items", 1)
        """Number of items in the sequence (default 1)"""

        self.length = avl.Factory.get_variable(f"{self.get_full_name()}.length", None)
        """Transfer length (bits) lambda function (optional, default None - random 1 to DATA_WIDTH)"""

    async def _send_(self, item : SequenceItem, randomize : bool = True) -> SequenceItem:
        """
        Send an item to the driver

        :param item: Item to send
        :param randomize: Randomize the item before sending (default True)
        :return: The item sent (miso updated by the driver)
        """

        await self.start_item(item)

        if randomize:
            item.randomize_request()

        await self.finish_item(item)

        return item

    async def next(self) -> SequenceItem:
        """
        Send the next random item in the sequence
        """

        item = SequenceItem(f"from_{self.name}", self)

        if self.length is not None:
            length = self.length()
            item.add_constraint("_c_length_", lambda x, y=length: x == y, item.length)

        return await self._send_(item, randomize=True)

    async def transfer(self, **kwargs) -> SequenceItem:
        """
        Send a directed transfer to the driver

        cs must be specified. Other fields not specified default to length=DATA_WIDTH and mosi=0.

        :param kwargs: Keyword arguments to set on the item
        :return: The item sent (miso updated by the driver)
        :raises ValueError: If cs is not specified
        """
        if "cs" not in kwargs:
            raise ValueError("transfer requires cs")

        item = SequenceItem(f"from_{self.name}", self)
        item.set("length", self.i_f.DATA_WIDTH)

        for k,v in kwargs.items():
            if hasattr(item, k):
                item.set(k, v)

        return await self._send_(item, randomize=False)

    async def body(self) -> None:
        """
        Body of the sequence
        """

        self.info(f"Starting sequence {self.get_full_name()} with {self.n_items} items")
        for _ in range(self.n_items):
            await self.next()


class MstMemorySequence(MstSequence):

    def __init__(self, name: str, parent: avl.Component) -> None:
        """
        Initialize the sequence

        Sequence of memory writes and reads, compatible with :any:`SlvMemoryDriver`.
        Each transfer is a command byte, an address of addr_width bits and one or more data bytes.

        :param name: Name of the sequence
        :param parent: Parent component of the sequence
        """
        super().__init__(name, parent)

        self.addr_width = avl.Factory.get_variable(f"{self.get_full_name()}.addr_width", 16)
        """Address width (bits) (default 16)"""

        if not isinstance(self.addr_width, int) or self.addr_width < 1:
            raise ValueError("addr_width must be an integer >= 1")

        self.write_cmd = avl.Factory.get_variable(f"{self.get_full_name()}.write_cmd", 0x02)
        """Write command (default 0x02)"""

        self.read_cmd = avl.Factory.get_variable(f"{self.get_full_name()}.read_cmd", 0x03)
        """Read command (default 0x03)"""

        self.max_bytes = avl.Factory.get_variable(f"{self.get_full_name()}.max_bytes", 1)
        """Maximum data bytes per random transfer (default 1)"""

        self.ranges = avl.Factory.get_variable(f"{self.get_full_name()}.ranges", None)
        """Dictionary of (cs index, start, end) : weight - end exclusive (optional, default None)"""

        if self.ranges is not None:
            for r in self.ranges:
                if r[2] > (1 << self.addr_width):
                    raise ValueError(f"Range {r} exceeds addr_width {self.addr_width}")

    def _frame_(self, cmd : int, addr : int, data : list[int]) -> tuple[int, int]:
        """
        Build the mosi data for a memory transfer

        :param cmd: Command
        :param addr: Address
        :param data: Data bytes
        :return: Transfer length and mosi
        """
        if addr < 0 or addr + max(len(data), 1) > (1 << self.addr_width):
            raise ValueError(f"Address {hex(addr)} with {len(data)} bytes exceeds addr_width {self.addr_width}")

        bits = self.i_f.to_bits(cmd, 8) + self.i_f.to_bits(addr, self.addr_width)
        for d in data:
            bits += self.i_f.to_bits(d, 8)

        if len(bits) > self.i_f.DATA_WIDTH:
            raise ValueError(f"Transfer length {len(bits)} exceeds DATA_WIDTH {self.i_f.DATA_WIDTH}")

        return len(bits), self.i_f.from_bits(bits)

    async def write(self, cs : int, addr : int, data : list[int]) -> SequenceItem:
        """
        Write bytes to memory

        :param cs: Chip select (1-hot)
        :param addr: Address of first byte
        :param data: Bytes to write
        :return: The item sent
        """
        length, mosi = self._frame_(self.write_cmd, addr, data)
        return await self.transfer(cs=cs, length=length, mosi=mosi)

    async def read(self, cs : int, addr : int, n : int) -> list[int]:
        """
        Read bytes from memory

        :param cs: Chip select (1-hot)
        :param addr: Address of first byte
        :param n: Number of bytes
        :return: Bytes read
        """
        length, mosi = self._frame_(self.read_cmd, addr, [0] * n)
        item = await self.transfer(cs=cs, length=length, mosi=mosi)

        bits = self.i_f.to_bits(int(item.get("miso")), length)[8 + self.addr_width:]
        return [self.i_f.from_bits(bits[i:i+8]) for i in range(0, 8 * n, 8)]

    async def body(self) -> None:
        """
        Body of the sequence - random writes and reads
        """

        self.info(f"Starting memory sequence {self.get_full_name()} with {self.n_items} items")
        for _ in range(self.n_items):
            n = random.randint(1, self.max_bytes)

            if self.ranges is not None:
                (idx, lo, hi) = random.choices(list(self.ranges.keys()), weights=list(self.ranges.values()), k=1)[0]
            else:
                (idx, lo, hi) = (random.randrange(self.i_f.CS_WIDTH), 0, 1 << self.addr_width)

            addr = random.randint(lo, hi - n)
            if random.random() < 0.5:
                await self.write(1 << idx, addr, [random.getrandbits(8) for _ in range(n)])
            else:
                await self.read(1 << idx, addr, n)

__all__ = ["MstSequence", "MstMemorySequence"]
