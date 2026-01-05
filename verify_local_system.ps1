param(
  [string]$BaseUrl = "http://127.0.0.1:25613"
)

$ErrorActionPreference = "Stop"

Write-Host "== 1) status/health ==" -ForegroundColor Cyan
Invoke-RestMethod "$BaseUrl/status" | Format-Table
Invoke-RestMethod "$BaseUrl/health" | Format-Table

Write-Host "`n== 2) create request ==" -ForegroundColor Cyan
$r = Invoke-RestMethod -Method POST "$BaseUrl/requests" -ContentType "application/json" -Body '{"kind":"demo","payload":{"x":13}}'
$r | Format-Table
$run_id = $r.run_id

Write-Host "`n== 3) approve ==" -ForegroundColor Cyan
Invoke-RestMethod -Method POST "$BaseUrl/approve/$run_id" -ContentType "application/json" -Body '{"approver":"partner","note":"ok"}' | Format-Table

Write-Host "`n== 4) execute (should be BLOCKED when EXECUTION_ENABLED=0) ==" -ForegroundColor Cyan
Invoke-RestMethod -Method POST "$BaseUrl/execute/$run_id" | Format-Table

Write-Host "`n== 5) advice create/get ==" -ForegroundColor Cyan
Invoke-RestMethod -Method POST "$BaseUrl/advice/$run_id" | Format-List
Invoke-RestMethod -Method GET  "$BaseUrl/advice/$run_id" | Format-List

Write-Host "`n== 6) rooms/events summary ==" -ForegroundColor Cyan
Invoke-RestMethod "$BaseUrl/rooms" | Format-List
Invoke-RestMethod "$BaseUrl/events/summary?limit=15" | Format-List

Write-Host "`n[OK] verify_local_system finished" -ForegroundColor Green
