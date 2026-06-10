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
    try {
        mineru --help | Out-Host
        return $LASTEXITCODE -eq 0
    }
    catch {
        Write-Host "mineru --help failed: $($_.Exception.Message)"
        return $false
    }
}

function Get-CondaExe {
    if ($env:CONDA_EXE -and (Test-Path -LiteralPath $env:CONDA_EXE)) {
        return $env:CONDA_EXE
    }
    $condaExe = (Get-Command conda.exe -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Source)
    if ($condaExe) {
        return $condaExe
    }
    throw "conda.exe not found"
}

Write-Section "Conda Env Guard"
if ($env:CONDA_DEFAULT_ENV -ne $ExpectedEnv) {
    Write-Host "FAIL: current env is '$($env:CONDA_DEFAULT_ENV)'."
    Write-Host "Please run:"
    Write-Host "  conda activate $ExpectedEnv"
    exit 1
}
Write-Host "current env = $($env:CONDA_DEFAULT_ENV)"

Write-Section "Session Guards"
$env:PYTHONNOUSERSITE = "1"
$env:PIP_USER = "0"
Write-Host "PYTHONNOUSERSITE = $env:PYTHONNOUSERSITE"
Write-Host "PIP_USER = $env:PIP_USER"

Write-Section "Python And Pip"
python -c "import sys; print(sys.executable)"
python -m pip --version

Write-Section "Pip Config"
python -m pip config list

Write-Section "Dependency Repair"
python -m pip install --force-reinstall --no-cache-dir requests "urllib3<3" certifi idna charset-normalizer sniffio "huggingface_hub==0.36.2"

Write-Section "Environment Purity Check"
$purity = Run-PythonJson -Code @"
import json
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
}

import requests
import urllib3
import certifi
import huggingface_hub

payload["requests_path"] = requests.__file__
payload["urllib3_path"] = urllib3.__file__
payload["certifi_path"] = certifi.where()
payload["hf_version"] = huggingface_hub.__version__
payload["hf_path"] = huggingface_hub.__file__

print(json.dumps(payload, ensure_ascii=False))
"@

Write-Host "python = $($purity.python_path)"
Write-Host "ENABLE_USER_SITE = $($purity.enable_user_site)"
Write-Host "requests = $($purity.requests_path)"
Write-Host "urllib3 = $($purity.urllib3_path)"
Write-Host "certifi = $($purity.certifi_path)"
Write-Host "hf = $($purity.hf_version)"
Write-Host "hf path = $($purity.hf_path)"

$polluted = @(
    $purity.requests_path,
    $purity.urllib3_path,
    $purity.certifi_path,
    $purity.hf_path
) | Where-Object { $_ -like "*$PollutionMarker*" }

if ($polluted.Count -gt 0) {
    Write-Host "FAIL: conda env is still polluted by user site-packages."
    Write-Host "Keep PYTHONNOUSERSITE=1 and rerun this repair script."
    exit 1
}

Write-Section "Certificate Env"
$cert = (python -c "import certifi; print(certifi.where())").Trim()
$env:REQUESTS_CA_BUNDLE = $cert
$env:SSL_CERT_FILE = $cert
Write-Host "REQUESTS_CA_BUNDLE = $env:REQUESTS_CA_BUNDLE"
Write-Host "SSL_CERT_FILE = $env:SSL_CERT_FILE"

Write-Section "Official HuggingFace API Test"
$official = Test-HfUrl -Url $OfficialUrl
Write-Host "official ok = $($official.ok)"
Write-Host "official status_code = $($official.status_code)"
Write-Host "official error_type = $($official.error_type)"
Write-Host "official error_message = $($official.error_message)"
Write-Host "official excerpt = $($official.excerpt)"

$useMirror = $false
if (-not $official.ok) {
    Write-Section "HF Mirror API Test"
    $env:HF_ENDPOINT = $MirrorBase
    $mirror = Test-HfUrl -Url $MirrorUrl -EndpointValue $MirrorBase
    Write-Host "mirror ok = $($mirror.ok)"
    Write-Host "mirror status_code = $($mirror.status_code)"
    Write-Host "mirror error_type = $($mirror.error_type)"
    Write-Host "mirror error_message = $($mirror.error_message)"
    Write-Host "mirror excerpt = $($mirror.excerpt)"
    if ($mirror.ok) {
        $useMirror = $true
    }
}

Write-Section "Persist Safe Env Vars"
$condaExe = Get-CondaExe
& $condaExe env config vars set -n $ExpectedEnv PYTHONNOUSERSITE=1
& $condaExe env config vars set -n $ExpectedEnv REQUESTS_CA_BUNDLE="$cert" SSL_CERT_FILE="$cert"
if ($useMirror) {
    & $condaExe env config vars set -n $ExpectedEnv HF_ENDPOINT=https://hf-mirror.com
}

Write-Section "MinerU Help"
$mineruHelpOk = Test-MineruHelp
Write-Host "mineru_help_ok = $mineruHelpOk"

Write-Section "Next Step"
Write-Host "Please re-activate the environment:"
Write-Host "  conda deactivate"
Write-Host "  conda activate $ExpectedEnv"
Write-Host ""
Write-Host "Then run:"
Write-Host "  mineru -p E:\mineru_lab\input -o E:\mineru_lab\output_new -b pipeline --formula false --table true"
