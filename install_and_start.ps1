$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $ProjectRoot

$LogsDir = Join-Path $ProjectRoot "logs"
$RuntimeDir = Join-Path $ProjectRoot ".runtime"
$SettingsPath = Join-Path $RuntimeDir "launcher_settings.json"
$InstallLog = Join-Path $LogsDir "install.log"
$StartupLog = Join-Path $LogsDir "startup.log"

New-Item -ItemType Directory -Force -Path $LogsDir | Out-Null
New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null

$env:PYTHONUTF8 = "1"
$env:CHEM_PDF_EXTRACTOR_LOG_DIR = $LogsDir

function Write-LauncherLog {
  param(
    [string]$Message,
    [string]$LogPath = $InstallLog
  )
  $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  Add-Content -LiteralPath $LogPath -Encoding UTF8 -Value "[$timestamp] $Message"
}

function Write-Step {
  param([string]$Message)
  Write-Host $Message
  Write-LauncherLog $Message
}

function Invoke-LoggedCommand {
  param(
    [string]$FilePath,
    [string[]]$Arguments,
    [string]$LogPath = $InstallLog,
    [string]$FailureHint = ""
  )
  $display = "$FilePath $($Arguments -join ' ')"
  Write-LauncherLog "Running: $display" $LogPath
  & $FilePath @Arguments 2>&1 | Tee-Object -FilePath $LogPath -Append
  $exitCode = $LASTEXITCODE
  Write-LauncherLog "Exit code: $exitCode" $LogPath
  if ($exitCode -ne 0) {
    $message = "Command failed: $display"
    if ($FailureHint) {
      $message = "$message`n$FailureHint"
    }
    throw $message
  }
}

function Test-Python311 {
  param([string]$PythonExe)
  try {
    $version = & $PythonExe -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
    return ($version -eq "3.11")
  } catch {
    return $false
  }
}

function Resolve-PythonCommand {
  param([string]$PythonExe)
  if ([string]::IsNullOrWhiteSpace($PythonExe)) {
    return $null
  }
  if (Test-Path -LiteralPath $PythonExe) {
    return (Resolve-Path -LiteralPath $PythonExe).Path
  }
  $command = Get-Command $PythonExe -ErrorAction SilentlyContinue
  if ($command) {
    return $command.Source
  }
  return $null
}

function Find-SystemPython311 {
  $pyLauncher = Get-Command "py.exe" -ErrorAction SilentlyContinue
  if ($pyLauncher) {
    try {
      $version = & $pyLauncher.Source -3.11 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
      if ($version -eq "3.11") {
        return @{ File = $pyLauncher.Source; Args = @("-3.11") }
      }
    } catch {}
  }

  foreach ($candidate in @("python3.11.exe", "python.exe")) {
    $resolved = Resolve-PythonCommand $candidate
    if ($resolved -and (Test-Python311 $resolved)) {
      return @{ File = $resolved; Args = @() }
    }
  }

  return $null
}

function Invoke-PythonCommand {
  param(
    [hashtable]$PythonCommand,
    [string[]]$Arguments,
    [string]$LogPath = $InstallLog,
    [string]$FailureHint = ""
  )
  $allArgs = @()
  if ($PythonCommand.Args) {
    $allArgs += $PythonCommand.Args
  }
  $allArgs += $Arguments
  Invoke-LoggedCommand -FilePath $PythonCommand.File -Arguments $allArgs -LogPath $LogPath -FailureHint $FailureHint
}

function Ensure-Python311ForVenv {
  $python = Find-SystemPython311
  if ($python) {
    Write-Step "Found Python 3.11 for virtual environment: $($python.File) $($python.Args -join ' ')"
    return $python
  }

  Write-Step "Python 3.11 was not found. Attempting installation with winget..."
  $winget = Get-Command "winget.exe" -ErrorAction SilentlyContinue
  if ($winget) {
    try {
      Invoke-LoggedCommand -FilePath $winget.Source -Arguments @("install", "-e", "--id", "Python.Python.3.11") -FailureHint "Python 3.11 installation through winget failed. You can install Python 3.11 manually and rerun the launcher."
    } catch {
      Write-LauncherLog "winget Python installation failed: $($_.Exception.Message)"
      Write-Host "winget could not install Python 3.11 automatically."
    }
  } else {
    Write-LauncherLog "winget.exe not found"
    Write-Host "winget was not found."
  }

  $python = Find-SystemPython311
  if ($python) {
    Write-Step "Python 3.11 is now available: $($python.File) $($python.Args -join ' ')"
    return $python
  }

  throw "Python 3.11 could not be found. Please install Python 3.11 manually from https://www.python.org/downloads/windows/ and rerun Start-Chem-PDF-Extractor.bat."
}

