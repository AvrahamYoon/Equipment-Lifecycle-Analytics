-- Service work-order export; header row at line 1 (no preamble rows in current format).
SELECT *
FROM read_csv_auto(
    ?,
    header = true,
    sample_size = -1
);
