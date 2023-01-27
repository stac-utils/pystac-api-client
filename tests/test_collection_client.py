import pytest

from pystac_client import CollectionClient
from pystac_client.client import Client

from .helpers import STAC_URLS


class TestCollectionClient:
    @pytest.mark.vcr
    def test_instance(self) -> None:
        client = Client.open(STAC_URLS["PLANETARY-COMPUTER"])
        collection = client.get_collection("aster-l1t")

        assert isinstance(collection, CollectionClient)
        assert str(collection) == "<CollectionClient id=aster-l1t>"

    @pytest.mark.vcr
    def test_get_items(self) -> None:
        client = Client.open(STAC_URLS["PLANETARY-COMPUTER"])
        collection = client.get_collection("aster-l1t")
        assert collection is not None
        for item in collection.get_items():
            assert item.collection_id == collection.id
            return

    @pytest.mark.vcr
    def test_get_item(self) -> None:
        client = Client.open(STAC_URLS["PLANETARY-COMPUTER"])
        collection = client.get_collection("aster-l1t")
        assert collection is not None
        item = collection.get_item("AST_L1T_00312272006020322_20150518201805")
        assert item
        assert item.id == "AST_L1T_00312272006020322_20150518201805"

        item = collection.get_item("for-sure-not-a-real-id")
        assert item is None

    @pytest.mark.vcr
    def test_get_item_with_item_search(self) -> None:
        client = Client.open(STAC_URLS["PLANETARY-COMPUTER"])
        collection = client.get_collection("aster-l1t")
        assert collection is not None
        assert client._stac_io
        client._stac_io.set_conformance(
            [
                "https://api.stacspec.org/v1.0.0-rc.2/core",
                "https://api.stacspec.org/v1.0.0-rc.2/item-search",
            ]
        )
        item = collection.get_item("AST_L1T_00312272006020322_20150518201805")
        assert item
        assert item.id == "AST_L1T_00312272006020322_20150518201805"

        item = collection.get_item("for-sure-not-a-real-id")
        assert item is None

        item = collection.get_item(
            "AST_L1T_00312272006020322_20150518201805", recursive=True
        )
        assert item
        assert item.id == "AST_L1T_00312272006020322_20150518201805"
