from typing import Optional, Dict, Any, Union
import warnings

import pystac

from pystac_client.exceptions import APIError
from pystac_client.conformance import ConformanceClasses
from pystac_client.stac_api_io import StacApiIO
from pystac_client.warnings import DoesNotConformTo, MissingLink

QUERYABLES_REL = "http://www.opengis.net/def/rel/ogc/1.0/queryables"
QUERYABLES_ENDPOINT = "queryables"


class StacAPIObject(pystac.STACObject):
    _stac_io: Optional[StacApiIO]

    def conforms_to(self, conformance_class: Union[str, ConformanceClasses]) -> bool:
        raise NotImplementedError


class BaseMixin(StacAPIObject):
    def _get_href(self, rel: str, link: Optional[pystac.Link], endpoint: str) -> str:
        if link and isinstance(link.href, str):
            href = link.absolute_href
        else:
            warnings.warn(MissingLink(rel, self.__class__.__name__), stacklevel=2)
            href = f"{self.self_href.rstrip('/')}/{endpoint}"
        return href


class QueryablesMixin(BaseMixin):
    """Mixin for adding support for /queryables endpoint"""

    def get_queryables(self, *collections: Optional[str]) -> Dict[str, Any]:
        """Return all queryables, or limit to those of specified collections.
        
        Queryables from multiple collections are unioned together, except in the case when the same queryable key has a different definition, in which case that key is dropped.

        Output is a dictionary that can be used in ``jsonshema.validate``
        Args:
            *collections: The IDs of the items to include.

        Return:
            Dict[str, Any]: Dictionary containing queryable fields
        """
        if collections and isinstance(self, pystac.Catalog):
            response = self.get_collection(collections[0]).get_queryables()
            response.pop("$id")
            for collection in collections[1:]:
                col_resp = self.get_collection(collection).get_queryables()
                response["properties"].update(col_resp["properties"])
            return response

        if self._stac_io is None:
            raise APIError("API access is not properly configured")

        if not self.conforms_to(ConformanceClasses.FILTER):
            raise DoesNotConformTo(ConformanceClasses.FILTER.name)

        url = self._get_queryables_href()

        result = self._stac_io.read_json(url)
        if "properties" not in result:
            raise APIError(
                f"Invalid response from {QUERYABLES_ENDPOINT}: "
                "expected 'properties' attribute"
            )

        return result

    def _get_queryables_href(self) -> str:
        link = self.get_single_link(QUERYABLES_REL)
        href = self._get_href(QUERYABLES_REL, link, QUERYABLES_ENDPOINT)
        return href
