# Copyright 2026 Apheleia
#
# Description:
# Apheleia Verification Library Slave Driver

import asyncio
import random

import avl
from cocotb.triggers import First

from ._driver import Driver
from ._item import SequenceItem


class SlvDriver(Driver):

    def __init__(self, name: str, parent: avl.Component) -> None:
        """
        Initialize the Slave Driver for the SPI agent.

        :param name: Name of the agent instance
        :type name: str
        :param parent: Parent component
        :type parent: Component
        """
        super().__init__(name, parent)

        self.idx = avl.Factory.get_variable(f"{self.get_full_name()}.idx", 0)
        """Index of the driver in the chip select (cs)."""

    def selected(self) -> bool:
        """
        Check if the slave is selected

        :return: True if cs[idx] is asserted
        :rtype: bool
        """
        cs = self.i_f.get("cs")
        return cs is not None and bool((self.i_f.cs_decode(cs) >> self.idx) & 1)

    async def reset(self) -> None:
        """
        Reset the driver - by default miso 0.
        """

        self.i_f.set("miso", 0)

    def miso_bit(self, item : SequenceItem, k : int) -> int:
        """
        Get miso bit k of the transfer (in transmission order).

        By default bits are taken from item.miso as a DATA_WIDTH bit value, i.e. when MSB first
        the response is left aligned. Bits beyond DATA_WIDTH are 0.

        :param item: The item being completed
        :type item: SequenceItem
        :param k: Bit index
        :type k: int
        :return: Bit
        :rtype: int
        """
        if k >= self.i_f.DATA_WIDTH:
            return 0
        return self.i_f.to_bits(int(item.get("miso")), self.i_f.DATA_WIDTH)[k]

    def mosi_bit(self, item : SequenceItem, k : int, bit : int) -> None:
        """
        Called when mosi bit k of the transfer (in transmission order) is sampled.

        By default does nothing.

        :param item: The item being completed
        :type item: SequenceItem
        :param k: Bit index
        :type k: int
        :param bit: Bit
        :type bit: int
        """
        pass

    async def drive(self, item : SequenceItem) -> None:
        """
        Complete a transfer, from chip select assertion to de-assertion.

        mosi is sampled and miso driven on the SCLK edges defined by the interface.
        On completion the item length, mosi and miso fields reflect the transfer.

        :param item: The sequence item to complete
        :type item: SequenceItem
        """
        i_f = self.i_f
        try:
            rx, tx = [], []
            edge = 0
            sclk = i_f.get("sclk")

            def sample_bit() -> None:
                if i_f.sample_index(len(rx), i_f.MASTER_DRIVE_EDGE, i_f.SLAVE_SAMPLE_EDGE) == edge:
                    rx.append(i_f.get("mosi", 0))
                    self.mosi_bit(item, len(rx) - 1, rx[-1])

            def drive_bit() -> None:
                if i_f.drive_index(len(tx), i_f.SLAVE_DRIVE_EDGE) == edge:
                    tx.append(self.miso_bit(item, len(tx)) & 1)
                    i_f.set("miso", tx[-1])

            drive_bit()
            while True:
                await First(i_f.sclk.value_change, i_f.cs.value_change)
                if i_f.get("sclk") != sclk:
                    sclk = i_f.get("sclk")
                    edge += 1
                    sample_bit()
                    drive_bit()

                if not self.selected():
                    break

            if i_f.is_leading(i_f.MASTER_DRIVE_EDGE) and i_f.is_leading(i_f.SLAVE_SAMPLE_EDGE):
                # Final bit sampled on chip select de-assertion
                edge += 1
                sample_bit()

            n = min(len(rx), i_f.DATA_WIDTH)
            tx.extend([0] * n)
            item.set("length", n)
            item.set("mosi", i_f.from_bits(rx[:n]))
            item.set("miso", i_f.from_bits(tx[:n]))

            # Clear the bus
            await self.quiesce()

            # Complete responses queued by the slave sequence
            if item.get_event("done") is not None:
                item.set_event("done")

        except asyncio.CancelledError:
            raise
        except Exception:
            self.debug(f"Slave drive task for item was cancelled by reset:\n{item}")

    async def get_next_item(self, item : SequenceItem = None) -> SequenceItem:
        """
        Wait for chip select assertion (out of reset) and get the item to be completed.

        The item is the next response queued by the slave sequence, if available on chip select assertion,
        otherwise a new item (miso 0). A queued response interrupted by reset is reused.

        :param item: The item interrupted by reset, defaults to None
        :type item: SequenceItem, optional
        :return: The next sequence item
        :rtype: SequenceItem
        """

        prev = self.selected()
        while True:
            await self.i_f.cs.value_change
            sel = self.selected()
            if sel and not prev and self.i_f.get("rst_n", 0):
                break
            prev = sel

        if item is not None and item.get_sequencer() is not None:
            next_item = item
        elif len(self.seq_item_port):
            next_item = self.seq_item_port.pop(0)
        else:
            next_item = SequenceItem(f"from_{self.name}", self)

        next_item.set("cs", 1 << self.idx)
        return next_item


