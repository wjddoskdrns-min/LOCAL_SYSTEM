# scripts/verify_local_system_step5.ps1
$ErrorActionPreference = "Stop"
$BaseUrl = "http://127.0.0.1:25613"

Write-Host "== Step5: Approver Allowlist + Advice ==" -ForegroundColor Cyan

# 1) create request
$r = Invoke-RestMethod -Method POST "$BaseUrl/requests" -ContentType "application/json" -Body '{"kind":"demo","payload":{"x":1}}'
$runId = $r.run_id
Write-Host "run_id=$runId"

# 2) approve with NOT-allowed approver (expect 403)
$notAllowedOk = $false
try {
  Invoke-RestMethod -Method POST "$BaseUrl/approve/$runId" -ContentType "application/json" -Body '{"approver":"intruder","note":"nope"}' | Out-Null
  $notAllowedOk = $false
} catch {
  if ($_.Exception.Response.StatusCode.value__ -eq 403) { $notAllowedOk = $true }
}

if (-not $notAllowedOk) {
  throw "Expected 403 for not-allowlisted approver, but did not get it."
}
Write-Host "[OK] not-allowed approver blocked (403)" -ForegroundColor Green

# 3) approve with allowed approver (expect 200)
$ap = Invoke-RestMethod -Method POST "$BaseUrl/approve/$runId" -ContentType "application/json" -Body '{"approver":"partner","note":"ok"}'
"$($ap.ok) $($ap.run_id) $($ap.state) executed=$($ap.executed)" | Write-Host

# 4) execute (depends on EXECUTION_ENABLED)
$ex = Invoke-RestMethod -Method POST "$BaseUrl/execute/$runId"
"$($ex.ok) $($ex.run_id) $($ex.state) executed=$($ex.executed)" | Write-Host

# 5) advice create/get should work regardless
$null = Invoke-RestMethod -Method POST "$BaseUrl/advice/$runId"
$ad2  = Invoke-RestMethod -Method GET  "$BaseUrl/advice/$runId"

if (-not $ad2.run_id) {
    throw "Advice GET failed"
}



Write-Host "[OK] Step5 verify finished" -ForegroundColor Green
