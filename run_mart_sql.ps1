
$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot

# Подключаем общую функцию выполнения SQL
. (Join-Path $ProjectRoot "scripts\Invoke-SqlFile.ps1")

Push-Location $ProjectRoot

try {
    # Загрузка данных и построение витрин
    $martSql = @(
        "05_load_mart_facts.sql",
        "06_build_market_prices.sql",
        "07_dimensions.sql",
        "08_mart_foreign_keys.sql"
    )

    foreach ($file in $martSql) {
        Invoke-SqlFile -File $file -ProjectRoot $ProjectRoot
    }

    Write-Host "`nВитрины Mart успешно построены"
}
finally {
    Pop-Location
}
