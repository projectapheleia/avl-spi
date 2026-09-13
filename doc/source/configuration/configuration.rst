.. _configuration:

AVL-SPI Configuration
=====================

AVL-SPI is configured via the provided RTL interface.

The default interface does not contain any modports or clocking blocks to remain compatible with \
the majority of simulators.

If the user wishes to add directionality or timing to the interface, they can do so by \
modifying the avl_spi.sv file.

Connecting the interface to the SPI bus should be done with standard assign statements.

In addition to the SPI signals the interface contains clk and rst_n. These are not part of the protocol, \
they provide the timebase for the master driver (SCLK generation) and reset for all components.

On each rising edge of clk, out of reset, the interface checks:

- Chip select is onehot0 (at most one slave selected, after applying CS_POLARITY).
- Chip select setup: at least CS_SETUP clk cycles from chip select assertion to the first SCLK edge.
- Chip select hold: at least CS_HOLD clk cycles from the last SCLK edge to chip select de-assertion.
- Inter-frame gap: at least CS_GAP clk cycles from chip select de-assertion to the next assertion. \
  Changing directly from one chip select to another is a gap of 0.

As the checks are clocked, events are measured to the nearest clk cycle. \
The checks are deliberately implemented as always blocks with $fatal, \
rather than concurrent assertions, in order to be supported on the widest range of simulators.

.. literalinclude:: ../../../avl_spi/rtl/avl_spi.sv
    :language: verilog

.. list-table:: Interface Parameters
   :header-rows: 1
   :widths: 25 15 60

   * - Parameter
     - Default
     - Description
   * - CS_WIDTH
     - 1
     - Number of chip selects (slaves).
   * - CS_POLARITY
     - '0
     - Chip select polarity, per bit. 0 = active low, 1 = active high.
   * - CS_SETUP
     - 1
     - Minimum clk cycles from chip select assertion to the first SCLK edge. 0 = unchecked.
   * - CS_HOLD
     - 1
     - Minimum clk cycles from the last SCLK edge to chip select de-assertion. 0 = unchecked.
   * - CS_GAP
     - 1
     - Minimum clk cycles between chip select de-assertion and the next assertion. 0 = unchecked.
   * - CPOL
     - 0
     - Clock polarity (SCLK idle level).
   * - MASTER_DRIVE_EDGE
     - 0
     - SCLK edge on which the master drives MOSI. 0 = falling, 1 = rising.
   * - MASTER_SAMPLE_EDGE
     - 1
     - SCLK edge on which the master samples MISO. 0 = falling, 1 = rising.
   * - SLAVE_DRIVE_EDGE
     - 0
     - SCLK edge on which the slave drives MISO. 0 = falling, 1 = rising.
   * - SLAVE_SAMPLE_EDGE
     - 1
     - SCLK edge on which the slave samples MOSI. 0 = falling, 1 = rising.
   * - LSB_FIRST
     - 0
     - Bit order. 0 = MSB first, 1 = LSB first.
   * - DATA_WIDTH
     - 8
     - Maximum transfer length (bits).

See :ref:`protocol` for how the edges are applied.

Integrating with a Build Environment
------------------------------------

AVL-SPI comes with a tools utility :func:`avl_spi._tools.get_verilog` to help integrate the library into your build environment.

This is exposed to the environment as the command line tool `avl-spi-get-verilog` which returns a list of all RTL files required \
for AVL-SPI.

An example of integrating with the verilator build environment is shown below:

.. code-block:: makefile

    # HDL source files
    VERILOG_SOURCES      += $(shell avl-spi-get-verilog)

    # include cocotb's make rules to take care of the simulator setup
    include $(shell cocotb-config --makefiles)/Makefile.sim


Connecting to the AVL Environment
---------------------------------

The recommended way to connect to the AVL environment is via the factory.

.. code-block:: python

    avl.Factory.set_variable("*.hdl", dut.spi_if)

When the agent is created it will automatically use this factory setting to connect to the SPI interface.

Parameterization
----------------

The AVL environment automatically picks up the parameters from the RTL interface. \
This ensures the AVL environment and HDL environment are always in sync.

Once connected the agent creates an internal :doc:`avl_spi.Interface </modules/avl_spi._interface>` object which is used to \
act as the physical interface to the SPI bus and share the parameters with the rest of the environment.

This internal interface is generated to serve 2 purposes:

    1. It abstracts the simulator specific behaviour of accessing interface signals and parameters.
    2. It provides helper methods for chip select polarity (:any:`Interface.cs_encode`, :any:`Interface.cs_decode`), \
       bit order (:any:`Interface.to_bits`, :any:`Interface.from_bits`) and edge timing (:any:`Interface.drive_index`, :any:`Interface.sample_index`).
