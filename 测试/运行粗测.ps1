$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$frontendDir = Join-Path $projectRoot 'frontend'
$adminSmokeScript = Join-Path $PSScriptRoot 'smoke_admin_health_records.py'

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Action
    )

    Write-Host ""
    Write-Host "==> $Name" -ForegroundColor Cyan
    & $Action
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed: $Name"
    }
}

if (-not (Test-Path $python)) {
    throw "Python virtualenv not found: $python"
}

Push-Location $projectRoot
try {
    Invoke-Step "Backend syntax check" {
        & $python -m py_compile `
            backend\app\features\health_data\router.py `
            backend\app\features\admin\router.py `
            backend\app\features\admin\service.py `
            backend\app\schemas.py
    }

    Invoke-Step "Backend smoke tests" {
        & $python -m unittest `
            backend.tests.p0.test_auth_p0 `
            backend.tests.p0.test_ai_admin_rag_p0 `
            backend.tests.p0.test_import_cache_resilience_p0 `
            backend.tests.p0.test_profile_health_p0.ProfileAndHealthP0Tests.test_pdf_record_can_be_public_and_visible_in_public_feed `
            backend.tests.p0.test_profile_health_p0.ProfileAndHealthP0Tests.test_private_profile_requires_original_private_key_and_public_profile_is_shareable
    }

    Invoke-Step "Admin health-record summary smoke test" {
        & $python $adminSmokeScript
    }

    Push-Location $frontendDir
    try {
        Invoke-Step "Frontend build check" {
            & npm.cmd run build
        }
    }
    finally {
        Pop-Location
    }

    Write-Host ""
    Write-Host "Smoke tests completed successfully." -ForegroundColor Green
}
finally {
    Pop-Location
}
