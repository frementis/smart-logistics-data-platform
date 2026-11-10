$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot

# Подключаем общую функцию выполнения SQL
. (Join-Path $ProjectRoot "scripts\Invoke-SqlFile.ps1")

Push-Location $ProjectRoot

try {
    # Загрузка данных и построение витрин
    $initialSql = @(
        "01_core.sql",
        "02_core_body_groups.sql",
        "03_mart_schema.sql",
        "04_mart_facts.sql",
        "09_ml_predictions.sql"
    )

    foreach ($file in $initialSql) {
        Invoke-SqlFile -File $file -ProjectRoot $ProjectRoot
    }

    Write-Host "`nСтруктура  БД успешно создана"
}
finally {
    Pop-Location
}
