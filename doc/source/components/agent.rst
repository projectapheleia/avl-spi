.. _agent:

AVL-SPI Agent
=============

.. inheritance-diagram:: avl_spi._agent_cfg
    :parts: 1

.. inheritance-diagram:: avl_spi._agent
    :parts: 1

Unlike many VIPs AVL-SPI does not contain an environment.

The AVL-SPI verification component is designed to be integrated easily into existing AVL environments, and \
as such an agent can be individually configured without a wider global environment.

The agent is composed of a master and slave side, which can be used independently or together, and \
a number of non-directional passive components. To configure the agent, the user must override the :doc:`avl_spi.AgentCfg </modules/avl_spi._agent_cfg>` class. \
The best way to do this is via the factory:

.. code-block:: python

    avl.Factory.set_variable("*.agent.cfg.has_master", True)
    avl.Factory.set_variable("*.agent.cfg.num_slave", 1)
    avl.Factory.set_variable("*.agent.cfg.has_monitor", True)

.. note::

    The :doc:`avl_spi.AgentCfg </modules/avl_spi._agent_cfg>` does not configure the SPI bus itself, only the agent. \
    The bus configuration is done via RTL interface (see :ref:`configuration` for more details.)

Sub-Components
--------------

.. toctree::
   :maxdepth: 1

   master
   slave
   monitor
   bandwidth
   coverage
   trace

