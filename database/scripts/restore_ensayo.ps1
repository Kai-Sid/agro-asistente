# Non-destructive restore essay into a temporary lab database.
# From repo root:
#   powershell -ExecutionPolicy Bypass -File .\database\scripts\restore_ensayo.ps1

param(
    [string]$DumpPath = "",
    [string]$MysqlExe = "C:\xampp\mysql\bin\mysql.exe",
    [string]$User = "root",
    [string]$LabDatabase = "agro_asistente_restore_lab"
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root

if (-not (Test-Path $MysqlExe)) {
    throw "mysql.exe not found at $MysqlExe"
}

if (-not $DumpPath) {
    $latest = Get-ChildItem ".\backups\mysql-agro_asistente-*.sql" |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($null -eq $latest) {
        throw "No SQL dump in backups/. Run database\scripts\backup.ps1 first."
    }
    $DumpPath = $latest.FullName
}

if (-not (Test-Path $DumpPath)) {
    throw "Dump not found: $DumpPath"
}

Write-Host "Dump: $DumpPath"
Write-Host "Lab DB: $LabDatabase"

$sqlCreate = "DROP DATABASE IF EXISTS ``$LabDatabase``; CREATE DATABASE ``$LabDatabase`` CHARACTER SET utf8mb4;"
& $MysqlExe -u $User -e $sqlCreate

$tempSql = Join-Path $env:TEMP "agro_restore_lab.sql"
$raw = Get-Content -Path $DumpPath -Raw
$raw = $raw -replace '(?im)^CREATE DATABASE.*?;', ("CREATE DATABASE IF NOT EXISTS ``{0}``;" -f $LabDatabase)
$raw = $raw -replace '(?im)^USE `.*?`;', ("USE ``{0}``;" -f $LabDatabase)
$raw = $raw -replace '(?im)^USE [^;]+;', ("USE ``{0}``;" -f $LabDatabase)
[System.IO.File]::WriteAllText($tempSql, $raw)

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $MysqlExe
$psi.Arguments = "-u $User $LabDatabase"
$psi.RedirectStandardInput = $true
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$proc = [System.Diagnostics.Process]::Start($psi)
$proc.StandardInput.Write([System.IO.File]::ReadAllText($tempSql))
$proc.StandardInput.Close()
$proc.WaitForExit()
if ($proc.ExitCode -ne 0) {
    throw ("mysql restore failed exit={0}" -f $proc.ExitCode)
}

$countSql = "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$LabDatabase';"
$check = & $MysqlExe -u $User -N -e $countSql
Write-Host ("Tables restored in {0}: {1}" -f $LabDatabase, $check)
if ([int]$check -lt 1) {
    throw "Restore lab has zero tables"
}

Write-Host ("ENSAYO_RESTORE_OK tablas={0} dump={1} db={2}" -f $check, (Split-Path $DumpPath -Leaf), $LabDatabase)
Write-Host "NOTE: working database agro_asistente was NOT modified."
