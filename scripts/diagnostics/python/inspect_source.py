from etl.extract import extract_prices, get_source_count


if __name__ == "__main__":
    count = get_source_count()
    print(f"Всего записей в public.prices: {count}")

    df = extract_prices(limit=5)

    print("\nПервые 5 записей:")
    print(df.to_string(index=False))

    print("\nТипы данных:")
    print(df.dtypes)
