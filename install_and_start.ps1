param(
  [ValidateSet("en", "zh")]
  [string]$Language = "en",
  [string]$UserRoot = ""
)

$ErrorActionPreference = "Stop"

try {
  $utf8NoBom = New-Object System.Text.UTF8Encoding $false
  [Console]::OutputEncoding = $utf8NoBom
  [Console]::InputEncoding = $utf8NoBom
  $OutputEncoding = $utf8NoBom
} catch {
  # Console encoding setup is best-effort only.
}

$AppRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($UserRoot)) {
  if ((Split-Path -Leaf $AppRoot) -ieq "app") {
    $UserRoot = Split-Path -Parent $AppRoot
  } else {
    $UserRoot = $AppRoot
  }
}
$UserRoot = [System.IO.Path]::GetFullPath($UserRoot)
Set-Location -LiteralPath $AppRoot

$InputDir = Join-Path $UserRoot "input_pdfs"
$OutputDir = Join-Path $UserRoot "提取结果"
$LogsDir = Join-Path $UserRoot "logs"
$RuntimeDir = Join-Path $UserRoot ".runtime"
$SettingsPath = Join-Path $RuntimeDir "launcher_settings.json"
$InstallLog = Join-Path $LogsDir "install.log"
$StartupLog = Join-Path $LogsDir "startup.log"

New-Item -ItemType Directory -Force -Path $LogsDir | Out-Null
New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null
New-Item -ItemType Directory -Force -Path $InputDir | Out-Null
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:CHEM_PDF_EXTRACTOR_USER_ROOT = $UserRoot
$env:CHEM_PDF_EXTRACTOR_LOG_DIR = $LogsDir

$Messages = @{
  en = @{
    ChooseBackend = "Please choose a PDF parsing backend:"
    PypdfDesc = "Lightweight mode | smallest install size | fastest install | best compatibility"
    PypdfSuitable = "Suitable for text-based PDFs."
    PypdfWeakness = "Weakness: weaker layout, table, and multi-column handling."
    PymupdfDesc = "Balanced fallback | medium install size | good speed | suitable for many research PDFs."
    PymupdfFallback = "Use this if you want a lighter install than MinerU."
    MineruDesc = "Enhanced default mode | large install size | slower first-time installation."
    MineruSuitable = "Suitable for complex layouts, tables, scanned PDFs, and high-performance PCs."
    MineruWarning = "Warning: requires more disk space, memory, installation time, and may download large dependencies or models."
    MineruDefault = "This is the v0.4.0 default backend if the user presses Enter."
    PreviousBackend = "Previous backend choice:"
    EnterReuse = "Enter 1, 2, or 3. Press Enter to reuse previous choice"
    EnterDefault = "Enter 1, 2, or 3. Press Enter for option 3"
    InvalidChoice = "Invalid input. Please enter 1, 2, 3, or press Enter."
    MineruFailed = "MinerU installation did not complete successfully."
    Reason = "Reason:"
    RetryMineru = "[1] Retry MinerU installation"
    ContinuePymupdf = "[2] Continue now with pymupdf4llm"
    Exit = "[3] Exit"
    Enter123 = "Enter 1, 2, or 3"
    StartingApp = "Starting Chem-PDF-Extractor local web app..."
    LocalUrl = "Local URL:"
    BrowserHint = "The browser should open automatically. If it does not, copy the URL above."
    KeepWindowOpen = "Keep this PowerShell window open while the server is running."
    StopHint = "Press Ctrl+C to stop the server."
    LauncherFailed = "Chem-PDF-Extractor launcher failed."
    Logs = "Logs:"
    Fallback = "Suggested fallback: rerun Start-Chem-PDF-Extractor.bat and choose option 2, pymupdf4llm."
    RetrySafe = "You can retry safely after fixing the issue."
  }
  zh = @{
    ChooseBackend = "请选择 PDF 解析后端："
    PypdfDesc = "轻量模式 | 安装体积最小 | 安装最快 | 兼容性最好"
    PypdfSuitable = "适合文本型 PDF。"
    PypdfWeakness = "弱点：版面、表格、多栏处理能力较弱。"
    PymupdfDesc = "均衡降级模式 | 中等安装体积 | 速度较好 | 适合多数科研 PDF。"
    PymupdfFallback = "如果希望安装比 MinerU 更轻，可以选择此项。"
    MineruDesc = "增强默认模式 | 安装体积大 | 首次安装较慢。"
    MineruSuitable = "适合复杂版面、表格、扫描类 PDF 和性能较好的电脑。"
    MineruWarning = "提示：需要更多磁盘空间、内存和安装时间，可能下载较大的依赖或模型。"
    MineruDefault = "如果直接按 Enter，将默认使用此选项。"
    PreviousBackend = "上次选择的后端："
    EnterReuse = "请输入 1、2 或 3。直接按 Enter 复用上次选择"
    EnterDefault = "请输入 1、2 或 3。直接按 Enter 使用选项 3"
    InvalidChoice = "输入无效。请输入 1、2、3，或直接按 Enter。"
    MineruFailed = "MinerU 安装未成功完成。"
    Reason = "原因："
    RetryMineru = "[1] 重试 MinerU 安装"
    ContinuePymupdf = "[2] 现在改用 pymupdf4llm 继续"
    Exit = "[3] 退出"
    Enter123 = "请输入 1、2 或 3"
    StartingApp = "正在启动 Chem-PDF-Extractor 本地网页应用..."
    LocalUrl = "本地网址："
    BrowserHint = "浏览器应会自动打开；如果没有打开，请复制上面的网址。"
    KeepWindowOpen = "服务运行期间请保持此 PowerShell 窗口打开。"
    StopHint = "按 Ctrl+C 可停止服务。"
    LauncherFailed = "Chem-PDF-Extractor 启动失败。"
    Logs = "日志："
    Fallback = "建议：重新运行 YiJianQiDong.bat，并选择选项 2 pymupdf4llm。"
    RetrySafe = "修复问题后可以安全重试。"
  }
}

