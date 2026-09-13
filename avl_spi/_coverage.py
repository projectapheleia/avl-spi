# Copyright 2026 Apheleia
#
# Description:
# Apheleia Verification Library Coverage

import avl

from ._item import SequenceItem


class Coverage(avl.Component):

    def __init__(self, name: str, parent: avl.Component) -> None:
        """
        Initialize Coverage

        :param name: Name of the coverage class.
        :type name: str
        :param parent: Parent component.
        :type parent: Component
        """
        super().__init__(name, parent)

        self.item_port = avl.List()
        self.item = SequenceItem("for_coverage", self)

        # Define coverage
        self.cg = avl.Covergroup("spi", self)
        self.cg.set_comment("SPI Coverage")

        # CS
        self.cp_cs = self.cg.add_coverpoint("cs", lambda: self.item.cs)
        self.cp_cs.set_comment("CS (1-hot select)")
        for i in range(self.item.cs.width):
            self.cp_cs.add_bin(f"{i}", lambda x, y=i : 0 != (x & (1<<y)))

        # LENGTH
        self.cp_length = self.cg.add_coverpoint("length", lambda: self.item.length)
        self.cp_length.set_comment("Transfer length (bits)")
        for i in range(1, self.item.mosi.width+1):
            self.cp_length.add_bin(f"{i}", i)
        self.cp_length.add_bin("length", range(0, self.item.mosi.width+1), stats=True)

        self.cc_csXlength = self.cg.add_covercross("csXlength", self.cp_cs, self.cp_length)
        self.cc_csXlength.set_comment("Cross CS and length")

        # MOSI
        self.cp_mosi = self.cg.add_coverpoint("mosi", lambda: self.item.mosi)
        self.cp_mosi.set_comment("MOSI (master out slave in data)")
        for i in range(self.item.mosi.width):
            self.cp_mosi.add_bin(f"[{i}] == 0", lambda x, y=i : 0 == (x & (1<<y)))
            self.cp_mosi.add_bin(f"[{i}] == 1", lambda x, y=i : 0 != (x & (1<<y)))

        # MISO
        self.cp_miso = self.cg.add_coverpoint("miso", lambda: self.item.miso)
        self.cp_miso.set_comment("MISO (master in slave out data)")
        for i in range(self.item.miso.width):
            self.cp_miso.add_bin(f"[{i}] == 0", lambda x, y=i : 0 == (x & (1<<y)))
            self.cp_miso.add_bin(f"[{i}] == 1", lambda x, y=i : 0 != (x & (1<<y)))

    async def run_phase(self) -> None:
        """
        Run phase for the coverage component.

        """

        while True:
            # Wait for an item to be available
            self.item = await self.item_port.blocking_get()

            # Sample
            self.cg.sample()

__all__ = ["Coverage"]
