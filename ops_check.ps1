# ops_check.ps1 (LOCAL_SYSTEM)
# 목적: double-click UX에서 서버 상태를 빠르게 점검하고 1줄 요약 출력
# 정책: 승인된 Verb만 사용(Test/Get/Invoke/Add/Convert/Write/New), 보안 프롬프트 제거, JSON 파싱 안전화

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# UTF-8 출력(콘솔에서 깨짐 완화)
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false) } catch {}

# -----------------------------
# Config
# -----------------------------
$BaseUrl = "http://127.0.0.1:25613"

# Required endpoints
$RequiredEndpoints = @(
  @{ Name="status"; Url="$BaseUrl/status" },
  @{ Name="health"; Url="$BaseUrl/health" }
)

# Optional visibility endpoints
$OptionalEndpoints = @(
  @{ Name="rooms"; Url="$BaseUrl/rooms" },
  @{ Name="events/summary"; Url="$BaseUrl/events/summary?tail=500&order=desc" }
)

# -----------------------------
# Utils
# -----------------------------
function Get-NowStamp {
  return (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
}

function Add-Result {
  param(
    [Parameter(Mandatory=$true)][ref]$Results,
    [Parameter(Mandatory=$true)][string]$Name,
    [Parameter(Mandatory=$true)][ValidateSet("PASS","WARN","FAIL","SKIP")][string]$Result,
    [Parameter(Mandatory=$false)][string]$Note = ""
  )
  $Results.Value += [pscustomobject]@{
    name   = $Name
    result = $Result
    note   = $Note
  }
}

function Convert-JsonSafely {
  param([Parameter(Mandatory=$true)][string]$Text)
  try {
    return ($Text | ConvertFrom-Json -ErrorAction Stop)
  } catch {
    return $null
  }
}

function Invoke-HttpGet {
  param(
    [Parameter(Mandatory=$true)][string]$Url,
    [int]$TimeoutSec = 5
  )

  # 반환 형식 통일: Code, Text, Json, Error
  $resp = [ordered]@{
    Code  = 0
    Text  = ""
    Json  = $null
    Error = ""
  }

  try {
    # 보안 프롬프트/HTML 파싱 리스크 회피:
    # - Invoke-RestMethod가 가장 깔끔(가능 시)
    # - JSON이 아니면 문자열로 처리
    $headers = @{
      "Accept" = "application/json, text/plain, */*"
    }

    try {
      $r = Invoke-RestMethod -Uri $Url -Method GET -TimeoutSec $TimeoutSec -Headers $headers
      # Invoke-RestMethod는 JSON이면 객체로 반환. 문자열이면 문자열.
      $resp.Code = 200
      if ($null -ne $r -and $r.GetType().Name -ne "String") {
        $resp.Json = $r
        $resp.Text = ($r | ConvertTo-Json -Depth 10 -Compress)
      } else {
        $resp.Text = [string]$r
        $resp.Json = Convert-JsonSafely -Text $resp.Text
      }
      return [pscustomobject]$resp
    } catch {
      # fallback: Invoke-WebRequest + UseBasicParsing
      $w = Invoke-WebRequest -Uri $Url -Method GET -UseBasicParsing -TimeoutSec $TimeoutSec -Headers $headers
      $resp.Code = [int]$w.StatusCode
      $resp.Text = [string]$w.Content
      $resp.Json = Convert-JsonSafely -Text $resp.Text
      return [pscustomobject]$resp
    }
  }
  catch {
    $resp.Error = $_.Exception.Message
    return [pscustomobject]$resp
  }
}

# -----------------------------
# Test functions (Approved Verbs)
# -----------------------------
function Test-RequiredEndpoint {
  param(
    [Parameter(Mandatory=$true)][ref]$Results,
    [Parameter(Mandatory=$true)][string]$Name,
    [Parameter(Mandatory=$true)][string]$Url
  )

  $r = Invoke-HttpGet -Url $Url

  if ($r.Code -eq 200 -or $r.Code -eq 204) {
    Add-Result -Results $Results -Name $Name -Result "PASS" -Note ""
    Write-Host ("/{0} PASS" -f $Name) -ForegroundColor Green
  } else {
    $msg = if ($r.Error) { $r.Error } else { ("HTTP {0}" -f $r.Code) }
    Add-Result -Results $Results -Name $Name -Result "FAIL" -Note $msg
    Write-Host ("/{0} FAIL ({1})" -f $Name, $msg) -ForegroundColor Red
  }
}

function Test-OptionalEndpoint {
  param(
    [Parameter(Mandatory=$true)][ref]$Results,
    [Parameter(Mandatory=$true)][string]$Name,
    [Parameter(Mandatory=$true)][string]$Url
  )

  $r = Invoke-HttpGet -Url $Url

  if ($r.Code -eq 200 -or $r.Code -eq 204) {
    Add-Result -Results $Results -Name $Name -Result "PASS" -Note ""
    Write-Host ("/{0} PASS" -f $Name) -ForegroundColor Green
  }
  elseif ($r.Code -eq 404) {
    # Optional은 기본적으로 WARN로(원하면 FAIL로 바꿀 수 있음)
    Add-Result -Results $Results -Name $Name -Result "WARN" -Note "Not Found"
    Write-Host ("/{0} WARN (Not Found)" -f $Name) -ForegroundColor Yellow
  }
  else {
    $msg = if ($r.Error) { $r.Error } else { ("HTTP {0}" -f $r.Code) }
    Add-Result -Results $Results -Name $Name -Result "WARN" -Note $msg
    Write-Host ("/{0} WARN ({1})" -f $Name, $msg) -ForegroundColor Yellow
  }
}

# -----------------------------
# Main
# -----------------------------
$Results = @()

Write-Host ""
Write-Host "=== OPS CHECK START ===" -ForegroundColor Cyan
Write-Host ("BaseUrl={0}" -f $BaseUrl) -ForegroundColor DarkGray
Write-Host ""

# Required checks
foreach ($e in $RequiredEndpoints) {
  Test-RequiredEndpoint -Results ([ref]$Results) -Name $e.Name -Url $e.Url
}

Write-Host ""
Write-Host "[rooms / events visibility]" -ForegroundColor Cyan

# Optional checks
foreach ($e in $OptionalEndpoints) {
  Test-OptionalEndpoint -Results ([ref]$Results) -Name $e.Name -Url $e.Url
}

# -------------------------------------------------
# Audit execution safety check
# -------------------------------------------------
Write-Host "[audit execution safety]" -ForegroundColor Cyan

$auditPath = Join-Path $PSScriptRoot "audit.jsonl"

if (-not (Test-Path $auditPath)) {
    $Results += [pscustomobject]@{
        name   = "audit_execution"
        result = "WARN"
        note   = "audit.jsonl not found"
    }
}
else {
    $lines = Get-Content $auditPath -ErrorAction SilentlyContinue

        $executed = @($lines | Where-Object { $_ -match '"executed"\s*:\s*1' })
        if ($executed.Count -gt 0) {

        $Results += [pscustomobject]@{
            name   = "audit_execution"
            result = "FAIL"
            note   = "executed=1 detected"
        }
    }
    else {
        $blocked = @($lines | Where-Object { $_ -match 'EXECUTE_BLOCKED' })
        if ($blocked.Count -gt 0) {

            $Results += [pscustomobject]@{
                name   = "audit_execution"
                result = "PASS"
                note   = "execution blocked as designed"
            }
        }
        else {
            $Results += [pscustomobject]@{
                name   = "audit_execution"
                result = "WARN"
                note   = "no execution attempt recorded"
            }
        }
    }
}

# Summary
Write-Host ""
Write-Host "=== OPS CHECK SUMMARY ===" -ForegroundColor Cyan

$pass = ($Results | Where-Object { $_.result -eq "PASS" } | Measure-Object).Count
$warn = ($Results | Where-Object { $_.result -eq "WARN" } | Measure-Object).Count
$fail = ($Results | Where-Object { $_.result -eq "FAIL" } | Measure-Object).Count
$skip = ($Results | Where-Object { $_.result -eq "SKIP" } | Measure-Object).Count

$final = if ($fail -gt 0) { "FAILED" } elseif ($warn -gt 0) { "DEGRADED" } else { "SYSTEM_OK" }

Write-Host ("PASS={0} WARN={1} FAIL={2} SKIP={3} FINAL={4}" -f $pass,$warn,$fail,$skip,$final)

Write-Host ("ONE_LINE_SUMMARY ts={0} pass={1} warn={2} fail={3} skip={4} final={5}" -f (Get-NowStamp),$pass,$warn,$fail,$skip,$final)

Write-Host ""
Write-Host "[ops_check finished]" -ForegroundColor Green
Write-Host "Press Enter to exit:" -ForegroundColor DarkGray
Read-Host | Out-Null