function Get-ExistingRuntimePython {
  $candidates = @(
    (Join-Path $ProjectRoot "bundled_runtime\python\python.exe"),
    (Join-Path $ProjectRoot ".venv\Scripts\python.exe"),
    (Join-Path $ProjectRoot "YiLaiHuanJing\python\python.exe"),
    (Join-Path $ProjectRoot "杩愯渚濊禆\python\python.exe")
  )

  foreach ($candidate in $candidates) {
    if (Test-Path -LiteralPath $candidate) {
      return (Resolve-Path -LiteralPath $candidate).Path
    }
  }
  return $null
}

function Ensure-ProjectPython {
  $existing = Get-ExistingRuntimePython
  if ($existing) {
    Write-Step "Using existing project Python: $existing"
    return $existing
  }

  $venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
  $venvDir = Join-Path $ProjectRoot ".venv"
  if (-not (Test-Path -LiteralPath $venvPython)) {
    $python311 = Ensure-Python311ForVenv
    Write-Step "Creating project virtual environment: $venvDir"
    Invoke-PythonCommand -PythonCommand $python311 -Arguments @("-m", "venv", $venvDir) -FailureHint "Failed to create .venv. Check logs/install.log and verify that Python 3.11 includes venv support."
  }

  if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "Virtual environment was created but .venv\Scripts\python.exe was not found."
  }
  Write-Step "Using project virtual environment Python: $venvPython"
  return (Resolve-Path -LiteralPath $venvPython).Path
}

function Get-PreviousBackend {
  if (-not (Test-Path -LiteralPath $SettingsPath)) {
    return ""
  }
  try {
    $settings = Get-Content -LiteralPath $SettingsPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $backend = [string]$settings.pdf_backend
    if ($backend -in @("pypdf_text", "pymupdf4llm", "mineru")) {
      return $backend
    }
  } catch {
    Write-LauncherLog "Failed to read previous launcher settings: $($_.Exception.Message)"
  }
  return ""
}

function Save-BackendChoice {
  param([string]$Backend)
  $payload = [ordered]@{
    pdf_backend = $Backend
    updated_at = (Get-Date).ToString("o")
  }
  $payload | ConvertTo-Json | Set-Content -LiteralPath $SettingsPath -Encoding UTF8
  Write-LauncherLog "Saved backend choice: $Backend"
}

function Select-PdfBackend {
  $previous = Get-PreviousBackend
  Write-LauncherLog "Previous backend setting: $previous"

  while ($true) {
    Write-Host ""
    Write-Host "Please choose a PDF parsing backend:"
    Write-Host ""
    Write-Host "[1] pypdf_text"
    Write-Host "Lightweight mode | smallest install size | fastest install | best compatibility"
    Write-Host "Suitable for text-based PDFs."
    Write-Host "Weakness: weaker layout, table, and multi-column handling."
    Write-Host ""
    Write-Host "[2] pymupdf4llm (recommended)"
    Write-Host "Standard mode | medium install size | good speed | suitable for most research PDFs."
    Write-Host "This remains the default if the user presses Enter."
    Write-Host ""
    Write-Host "[3] mineru"
    Write-Host "Enhanced mode | large install size | slow first-time installation."
    Write-Host "Suitable for complex layouts, tables, scanned PDFs, and high-performance PCs."
    Write-Host "Warning: requires more disk space, memory, installation time, and may download large dependencies or models."
    Write-Host ""
    if ($previous) {
      Write-Host "Previous backend choice: $previous"
      $choice = Read-Host "Enter 1, 2, or 3. Press Enter to reuse previous choice"
      if ([string]::IsNullOrWhiteSpace($choice)) {
        Save-BackendChoice $previous
        return $previous
      }
    } else {
      $choice = Read-Host "Enter 1, 2, or 3. Press Enter for option 2"
      if ([string]::IsNullOrWhiteSpace($choice)) {
        Save-BackendChoice "pymupdf4llm"
        return "pymupdf4llm"
      }
    }

    switch ($choice.Trim()) {
      "1" { Save-BackendChoice "pypdf_text"; return "pypdf_text" }
      "2" { Save-BackendChoice "pymupdf4llm"; return "pymupdf4llm" }
      "3" { Save-BackendChoice "mineru"; return "mineru" }
      default {
        Write-Host "Invalid input. Please enter 1, 2, 3, or press Enter."
      }
    }
  }
}

function Install-Requirements {
  param(
    [string]$PythonExe,
    [string]$RequirementsFile
  )
  if (-not (Test-Path -LiteralPath $RequirementsFile)) {
    throw "Requirements file not found: $RequirementsFile"
  }
  Write-Step "Installing dependencies from $RequirementsFile"
  Invoke-LoggedCommand -FilePath $PythonExe -Arguments @("-m", "pip", "install", "--upgrade", "pip") -FailureHint "pip upgrade failed. You can retry safely."
  Invoke-LoggedCommand -FilePath $PythonExe -Arguments @("-m", "pip", "install", "-r", $RequirementsFile) -FailureHint "Dependency installation failed. Check logs/install.log. You can retry safely."
  Write-Step "Finished installing dependencies from $RequirementsFile"
}

