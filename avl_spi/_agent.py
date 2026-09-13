# Copyright 2026 Apheleia
#
# Description:
# Apheleia Verification Library Agent

import avl
import cocotb
from cocotb.handle import HierarchyObject
from cocotb.triggers import NextTimeStep, RisingEdge

from ._agent_cfg import AgentCfg
from ._bandwidth import Bandwidth
from ._coverage import Coverage
from ._interface import Interface
from ._mdriver import MstDriver
from ._monitor import Monitor
from ._msequence import MstSequence
from ._sdriver import SlvDriver
from ._ssequence import SlvSequence


class Agent(avl.Agent):
    def __init__(self, name: str, parent: avl.Component) -> None:
        """
        Initialize the avl-spi Agent

        :param name: Name of the agent instance
        :type name: str
        :param parent: Parent component
        :type parent: Component
        """
        super().__init__(name, parent)

        # Create configuration and export to children
        self.cfg = avl.Factory.get_variable(f"{self.get_full_name()}.cfg", AgentCfg("cfg", self))
        avl.Factory.set_variable(f"{self.get_full_name()}.*.cfg", self.cfg)

        # Bind HDL to establish parameters and configuration
        self._bind_(avl.Factory.get_variable(f"{self.get_full_name()}.hdl", None))

        # Create sequencer and driver if master is enabled
        if self.cfg.has_master:
            self.msqr = avl.Sequencer("msqr", self)
            self.mseq = MstSequence("mseq", self.msqr)
            self.mdrv = MstDriver("mdrv", self)
            self.msqr.seq_item_export.connect(self.mdrv.seq_item_port)

        # Create sequencer, sequence and driver for each slave
        if self.cfg.num_slave > 1:
            self.ssqr, self.sseq, self.sdrv = [], [], []
            for i in range(self.cfg.num_slave):
                avl.Factory.set_variable(f"{self.get_full_name()}.sdrv_{i}.idx", i)
                self.ssqr.append(avl.Sequencer(f"ssqr_{i}", self))
                self.sseq.append(SlvSequence("sseq", self.ssqr[i]))
                self.sdrv.append(SlvDriver(f"sdrv_{i}", self))
                self.ssqr[i].seq_item_export.connect(self.sdrv[i].seq_item_port)
        elif self.cfg.num_slave == 1:
            self.ssqr = avl.Sequencer("ssqr", self)
            self.sseq = SlvSequence("sseq", self.ssqr)
            self.sdrv = SlvDriver("sdrv", self)
            self.ssqr.seq_item_export.connect(self.sdrv.seq_item_port)

        # Create monitor if enabled
        if self.cfg.has_monitor:
            self.monitor = Monitor("monitor", self)

            if self.cfg.has_coverage:
                self.coverage = Coverage("coverage", self)
                self.monitor.item_export.connect(self.coverage.item_port)

            if self.cfg.has_bandwidth:
                self.bandwidth = Bandwidth("bandwidth", self)
                self.monitor.item_export.connect(self.bandwidth.item_port)

            if self.cfg.has_trace:
                self.trace = avl.Trace("trace", self)
                self.monitor.item_export.connect(self.trace.item_port)

    def _bind_(self, hdl) -> None:
        """
        Bind the agent to a hardware description language (HDL) interface.
        This method is used to associate the agent with a specific HDL interface,
        allowing it to interact with the hardware model.

        :param hdl: The HDL interface to bind to the agent
        :type hdl: HierarchyObject
        :raises TypeError: If `hdl` is not an instance of HierarchyObject
        """
        if not isinstance(hdl, HierarchyObject):
            raise TypeError(f"Expected HierarchyObject, got {type(hdl)}")

        # Assign Interface
        self.i_f = Interface(hdl)
        avl.Factory.set_variable(f"{self.get_full_name()}.*.i_f", self.i_f)

    async def run_phase(self) -> None:
        """
        Run the agent's phase. This method is called to start the agent's operation.
        It starts the slave sequences, and the master sequence if the master is enabled.
        Slave sequences are not awaited, as they depend on transfers from the master.
        """

        self.raise_objection()
        await NextTimeStep()

        if self.cfg.num_slave > 0:
            for s in (self.sseq if isinstance(self.sseq, list) else [self.sseq]):
                cocotb.start_soon(s.start())

        if self.cfg.has_master:
            await self.mseq.start()

        # Run-off
        for _ in range(10):
            await RisingEdge(self.i_f.clk)

        self.drop_objection()

__all__ = ["Agent"]
