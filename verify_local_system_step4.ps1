param(
  [string]$BaseUrl = "http://127.0.0.1:25613"
)

$ErrorActionPreference = "Stop"

Write-Host "== Step4: EXECUTION_ENABLED=1 should EXECUTE ==" -ForegroundColor Cyan

# 1) create
$r = Invoke-RestMethod -Method POST "$BaseUrl/requests" -ContentType "application/json" -Body '{"kind":"demo","payload":{"x":13}}'
$run_id = $r.run_id
Write-Host "run_id=$run_id" -ForegroundColor Yellow

# 2) approve
Invoke-RestMethod -Method POST "$BaseUrl/approve/$run_id" -ContentType "application/json" -Body '{"approver":"partner","note":"ok"}' | Format-Table

# 3) execute (should be EXECUTED)
$ex = Invoke-RestMethod -Method POST "$BaseUrl/execute/$run_id"
$ex | Format-Table

if ($ex.state -ne "EXECUTED" -or $ex.executed -ne 1) {
  throw "FAILED: expected EXECUTED/executed=1 but got state=$($ex.state), executed=$($ex.executed)"
}

# 4) advice (should exist)
Invoke-RestMethod -Method POST "$BaseUrl/advice/$run_id" | Format-List
Invoke-RestMethod -Method GET  "$BaseUrl/advice/$run_id" | Format-List

Write-Host "`n[OK] Step4 pass: execution allowed and executed" -ForegroundColor Green
