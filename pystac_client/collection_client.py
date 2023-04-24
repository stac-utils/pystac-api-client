from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Union,
    cast,
)
import warnings

import pystac

from pystac_client._utils import Modifiable, call_modifier
from pystac_client.conformance import ConformanceClasses
from pystac_client.exceptions import APIError
from pystac_client.item_search import ItemSearch
from pystac_client.mixins import QueryablesMixin
from pystac_client.stac_api_io import StacApiIO
from pystac_client.warnings import (
    FALLBACK_MSG,
    FallbackToPystac,
    DOES_NOT_CONFORM_TO,
    DoesNotConformTo,
)

if TYPE_CHECKING:
    from pystac.item import Item as Item_Type
    from pystac_client import Client


class CollectionClient(pystac.Collection, QueryablesMixin):
    modifier: Callable[[Modifiable], None]
    _stac_io: StacApiIO

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
        root: Optional[Union[pystac.Catalog, Client]] = None,
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

    def set_root(self, root: Optional[Union[pystac.Catalog, Client]]) -> None:
        # hook in to set_root and use it for setting _stac_io
        super().set_root(root=root)
        if root is None:
            raise ValueError("`CollectionClient.root` must be set")
        elif root._stac_io is not None and isinstance(root._stac_io, StacApiIO):
            self._stac_io = root._stac_io
        else:
            raise ValueError("`CollectionClient.root` must be a valid `Client` object")

    def get_root(self) -> Client:
        from pystac_client.client import Client

        root = super().get_root()
        if root is None or not isinstance(root, Client):
            raise ValueError(
                "`CollectionClient.root` is not have a valid `Client` object."
            )
        return root

    def conforms_to(self, conformance_class: ConformanceClasses) -> bool:
        root = self.get_root()
        return root.conforms_to(conformance_class)

    def get_items(self) -> Iterator["Item_Type"]:
        """Return all items in this Collection.

        If the Collection contains a link of with a `rel` value of `items`,
        that link will be used to iterate through items. Otherwise, the default
        PySTAC behavior is assumed.

        Return:
            Iterator[Item]: Iterator of items whose parent is this catalog.
        """
        root = self.get_root()
        if root.conforms_to(ConformanceClasses.ITEM_SEARCH):
            search = ItemSearch(
                url=self._items_href(),
                method="GET",
                client=root,
                collections=[self.id],
                modifier=self.modifier,
            )
            yield from search.items()
        else:
            if root.has_conforms_to():
                warnings.warn(
                    DOES_NOT_CONFORM_TO(ConformanceClasses.ITEM_SEARCH),
                    DoesNotConformTo,
                )
            warnings.warn(FALLBACK_MSG, category=FallbackToPystac)
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
            if root.conforms_to(ConformanceClasses.FEATURES) and self._stac_io:
                url = f"{self._items_href().rstrip('/')}/{id}"
                try:
                    obj = self._stac_io.read_stac_object(url, root=self)
                    item = cast(Optional[pystac.Item], obj)
                except APIError as err:
                    if err.status_code and err.status_code == 404:
                        return None
                    else:
                        raise err
            elif root.conforms_to(ConformanceClasses.ITEM_SEARCH) and self._stac_io:
                item_search = ItemSearch(
                    url=root._search_href(),
                    method="GET",
                    client=root,
                    ids=[id],
                    collections=[self.id],
                    modifier=self.modifier,
                )
                item = next(item_search.items(), None)
            else:
                if root.has_conforms_to():
                    warnings.warn(
                        DOES_NOT_CONFORM_TO("FEATURES or ITEM_SEARCH"),
                        category=DoesNotConformTo,
                    )
                warnings.warn(FALLBACK_MSG, category=FallbackToPystac)
                item = super().get_item(id, recursive=False)
        else:
            warnings.warn(FALLBACK_MSG, category=FallbackToPystac)
            item = super().get_item(id, recursive=True)

        if item:
            call_modifier(self.modifier, item)

        return item

    def _items_href(self) -> str:
        link = self.get_single_link("items")
        return StacApiIO._get_href(self, "items", link, "items")
