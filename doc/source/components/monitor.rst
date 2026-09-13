.. _monitor:

AVL-SPI Monitor
===============

.. inheritance-diagram:: avl_spi._monitor
    :parts: 2


The :any:`Monitor <avl_spi._monitor.Monitor>` module is a passive component that observes the bus transactions and provides a way to collect and analyze the data.

Its behavior is as you would expect for any AVL or UVM monitor. It observes the bus signals and generates transactions based on the observed activity, \
passing it to the item_export for further processing.

.. code-block:: python

    avl.Factory.set_variable("*.agent.cfg.has_monitor", True)

Each transfer, from chip select assertion to de-assertion, generates a single :any:`SequenceItem`:

- mosi is sampled on the slave sample edge.
- miso is sampled on the master sample edge.
- length is the number of mosi bits sampled.

A warning is issued if SCLK is not idle (CPOL) on chip select assertion.
