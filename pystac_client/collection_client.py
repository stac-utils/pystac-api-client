from typing import TYPE_CHECKING, Any, Callable, Dict, Iterator, List, Optional, cast

import pystac

from pystac_client._utils import Modifiable, call_modifier
from pystac_client.conformance import ConformanceClasses
from pystac_client.exceptions import APIError
from pystac_client.item_search import ItemSearch
from pystac_client.stac_api_io import StacApiIO

if TYPE_CHECKING:
    from pystac.item import Item as Item_Type


class CollectionClient(pystac.Collection):
    modifier: Callable[[Modifiable], None]
    _stac_io: Optional[StacApiIO]

    def __init__(
        self,
        id: str,
        description: str,
        extent: pystac.Extent,
        title: Optional[str] = None,
        stac_extensions: Optional[List[str]] = None,
        href: Optional[str] = None,
        extra_fields: Optional[Dict[str, Any]] = None,
        catalog_type: Optional[pystac.CatalogType] = None,
        license: str = "proprietary",
        keywords: Optional[List[str]] = None,
        providers: Optional[List[pystac.Provider]] = None,
        summaries: Optional[pystac.Summaries] = None,
        *,
        modifier: Optional[Callable[[Modifiable], None]] = None,
        **kwargs: Dict[str, Any],
    ):
        # TODO(pystac==1.6.0): Add `assets` as a regular keyword
        super().__init__(
            id,
            description,
            extent,
            title,
            stac_extensions,
            href,
            extra_fields,
            catalog_type,
            license,
            keywords,
            providers,
            summaries,
            **kwargs,
        )
        # error: Cannot assign to a method  [assignment]
        # https://github.com/python/mypy/issues/2427
        setattr(self, "modifier", modifier)

    @classmethod
    def from_dict(
        cls,
        d: Dict[str, Any],
        href: Optional[str] = None,
        root: Optional[pystac.Catalog] = None,
        migrate: bool = False,
        preserve_dict: bool = True,
        modifier: Optional[Callable[[Modifiable], None]] = None,
    ) -> "CollectionClient":
        result = super().from_dict(d, href, root, migrate, preserve_dict)
        # error: Cannot assign to a method  [assignment]
        # https://github.com/python/mypy/issues/2427
        setattr(result, "modifier", modifier)
        return result

    def __repr__(self) -> str:
        return "<CollectionClient id={}>".format(self.id)

    def get_items(self) -> Iterator["Item_Type"]:
        """Return all items in this Collection.

        If the Collection contains a link of with a `rel` value of `items`,
        that link will be used to iterate through items. Otherwise, the default
        PySTAC behavior is assumed.

        Return:
            Iterator[Item]: Iterator of items whose parent is this catalog.
        """

        link = self.get_single_link("items")
        root = self.get_root()
        if link is not None and root is not None:
            # error: Argument "stac_io" to "ItemSearch" has incompatible type
            # "Optional[StacIO]"; expected "Optional[StacApiIO]"  [arg-type]
            # so we add these asserts
            stac_io = root._stac_io
            assert stac_io
            assert isinstance(stac_io, StacApiIO)

            search = ItemSearch(
                url=link.href,
                method="GET",
                stac_io=stac_io,
                modifier=self.modifier,
            )
            yield from search.items()
        else:
            for item in super().get_items():
                call_modifier(self.modifier, item)
                yield item

    def get_item(self, id: str, recursive: bool = False) -> Optional["Item_Type"]:
        """Returns an item with a given ID.

        If the collection conforms to
        [ogcapi-features](https://github.com/radiantearth/stac-api-spec/blob/738f4837ac6bea041dc226219e6d13b2c577fb19/ogcapi-features/README.md),
        this will use the `/collections/{collectionId}/items/{featureId}`.
        If not, and the collection conforms to [item
        search](https://github.com/radiantearth/stac-api-spec/blob/2d3c0cf644af9976eecbf32aec77b9a137268e12/item-search/README.md),
        this will use `/search?ids={featureId}&collections={collectionId}`.
        Otherwise, the default PySTAC behavior is used.

        Args:
            id : The ID of the item to find.
            recursive : If True, search this catalog and all children for the
                item; otherwise, only search the items of this catalog. Defaults
                to False.

        Return:
            Item or None: The item with the given ID, or None if not found.
        """
        if not recursive:
            root = self.get_root()
            assert root
            stac_io = root._stac_io
            assert stac_io
            assert isinstance(stac_io, StacApiIO)
            items_link = self.get_single_link("items")
            if root:
                search_link = root.get_single_link("search")
            else:
                search_link = None
            if (
                stac_io.conforms_to(ConformanceClasses.FEATURES)
                and items_link is not None
            ):
                url = f"{items_link.href}/{id}"
                try:
                    obj = stac_io.read_stac_object(url, root=self)
                    item = cast(Optional[pystac.Item], obj)
                except APIError as err:
                    if err.status_code and err.status_code == 404:
                        return None
                    else:
                        raise err
                assert isinstance(item, pystac.Item)
            elif (
                stac_io.conforms_to(ConformanceClasses.ITEM_SEARCH)
                and search_link
                and search_link.href
            ):
                item_search = ItemSearch(
                    url=search_link.href,
                    method="GET",
                    stac_io=self._stac_io,
                    ids=[id],
                    collections=[self.id],
                    modifier=self.modifier,
                )
                item = next(item_search.items(), None)
            else:
                item = super().get_item(id, recursive=False)
        else:
            item = super().get_item(id, recursive=True)

        if item:
            call_modifier(self.modifier, item)

        return item
