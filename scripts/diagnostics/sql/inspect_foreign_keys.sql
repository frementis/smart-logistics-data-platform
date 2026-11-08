-- Список внешних ключей витрин
SELECT
    conrelid::REGCLASS AS table_name,
    conname AS constraint_name,
    confrelid::REGCLASS AS referenced_table
FROM pg_constraint
WHERE contype = 'f'
  AND connamespace = 'mart'::REGnamespace
ORDER BY table_name, constraint_name;

-- Количество связей по таблицам
SELECT
    'market_price_facts' AS table_name,
    COUNT(*) AS rows_count
FROM mart.market_price_facts

UNION ALL

SELECT
    'market_prices',
    COUNT(*)
FROM mart.market_prices;