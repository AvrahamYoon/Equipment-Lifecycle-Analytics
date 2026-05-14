-- Equipment summary merged CSV; types left wide so Python taxonomy matches prior pandas loads.
SELECT *
FROM read_csv_auto(
    ?,
    header = true,
    all_varchar = true,
    sample_size = -1
);
