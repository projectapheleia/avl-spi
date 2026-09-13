# Copyright 2026 Apheleia
#
# Description:
# Apheleia Verification Library Tools

from importlib.resources import files


def get_verilog():
    """
    Get the path to the Verilog source files for the SPI agent.

    :return: Path to the Verilog source files
    :rtype: pathlib.Path
    """
    path = files("avl_spi.rtl").joinpath("avl_spi.sv")
    print(path)
