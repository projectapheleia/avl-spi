# Copyright 2026 Apheleia
#
# Description:
# Apheleia Verification Library Monitor

import asyncio

import avl
from cocotb.triggers import FallingEdge, First, RisingEdge, select

from ._item import SequenceItem


class Monitor(avl.Monitor):
    def __init__(self, name: str, parent: avl.Component) -> None:
        """
        Initialize the Monitor for the SPI agent.

        :param name: Name of the agent instance
        :type name: str
        :param parent: Parent component
        :type parent: Component
        """
        super().__init__(name, parent)

        self.i_f = avl.Factory.get_variable(f"{self.get_full_name()}.i_f", None)

    async def monitor(self) -> None:
        """
        Monitor a transfer, from chip select assertion to change.

        mosi is sampled on the slave sample edge and miso on the master sample edge.
        """
        i_f = self.i_f
        try:
            item = SequenceItem(f"from_{self.name}", self)
            cs = i_f.cs_decode(i_f.get("cs"))
            item.set("cs", cs)

            mosi, miso = [], []
            edge = 0
            sclk = i_f.get("sclk")

            if sclk != i_f.CPOL:
                self.warning(f"sclk ({sclk}) not idle (CPOL={i_f.CPOL}) on chip select assertion")

            def sample_bits() -> None:
                if i_f.sample_index(len(mosi), i_f.MASTER_DRIVE_EDGE, i_f.SLAVE_SAMPLE_EDGE) == edge:
                    mosi.append(i_f.get("mosi", 0))
                if i_f.sample_index(len(miso), i_f.SLAVE_DRIVE_EDGE, i_f.MASTER_SAMPLE_EDGE) == edge:
                    miso.append(i_f.get("miso", 0))

            while True:
                await First(i_f.sclk.value_change, i_f.cs.value_change)
                if i_f.get("sclk") != sclk:
                    sclk = i_f.get("sclk")
                    edge += 1
                    sample_bits()

                if i_f.get("cs") is None or i_f.cs_decode(i_f.get("cs")) != cs:
                    break

            # Final bit sampled on chip select de-assertion
            edge += 1
            if i_f.is_leading(i_f.MASTER_DRIVE_EDGE) and i_f.is_leading(i_f.SLAVE_SAMPLE_EDGE):
                if i_f.sample_index(len(mosi), i_f.MASTER_DRIVE_EDGE, i_f.SLAVE_SAMPLE_EDGE) == edge:
                    mosi.append(i_f.get("mosi", 0))
            if i_f.is_leading(i_f.SLAVE_DRIVE_EDGE) and i_f.is_leading(i_f.MASTER_SAMPLE_EDGE):
                if i_f.sample_index(len(miso), i_f.SLAVE_DRIVE_EDGE, i_f.MASTER_SAMPLE_EDGE) == edge:
                    miso.append(i_f.get("miso", 0))

            n = min(len(mosi), i_f.DATA_WIDTH)
            miso.extend([0] * n)
            item.set("length", n)
            item.set("mosi", i_f.from_bits(mosi[:n]))
            item.set("miso", i_f.from_bits(miso[:n]))

            # Send to export
            self.item_export.write(item)

        except asyncio.CancelledError:
            raise
        except Exception:
            self.debug("Monitor task was cancelled by reset")

    async def run_phase(self):
        """
        Run phase for the Monitor.

        Starts a monitor task on each chip select assertion, restarting on reset.
        """

        async def wait_on_reset() -> None:
            try:
                await FallingEdge(self.i_f.rst_n)
            except asyncio.CancelledError:
                raise
            except Exception:
                pass

        while True:
            cs = self.i_f.get("cs")
            if self.i_f.get("rst_n", 0) == 0 or cs is None or self.i_f.cs_decode(cs) == 0:
                await First(self.i_f.cs.value_change, RisingEdge(self.i_f.rst_n))
                continue

            # Monitor or reset - whichever completes first cancels the other
            await select(self.monitor(), wait_on_reset())

__all__ = ["Monitor"]
