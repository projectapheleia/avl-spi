# Copyright 2026 Apheleia
#
# Description:
# Apheleia Verification Library SPI example


import avl
import avl_spi
import cocotb


class DirectedSequence(avl_spi.MstMemorySequence):
    async def body(self) -> None:
        self.info(f"Starting Master directed sequence {self.get_full_name()}")

        # Single byte write and read back
        await self.write(cs=1, addr=0x0010, data=[0xa5])
        assert await self.read(cs=1, addr=0x0010, n=1) == [0xa5]

        # Burst write and partial read back
        await self.write(cs=1, addr=0x0100, data=[0xde, 0xad, 0xbe, 0xef, 0xca])
        assert await self.read(cs=1, addr=0x0101, n=3) == [0xad, 0xbe, 0xef]

        # Out of range write is ignored
        await self.write(cs=1, addr=0x1000, data=[0x12])

        # Unrecognized command returns 0
        item = await self.transfer(cs=1, length=32, mosi=0xff000000)
        assert item.miso == 0


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
    Example SPI mode 0 with a directed memory sequence
        - Single active low chip select
        - 16-bit address, memory slave range (0x0000, 0x1000)
        - Single byte and burst writes checked by read back
        - Out of range write and unrecognized command

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

    # Set the address width for the master sequence and slave driver
    avl.Factory.set_variable("*.agent.msqr.mseq.addr_width", 16)
    avl.Factory.set_variable("*.agent.sdrv.addr_width", 16)

    # Set the range for the slave driver
    avl.Factory.set_variable("*.agent.sdrv.ranges", [(0x0000, 0x1000)])

    avl.Factory.set_override_by_type(avl_spi.SlvDriver, avl_spi.SlvMemoryDriver)
    avl.Factory.set_override_by_type(avl_spi.MstSequence, DirectedSequence)
    e = example_env("env", None)
    await e.start()

