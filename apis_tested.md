Here are the APIs that I tested:

- `GET /wines`: Returns a list of wines. It can be filtered by `country`, `region`, and `variety`.
- `GET /regions`: Returns a list of regions. It can be filtered by `country`, `min_wines` and can be grouped by country. It can be sorted by `name`, `country`, `wine_count`.
- `GET /regions/{region_name}/wines`: Returns a list of wines for a given region.
- `GET /grapes`: Returns a list of grapes. It can be filtered by `min_wines`, `variety`, `region`. It can be sorted by `name`, `wine_count`.
- `GET /grapes/{grape_name}/wines`: Returns a list of wines for a given grape.