# Backup MySQL + knowledge (+ Chroma si existe). Ver docs/RUNBOOK_BACKUP.md
param(
    [string]$MysqlBin = "C:\xampp\mysql\bin\mysqldump.exe",
    [string]$User = "root",
    [string]$Database = "agro_asistente",
    [string]$OutDir = ""
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
if (-not $OutDir) {
    $OutDir = Join-Path $root "backups"
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$fecha = Get-Date -Format "yyyyMMdd-HHmmss"
$sql = Join-Path $OutDir "mysql-$Database-$fecha.sql"

if (-not (Test-Path $MysqlBin)) {
    Write-Error "mysqldump no encontrado: $MysqlBin"
}

& $MysqlBin -u $User --databases $Database --routines --triggers -r $sql
Write-Host "MySQL dump: $sql"

$knowledge = Join-Path $root "knowledge"
if (Test-Path $knowledge) {
    $zipK = Join-Path $OutDir "knowledge-$fecha.zip"
    Compress-Archive -Path $knowledge -DestinationPath $zipK -Force
    Write-Host "Knowledge zip: $zipK"
}

$chroma = Join-Path $root "backend\chroma_data"
if (Test-Path $chroma) {
    $zipC = Join-Path $OutDir "chroma-$fecha.zip"
    Compress-Archive -Path $chroma -DestinationPath $zipC -Force
    Write-Host "Chroma zip: $zipC"
}

Write-Host "Backup completado en $OutDir"
