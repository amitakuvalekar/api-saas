I did not test all parameters for all APIs.

For `GET /wines`, I tested filtering by `country`.
For `GET /regions`, I tested filtering by `country`.
For `GET /regions/{region_name}/wines`, I tested the `region_name` path parameter.
For `GET /grapes`, I only tested the base endpoint without any parameters.
For `GET /grapes/{grape_name}/wines`, I tested the `grape_name` path parameter.

I did not test combinations of parameters, nor all individual parameters like `region` and `variety` for `/wines`, or `group_by_country`, `min_wines`, `sort_by`, `order` for `/regions`, or any of the parameters for `/grapes` (e.g., `min_wines`, `variety`, `region`, `sort_by`, `order`).