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
    Example SPI mode 0 with multiple memory slaves
        - 3 chip selects with mixed polarity (cs[1] active high, cs[0] and cs[2] active low)
        - 100 random memory writes and reads of 1-4 bytes
            - 24-bit address
            - slave 0 range (0x000000, 0x000100)
            - slave 1 range (0x100000, 0x100100)
            - slave 2 range (0x200000, 0x200100)
        - memory based miso

    :param dut: The DUT instance
    :return: None
    """
    avl.Factory.set_variable("*.clk", dut.clk)
    avl.Factory.set_variable("*.rst_n", dut.rst_n)
    avl.Factory.set_variable("*.hdl", dut.spi_if)
    avl.Factory.set_variable("*.agent.cfg.has_master", True)
    avl.Factory.set_variable("*.agent.cfg.num_slave", 3)
    avl.Factory.set_variable("*.agent.cfg.has_monitor", True)
    avl.Factory.set_variable("*.agent.cfg.has_coverage", True)
    avl.Factory.set_variable("*.agent.cfg.has_bandwidth", True)
    avl.Factory.set_variable("*.agent.cfg.has_trace", True)
    avl.Factory.set_variable("*.agent.msqr.mseq.n_items", 100)
    avl.Factory.set_variable("*.agent.msqr.mseq.max_bytes", 4)
    avl.Factory.set_variable("*.agent.mdrv.rate_limit", lambda : 0.5)

    # Set the address width for the master sequence and all slave drivers
    avl.Factory.set_variable("*.agent.*.addr_width", 24)

    # Set the ranges for the slave drivers
    avl.Factory.set_variable("*.agent.sdrv_0.ranges", [(0x000000, 0x000100)])
    avl.Factory.set_variable("*.agent.sdrv_1.ranges", [(0x100000, 0x100100)])
    avl.Factory.set_variable("*.agent.sdrv_2.ranges", [(0x200000, 0x200100)])

    # Set the ranges for the master sequence
    ranges = {
        (0, 0x000000, 0x000100): 0.5,
        (1, 0x100000, 0x100100): 0.3,
        (2, 0x200000, 0x200100): 0.2,
    }
    avl.Factory.set_variable("*.agent.msqr.mseq.ranges", ranges)

    avl.Factory.set_override_by_type(avl_spi.MstSequence, avl_spi.MstMemorySequence)
    avl.Factory.set_override_by_type(avl_spi.SlvDriver, avl_spi.SlvMemoryDriver)
    e = example_env("env", None)
    await e.start()

