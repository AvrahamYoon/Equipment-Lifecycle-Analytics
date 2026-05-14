-- Merge pre-shaped frames registered in DuckDB (same logical columns, union by name).
-- Python substitutes {{UNION_BODY}} with a chain like:
--   SELECT * FROM _merge_0 UNION ALL BY NAME SELECT * FROM _merge_1 ...
SELECT *
FROM (
{{UNION_BODY}}
) AS _merged;
