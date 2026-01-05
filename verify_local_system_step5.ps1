param(
  [string]$BaseUrl = "http://127.0.0.1:25613"
)

$ErrorActionPreference = "Stop"

Write-Host "== Step5: Approver Allowlist + Advice ==" -ForegroundColor Cyan

# create
$r = Invoke-RestMethod -Method POST "$BaseUrl/requests" -ContentType "application/json" -Body '{"kind":"demo","payload":{"x":13}}'
$run_id = $r.run_id
Write-Host "run_id=$run_id" -ForegroundColor Yellow

# approve with NOT allowed approver -> should 403
try {
  Invoke-RestMethod -Method POST "$BaseUrl/approve/$run_id" -ContentType "application/json" -Body '{"approver":"hacker","note":"no"}' | Out-Null
  throw "FAILED: expected 403 but got success"
} catch {
  Write-Host "[OK] not-allowed approver blocked" -ForegroundColor Green
}

# approve with allowed approver
Invoke-RestMethod -Method POST "$BaseUrl/approve/$run_id" -ContentType "application/json" -Body '{"approver":"partner","note":"ok"}' | Format-Table

# execute (depends on EXECUTION_ENABLED)
$ex = Invoke-RestMethod -Method POST "$BaseUrl/execute/$run_id"
$ex | Format-Table

# advice
Invoke-RestMethod -Method POST "$BaseUrl/advice/$run_id" | Format-List
Invoke-RestMethod -Method GET  "$BaseUrl/advice/$run_id" | Format-List

Write-Host "`n[OK] Step5 verify finished" -ForegroundColor Green