function Get-LauncherText {
  param([string]$Key)
  if ($Messages.ContainsKey($Language) -and $Messages[$Language].ContainsKey($Key)) {
    return $Messages[$Language][$Key]
  }
  return $Messages["en"][$Key]
}

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

  $stdoutPath = Join-Path $LogsDir ("native-stdout-{0}.log" -f ([guid]::NewGuid().ToString("N")))
  $stderrPath = Join-Path $LogsDir ("native-stderr-{0}.log" -f ([guid]::NewGuid().ToString("N")))
  $quotedArgs = @()
  foreach ($argument in $Arguments) {
    if ($argument -match '\s') {
      $quotedArgs += ('"{0}"' -f ($argument -replace '"', '\"'))
    } else {
      $quotedArgs += $argument
    }
  }

  try {
    $process = Start-Process -FilePath $FilePath -ArgumentList $quotedArgs -NoNewWindow -Wait -PassThru -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
    $exitCode = $process.ExitCode

    if (Test-Path -LiteralPath $stdoutPath) {
      $stdout = Get-Content -LiteralPath $stdoutPath -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
      if ($stdout) {
        Write-LauncherLog "stdout:" $LogPath
        Add-Content -LiteralPath $LogPath -Encoding UTF8 -Value $stdout
        Write-Host $stdout
      }
    }
    if (Test-Path -LiteralPath $stderrPath) {
      $stderr = Get-Content -LiteralPath $stderrPath -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
      if ($stderr) {
        Write-LauncherLog "stderr:" $LogPath
        Add-Content -LiteralPath $LogPath -Encoding UTF8 -Value $stderr
        Write-Host $stderr
      }
    }
  } finally {
    Remove-Item -LiteralPath $stdoutPath, $stderrPath -Force -ErrorAction SilentlyContinue
  }

  Write-LauncherLog "Exit code: $exitCode" $LogPath
  if ($exitCode -ne 0) {
    $message = "Command failed: $display"
    if ($FailureHint) {
      $message = "$message`n$FailureHint"
    }
    throw $message
  }
}

function Add-ProjectScriptsToPath {
  param([string]$PythonExe)
  $scriptsDir = Split-Path -Parent $PythonExe
  if ((Test-Path -LiteralPath $scriptsDir) -and ($env:PATH -notlike "*$scriptsDir*")) {
    $env:PATH = "$scriptsDir;$env:PATH"
    Write-LauncherLog "Prepended project Scripts directory to PATH: $scriptsDir"
  }
  return $scriptsDir
}

