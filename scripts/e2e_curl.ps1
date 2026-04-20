$ErrorActionPreference = "Stop"
$BASE = "http://localhost:8000"

function Step {
    param([string]$title)
    Write-Host ""
    Write-Host "=== $title ===" -ForegroundColor Cyan
}

function Run {
    param([string[]]$curlArgs)
    & curl.exe @curlArgs
    Write-Host ""
}

$tmp = Join-Path $env:TEMP "credit-e2e"
New-Item -ItemType Directory -Force -Path $tmp | Out-Null

$wrongPass = Join-Path $tmp "wrong.json"
'{"login":"admin","password":"wrong"}' | Set-Content -Encoding ascii $wrongPass

$goodPass = Join-Path $tmp "good.json"
'{"login":"admin","password":"admin"}' | Set-Content -Encoding ascii $goodPass

Step "1. Auth: wrong password (expect 401)"
Run @("-s","-o","-","-w","`nHTTP %{http_code}`n","-X","POST","$BASE/api/v1/auth/token","-H","Content-Type: application/json","--data-binary","@$wrongPass")

Step "2. Auth: correct credentials (expect 200 + token)"
$raw = & curl.exe -s -X POST "$BASE/api/v1/auth/token" -H "Content-Type: application/json" --data-binary "@$goodPass"
Write-Host $raw
$token = ($raw | ConvertFrom-Json).access_token
Write-Host ""
Write-Host "Token obtained (len=$($token.Length))" -ForegroundColor Green

Step "3. /user_credits/1 without auth (expect 401)"
Run @("-s","-o","-","-w","`nHTTP %{http_code}`n","$BASE/api/v1/user_credits/1")

Step "4. /user_credits/1 with JWT (expect 200, truncated)"
$body = & curl.exe -s -w "`nHTTP %{http_code}" -H "Authorization: Bearer $token" "$BASE/api/v1/user_credits/1"
Write-Host $body
Write-Host ""

Step "5. /user_credits/99999999 unknown user (expect 404)"
Run @("-s","-o","-","-w","`nHTTP %{http_code}`n","-H","Authorization: Bearer $token","$BASE/api/v1/user_credits/99999999")

Step "6. /plans_performance?check_date=2024-06-01 (expect 200, first 2 items)"
$perf = & curl.exe -s -H "Authorization: Bearer $token" "$BASE/api/v1/plans_performance?check_date=2024-06-01"
$arr = $perf | ConvertFrom-Json
Write-Host "Items returned: $($arr.Count)"
$arr | Select-Object -First 2 | ConvertTo-Json -Depth 5 | Write-Host

Step "7. /year_performance?year=2021 (expect 200, months of real data)"
$year = & curl.exe -s -H "Authorization: Bearer $token" "$BASE/api/v1/year_performance?year=2021"
$yearArr = $year | ConvertFrom-Json
Write-Host "Months returned: $($yearArr.Count)"
$yearArr | Select-Object -First 2 | ConvertTo-Json -Depth 5 | Write-Host

Step "8. /year_performance?year=1700 invalid (expect 422)"
Run @("-s","-o","-","-w","`nHTTP %{http_code}`n","-H","Authorization: Bearer $token","$BASE/api/v1/year_performance?year=1700")

Step "9. /plans_insert with valid xlsx (expect 201)"
$xlsx = Join-Path $tmp "plans_new.xlsx"
$builder = Join-Path (Get-Location) "scripts\_build_test_xlsx.py"
& .\.venv\Scripts\python.exe $builder $xlsx valid
Run @("-s","-o","-","-w","`nHTTP %{http_code}`n","-X","POST","$BASE/api/v1/plans_insert","-H","Authorization: Bearer $token","-F","file=@$xlsx")

Step "10. /plans_insert duplicate period/category (expect 422)"
Run @("-s","-o","-","-w","`nHTTP %{http_code}`n","-X","POST","$BASE/api/v1/plans_insert","-H","Authorization: Bearer $token","-F","file=@$xlsx")

Step "11. /plans_insert bad xlsx - period not first of month (expect 422)"
$xlsxBad = Join-Path $tmp "plans_bad.xlsx"
& .\.venv\Scripts\python.exe $builder $xlsxBad bad_period
Run @("-s","-o","-","-w","`nHTTP %{http_code}`n","-X","POST","$BASE/api/v1/plans_insert","-H","Authorization: Bearer $token","-F","file=@$xlsxBad")

Step "DONE"
