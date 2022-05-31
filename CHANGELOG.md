# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased] - TBD

### Added

- lru_cache to several methods [#167](https://github.com/stac-utils/pystac-client/pull/167)

### Changed

- Better error message when trying to search a non-item-search-conforming catalog [#164](https://github.com/stac-utils/pystac-client/pull/164)

### Fixed

- Search sortby parameter now has correct typing and correctly handles both GET and POST JSON parameter formats. [#175](https://github.com/stac-utils/pystac-client/pull/175)
- Search fields parameter now has correct typing and correctly handles both GET and POST JSON parameter formats. [#184](https://github.com/stac-utils/pystac-client/pull/184)
 
## [v0.3.5] - 2022-05-26

### Fixed

- Search against earth-search v0 failed with message "object of type 'Link' has no len()" [#179](https://github.com/stac-utils/pystac-client/pull/179)

## [v0.3.4] - 2022-05-18

### Added

- Direct item GET via ogcapi-features, if conformant [#166](https://github.com/stac-utils/pystac-client/pull/166)

### Changed

- Relaxed media type requirement for search links [#160](https://github.com/stac-utils/pystac-client/pull/160), [#165](https://github.com/stac-utils/pystac-client/pull/165)

## [v0.3.3] - 2022-04-28

### Added

- Add `--filter-lang` parameter to allow specifying other filter language to be used within the `--filter` parameter [#140](https://github.com/stac-utils/pystac-client/pull/140)
- CI checks against minimum versions of all dependencies and any pre-release versions of PySTAC [#144](https://github.com/stac-utils/pystac-client/pull/144)

### Changed

- Relaxed upper bound on PySTAC dependency [#144](https://github.com/stac-utils/pystac-client/pull/144)
- Bumped PySTAC dependency to >= 1.4.0 [#147](https://github.com/stac-utils/pystac-client/pull/147)
- Search `filter-lang` defaults to `cql2-json` instead of `cql-json`
- Search `filter-lang` will be set to `cql2-json` if the `filter` is a dict, or `cql2-text` if it is a string
- Search parameter `intersects` is now typed to only accept a str, dict, or object that implements `__geo_interface__`

## Removed

- Client parameter `require_geojson_link` has been removed.

## [v0.3.2] - 2022-01-11

### Added

- `Client.search` accepts an optional `filter_lang` argument for `filter` requests [#128](https://github.com/stac-utils/pystac-client/pull/128)
- Added support for filtering the search endpoint using the `media_type` in `Client.open` [#142](https://github.com/stac-utils/pystac-client/pull/142)

### Fixed
- Values from `parameters` and `headers` arguments to `Client.open` and `Client.from_file` are now also used in requests made from `CollectionClient` instances
  fetched from the same API ([#126](https://github.com/stac-utils/pystac-client/pull/126))
- The tests folder is no longer installed as a package.

## [v0.3.1] - 2021-11-17

### Changed
- Update min PySTAC version to 1.2
- Default page size limit set to 100 rather than relying on the server default
- Fetch single collection directly from endpoint in API rather than iterating through children (Issue #114)[https://github.com/stac-utils/pystac-client/issues/114]

### Added

- Adds `--block-network` option to all test commands to ensure no network requests are made during unit tests
  [#119](https://github.com/stac-utils/pystac-client/pull/119)
- `parameters` argument to `StacApiIO`, `Client.open`, and `Client.from_file` to allow query string parameters to be passed to all requests
  [#118](https://github.com/stac-utils/pystac-client/pull/118)

### Fixed

- `Client.get_collections` raised an exception when API did not publish `/collections` conformance class instead of falling back to using child links
  [#120](https://github.com/stac-utils/pystac-client/pull/120)

## [v0.3.0] - 2021-09-28

### Added
- Jupyter Notebook tutorials
- Basic CQL-JSON filtering [#100](https://github.com/stac-utils/pystac-client/pull/100)

### Changed

- Improved performance when constructing `pystac.ItemCollection` objects.
- Relax `requests` dependency [#87](https://github.com/stac-utils/pystac-client/pull/87)
- Use regular expressions for checking conformance classes [#97](https://github.com/stac-utils/pystac-client/pull/97)
- Reorganized documentation, updated all docs

### Fixed

- `ItemSearch` now correctly handles times without a timezone specifier [#92](https://github.com/stac-utils/pystac-client/issues/92)
- queries including `gsd` cast to string to float when using shortcut query syntax (i.e., "key=val" strings). [#98](https://github.com/stac-utils/pystac-client/pull/97)
- Documentation lints [#108](https://github.com/stac-utils/pystac-client/pull/108)

## [v0.2.0] - 2021-08-04

### Added

- `Client.open` falls back to the `STAC_URL` environment variable if no url is provided as an argument [#48](https://github.com/stac-utils/pystac-client/pull/48)
- New Search.get_pages() iterator function to retrieve pages as raw JSON, not as ItemCollections
- `StacApiIO` class added, subclass from PySTAC `StacIO`. A `StacApiIO` instance is used for all IO for a Client instance, and all requests
are in a single HTTP session, handle pagination and respects conformance
- `conformance.CONFORMANCE_CLASSES` dictionary added containing all STAC API Capabilities from stac-api-spec
- `collections` subcommand to CLI, for saving all Collections in catalog as JSON
- `Client.get_collections` overrides Catalog to use /collections endpoint if API conforms
- `Client.get_collection(<collection_id>)` for getting specific collection
- `Client.get_items` and `Client.get_all_items` override Catalog functions to use search endpoint instead of traversing catalog

### Changed

- Update to use PySTAC 1.1.0
- IO changed to use PySTAC's new StacIO base class. 
- `Search.item_collections()` renamed to `Search.get_item_collections()`
- `Search.item_collections()` renamed to `Search.get_items()`
- Conformance is checked by each individual function that requires a particular conformance
- STAC API testing URLs changed to updated APIs
- `ItemSearch.get_pages()` function moved to StacApiIO class for general use
- Logging is now enabled in the CLI in all cases.
  If data are being printed to stdout, logging goes to stderr.
  [#79](https://github.com/stac-utils/pystac-client/pull/79)
- Improved logging for GET requests (prints encoded URL)

### Fixed

- Running `stac-client` with no arguments no longer raises a confusing exception [#52](https://github.com/stac-utils/pystac-client/pull/52)
- `Client.get_collections_list` [#44](https://github.com/stac-utils/pystac-client/issues/44)
- The regular expression used for datetime parsing [#59](https://github.com/stac-utils/pystac-client/pull/59)
- `Client.from_file` now works as expected, using `Client.open` is not required, although it will fetch STAC_URL from an envvar

### Removed

- `get_pages` and `simple_stac_resolver` functions from `pystac_client.stac_io` (The new StacApiIO class understands `Link` objects)
- `Client.search()` no longer accepts a `next_resolver` argument
- pystac.extensions modules, which were based on PySTAC's previous extension implementation, replaced in 1.0.0
- `stac_api_object.StacApiObjectMixin`, replaced with conformance checking in `StacApiIO`
- PySTAC Collection objects can no longer be passed in as `collections` arguments to the `ItemSearch` class (just pass ids)
- `Catalog.get_collection_list` (was alias to `get_child_links`) because made assumption about this being an API only. Also redundant with `Catalog.get_collections`
- `Search.item_collections()`
- `Search.items()`
- STAC_URL environment variable in Client.open(). url parameter in Client is now required
- STAC_URL environment variable in CLI. CLI now has a required positional argument for the URL

## [v0.1.1] - 2021-04-16

### Added

- `ItemSearch.items_as_collection` [#37](https://github.com/stac-utils/pystac-client/pull/37)
- Documentation [published on ReadTheDocs](https://pystac-client.readthedocs.io/en/latest/) [#46](https://github.com/stac-utils/pystac-client/pull/46)

### Fixed

- Include headers in STAC_IO [#38](https://github.com/stac-utils/pystac-client/pull/38)
- README updated to reflect actual CLI behavior

### Changed

- CLI: pass in heades as list of KEY=VALUE pairs

## [v0.1.0] - 2021-04-14

Initial release.

[Unreleased]: <https://github.com/stac-utils/pystac-client/compare/v0.3.5...main>
[v0.3.5]: <https://github.com/stac-utils/pystac-client/compare/v0.3.4..v0.3.5>
[v0.3.4]: <https://github.com/stac-utils/pystac-client/compare/v0.3.3..v0.3.4>
[v0.3.3]: <https://github.com/stac-utils/pystac-client/compare/v0.3.2..v0.3.3>
[v0.3.2]: <https://github.com/stac-utils/pystac-client/compare/v0.3.1..v0.3.2>
[v0.3.1]: <https://github.com/stac-utils/pystac-client/compare/v0.3.0..v0.3.1>
[v0.3.0]: <https://github.com/stac-utils/pystac-client/compare/v0.2.0..v0.3.0>
[v0.2.0]: <https://github.com/stac-utils/pystac-client/compare/v0.1.1..v0.2.0>
[v0.1.1]: <https://github.com/stac-utils/pystac-client/compare/v0.1.0..v0.1.1>
[v0.1.0]: <https://github.com/stac-utils/pystac-client/tree/v0.1.0>
