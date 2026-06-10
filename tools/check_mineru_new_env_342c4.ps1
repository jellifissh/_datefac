$ErrorActionPreference = "Stop"

$ExpectedEnv = "mineru_new"
$PollutionMarker = "AppData\Roaming\Python\Python312\site-packages"
$OfficialUrl = "https://huggingface.co/api/models/opendatalab/PDF-Extract-Kit-1.0"
$MirrorBase = "https://hf-mirror.com"
$MirrorUrl = "$MirrorBase/api/models/opendatalab/PDF-Extract-Kit-1.0"

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host "=== $Title ==="
}

function Mask-ProxyValue {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) {
        return ""
    }
    try {
        $uri = [System.Uri]$Value
        return "{0}://{1}:{2}" -f $uri.Scheme, $uri.Host, $uri.Port
    }
    catch {
        if ($Value.Length -le 24) {
            return $Value
        }
        return $Value.Substring(0, 24) + "...masked"
    }
}

function Run-PythonJson {
    param([string]$Code)
    $tmp = [System.IO.Path]::GetTempFileName() + ".py"
    try {
        Set-Content -LiteralPath $tmp -Value $Code -Encoding UTF8
        $output = python $tmp
        if ($LASTEXITCODE -ne 0) {
            throw "python command failed"
        }
        return ($output | Out-String | ConvertFrom-Json)
    }
    finally {
        if (Test-Path -LiteralPath $tmp) {
            Remove-Item -LiteralPath $tmp -Force
        }
    }
}

function Test-HfUrl {
    param(
        [string]$Url,
        [string]$EndpointValue = ""
    )
    $code = @"
import json
import os
import requests

endpoint = r'''$EndpointValue'''
url = r'''$Url'''
if endpoint:
    os.environ["HF_ENDPOINT"] = endpoint
    url = endpoint.rstrip("/") + "/api/models/opendatalab/PDF-Extract-Kit-1.0"

payload = {
    "url": url,
    "ok": False,
    "status_code": None,
    "error_type": "",
    "error_message": "",
    "excerpt": "",
}

try:
    response = requests.get(url, timeout=20)
    payload["ok"] = True
    payload["status_code"] = response.status_code
    payload["excerpt"] = response.text[:160]
except Exception as exc:
    payload["error_type"] = type(exc).__name__
    payload["error_message"] = str(exc)

print(json.dumps(payload, ensure_ascii=False))
"@
    return Run-PythonJson -Code $code
}

function Test-MineruHelp {
    $result = @{
        ok = $false
        error = ""
    }
    try {
        $null = mineru --help 2>&1
        if ($LASTEXITCODE -eq 0) {
            $result.ok = $true
        }
        else {
            $result.error = "mineru --help returned exit code $LASTEXITCODE"
        }
    }
    catch {
        $result.error = $_.Exception.Message
    }
    return $result
}

Write-Section "Current Conda Env"
$currentEnv = $env:CONDA_DEFAULT_ENV
Write-Host "CONDA_DEFAULT_ENV = $currentEnv"
if ($currentEnv -ne $ExpectedEnv) {
    Write-Host "WARNING: current env is not $ExpectedEnv"
}

Write-Section "Python Package Provenance"
$pythonInfo = Run-PythonJson -Code @"
import json
import os
import site
import sys

payload = {
    "python_path": sys.executable,
    "enable_user_site": site.ENABLE_USER_SITE,
    "requests_path": "",
    "urllib3_path": "",
    "certifi_path": "",
    "hf_version": "",
    "hf_path": "",
    "pip_path": "",
    "requests_import_error": "",
    "urllib3_import_error": "",
    "certifi_import_error": "",
    "hf_import_error": "",
}

try:
    import requests
    payload["requests_path"] = requests.__file__
except Exception as exc:
    payload["requests_import_error"] = str(exc)

try:
    import urllib3
    payload["urllib3_path"] = urllib3.__file__
except Exception as exc:
    payload["urllib3_import_error"] = str(exc)

try:
    import certifi
    payload["certifi_path"] = certifi.where()
except Exception as exc:
    payload["certifi_import_error"] = str(exc)

try:
    import huggingface_hub
    payload["hf_version"] = huggingface_hub.__version__
    payload["hf_path"] = huggingface_hub.__file__
except Exception as exc:
    payload["hf_import_error"] = str(exc)

try:
    import pip
    payload["pip_path"] = pip.__file__
except Exception:
    pass

