# Copyright 2026 Apheleia
#
# Description:
# Apheleia Verification Library SPI example


import avl
import avl_spi
import cocotb


class example_env(avl.Env):

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.hdl = avl.Factory.get_variable(f"{self.get_full_name()}.hdl", None)
        self.clk = avl.Factory.get_variable(f"{self.get_full_name()}.clk", None)
        self.rst_n = avl.Factory.get_variable(f"{self.get_full_name()}.rst_n", None)
        self.agent = avl_spi.Agent("agent", self)

    async def run_phase(self):
        self.raise_objection()

        cocotb.start_soon(self.timeout(1, units="ms"))
        cocotb.start_soon(self.clock(self.clk, 100))
        await self.async_reset(self.rst_n, duration=100, units="ns", active_high=False)

        self.drop_objection()

@cocotb.test
async def test(dut):
    """
    Example SPI mode 1 (CPOL=0, CPHA=1)
        - Single active low chip select
        - Drive on rising edge, sample on falling edge
        - 100 random length (1-16 bit) MSB first transfers
        - random miso

    :param dut: The DUT instance
    :return: None
    """
    avl.Factory.set_variable("*.clk", dut.clk)
    avl.Factory.set_variable("*.rst_n", dut.rst_n)
    avl.Factory.set_variable("*.hdl", dut.spi_if)
    avl.Factory.set_variable("*.agent.cfg.has_master", True)
    avl.Factory.set_variable("*.agent.cfg.num_slave", 1)
    avl.Factory.set_variable("*.agent.cfg.has_monitor", True)
    avl.Factory.set_variable("*.agent.cfg.has_coverage", True)
    avl.Factory.set_variable("*.agent.cfg.has_bandwidth", True)
    avl.Factory.set_variable("*.agent.cfg.has_trace", True)
    avl.Factory.set_variable("*.agent.msqr.mseq.n_items", 100)

    avl.Factory.set_override_by_type(avl_spi.SlvDriver, avl_spi.SlvRandomDriver)
    e = example_env("env", None)
    await e.start()