class SlvRandomDriver(SlvDriver):
    def __init__(self, name: str, parent: avl.Component) -> None:
        """
        Initialize the Random Slave Driver for the SPI agent.

        :param name: Name of the agent instance
        :type name: str
        :param parent: Parent component
        :type parent: Component
        """
        super().__init__(name, parent)

    async def get_next_item(self, item : SequenceItem = None) -> SequenceItem:
        """
        Get the next sequence item, randomizing the response (miso) if not queued by the slave sequence.
        """
        item = await super().get_next_item(item)
        if item.get_sequencer() is None:
            item.randomize_response()

        return item


class SlvMemoryDriver(SlvDriver):
    def __init__(self, name: str, parent: avl.Component) -> None:
        """
        Initialize the Memory Slave Driver for the SPI agent.

        Each transfer is a command byte, an address of addr_width bits and data bytes:

        - write_cmd: data bytes are written to memory from the address.
        - read_cmd: data bytes are driven on miso from memory from the address.
        - other commands are ignored and miso is 0.

        Addresses outside the configured ranges ignore writes and return random data.
        Responses queued by the slave sequence are completed, but their miso is ignored.

        :param name: Name of the agent instance
        :type name: str
        :param parent: Parent component
        :type parent: Component
        """
        super().__init__(name, parent)
        self.memory = avl.Memory(width=8)
        self.memory.miss = lambda address : None

        self.addr_width = avl.Factory.get_variable(f"{self.get_full_name()}.addr_width", 16)
        """Address width (bits) (default 16)"""

        if not isinstance(self.addr_width, int) or self.addr_width < 1:
            raise ValueError("addr_width must be an integer >= 1")

        self.write_cmd = avl.Factory.get_variable(f"{self.get_full_name()}.write_cmd", 0x02)
        """Write command (default 0x02)"""

        self.read_cmd = avl.Factory.get_variable(f"{self.get_full_name()}.read_cmd", 0x03)
        """Read command (default 0x03)"""

        # Add ranges to the memory if specified in the configuration
        self.ranges = avl.Factory.get_variable(f"{self.get_full_name()}.ranges", None)
        """List of (start, end) address ranges - end exclusive"""
        if self.ranges is not None:
            for r in self.ranges:
                if r[1] > (1 << self.addr_width):
                    raise ValueError(f"Range {r} exceeds addr_width {self.addr_width}")
                self.memory.add_range(r[0], r[1])

        self._rx_ = []
        self._cmd_ = None
        self._addr_ = None
        self._byte_ = (None, 0)

    async def get_next_item(self, item : SequenceItem = None) -> SequenceItem:
        """
        Get the next sequence item and reset the command decode.
        """
        item = await super().get_next_item(item)
        self._rx_ = []
        self._cmd_ = None
        self._addr_ = None
        self._byte_ = (None, 0)
        return item

    def _read_byte_(self, address : int) -> int:
        """
        Read a byte from memory, random if the address is not valid
        """
        if self.memory._check_address_(address):
            return self.memory.read(address)
        return random.getrandbits(8)

    def mosi_bit(self, item : SequenceItem, k : int, bit : int) -> None:
        """
        Decode the command and address, and write data bytes to memory.
        """
        self._rx_.append(bit)
        hdr = 8 + self.addr_width
        n = len(self._rx_)

        if n == 8:
            self._cmd_ = self.i_f.from_bits(self._rx_[0:8])
        elif n == hdr:
            self._addr_ = self.i_f.from_bits(self._rx_[8:hdr])
        elif n > hdr and (n - hdr) % 8 == 0 and self._cmd_ == self.write_cmd:
            address = self._addr_ + (n - hdr) // 8 - 1
            if self.memory._check_address_(address):
                self.memory.write(address, self.i_f.from_bits(self._rx_[-8:]))

    def miso_bit(self, item : SequenceItem, k : int) -> int:
        """
        Drive data bytes from memory for read commands.

        The final address bit must be sampled before the first data bit is driven, otherwise 0 is driven.
        """
        hdr = 8 + self.addr_width
        if k < hdr or self._cmd_ != self.read_cmd or self._addr_ is None:
            return 0

        address = self._addr_ + (k - hdr) // 8
        if self._byte_[0] != address:
            self._byte_ = (address, self._read_byte_(address))

        return self.i_f.to_bits(self._byte_[1], 8)[(k - hdr) % 8]

__all__ = ["SlvDriver", "SlvRandomDriver", "SlvMemoryDriver"]
