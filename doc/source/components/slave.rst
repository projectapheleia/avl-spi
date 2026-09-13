.. _slave:

AVL-SPI Slave
=============

.. inheritance-diagram:: avl_spi._sdriver
    :parts: 2

The slave side of the AVL-SPI agent follows the standard AVL / UVM structure of sequence, sequencer and driver, \
with one sequence, sequencer and driver per chip select.

As the slave is responsive, the driver does not wait for the sequence. Responses are queued by the sequence in advance, \
and the driver provides a default response when none is queued.

Slave Driver
------------

The slave driver implements the legal protocol for the bus via 3 user defined tasks:

- :any:`SlvDriver.reset` Action to be taken on bus reset. By default miso is set to 0.
- :any:`Driver.quiesce` Action to be taken between transfers. By default miso is set to 0.
- :any:`SlvDriver.drive` Action of completing the transfer, from chip select assertion to de-assertion.

A single function is called on chip select assertion to get the item to be completed - the next response queued by \
the slave sequence, or a new item if none is queued:

- :any:`SlvDriver.get_next_item`

As SPI is full duplex, the response can also be decided bit by bit, during the transfer, via 2 functions:

- :any:`SlvDriver.miso_bit` Returns the miso bit to drive. By default taken from item.miso.
- :any:`SlvDriver.mosi_bit` Called with each sampled mosi bit. By default does nothing.

.. note::

    By default miso is driven from item.miso as a DATA_WIDTH value, as the slave does not know the transfer length in advance. \
    When MSB first, responses shorter than DATA_WIDTH must be left aligned.

Each :any:`SlvDriver` is configured with an index :any:`SlvDriver.idx` that corresponds to its chip select. \
This index is assigned automatically by the :any:`Agent <avl_spi._agent.Agent>` based on the number of slaves.

3 drivers are provided:

- :any:`SlvDriver` - The default driver that completes the transfer (miso from the queued response, otherwise 0).
- :any:`SlvRandomDriver` - As :any:`SlvDriver`, but randomizes miso when no response is queued.
- :any:`SlvMemoryDriver` - Completes the transfer behaving as a memory device (queued miso is ignored).

Slave Sequence
--------------

.. inheritance-diagram:: avl_spi._ssequence
    :parts: 1

The agent starts each :any:`SlvSequence` alongside the master sequence. By default n_items is 0 and no responses are queued.

- :any:`SlvSequence.respond` Queues a directed response and returns the item once the transfer completes, with length and mosi updated.
- :any:`SlvSequence.next` Queues a random response.

A queued response is used by the next transfer to assert the slave's chip select.

.. code-block:: python

    avl.Factory.set_variable("*.agent.ssqr.sseq.n_items", 100)   # Single slave
    avl.Factory.set_variable("*.agent.ssqr_1.sseq.n_items", 100) # Slave 1 of many

Example
~~~~~~~

.. literalinclude:: ../../../examples/spi/slave-sequence/cocotb/example.py
    :language: python

Memory Slave Driver
-------------------

The memory slave driver decodes each transfer as a command byte, an address and data bytes, \
in the style of common SPI EEPROM and flash devices. Each field follows the interface bit order.

.. list-table:: Memory Transfer
   :header-rows: 1

   * - Field
     - Bits
     - Description
   * - Command
     - 8
     - write_cmd (default 0x02) or read_cmd (default 0x03).
   * - Address
     - addr_width (default 16)
     - Address of the first data byte.
   * - Data
     - 8 per byte
     - Write: mosi bytes written from the address. Read: memory bytes driven on miso from the address.

The address width is set by the addr_width variable, which must match the :any:`MstMemorySequence`.

The memory slave driver must be configured to support one or more address ranges, within addr_width bits. \
The ranges are defined as tuples of (start, end) addresses, where end is exclusive.

.. code-block:: python

    avl.Factory.set_variable("*.agent.sdrv.addr_width", 24)
    avl.Factory.set_variable("*.agent.sdrv.ranges", [(0x000000, 0x001000)])

If the transfer is accessing an address outside the ranges, the driver will:

- Ignore writes.
- Randomize read data.

Unrecognized commands are ignored and miso is 0.

This is easy to override in the :any:`SlvMemoryDriver.mosi_bit` and :any:`SlvMemoryDriver.miso_bit` methods.

Example
~~~~~~~

.. literalinclude:: ../../../examples/spi/directed/cocotb/example.py
    :language: python
