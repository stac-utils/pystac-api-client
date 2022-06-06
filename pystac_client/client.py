from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict, Iterable, Optional

import pystac
import pystac.validation

from pystac_client.collection_client import CollectionClient
from pystac_client.conformance import ConformanceClasses
from pystac_client.errors import ClientTypeError
from pystac_client.exceptions import APIError
from pystac_client.item_search import ItemSearch
from pystac_client.stac_api_io import StacApiIO

if TYPE_CHECKING:
    from pystac.item import Item as Item_Type


class Client(pystac.Catalog):
    """A Client for interacting with the root of a STAC Catalog or API

    Instances of the ``Client`` class inherit from :class:`pystac.Catalog`
    and provide a convenient way of interacting
    with STAC Catalogs OR STAC APIs that conform to the `STAC API spec
    <https://github.com/radiantearth/stac-api-spec>`_.
    In addition to being a valid
    `STAC Catalog
    <https://github.com/radiantearth/stac-spec/blob/master/catalog-spec/catalog-spec.md>`_
    APIs that have a ``"conformsTo"`` indicate that it supports additional
    functionality on top of a normal STAC Catalog,
    such as searching items (e.g., /search endpoint).
    """

    def __repr__(self) -> str:
        return "<Client id={}>".format(self.id)

    @classmethod
    def open(
        cls,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        ignore_conformance: bool = False,
    ) -> "Client":
        """Opens a STAC Catalog or API
        This function will read the root catalog of a STAC Catalog or API

        Args:
            url : The URL of a STAC Catalog. If not specified, this will use the
                `STAC_URL` environment variable.
            headers : A dictionary of additional headers to use in all requests
                made to any part of this Catalog/API.
            parameters: Optional dictionary of query string parameters to
                include in all requests.
            ignore_conformance : Ignore any advertised Conformance Classes in this
                Catalog/API. This means that
                functions will skip checking conformance, and may throw an unknown
                error if that feature is
                not supported, rather than a :class:`NotImplementedError`.

        Return:
            catalog : A :class:`Client` instance for this Catalog/API
        """
        cat = cls.from_file(url, headers=headers, parameters=parameters)
        search_link = cat.get_search_link()
        # if there is a search link, but no conformsTo advertised, ignore
        # conformance entirely
        # NOTE: this behavior to be deprecated as implementations become conformant
        if ignore_conformance or (
            "conformsTo" not in cat.extra_fields.keys()
            and search_link
            and search_link.href
            and len(search_link.href) > 0
        ):
            cat._stac_io.set_conformance(None)
        return cat

    @classmethod
    def from_file(
        cls,
        href: str,
        stac_io: Optional[pystac.StacIO] = None,
        headers: Optional[Dict[str, str]] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> "Client":
        """Open a STAC Catalog/API

        Returns:
            Client: A Client (PySTAC Catalog) of the root Catalog for this Catalog/API
        """
        if stac_io is None:
            stac_io = StacApiIO(headers=headers, parameters=parameters)

        cat = super().from_file(href, stac_io)

        cat._stac_io._conformance = cat.extra_fields.get("conformsTo", [])

        return cat

    def _supports_collections(self) -> bool:
        return self._conforms_to(ConformanceClasses.COLLECTIONS) or self._conforms_to(
            ConformanceClasses.FEATURES
        )

    # TODO: fix this with the stac_api_io() method in a future PR
    def _conforms_to(self, conformance_class: ConformanceClasses) -> bool:
        return self._stac_io.conforms_to(conformance_class)  # type: ignore

    @classmethod
    def from_dict(
        cls,
        d: Dict[str, Any],
        href: Optional[str] = None,
        root: Optional[pystac.Catalog] = None,
        migrate: bool = False,
        preserve_dict: bool = True,
    ) -> "Client":
        try:
            return super().from_dict(
                d=d, href=href, root=root, migrate=migrate, preserve_dict=preserve_dict
            )
        except pystac.STACTypeError:
            raise ClientTypeError(
                f"Could not open Client (href={href}), "
                f"expected type=Catalog, found type={d.get('type', None)}"
            )

    @lru_cache()
    def get_collection(self, collection_id: str) -> CollectionClient:
        """Get a single collection from this Catalog/API

        Args:
            collection_id: The Collection ID to get

        Returns:
            CollectionClient: A STAC Collection
        """
        if self._supports_collections():
            url = f"{self.get_self_href()}/collections/{collection_id}"
            collection = CollectionClient.from_dict(
                self._stac_io.read_json(url), root=self
            )
            return collection
        else:
            for col in self.get_collections():
                if col.id == collection_id:
                    return col

    def get_collections(self) -> Iterable[CollectionClient]:
        """Get Collections in this Catalog

            Gets the collections from the /collections endpoint if supported,
            otherwise fall back to Catalog behavior of following child links

        Return:
            Iterable[CollectionClient]: Iterator through Collections in Catalog/API
        """
        if self._supports_collections():
            url = self.get_self_href() + "/collections"
            for page in self._stac_io.get_pages(url):
                if "collections" not in page:
                    raise APIError("Invalid response from /collections")
                for col in page["collections"]:
                    collection = CollectionClient.from_dict(col, root=self)
                    yield collection
        else:
            yield from super().get_collections()

    def get_items(self) -> Iterable["Item_Type"]:
        """Return all items of this catalog.

        Return:
            Iterable[Item]:: Generator of items whose parent is this catalog.
        """
        if self._conforms_to(ConformanceClasses.ITEM_SEARCH):
            search = self.search()
            yield from search.items()
        else:
            return super().get_items()

    def get_all_items(self) -> Iterable["Item_Type"]:
        """Get all items from this catalog and all subcatalogs. Will traverse
        any subcatalogs recursively, or use the /search endpoint if supported

        Returns:
            Iterable[Item]:: All items that belong to this catalog, and all
                catalogs or collections connected to this catalog through
                child links.
        """
        if self._conforms_to(ConformanceClasses.ITEM_SEARCH):
            yield from self.get_items()
        else:
            yield from super().get_items()

    def search(self, **kwargs: Any) -> ItemSearch:
        """Query the ``/search`` endpoint using the given parameters.

        This method returns an :class:`~pystac_client.ItemSearch` instance, see that
        class's documentation for details on how to get the number of matches and
        iterate over results. All keyword arguments are passed directly to the
        :class:`~pystac_client.ItemSearch` instance.

        .. warning::

            This method is only implemented if the API conforms to the
            `STAC API - Item Search
            <https://github.com/radiantearth/stac-api-spec/tree/master/item-search>`__
            spec *and* contains a link with a ``"rel"`` type of ``"search"`` in its
            root catalog. If the API does not meet either of these criteria, this
            method will raise a :exc:`NotImplementedError`.

        Args:
            **kwargs : Any parameter to the :class:`~pystac_client.ItemSearch` class,
             other than `url`, `conformance`, and `stac_io` which are set from this
             Client instance

        Returns:
            search : An ItemSearch instance that can be used to iterate through Items.

        Raises:
            NotImplementedError: If the API does not conform to the `Item Search spec
                <https://github.com/radiantearth/stac-api-spec/tree/master/item-search>`__
                or does not have a link with
                a ``"rel"`` type of ``"search"``.
        """
        if not self._conforms_to(ConformanceClasses.ITEM_SEARCH):
            raise NotImplementedError(
                "This catalog does not support search because it "
                f'does not conform to "{ConformanceClasses.ITEM_SEARCH}"'
            )
        search_link = self.get_search_link()
        if search_link is None:
            raise NotImplementedError(
                'No link with "rel" type of "search" could be found in this catalog'
            )

        return ItemSearch(
            search_link.target,
            stac_io=self._stac_io,
            client=self,
            **kwargs,
        )

    def get_search_link(self) -> Optional[pystac.Link]:
        """Returns this client's search link.

        Searches for a link with rel="search" and either a GEOJSON or JSON media type.

        Returns:
            Optional[pystac.Link]: The search link, or None if there is not one found.
        """
        return next(
            (
                link
                for link in self.links
                if link.rel == "search"
                and (
                    link.media_type == pystac.MediaType.GEOJSON
                    or link.media_type == pystac.MediaType.JSON
                )
            ),
            None,
        )
