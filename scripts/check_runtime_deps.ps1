param(
  [switch]$AutoStart,
  [int]$TimeoutSeconds = 25,
  [string]$GanacheHost = "127.0.0.1",
  [int]$GanachePort = 8545,
  [int]$OllamaPort = 11434
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Test-TcpPort {
  param(
    [Parameter(Mandatory = $true)][string]$TargetHost,
    [Parameter(Mandatory = $true)][int]$Port
  )
  $client = New-Object System.Net.Sockets.TcpClient
  try {
    $iar = $client.BeginConnect($TargetHost, $Port, $null, $null)
    $ok = $iar.AsyncWaitHandle.WaitOne(600)
    if (-not $ok) { return $false }
    $client.EndConnect($iar) | Out-Null
    return $true
  } catch {
    return $false
  } finally {
    $client.Close()
  }
}

function Wait-Port {
  param(
    [string]$TargetHost,
    [int]$Port,
    [int]$Seconds
  )
  $deadline = (Get-Date).AddSeconds($Seconds)
  while ((Get-Date) -lt $deadline) {
    if (Test-TcpPort -TargetHost $TargetHost -Port $Port) {
      return $true
    }
    Start-Sleep -Milliseconds 500
  }
  return $false
}

function Has-Command {
  param([string]$Name)
  return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Start-OllamaIfNeeded {
  if (Test-TcpPort -TargetHost "127.0.0.1" -Port $OllamaPort) {
    Write-Host "[OK] Ollama is running on 127.0.0.1:$OllamaPort"
    return $true
  }

  Write-Host "[WARN] Ollama is not reachable on 127.0.0.1:$OllamaPort"
  if (-not $AutoStart) {
    return $false
  }
  if (-not (Has-Command "ollama")) {
    Write-Host "[ERROR] ollama command not found in PATH."
    return $false
  }

  Write-Host "[INFO] Starting Ollama service..."
  Start-Process -FilePath "ollama" -ArgumentList @("serve") -WindowStyle Hidden | Out-Null
  if (Wait-Port -TargetHost "127.0.0.1" -Port $OllamaPort -Seconds $TimeoutSeconds) {
    Write-Host "[OK] Ollama started."
    return $true
  }
  Write-Host "[ERROR] Ollama failed to start within timeout."
  return $false
}

function Start-GanacheIfNeeded {
  if (Test-TcpPort -TargetHost $GanacheHost -Port $GanachePort) {
    Write-Host "[OK] Ganache RPC is running on $GanacheHost`:$GanachePort"
    return $true
  }

  Write-Host "[WARN] Ganache RPC is not reachable on $GanacheHost`:$GanachePort"
  if (-not $AutoStart) {
    return $false
  }

  $ganacheCmd = $null
  if (Has-Command "ganache") {
    $ganacheCmd = "ganache"
  } elseif (Has-Command "ganache-cli") {
    $ganacheCmd = "ganache-cli"
  } elseif (Has-Command "npx") {
    $ganacheCmd = "npx"
  } else {
    Write-Host "[ERROR] ganache/ganache-cli/npx not found in PATH."
    return $false
  }

  Write-Host "[INFO] Starting Ganache..."
  if ($ganacheCmd -eq "npx") {
    Start-Process -FilePath "npx" -ArgumentList @("ganache", "-h", $GanacheHost, "-p", "$GanachePort") -WindowStyle Hidden | Out-Null
  } else {
    Start-Process -FilePath $ganacheCmd -ArgumentList @("-h", $GanacheHost, "-p", "$GanachePort") -WindowStyle Hidden | Out-Null
  }

  if (Wait-Port -TargetHost $GanacheHost -Port $GanachePort -Seconds $TimeoutSeconds) {
    Write-Host "[OK] Ganache started."
    return $true
  }
  Write-Host "[ERROR] Ganache failed to start within timeout."
  return $false
}

$ollamaOk = Start-OllamaIfNeeded
$ganacheOk = Start-GanacheIfNeeded

if ($ollamaOk -and $ganacheOk) {
  Write-Host "[DONE] Runtime dependencies are ready."
  exit 0
}

Write-Host "[FAIL] Some runtime dependencies are not ready."
if (-not $ollamaOk) { Write-Host "  - Ollama: expected 127.0.0.1:$OllamaPort" }
if (-not $ganacheOk) { Write-Host "  - Ganache: expected $GanacheHost`:$GanachePort" }
exit 1