print(json.dumps(payload, ensure_ascii=False))
"@

Write-Host "python path = $($pythonInfo.python_path)"
Write-Host "pip path = $($pythonInfo.pip_path)"
Write-Host "ENABLE_USER_SITE = $($pythonInfo.enable_user_site)"
Write-Host "requests path = $($pythonInfo.requests_path)"
Write-Host "urllib3 path = $($pythonInfo.urllib3_path)"
Write-Host "certifi path = $($pythonInfo.certifi_path)"
Write-Host "huggingface_hub version = $($pythonInfo.hf_version)"
Write-Host "huggingface_hub path = $($pythonInfo.hf_path)"

if ($pythonInfo.requests_import_error) { Write-Host "requests import error = $($pythonInfo.requests_import_error)" }
if ($pythonInfo.urllib3_import_error) { Write-Host "urllib3 import error = $($pythonInfo.urllib3_import_error)" }
if ($pythonInfo.certifi_import_error) { Write-Host "certifi import error = $($pythonInfo.certifi_import_error)" }
if ($pythonInfo.hf_import_error) { Write-Host "huggingface_hub import error = $($pythonInfo.hf_import_error)" }

Write-Section "SSL And Endpoint Env"
Write-Host "REQUESTS_CA_BUNDLE = $env:REQUESTS_CA_BUNDLE"
Write-Host "SSL_CERT_FILE = $env:SSL_CERT_FILE"
Write-Host "HF_ENDPOINT = $env:HF_ENDPOINT"
Write-Host "HTTP_PROXY = $(Mask-ProxyValue $env:HTTP_PROXY)"
Write-Host "HTTPS_PROXY = $(Mask-ProxyValue $env:HTTPS_PROXY)"
Write-Host "ALL_PROXY = $(Mask-ProxyValue $env:ALL_PROXY)"

Write-Section "HuggingFace Official API Test"
$official = Test-HfUrl -Url $OfficialUrl
Write-Host "official ok = $($official.ok)"
Write-Host "official status_code = $($official.status_code)"
Write-Host "official error_type = $($official.error_type)"
Write-Host "official error_message = $($official.error_message)"
Write-Host "official excerpt = $($official.excerpt)"

Write-Section "HF Mirror API Test"
$mirror = Test-HfUrl -Url $MirrorUrl -EndpointValue $MirrorBase
Write-Host "mirror ok = $($mirror.ok)"
Write-Host "mirror status_code = $($mirror.status_code)"
Write-Host "mirror error_type = $($mirror.error_type)"
Write-Host "mirror error_message = $($mirror.error_message)"
Write-Host "mirror excerpt = $($mirror.excerpt)"

Write-Section "MinerU Help Check"
$mineruHelp = Test-MineruHelp
Write-Host "mineru_help_ok = $($mineruHelp.ok)"
Write-Host "mineru_help_error = $($mineruHelp.error)"

Write-Section "Suggestions"
$hasPollution = @(
    $pythonInfo.requests_path,
    $pythonInfo.urllib3_path,
    $pythonInfo.certifi_path,
    $pythonInfo.hf_path
) | Where-Object { $_ -and $_ -like "*$PollutionMarker*" }

if ($hasPollution.Count -gt 0) {
    Write-Host "SUGGESTION: user site-packages pollution detected. Run tools\\repair_mineru_new_env_342c4.ps1 after activating mineru_new."
}
if ($pythonInfo.urllib3_import_error -or [string]::IsNullOrWhiteSpace($pythonInfo.urllib3_path)) {
    Write-Host "SUGGESTION: urllib3 is missing or not importable. Run the repair script."
}
if ($pythonInfo.hf_version -and $pythonInfo.hf_version -match '^[1-9]\.') {
    Write-Host "SUGGESTION: huggingface_hub is >= 1.0. Downgrade to 0.36.2 with the repair script."
}
if (-not $official.ok -and $mirror.ok) {
    Write-Host "SUGGESTION: official HuggingFace failed but mirror succeeded. Persist HF_ENDPOINT to https://hf-mirror.com."
}
if (-not $official.ok -and -not $mirror.ok) {
    Write-Host "SUGGESTION: both official and mirror endpoints failed. Check HTTPS_PROXY / HTTP_PROXY and certificate trust chain."
}
if (-not $mineruHelp.ok) {
    Write-Host "SUGGESTION: mineru --help failed. Re-activate mineru_new and rerun the repair script."
}
