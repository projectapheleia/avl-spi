# AVL-SPI - Apheleia Verification Library SPI Verification Component

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)


AVL-SPI has been developed by experienced, industry professional verification engineers to provide a simple, \
extensible verification component for the [Serial Peripheral Interface](https://en.wikipedia.org/wiki/Serial_Peripheral_Interface) \
developed in [Python](https://www.python.org/) and the [AVL](https://avl-core.readthedocs.io/en/latest/index.html) library.

AVL is built on the [CocoTB](https://docs.cocotb.org/en/stable/) framework, but aims to combine the best elements of \
[UVM](https://accellera.org/community/uvm) in a more engineer friendly and efficient way.

## CocoTB 2.0

AVL-SPI supports [CocoTB 2.0](https://docs.cocotb.org/en/development/upgrade-2.0.html) and requires CocoTB 2.1 or later.

## Protocol Features

| Signal Name | Description | Driven By |
|-------------|-------------|-----------|
| SCLK        | Serial clock. Idles at CPOL. | Master |
| CS          | Chip select; one per slave. Polarity configurable per slave. | Master |
| MOSI        | Master out, slave in serial data. | Master |
| MISO        | Master in, slave out serial data. | Slave |

> **Note:** At present only single bit, uni-directional SPI is supported. Each SCLK cycle transfers one bit on MOSI (master to slave) and one bit on MISO (slave to master). Bi-directional (3-wire), dual, quad and QPI modes are not supported.

## Component Features

- Simple RTL interface to interact with HDL and define parameter and configuration options
- Multiple chip selects with individual polarity
- Clock polarity and individual drive and sample edges for master and slave (all 4 SPI modes and beyond)
- Variable transfer length, MSB or LSB first
- Chip select onehot0, setup, hold and inter-frame gap checks in the RTL interface
- Master sequence, sequencer and driver with rate limiter, SCLK frequency and chip select timing control
- Slave sequence, sequencer and driver with vanilla, random and memory response patterns
- Monitor
- Bandwidth monitor generating bus activity plots over user defined windows during simulation
- Functional coverage
- Searchable trace file generation

---

## 📦 Installation

### Using `pip`
```sh
# Standard build
pip install avl-spi

# Development build
pip install avl-spi[dev]
```

### Install from Source
```sh
git clone https://github.com/projectapheleia/avl-spi.git
cd avl-spi

# Standard build
pip install .

# Development build
pip install .[dev]
```

Alternatively if you want to create a [virtual environment](https://docs.python.org/3/library/venv.html) rather than install globally a script is provided. This will install, with edit privileges to local virtual environment.

This script assumes you have [Graphviz](https://graphviz.org/download/) and appropriate simulator installed, so all examples and documentation will build out of the box.


```sh
git clone https://github.com/projectapheleia/avl-spi.git
cd avl-spi
source avl-spi.sh
```

## 📖 Documentation

In order to build the documentation you must have installed the development build.

### Build from Source
```sh
cd doc
make html
<browser> build/html/index.html
```
## 🏃 Examples

In order to run all the examples you must have installed the development build.

To run all examples:

```sh
cd examples

# To run
make -j 8 sim

# To clean
make -j 8 clean
```

To run an individual example:

```sh
cd examples/THE EXAMPLE YOU WANT

# To run
make sim

# To clean
make clean
```

The examples use the [CocoTB Makefile](https://docs.cocotb.org/en/stable/building.html) and default to [Verilator](https://www.veripool.org/verilator/) with all waveforms generated. This can be modified using the standard CocoTB build system.

---


## 🧹 Code Style & Linting

This project uses [**Ruff**](https://docs.astral.sh/ruff/) for linting and formatting.

Check code for issues:

```sh
ruff check .
```

Automatically fix common issues:

```sh
ruff check . --fix
```



## 📧 Contact

- Email: avl@projectapheleia.net
- GitHub: [projectapheleia](https://github.com/projectapheleia)
