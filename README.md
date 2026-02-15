GET /wines
Description: Retrieve all unique wines present in the database
Query parameters: country, region


GET /regions
Description: Retrieve all unique wine regions with wine counts and optional country grouping.
Query parameters: country, group_by_country, min_wines, sort_by


GET /regions/{region_name}/wines
Description: Alternative endpoint using URL-encoded region name instead of ID.
Path parameter: region_name

GET /grapes
Description: Retrieve all grape varieties with frequency, metadata, and primary regions.
Query parameters: min_wines, variety, region, sort_by, order


GET /grapes/{grape_name}/wines
Description: Alternative endpoint using URL-encoded grape name instead of ID.
Path parameter: grape_name