param(
  [Parameter(Mandatory = $true)]
  [string]$Url,

  [int]$TimeoutSeconds = 30,
  [int]$IntervalMs = 700
)

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)

while ((Get-Date) -lt $deadline) {
  try {
    $resp = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 3
    if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) {
      Write-Output "OK"
      exit 0
    }
  } catch {
  }

  Start-Sleep -Milliseconds $IntervalMs
}

Write-Output "TIMEOUT"
exit 1
