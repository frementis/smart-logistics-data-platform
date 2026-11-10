function Invoke-SqlFile {
    param(
        [Parameter(Mandatory)]
        [string]$File,

        [Parameter(Mandatory)]
        [string]$ProjectRoot
    )

    Write-Host "`nВыполнение $File..."

    $sourcePath = Join-Path $ProjectRoot "sql\$File"
    $containerPath = "/tmp/$File"

    if (-not (Test-Path $sourcePath)) {
        throw "SQL-файл не найден: $sourcePath"
    }

    docker compose cp $sourcePath "postgres:$containerPath"

    if ($LASTEXITCODE -ne 0) {
        throw "Ошибка копирования SQL-файла: $File"
    }

    docker compose exec -T postgres psql -U app -d deals_bigdata -v ON_ERROR_STOP=1 -f $containerPath

    if ($LASTEXITCODE -ne 0) {
        throw "Ошибка выполнения SQL-файла: $File"
    }

    Write-Host "Успешно: $File"

}