function Install-MinerU {
  param([string]$PythonExe)
  $mineruRequirements = Join-Path $ProjectRoot "requirements-mineru.txt"
  if (-not (Test-Path -LiteralPath $mineruRequirements)) {
    throw "requirements-mineru.txt was not found."
  }

  Write-Step "Installing optional MinerU backend. This may take a long time and may download large files."
  try {
    Write-LauncherLog "MinerU installation start"
    Invoke-LoggedCommand -FilePath $PythonExe -Arguments @("-m", "pip", "install", "--upgrade", "uv") -FailureHint "Failed to install uv for MinerU."
    $uvExe = Join-Path (Split-Path -Parent $PythonExe) "uv.exe"
    if (-not (Test-Path -LiteralPath $uvExe)) {
      $uvCommand = Get-Command "uv.exe" -ErrorAction SilentlyContinue
      if ($uvCommand) {
        $uvExe = $uvCommand.Source
      }
    }
    if (-not (Test-Path -LiteralPath $uvExe)) {
      throw "uv was installed but uv.exe was not found."
    }
    Invoke-LoggedCommand -FilePath $uvExe -Arguments @("pip", "install", "--python", $PythonExe, "-r", $mineruRequirements) -FailureHint "MinerU installation failed. Try rerunning the launcher and selecting option 2, pymupdf4llm, instead."
    Write-LauncherLog "MinerU installation finished"
    Write-Step "MinerU backend installation finished."
  } catch {
    Write-LauncherLog "MinerU installation failed: $($_.Exception.Message)"
    throw "MinerU installation failed. Check logs/install.log. You can retry safely, or rerun the launcher and choose option 2, pymupdf4llm, instead.`n$($_.Exception.Message)"
  }
}

function Install-DependenciesForBackend {
  param(
    [string]$PythonExe,
    [string]$Backend
  )
  switch ($Backend) {
    "pypdf_text" {
      Install-Requirements -PythonExe $PythonExe -RequirementsFile (Join-Path $ProjectRoot "requirements-core.txt")
    }
    "pymupdf4llm" {
      Install-Requirements -PythonExe $PythonExe -RequirementsFile (Join-Path $ProjectRoot "requirements.txt")
    }
    "mineru" {
      Install-Requirements -PythonExe $PythonExe -RequirementsFile (Join-Path $ProjectRoot "requirements.txt")
      Install-MinerU -PythonExe $PythonExe
    }
    default {
      throw "Unknown backend selected: $Backend"
    }
  }
}

try {
  Write-LauncherLog "===== Windows first-run launcher started =====" $StartupLog
  Write-LauncherLog "project_root: $ProjectRoot" $StartupLog
  Write-LauncherLog "logs_dir: $LogsDir" $StartupLog

  $backend = Select-PdfBackend
  Write-Step "Selected PDF backend: $backend"
  $pythonExe = Ensure-ProjectPython
  Write-Step "Project Python: $pythonExe"

  Install-DependenciesForBackend -PythonExe $pythonExe -Backend $backend

  $url = "http://127.0.0.1:8766/"
  $startupArgs = @("-m", "chem_pdf_extractor", "--pdf-mode", $backend, "--open-browser")
  Write-LauncherLog "App startup command: $pythonExe $($startupArgs -join ' ')" $StartupLog
  Write-Host ""
  Write-Host "Starting Chem-PDF-Extractor local web app..."
  Write-Host "Local URL: $url"
  Write-Host "The browser should open automatically. If it does not, copy the URL above."
  Write-Host "Keep this PowerShell window open while the server is running."
  Write-Host "Press Ctrl+C to stop the server."
  Write-Host ""

  & $pythonExe @startupArgs 2>&1 | Tee-Object -FilePath $StartupLog -Append
  $exitCode = $LASTEXITCODE
  Write-LauncherLog "App process exited with code: $exitCode" $StartupLog
  exit $exitCode
} catch {
  Write-LauncherLog "Launcher error: $($_.Exception.Message)" $StartupLog
  Write-Host ""
  Write-Host "Chem-PDF-Extractor launcher failed."
  Write-Host $_.Exception.Message
  Write-Host ""
  Write-Host "Logs:"
  Write-Host "  $InstallLog"
  Write-Host "  $StartupLog"
  Write-Host ""
  Write-Host "Suggested fallback: rerun Start-Chem-PDF-Extractor.bat and choose option 2, pymupdf4llm."
  Write-Host "You can retry safely after fixing the issue."
  exit 1
}
