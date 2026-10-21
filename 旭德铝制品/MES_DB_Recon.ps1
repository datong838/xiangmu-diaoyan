# ============================================================
#  MES_DB_Recon.ps1  --  READ-ONLY reconnaissance script
#
#  This script NEVER modifies anything.
#  It does NOT reboot, does NOT stop/start any service,
#  does NOT change IP or network settings,
#  does NOT connect to or query any database.
#
#  HOW TO RUN (no admin rights needed):
#      powershell -ExecutionPolicy Bypass -File .\MES_DB_Recon.ps1
#
#  OUTPUT: MES_DB_Recon_<timestamp>.txt  in the same folder
#
#  WARNING: the report may contain plain-text database passwords.
#           Handle it like a password. Do not paste it into chat.
# ============================================================

$ErrorActionPreference = 'SilentlyContinue'
$ProgressPreference    = 'SilentlyContinue'

$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $dir) { $dir = (Get-Location).Path }
$out = Join-Path $dir ("MES_DB_Recon_" + (Get-Date -Format 'yyyyMMdd_HHmmss') + ".txt")

"============================================================" | Out-File $out
" MES DB RECON  (READ-ONLY)"                                  | Out-File $out -Append
" Host : $env:COMPUTERNAME"                                   | Out-File $out -Append
" User : $env:USERNAME"                                       | Out-File $out -Append
" Time : $(Get-Date)"                                         | Out-File $out -Append
"============================================================" | Out-File $out -Append

# ---------- [1] Network ----------
"`n[1] NETWORK CONFIGURATION" | Out-File $out -Append
ipconfig /all | Out-File $out -Append
"`n-- ARP / neighbour cache (other machines visible on this LAN) --" | Out-File $out -Append
arp -a | Out-File $out -Append

# ---------- [2] Listening ports ----------
"`n[2] LISTENING TCP PORTS ON THIS MACHINE" | Out-File $out -Append
netstat -ano -p tcp | Select-String 'LISTENING' | Out-File $out -Append

# ---------- [3] Database services and processes ----------
"`n[3] DATABASE SERVICES / PROCESSES" | Out-File $out -Append
Get-Service | Where-Object { $_.DisplayName -match 'SQL|MySQL|MariaDB|Oracle|Postgre|Mongo' } |
  Format-Table -AutoSize | Out-File $out -Append -Width 250
"`n-- running processes --" | Out-File $out -Append
Get-Process | Where-Object { $_.ProcessName -match 'sqlservr|mysqld|mariadbd|oracle|postgres|mongod' } |
  Format-Table -AutoSize | Out-File $out -Append -Width 250

# ---------- [4] .udl files ----------
"`n[4] .UDL FILES (often contain a complete connection string)" | Out-File $out -Append
Get-ChildItem -Path 'C:\','D:\','E:\' -Filter *.udl -Recurse -Depth 4 -Force -ErrorAction SilentlyContinue |
  ForEach-Object {
    "FILE: $($_.FullName)"
    Get-Content $_.FullName | Select-String 'Source|Catalog|Password|User ID|Provider'
  } | Out-File $out -Append

# ---------- [5] Connection strings inside config files ----------
"`n[5] CONNECTION STRINGS FOUND IN CONFIG FILES" | Out-File $out -Append
$roots = @('C:\Program Files','C:\Program Files (x86)','C:\ProgramData','D:\','E:\')
$inc   = @('*.config','*.ini','*.xml','*.json','*.properties','*.txt')
$pat   = 'Data Source|Initial Catalog|jdbc:|DBQ=|ServerName|database\s*=|SERVER\s*='

foreach ($r in $roots) {
  if (-not (Test-Path $r)) { continue }
  "`n--- scanning $r ---" | Out-File $out -Append
  Get-ChildItem -Path $r -Include $inc -Recurse -Depth 4 -Force -ErrorAction SilentlyContinue |
    Select-String -Pattern $pat -ErrorAction SilentlyContinue |
    Select-Object -First 80 |
    ForEach-Object { "$($_.FileName) :: $($_.Line.Trim())" } |
    Out-File $out -Append
}

# ---------- [6] ODBC data sources ----------
"`n[6] ODBC DATA SOURCE NAMES (DSN)" | Out-File $out -Append
"-- Machine DSN (HKLM) --" | Out-File $out -Append
Get-ItemProperty -Path 'HKLM:\SOFTWARE\ODBC\ODBC.INI\*' -ErrorAction SilentlyContinue |
  Format-List | Out-File $out -Append
"-- User DSN (HKCU) --" | Out-File $out -Append
Get-ItemProperty -Path 'HKCU:\SOFTWARE\ODBC\ODBC.INI\*' -ErrorAction SilentlyContinue |
  Format-List | Out-File $out -Append
"-- 64-bit syswow DSN --" | Out-File $out -Append
Get-ItemProperty -Path 'HKLM:\SOFTWARE\WOW6432Node\ODBC\ODBC.INI\*' -ErrorAction SilentlyContinue |
  Format-List | Out-File $out -Append

# ---------- [7] How to read the result ----------
"`n[7] HOW TO READ THIS REPORT" | Out-File $out -Append
"Priority: look at section [4] and [5] first."            | Out-File $out -Append
"A typical line looks like:"                              | Out-File $out -Append
"   Data Source=192.168.1.10,1433; Initial Catalog=MESDB; User ID=sa; Password=xxxx" | Out-File $out -Append
"which tells you:   IP=192.168.1.10   PORT=1433   DB=MESDB" | Out-File $out -Append
""                                                        | Out-File $out -Append
"PORT -> ENGINE:"                                         | Out-File $out -Append
"   1433  = Microsoft SQL Server"                         | Out-File $out -Append
"   3306  = MySQL / MariaDB"                              | Out-File $out -Append
"   1521  = Oracle"                                       | Out-File $out -Append
"   5432  = PostgreSQL"                                   | Out-File $out -Append
"   27017 = MongoDB"                                      | Out-File $out -Append
""                                                        | Out-File $out -Append
"If a config uses 'jdbc:mysql://...' or 'jdbc:oracle:thin:@...'," | Out-File $out -Append
"the engine is named directly in the string."              | Out-File $out -Append
""                                                        | Out-File $out -Append
"Report location: $out"                                   | Out-File $out -Append

Write-Host ""
Write-Host "Done. Report saved to:" -ForegroundColor Green
Write-Host $out
Write-Host ""
Write-Host "Open section [4] and [5] first. Look for 'Data Source' or 'jdbc:'." -ForegroundColor Yellow
