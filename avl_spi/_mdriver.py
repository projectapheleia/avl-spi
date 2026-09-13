# Copyright 2026 Apheleia
#
# Description:
# Apheleia Verification Library Master Driver

import asyncio
import random

import avl
from cocotb.triggers import FallingEdge, RisingEdge

from ._driver import Driver
from ._item import SequenceItem


class MstDriver(Driver):

    def __init__(self, name: str, parent: avl.Component) -> None:
        """
        Initialize the Master Driver for the SPI agent.

        :param name: Name of the agent instance
        :type name: str
        :param parent: Parent component
        :type parent: Component
        """
        super().__init__(name, parent)

        self.rate_limit = avl.Factory.get_variable(f"{self.get_full_name()}.rate_limit", lambda : 1.0)
        """Rate limit for starting transfers. lambda function (0.0 - 1.0)"""

        if not callable(self.rate_limit):
            raise TypeError("rate_limit must be a callable (lambda function) that returns a float between 0.0 and 1.0")

        self.half_period = avl.Factory.get_variable(f"{self.get_full_name()}.half_period", 1)
        """SCLK half period (clk cycles)"""

        if not isinstance(self.half_period, int) or self.half_period < 1:
            raise ValueError("half_period must be an integer >= 1")

        self.cs_setup = avl.Factory.get_variable(f"{self.get_full_name()}.cs_setup", max(self.i_f.CS_SETUP, self.half_period))
        """Chip select assertion to first SCLK edge (clk cycles) (default max(CS_SETUP, half_period))"""

        self.cs_hold = avl.Factory.get_variable(f"{self.get_full_name()}.cs_hold", max(self.i_f.CS_HOLD, self.half_period))
        """Last SCLK edge to chip select de-assertion (clk cycles) (default max(CS_HOLD, half_period))"""

        self.cs_gap = avl.Factory.get_variable(f"{self.get_full_name()}.cs_gap", max(self.i_f.CS_GAP, self.half_period))
        """Minimum chip select de-assertion between transfers (clk cycles) (default max(CS_GAP, half_period))"""

        for name in ["cs_setup", "cs_hold", "cs_gap"]:
            if not isinstance(getattr(self, name), int) or getattr(self, name) < 0:
                raise ValueError(f"{name} must be an integer >= 0")

    async def reset(self) -> None:
        """
        Reset the driver - chip selects de-asserted, sclk idle (CPOL) and mosi 0.
        """

        self.i_f.set("cs", self.i_f.cs_encode(0))
        self.i_f.set("sclk", self.i_f.CPOL)
        self.i_f.set("mosi", 0)

    async def quiesce(self) -> None:
        """
        Quiesce the driver between transfers - by default mosi 0.
        """

        self.i_f.set("mosi", 0)

    async def wait_cycles(self, n : int) -> None:
        """
        Wait n rising edges of clk.

        :param n: Number of clk cycles
        :type n: int
        """

        for _ in range(n):
            await RisingEdge(self.i_f.clk)

    async def drive(self, item : SequenceItem) -> None:
        """
        Drive a transfer based on the provided sequence item.

        Chip select is asserted on a rising edge of clk. The first SCLK edge follows cs_setup clk cycles later,
        then SCLK toggles every half_period. Chip select is de-asserted cs_hold clk cycles after the final SCLK edge,
        and remains de-asserted for at least cs_gap clk cycles.
        miso is sampled on its SCLK edge. mosi is driven on the falling edge of clk following its SCLK edge
        (or chip select assertion). The miso item field is updated with the sampled data.

        :param item: The sequence item containing the values to drive
        :type item: SequenceItem
        """
        i_f = self.i_f
        try:
            length = int(item.get("length"))
            tx = i_f.to_bits(int(item.get("mosi")), length)
            rx = []
            sclk = i_f.CPOL

            # Rate Limiter
            await RisingEdge(i_f.clk)
            rate = self.rate_limit()
            while random.random() > rate:
                await RisingEdge(i_f.clk)

            i_f.set("cs", i_f.cs_encode(int(item.get("cs"))))

            for edge in range(2 * length + 1):
                if edge > 0:
                    await self.wait_cycles(self.cs_setup if edge == 1 else self.half_period)
                    if i_f.sample_index(len(rx), i_f.SLAVE_DRIVE_EDGE, i_f.MASTER_SAMPLE_EDGE) == edge:
                        rx.append(i_f.get("miso", 0))
                    sclk ^= 1
                    i_f.set("sclk", sclk)

                if len(tx) and i_f.drive_index(length - len(tx), i_f.MASTER_DRIVE_EDGE) == edge:
                    await FallingEdge(i_f.clk)
                    i_f.set("mosi", tx.pop(0))

            await self.wait_cycles(self.cs_hold)
            if len(rx) < length:
                # Final bit sampled on chip select de-assertion
                rx.append(i_f.get("miso", 0))
            i_f.set("cs", i_f.cs_encode(0))
            await self.wait_cycles(self.cs_gap)

            item.set("miso", i_f.from_bits(rx))

            # Clear the bus
            await self.quiesce()

            item.set_event("done")

        except asyncio.CancelledError:
            raise
        except Exception:
            self.warning(f"Master drive task for item was cancelled by reset:\n{item}")

    async def get_next_item(self, item : SequenceItem = None) -> SequenceItem:
        """
        Get the next sequence item.

        This method retrieves the next sequence item from the sequencer or
        the previously reset interrupted item, and waits for reset to complete.

        :param item: The sequence item to retrieve, defaults to None
        :type item: SequenceItem, optional
        :return: The next sequence item
        :rtype: SequenceItem
        """

        next_item = item if item is not None else await self.seq_item_port.blocking_get()

        while self.i_f.get("rst_n", 0) == 0:
            await RisingEdge(self.i_f.clk)

        return next_item

__all__ = ["MstDriver"]
