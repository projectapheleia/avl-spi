# Copyright 2026 Apheleia
#
# Description:
# Apheleia Verification Library Sequence Item

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import avl
from avl._core._lazy import lazy_import

if TYPE_CHECKING:
    from z3 import BoolRef

# Deferred until randomization
z3 = lazy_import("z3")


class SequenceItem(avl.SequenceItem):
    def __init__(self, name: str, parent: avl.Component) -> None:
        """
        Initialize the sequence item

        :param name: Name of the sequence item
        :param parent: Parent component of the sequence item
        """
        super().__init__(name, parent)

        # Handle to interface - defines capabilities and parameters
        i_f = avl.Factory.get_variable(f"{self.get_full_name()}.i_f", None)

        self.cs = avl.Logic(0, width=i_f.CS_WIDTH, fmt=hex)
        """Chip select (1-hot, 1 = selected regardless of polarity)"""

        self.length = avl.Logic(0, width=i_f.DATA_WIDTH.bit_length(), fmt=str)
        """Transfer length (bits)"""

        self.mosi = avl.Logic(0, width=i_f.DATA_WIDTH, fmt=hex)
        """Master out slave in data"""

        self.miso = avl.Logic(0, width=i_f.DATA_WIDTH, fmt=hex)
        """Master in slave out data"""

        # Constraints
        self.add_constraint("c_cs_valid", lambda x : x != 0, self.cs)
        self.add_constraint("c_cs_1hot", lambda x : (x & (x-1)) == 0, self.cs)
        self.add_constraint("c_length", lambda x, y=i_f.DATA_WIDTH : z3.And(z3.UGE(x, 1), z3.ULE(x, y)), self.length)

        # By default transpose to make more readable
        self.set_table_fmt(transpose=True)

    def set(self, name : str, value : int) -> None:
        """
        Set the value of a field in the sequence item - if it exists.

        :param name: Name of the field to set
        :param value: Value to set for the field
        """
        signal = getattr(self, name, None)
        if signal is not None:
            signal.value = value

    def get(self, name : str, default : Any = None) -> int:
        """
        Get the value of a field in the sequence item - if it exists.

        :param name: Name of the field to get
        :param default: Default value to return if the field does not exist
        :return: Value of the field or default value
        """
        signal = getattr(self, name, None)
        if signal is not None:
            return signal.value
        return default

    def randomize_request(self, hard: list[BoolRef] = None, soft: list[BoolRef] = None) -> None:
        """
        Randomize the master fields of the sequence item (cs, length, mosi).

        mosi is masked to length bits.
        """
        self.miso._auto_random_ = False
        self.randomize(hard=hard, soft=soft)
        self.miso._auto_random_ = True

        self.mosi.value = int(self.mosi.value) & ((1 << int(self.length.value)) - 1)

    def randomize_response(self, hard: list[BoolRef] = None, soft: list[BoolRef] = None) -> None:
        """
        Randomize the slave fields of the sequence item (miso).
        """
        for f in ["cs", "length", "mosi"]:
            getattr(self, f)._auto_random_ = False

        self.randomize(hard=hard, soft=soft)

        for f in ["cs", "length", "mosi"]:
            getattr(self, f)._auto_random_ = True

__all__ = ["SequenceItem"]
