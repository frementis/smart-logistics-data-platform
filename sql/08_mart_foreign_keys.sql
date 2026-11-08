BEGIN;

DO $$
BEGIN
    -- Фактовая таблица отдельных перевозок

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_market_facts_core_price'
          AND conrelid = 'mart.market_price_facts'::regclass
    ) THEN
        ALTER TABLE mart.market_price_facts
            ADD CONSTRAINT fk_market_facts_core_price
            FOREIGN KEY (price_id)
            REFERENCES core.prices(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_market_facts_month'
          AND conrelid = 'mart.market_price_facts'::regclass
    ) THEN
        ALTER TABLE mart.market_price_facts
            ADD CONSTRAINT fk_market_facts_month
            FOREIGN KEY (month_date)
            REFERENCES mart.dim_month(month_date);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_market_facts_loading_city'
          AND conrelid = 'mart.market_price_facts'::regclass
    ) THEN
        ALTER TABLE mart.market_price_facts
            ADD CONSTRAINT fk_market_facts_loading_city
            FOREIGN KEY (loading_city_gcid)
            REFERENCES mart.dim_city(gc_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_market_facts_unloading_city'
          AND conrelid = 'mart.market_price_facts'::regclass
    ) THEN
        ALTER TABLE mart.market_price_facts
            ADD CONSTRAINT fk_market_facts_unloading_city
            FOREIGN KEY (unloading_city_gcid)
            REFERENCES mart.dim_city(gc_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_market_facts_body_group'
          AND conrelid = 'mart.market_price_facts'::regclass
    ) THEN
        ALTER TABLE mart.market_price_facts
            ADD CONSTRAINT fk_market_facts_body_group
            FOREIGN KEY (body_group)
            REFERENCES mart.dim_body_group(body_group);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_market_facts_weight_category'
          AND conrelid = 'mart.market_price_facts'::regclass
    ) THEN
        ALTER TABLE mart.market_price_facts
            ADD CONSTRAINT fk_market_facts_weight_category
            FOREIGN KEY (weight_category)
            REFERENCES mart.dim_weight_category(weight_category);
    END IF;


    -- Агрегированная витрина

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_market_prices_month'
          AND conrelid = 'mart.market_prices'::regclass
    ) THEN
        ALTER TABLE mart.market_prices
            ADD CONSTRAINT fk_market_prices_month
            FOREIGN KEY (month_date)
            REFERENCES mart.dim_month(month_date);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_market_prices_loading_city'
          AND conrelid = 'mart.market_prices'::regclass
    ) THEN
        ALTER TABLE mart.market_prices
            ADD CONSTRAINT fk_market_prices_loading_city
            FOREIGN KEY (loading_city_gcid)
            REFERENCES mart.dim_city(gc_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_market_prices_unloading_city'
          AND conrelid = 'mart.market_prices'::regclass
    ) THEN
        ALTER TABLE mart.market_prices
            ADD CONSTRAINT fk_market_prices_unloading_city
            FOREIGN KEY (unloading_city_gcid)
            REFERENCES mart.dim_city(gc_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_market_prices_body_group'
          AND conrelid = 'mart.market_prices'::regclass
    ) THEN
        ALTER TABLE mart.market_prices
            ADD CONSTRAINT fk_market_prices_body_group
            FOREIGN KEY (body_group)
            REFERENCES mart.dim_body_group(body_group);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_market_prices_weight_category'
          AND conrelid = 'mart.market_prices'::regclass
    ) THEN
        ALTER TABLE mart.market_prices
            ADD CONSTRAINT fk_market_prices_weight_category
            FOREIGN KEY (weight_category)
            REFERENCES mart.dim_weight_category(weight_category);
    END IF;

END
$$;

COMMIT;