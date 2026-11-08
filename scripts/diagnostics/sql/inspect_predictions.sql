SELECT
    COUNT(*) AS total_predictions,
    COUNT(DISTINCT price_id) AS unique_prices,
    COUNT(*) FILTER (WHERE dataset_split = 'test') AS test_count,
    COUNT(*) FILTER (WHERE dataset_split = 'future') AS future_count
FROM mart.ml_predictions;