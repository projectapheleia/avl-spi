# Copyright 2026 Apheleia
#
# Description:
# Apheleia Verification Library Interface

from typing import Any

from cocotb.handle import HierarchyObject

parameters = [
    "CLASSIFICATION",
    "CS_WIDTH",
    "CS_POLARITY",
    "CS_SETUP",
    "CS_HOLD",
    "CS_GAP",
    "CPOL",
    "MASTER_DRIVE_EDGE",
    "MASTER_SAMPLE_EDGE",
    "SLAVE_DRIVE_EDGE",
    "SLAVE_SAMPLE_EDGE",
    "LSB_FIRST",
    "DATA_WIDTH",
]

signals = [
  "clk",
  "cs",
  "miso",
  "mosi",
  "rst_n",
  "sclk",
]

class Interface:
    def __init__(self, hdl : HierarchyObject) -> None:
        """
        Create an interface
        Work around simulator specific issues with accessing interface signals and parameters.
        """
        # Parameters
        for p in parameters:
            # Parameters not exposed by list() in some simulators - look up explicitly
            v = getattr(hdl, p)
            if isinstance(v.value, bytes):
                setattr(self, p, str(v.value.decode("utf-8")))
            else:
                setattr(self, p, int(v.value))

        # Signals
        for s in signals:
            # Some simulators do not expose signals inside interfaces through list(hdl).
            # Populate the _sub_handle cache explicitly.
            child = getattr(hdl, s)
            setattr(self, child._name, child)

        if self.CLASSIFICATION != "SPI":
            raise TypeError(f"Expected SPI classification, got {self.CLASSIFICATION}")

        if self.CS_WIDTH < 1:
            raise ValueError(f"Invalid CS_WIDTH: {self.CS_WIDTH}")

        if self.DATA_WIDTH < 1:
            raise ValueError(f"Invalid DATA_WIDTH: {self.DATA_WIDTH}")

        for p in ["CS_SETUP", "CS_HOLD", "CS_GAP"]:
            if getattr(self, p) < 0:
                raise ValueError(f"Invalid {p}: {getattr(self, p)}")

        for p in ["CPOL", "MASTER_DRIVE_EDGE", "MASTER_SAMPLE_EDGE", "SLAVE_DRIVE_EDGE", "SLAVE_SAMPLE_EDGE", "LSB_FIRST"]:
            if getattr(self, p) not in [0, 1]:
                raise ValueError(f"Invalid {p}: {getattr(self, p)}")

    def set(self, name : str, value : int) -> None:
        """
        Set the value of a signal (if signal exists)

        :param name: The name of the signal
        :type name: str
        :param value: The value to set
        :type value: int
        :return: None
        """
        signal = getattr(self, name, None)
        if signal is not None:
            signal.value = value

    def get(self, name : str, default : Any = None) -> int:
        """
        Get the value of a signal (if signal exists and is resolvable)

        :param name: The name of the signal
        :type name: str
        :param default: The default value to return if signal does not exist or is not resolvable
        :type default: Any
        :return: The value of the signal or the default value
        :rtype: int
        """
        signal = getattr(self, name, None)
        if signal is not None and signal.value.is_resolvable:
            return int(signal.value)
        return default

    def cs_encode(self, cs : int) -> int:
        """
        Convert a logical chip select (1-hot, 1 = selected) to the HDL value by applying CS_POLARITY

        :param cs: Logical chip select
        :type cs: int
        :return: HDL chip select
        :rtype: int
        """
        return ~(cs ^ self.CS_POLARITY) & ((1 << self.CS_WIDTH) - 1)

    def cs_decode(self, value : int) -> int:
        """
        Convert a HDL chip select value to a logical chip select (1 = selected) by applying CS_POLARITY

        :param value: HDL chip select
        :type value: int
        :return: Logical chip select
        :rtype: int
        """
        return self.cs_encode(value)

    def is_leading(self, edge : int) -> bool:
        """
        Check if an edge (0 = falling, 1 = rising) is the leading edge of an SCLK cycle, as defined by CPOL

        :param edge: Edge
        :type edge: int
        :return: True if leading edge
        :rtype: bool
        """
        return edge != self.CPOL

    def drive_index(self, k : int, drive : int) -> int:
        """
        Get the SCLK edge on which bit k is driven

        Edges are counted from chip select assertion (0).
        Leading edge drivers drive bit k on edge 2k+1.
        Trailing edge drivers drive bit 0 on chip select assertion and bit k on edge 2k.

        :param k: Bit index (in transmission order)
        :type k: int
        :param drive: Drive edge
        :type drive: int
        :return: Edge index
        :rtype: int
        """
        return 2 * k + 1 if self.is_leading(drive) else 2 * k

    def sample_index(self, k : int, drive : int, sample : int) -> int:
        """
        Get the SCLK edge on which bit k is sampled - the first sample edge after it is driven

        When drive and sample are both leading edges the final bit falls beyond the last SCLK edge
        and is sampled on chip select de-assertion.

        :param k: Bit index (in transmission order)
        :type k: int
        :param drive: Drive edge
        :type drive: int
        :param sample: Sample edge
        :type sample: int
        :return: Edge index
        :rtype: int
        """
        idx = self.drive_index(k, drive) + 1
        if (idx % 2 == 1) != self.is_leading(sample):
            idx += 1
        return idx

    def to_bits(self, value : int, length : int) -> list[int]:
        """
        Split a value into bits in transmission order (LSB_FIRST)

        :param value: Value
        :type value: int
        :param length: Number of bits
        :type length: int
        :return: Bits
        :rtype: list[int]
        """
        bits = [(value >> i) & 1 for i in range(length)]
        return bits if self.LSB_FIRST else bits[::-1]

    def from_bits(self, bits : list[int]) -> int:
        """
        Combine bits in transmission order (LSB_FIRST) into a value

        :param bits: Bits
        :type bits: list[int]
        :return: Value
        :rtype: int
        """
        order = bits if self.LSB_FIRST else bits[::-1]
        return sum(b << i for i, b in enumerate(order))

__all__ = ["Interface"]
