# Copyright 2026 Apheleia
#
# Description:
# Apheleia Verification Library SPI example


import avl
import avl_spi
import cocotb


class MasterSequence(avl_spi.MstSequence):
    async def body(self) -> None:
        self.info(f"Starting Master directed sequence {self.get_full_name()}")

        for i in range(10):
            item = await self.transfer(cs=1, length=16, mosi=0x1000 + i)
            assert item.miso == 0xa500 + i


class SlaveSequence(avl_spi.SlvSequence):
    async def body(self) -> None:
        self.info(f"Starting Slave directed sequence {self.get_full_name()}")

        for i in range(10):
            item = await self.respond(miso=0xa500 + i)
            assert item.mosi == 0x1000 + i
            assert item.length == 16


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
    Example SPI mode 0 with directed master and slave sequences
        - Single active low chip select
        - 10 16-bit transfers
        - miso responses queued by the slave sequence, checked by the master
        - mosi checked by the slave sequence

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

    avl.Factory.set_override_by_type(avl_spi.MstSequence, MasterSequence)
    avl.Factory.set_override_by_type(avl_spi.SlvSequence, SlaveSequence)
    e = example_env("env", None)
    await e.start()

