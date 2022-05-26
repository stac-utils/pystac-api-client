from typing import TYPE_CHECKING, Iterable

import pystac

from pystac_client.item_search import ItemSearch

if TYPE_CHECKING:
    from pystac.item import Item as Item_Type


class CollectionClient(pystac.Collection):
    def __repr__(self) -> str:
        return "<CollectionClient id={}>".format(self.id)

    def get_items(self) -> Iterable["Item_Type"]:
        """Return all items in this Collection.

        If the Collection contains a link of with a `rel` value of `items`, that link will be
        used to iterate through items. Otherwise, the default PySTAC behavior is assumed.

        Return:
            Iterable[Item]: Generator of items whose parent is this catalog.
        """

        link = self.get_single_link("items")
        if link is not None and (root := self.get_root()):
            search = ItemSearch(link.href, method="GET", stac_io=root._stac_io)
            yield from search.get_items()
        else:
            yield from super().get_items()
