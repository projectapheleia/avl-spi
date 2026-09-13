.. _protocol:

Protocol Support
================

AVL-SPI supports the Serial Peripheral Interface as described in `SPI <https://en.wikipedia.org/wiki/Serial_Peripheral_Interface>`_, \
using the traditional master / slave signal names.

.. list-table:: SPI Signal List
   :header-rows: 1
   :widths: 15 20 48 17

   * - Signal Name
     - Alternative Names
     - Description
     - Driven By
   * - SCLK
     - SCK, CLK
     - Serial clock. Idles at CPOL.
     - Master
   * - CS
     - SS, CE
     - Chip select; one per slave. Polarity is configurable per slave.
     - Master
   * - MOSI
     - COPI, PICO, SDO
     - Master out, slave in serial data.
     - Master
   * - MISO
     - CIPO, POCI, SDI
     - Master in, slave out serial data. Driven only by the selected slave.
     - Slave

Transfers
---------

A transfer starts when a chip select is asserted and ends when it is de-asserted. The master generates one SCLK cycle per bit. \
MOSI and MISO are transferred simultaneously (full duplex), MSB first by default.

Multiple slaves are supported via independent chip selects.

.. note::

    At present only single bit, uni-directional SPI is supported. Each SCLK cycle transfers one bit on MOSI (master to slave) \
    and one bit on MISO (slave to master). Bi-directional (3-wire), dual, quad and QPI modes are not supported.

Clock Polarity and Edges
------------------------

CPOL defines the idle level of SCLK and therefore which edge is leading (first after idle) and which is trailing.

Rather than CPHA, the drive and sample edges of the master and slave are configured individually. \
The 4 standard modes are:

.. list-table:: SPI Modes
   :header-rows: 1

   * - Mode
     - CPOL
     - CPHA
     - Drive Edge
     - Sample Edge
   * - 0
     - 0
     - 0
     - Falling
     - Rising
   * - 1
     - 0
     - 1
     - Rising
     - Falling
   * - 2
     - 1
     - 0
     - Rising
     - Falling
   * - 3
     - 1
     - 1
     - Falling
     - Rising

In general, for each direction:

- A leading edge driver drives each bit on a leading edge.
- A trailing edge driver drives the first bit on chip select assertion and subsequent bits on trailing edges (CPHA=0 behavior).
- Each bit is sampled on the first sample edge after it is driven. Where the sample edge matches the drive edge, sampling occurs a full SCLK cycle later.
- Where both drive and sample are leading edges, the final bit is sampled on chip select de-assertion.
