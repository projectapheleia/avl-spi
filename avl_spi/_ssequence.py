# Copyright 2026 Apheleia
#
# Description:
# Apheleia Verification Library Slave Sequence

import avl

from ._item import SequenceItem


class SlvSequence(avl.Sequence):

    def __init__(self, name: str, parent: avl.Component) -> None:
        """
        Initialize the sequence

        Sequence of slave responses. Each response is queued and used by the slave driver
        for the next transfer. Transfers with no queued response use the driver default.

        :param name: Name of the sequence
        :param parent: Parent component of the sequence
        """
        super().__init__(name, parent)

        self.i_f = avl.Factory.get_variable(f"{self.get_full_name()}.i_f", None)
        """Handle to interface - defines capabilities and parameters"""

        self.n_items = avl.Factory.get_variable(f"{self.get_full_name()}.n_items", 0)
        """Number of items in the sequence (default 0)"""

    async def _send_(self, item : SequenceItem, randomize : bool = True) -> SequenceItem:
        """
        Queue an item for the driver

        :param item: Item to send
        :param randomize: Randomize the response before sending (default True)
        :return: The item once the transfer completes (length and mosi updated by the driver)
        """

        await self.start_item(item)

        if randomize:
            item.randomize_response()

        await self.finish_item(item)

        return item

    async def next(self) -> SequenceItem:
        """
        Queue the next random response in the sequence
        """

        item = SequenceItem(f"from_{self.name}", self)
        return await self._send_(item, randomize=True)

    async def respond(self, **kwargs) -> SequenceItem:
        """
        Queue a directed response for the next transfer

        miso is driven as a DATA_WIDTH value, i.e. left aligned when MSB first.

        :param kwargs: Keyword arguments to set on the item
        :return: The item once the transfer completes (length and mosi updated by the driver)
        """
        item = SequenceItem(f"from_{self.name}", self)

        for k,v in kwargs.items():
            if hasattr(item, k):
                item.set(k, v)

        return await self._send_(item, randomize=False)

    async def body(self) -> None:
        """
        Body of the sequence
        """

        self.info(f"Starting slave sequence {self.get_full_name()} with {self.n_items} items")
        for _ in range(self.n_items):
            await self.next()

__all__ = ["SlvSequence"]
