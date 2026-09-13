# Copyright 2026 Apheleia
#
# Description:
# Apheleia Verification Library Base Driver


import asyncio

import avl
from cocotb.triggers import FallingEdge, select

from ._item import SequenceItem


class Driver(avl.Driver):

    def __init__(self, name: str, parent: avl.Component) -> None:
        """
        Initialize the Driver for the SPI agent.

        :param name: Name of the agent instance
        :type name: str
        :param parent: Parent component
        :type parent: Component
        """
        super().__init__(name, parent)

        self.i_f = avl.Factory.get_variable(f"{self.get_full_name()}.i_f", None)

    async def reset(self) -> None:
        """
        Reset the driver by setting all signals to their default values.
        This method is called when the driver is reset.

        Must be implemented in subclasses.
        """

        raise NotImplementedError("Reset method must be implemented in subclasses")

    async def wait_on_reset(self) -> None:
        """
        Wait for the reset signal to go low and then call the reset method.
        """

        try:
            await FallingEdge(self.i_f.rst_n)
            await self.reset()
        except asyncio.CancelledError:
            raise
        except Exception:
            pass

    async def quiesce(self) -> None:
        """
        Quiesce the driver between transfers.

        By default calls reset() to set all signals to their default values.
        Can be overridden in subclasses to add randomization or other behavior.
        """

        await self.reset()

    async def drive(self, item : SequenceItem) -> None:
        """
        Drive a transfer based on the provided sequence item.

        :param item: The sequence item containing the values to drive
        :type item: SequenceItem
        """
        raise NotImplementedError("Drive method must be implemented in subclasses")

    async def get_next_item(self, item : SequenceItem = None) -> SequenceItem:
        """
        Get the next sequence item.

        For the master driver this method retrieves the next sequence item from the sequencer or
        the previously reset interrupted item.

        For the slave driver this method waits for chip select assertion and gets the item to be completed -
        the next response queued by the slave sequence, or a new item.

        :param item: The sequence item to retrieve, defaults to None
        :type item: SequenceItem, optional
        :return: The next sequence item
        :rtype: SequenceItem
        :raises NotImplementedError: If the method is not implemented in subclasses
        """

        raise NotImplementedError("get_next_item method must be implemented in subclasses")

    async def run_phase(self):
        """
        Run phase for the Driver.

        Drives each item, restarting on reset.
        """
        item = None

        # Start from reset state
        await self.reset()

        while True:
            item = await self.get_next_item(item)

            # Drive or reset - whichever completes first cancels the other
            idx, _ = await select(self.drive(item), self.wait_on_reset())

            if idx == 0:
                item = None

__all__ = ["Driver"]
