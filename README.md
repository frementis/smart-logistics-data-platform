# Smart Logistics Data & ML Platform

Тестовый проект Middle Data Engineer. Реализован ETL-процесс обработки данных о грузоперевозках, аналитическая витрина рыночных цен и ML-модель прогнозирования стоимости перевозки.

## 1. Архитектура

Проект построен на PostgreSQL и Python. Обработка данных разделена на три основных слоя:

- **Public** — исходные данные.
- **Core** — обработанные записи и карантин некорректных данных.
- **Mart** — фактологическая и агрегированная витрины, справочники и ML-прогнозы.

Основной поток:

```text
Public → Python ETL → Core → Mart → ML Dataset → CatBoost → Predictions
                         |
                         └→ Quarantine
```

## 2. Стек

- База данных - PostgreSQL 17, SQL.
- ETL - Python, Pandas, NumPy, SQLAlchemy, Psycopg.
- ML - CatBoost, Scikit-learn.
- Инфраструктура - Docker, Docker Compose.
- Тестирование - Pytest.

## 3. Структура проекта

```text
smart-logistics/
├── attachments/       # Материалы задания
├── etl/               # ETL и ML-модули
├── models/            # Обученная модель
├── scripts/
│   └── diagnostics/   # Диагностические скрипты
├── sql/               # SQL-схемы и витрины
├── tests/             # Автоматические тесты
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 4. Запуск проекта

Требования: Docker Desktop, Python 3.11+, Git.

**Подготовка окружения:**

```powershell
Copy-Item .env.example .env
# Указать POSTGRES_PASSWORD в .env

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
docker compose up -d
```


**Подготовка базы данных:**

SQL-скрипты выполняются из корня проекта через PostgreSQL в Docker.

```powershell
function Invoke-SqlFile {
    param([string]$File)

    Write-Host "`nВыполнение $File..."

    Get-Content ".\sql\$File" -Raw |
        docker compose exec -T postgres psql -U app -d deals_bigdata -v ON_ERROR_STOP=1

    if ($LASTEXITCODE -ne 0) {
        throw "Ошибка выполнения SQL-файла: $File"
    }
}
```

**Создание Core и Mart:**

```powershell
$initialSql = @(
    "01_core.sql",
    "02_core_body_groups.sql",
    "03_mart_schema.sql",
    "04_mart_facts.sql",
    "09_ml_predictions.sql"
)

foreach ($file in $initialSql) {
    Invoke-SqlFile $file
}
```

**ETL и построение витрин:**

```powershell
python -m etl.run
python .\scripts\diagnostics\python\run_body_groups.py
```

**Загрузка фактов, агрегатов и справочников:**

```powershell
$martSql = @(
    "05_load_mart_facts.sql",
    "06_build_market_prices.sql",
    "07_dimensions.sql",
    "08_mart_foreign_keys.sql"
)

foreach ($file in $martSql) {
    Invoke-SqlFile $file
}
```

**Обучение и прогнозирование:**

```powershell
python -m etl.train
python -m etl.predict
```

Модель сохраняется в `models/catboost_price_model.cbm`, результаты прогнозирования в `mart.ml_predictions`

## 5. Реализовано

- Пакетная обработка данных по 10 000 записей;
- Валидация, конвертация валют и карантин некорректных записей;
- Идемпотентная загрузка через UPSERT;
- Нормализация типов кузова и весовых категорий;
- Построение витрины с процентилями, средними ценами, динамикой рынка и оценкой надёжности данных;
- Обучение CatBoost с временным разделением выборок;
- Batch inference для тестовых и будущих записей.


## 6. Результаты

Исходных записей - 300 000
Загружено в Core - 298 369
Карантин - 1 631
Записей в фактовой витрине - 289 611
Агрегированных групп - 202 899
ML-прогнозов - 17 598
Автоматических тестов - 38

**Метрики CatBoost на тестовой выборке:**
```text
R^2 - 0.9180
MAPE - 15.64%
RMSE - 54 741 Р
MAE - 28 355 Р
```

## 7. Особенности
- Для конвертации валют используется курс на соответствующую дату без подстановки ближайшего;
- Для временного разделения ML-выборки используются фиксированные границы без перемешивания;
- Для будущих прогнозов фактическая цена и метрики ошибки остаются NULL;
- Повторный запуск ETL не создаёт дубликатов;
- В `attachments/` сохранены исходное задание, требования к данным, материалы обсуждений и ML-отчёт.