function Set-MinerUEnvironmentIfAvailable {
  param([string]$PythonExe)
  $scriptsDir = Add-ProjectScriptsToPath -PythonExe $PythonExe
  $mineruExe = Join-Path $scriptsDir "mineru.exe"
  if (Test-Path -LiteralPath $mineruExe) {
    $resolvedMinerU = (Resolve-Path -LiteralPath $mineruExe).Path
    $env:MINERU_COMMAND = $resolvedMinerU
    Write-LauncherLog "MINERU_COMMAND set to: $resolvedMinerU"
    return $true
  }
  Write-LauncherLog "mineru.exe not found in project Scripts directory: $mineruExe"
  return $false
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
    (Join-Path $UserRoot "bundled_runtime\python\python.exe"),
    (Join-Path $RuntimeDir ".venv\Scripts\python.exe"),
    (Join-Path $AppRoot ".venv\Scripts\python.exe"),
    (Join-Path $UserRoot "YiLaiHuanJing\python\python.exe"),
    (Join-Path $UserRoot "运行依赖\python\python.exe"),
    (Join-Path $AppRoot "YiLaiHuanJing\python\python.exe"),
    (Join-Path $AppRoot "运行依赖\python\python.exe")
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

  $venvDir = Join-Path $RuntimeDir ".venv"
  $venvPython = Join-Path $venvDir "Scripts\python.exe"
  if (-not (Test-Path -LiteralPath $venvPython)) {
    $python311 = Ensure-Python311ForVenv
    Write-Step "Creating project virtual environment: $venvDir"
    Invoke-PythonCommand -PythonCommand $python311 -Arguments @("-m", "venv", $venvDir) -FailureHint "Failed to create runtime virtual environment. Check logs/install.log and verify that Python 3.11 includes venv support."
  }

  if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "Virtual environment was created but runtime .venv\Scripts\python.exe was not found."
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
    Write-Host (Get-LauncherText "ChooseBackend")
    Write-Host ""
    Write-Host "[1] pypdf_text"
    Write-Host (Get-LauncherText "PypdfDesc")
    Write-Host (Get-LauncherText "PypdfSuitable")
    Write-Host (Get-LauncherText "PypdfWeakness")
    Write-Host ""
    Write-Host "[2] pymupdf4llm"
    Write-Host (Get-LauncherText "PymupdfDesc")
    Write-Host (Get-LauncherText "PymupdfFallback")
    Write-Host ""
    Write-Host "[3] mineru"
    Write-Host (Get-LauncherText "MineruDesc")
    Write-Host (Get-LauncherText "MineruSuitable")
    Write-Host (Get-LauncherText "MineruWarning")
    Write-Host (Get-LauncherText "MineruDefault")
    Write-Host ""
    if ($previous) {
      $previousLabel = Get-LauncherText "PreviousBackend"
      Write-Host "$previousLabel $previous"
      $choice = Read-Host (Get-LauncherText "EnterReuse")
      if ([string]::IsNullOrWhiteSpace($choice)) {
        Save-BackendChoice $previous
        return $previous
      }
    } else {
      $choice = Read-Host (Get-LauncherText "EnterDefault")
      if ([string]::IsNullOrWhiteSpace($choice)) {
        Save-BackendChoice "mineru"
        return "mineru"
      }
    }

    switch ($choice.Trim()) {
      "1" { Save-BackendChoice "pypdf_text"; return "pypdf_text" }
      "2" { Save-BackendChoice "pymupdf4llm"; return "pymupdf4llm" }
      "3" { Save-BackendChoice "mineru"; return "mineru" }
      default {
        Write-Host (Get-LauncherText "InvalidChoice")
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
  $mineruRequirements = Join-Path $AppRoot "requirements-mineru.txt"
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
    Set-MinerUEnvironmentIfAvailable -PythonExe $PythonExe | Out-Null
    Write-LauncherLog "MinerU installation finished"
    Write-Step "MinerU backend installation finished."
  } catch {
    Write-LauncherLog "MinerU installation failed: $($_.Exception.Message)"
    throw "MinerU installation failed. Check logs/install.log.`n$($_.Exception.Message)"
  }
}

function Resolve-MinerUInstallFailure {
  param(
    [string]$PythonExe,
    [string]$FailureMessage
  )
  while ($true) {
    Write-Host ""
    Write-Host (Get-LauncherText "MineruFailed")
    $reasonLabel = Get-LauncherText "Reason"
    Write-Host "$reasonLabel $FailureMessage"
    Write-Host ""
    Write-Host (Get-LauncherText "RetryMineru")
    Write-Host (Get-LauncherText "ContinuePymupdf")
    Write-Host (Get-LauncherText "Exit")
    $choice = Read-Host (Get-LauncherText "Enter123")
    switch ($choice.Trim()) {
      "1" {
        try {
          Install-MinerU -PythonExe $PythonExe
          Save-BackendChoice "mineru"
          return "mineru"
        } catch {
          $FailureMessage = $_.Exception.Message
          Write-LauncherLog "MinerU retry failed: $FailureMessage"
        }
      }
      "2" {
        Write-Step "Continuing with pymupdf4llm backend."
        Save-BackendChoice "pymupdf4llm"
        return "pymupdf4llm"
      }
      "3" {
        throw "MinerU installation was cancelled by the user."
      }
      default {
        Write-Host (Get-LauncherText "Enter123")
      }
    }
  }
}

function Install-DependenciesForBackend {
  param(
    [string]$PythonExe,
    [string]$Backend
  )
  switch ($Backend) {
    "pypdf_text" {
      Install-Requirements -PythonExe $PythonExe -RequirementsFile (Join-Path $AppRoot "requirements-core.txt")
      return "pypdf_text"
    }
    "pymupdf4llm" {
      Install-Requirements -PythonExe $PythonExe -RequirementsFile (Join-Path $AppRoot "requirements.txt")
      return "pymupdf4llm"
    }
    "mineru" {
      Install-Requirements -PythonExe $PythonExe -RequirementsFile (Join-Path $AppRoot "requirements.txt")
      try {
        Install-MinerU -PythonExe $PythonExe
        Save-BackendChoice "mineru"
        return "mineru"
      } catch {
        Write-LauncherLog "MinerU install flow requires user decision: $($_.Exception.Message)"
        return Resolve-MinerUInstallFailure -PythonExe $PythonExe -FailureMessage $_.Exception.Message
      }
    }
    default {
      throw "Unknown backend selected: $Backend"
    }
  }
}

try {
  Write-LauncherLog "===== Windows first-run launcher started =====" $StartupLog
  Write-LauncherLog "app_root: $AppRoot" $StartupLog
  Write-LauncherLog "user_root: $UserRoot" $StartupLog
  Write-LauncherLog "input_dir: $InputDir" $StartupLog
  Write-LauncherLog "output_dir: $OutputDir" $StartupLog
  Write-LauncherLog "logs_dir: $LogsDir" $StartupLog

  $backend = Select-PdfBackend
  Write-Step "Selected PDF backend: $backend"
  $pythonExe = Ensure-ProjectPython
  Write-Step "Project Python: $pythonExe"

  $backend = Install-DependenciesForBackend -PythonExe $pythonExe -Backend $backend
  Add-ProjectScriptsToPath -PythonExe $pythonExe | Out-Null
  if ($backend -eq "mineru") {
    if (-not (Set-MinerUEnvironmentIfAvailable -PythonExe $pythonExe)) {
      Write-LauncherLog "MinerU backend selected, but mineru.exe was not found before app startup."
    }
  }

  $url = "http://127.0.0.1:8766/"
  $startupArgs = @("-m", "chem_pdf_extractor", "--pdf-mode", $backend, "--open-browser")
  Write-LauncherLog "App startup command: $pythonExe $($startupArgs -join ' ')" $StartupLog
  Write-Host ""
  Write-Host (Get-LauncherText "StartingApp")
  $localUrlLabel = Get-LauncherText "LocalUrl"
  Write-Host "$localUrlLabel $url"
  Write-Host (Get-LauncherText "BrowserHint")
  Write-Host (Get-LauncherText "KeepWindowOpen")
  Write-Host (Get-LauncherText "StopHint")
  Write-Host ""

  & $pythonExe @startupArgs 2>&1 | Tee-Object -FilePath $StartupLog -Append
  $exitCode = $LASTEXITCODE
  Write-LauncherLog "App process exited with code: $exitCode" $StartupLog
  exit $exitCode
} catch {
  Write-LauncherLog "Launcher error: $($_.Exception.Message)" $StartupLog
  Write-Host ""
  Write-Host (Get-LauncherText "LauncherFailed")
  Write-Host $_.Exception.Message
  Write-Host ""
  Write-Host (Get-LauncherText "Logs")
  Write-Host "  $InstallLog"
  Write-Host "  $StartupLog"
  Write-Host ""
  Write-Host (Get-LauncherText "Fallback")
  Write-Host (Get-LauncherText "RetrySafe")
  exit 1
}
