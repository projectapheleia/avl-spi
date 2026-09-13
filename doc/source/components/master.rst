.. _master:

AVL-SPI Master
==============


The master side of the AVL-SPI agent follows the standard AVL / UVM structure of sequence, sequencer and driver.

Master Sequence
---------------

.. inheritance-diagram:: avl_spi._msequence
    :parts: 1

:any:`MstSequence` generates a stream of randomized :any:`SequenceItem` items.

The length of the sequence is defined by the n_items variable, which defaults to 1, but is expected to be overridden by the factory.

The transfer length (bits) is randomized between 1 and DATA_WIDTH, unless a length function is provided.

.. code-block:: python

    avl.Factory.set_variable("*.agent.msqr.mseq.n_items", 100)
    avl.Factory.set_variable("*.agent.msqr.mseq.length", lambda: 8)

:any:`MstSequence.transfer` sends a directed transfer and returns the item with the miso data sampled by the driver.

.. code-block:: python

    item = await self.transfer(cs=0x1, length=16, mosi=0x1234)

Master Memory Sequence
~~~~~~~~~~~~~~~~~~~~~~

:any:`MstMemorySequence` generates random writes and reads compatible with the :any:`SlvMemoryDriver`, \
and provides :any:`MstMemorySequence.write` and :any:`MstMemorySequence.read` for directed tests.

The addr_width, write_cmd and read_cmd variables must match the slave. Addresses and ranges must fit within addr_width bits. \
A dictionary of ranges, of the form (cs index, start, end) : weight, can be provided to target valid addresses.

.. code-block:: python

    avl.Factory.set_override_by_type(avl_spi.MstSequence, avl_spi.MstMemorySequence)
    avl.Factory.set_variable("*.agent.msqr.mseq.max_bytes", 4)
    avl.Factory.set_variable("*.agent.msqr.mseq.ranges", {(0, 0x0000, 0x0100): 0.5, (1, 0x1000, 0x1100): 0.5})

The user is expected to extend the sequences for custom behavior.

Master Driver
-------------

.. inheritance-diagram:: avl_spi._mdriver
    :parts: 2

The master driver implements the legal protocol for the bus via 3 user defined tasks:

- :any:`MstDriver.reset` Action to be taken on bus reset. By default chip selects are de-asserted, sclk is idle and mosi is 0.
- :any:`MstDriver.quiesce` Action to be taken between transfers. By default mosi is set to 0.
- :any:`MstDriver.drive` Action of driving the transfer on the bus.

All timing is derived from the interface clk:

- Chip select is asserted on a rising edge of clk.
- The first SCLK edge is cs_setup clk cycles after chip select assertion. SCLK then toggles every half_period clk cycles.
- MISO is sampled on its SCLK edge. MOSI is driven on the falling edge of clk following its SCLK edge.
- Chip select is de-asserted cs_hold clk cycles after the final SCLK edge, and remains de-asserted for at least cs_gap clk cycles.

Chip Select Timing
~~~~~~~~~~~~~~~~~~

By default cs_setup, cs_hold and cs_gap are the larger of half_period and the interface CS_SETUP, CS_HOLD and CS_GAP, \
so the master always passes the interface checks (see :ref:`configuration`).

They can be overridden, for example to test a slave's tolerance. Values below the interface minimums trigger the interface checks.

.. code-block:: python

    avl.Factory.set_variable("*.agent.mdrv.cs_setup", 8)
    avl.Factory.set_variable("*.agent.mdrv.cs_hold", 8)
    avl.Factory.set_variable("*.agent.mdrv.cs_gap", 16)

The cs-timing example shows the defaults meeting the interface minimums. \
The cs-setup-violation, cs-hold-violation and cs-gap-violation examples override each value below its minimum, \
and expect the simulation to end with the interface $fatal:

.. literalinclude:: ../../../examples/spi/cs-gap-violation/cocotb/example.py
    :language: python

Rate Control
~~~~~~~~~~~~

By setting the rate_limit variable in the :any:`MstDriver` class, \
using a lambda function that returns a value between 0.0 and 1.0 the user can control the gap between transfers, \
in addition to the minimum cs_gap.

The SCLK frequency is controlled by the half_period variable (clk cycles).

.. code-block:: python

    avl.Factory.set_variable("*.agent.mdrv.rate_limit", lambda: 0.1)
    avl.Factory.set_variable("*.agent.mdrv.half_period", 4)
