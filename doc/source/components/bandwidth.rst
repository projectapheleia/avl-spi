.. _bandwidth:

AVL-SPI Bandwidth Monitor
=========================

.. inheritance-diagram:: avl_spi._bandwidth
    :parts: 2


The :any:`Bandwidth <avl_spi._bandwidth.Bandwidth>` module is a passive component that hangs off the :any:`Monitor <avl_spi._monitor.Monitor>` item_export.

The user defines a rolling time window. During each window the bandwidth monitor tallies the number of bits transferred during that period.

In the :any:`report_phase <avl_spi._bandwidth.Bandwidth.report_phase>` a bar plot of the bandwidth over time is generated.

.. code-block:: python

    avl.Factory.set_variable("*.agent.cfg.has_bandwidth", True)

.. image:: /images/bandwidth.png
