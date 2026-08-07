# build.ps1 — builds a single-file, no-console .exe with PyInstaller.
# Run from the project root in PowerShell:  .\build.ps1
#
# Auto-detects whether you have the `py` launcher or just `python` on PATH,
# and validates that the interpreter is 3.11 or newer (we need stdlib `tomllib`).

$ErrorActionPreference = "Stop"

# --- 1. Resolve a usable Python interpreter ---------------------------------
function Resolve-Python {
    # Prefer the launcher because it can pin a specific minor version.
    if (Get-Command py -ErrorAction SilentlyContinue) {
        foreach ($v in @("-3.12", "-3.11", "")) {
            try {
                $args = if ($v) { @($v) } else { @() }
                $version = & py @args -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
                if ($LASTEXITCODE -eq 0 -and $version) {
                    $major, $minor = $version.Trim().Split('.')
                    if ([int]$major -ge 3 -and [int]$minor -ge 11) {
                        return @{ Cmd = "py"; Args = $args }
                    }
                }
            } catch { }
        }
    }

    # Fall back to plain `python` on PATH.
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $version = & python -c "import sys; print('%d.%d' % sys.version_info[:2])"
        $major, $minor = $version.Trim().Split('.')
        if ([int]$major -ge 3 -and [int]$minor -ge 11) {
            return @{ Cmd = "python"; Args = @() }
        }
        throw "Found python $version but QuitAll-Win needs 3.11 or newer. Install with: winget install --id Python.Python.3.12"
    }

    throw "No Python interpreter found. Install with: winget install --id Python.Python.3.12"
}

$py = Resolve-Python
Write-Host "Using interpreter: $($py.Cmd) $($py.Args -join ' ')" -ForegroundColor Cyan

# --- 2. Create venv if missing ----------------------------------------------
if (-not (Test-Path ".venv")) {
    & $py.Cmd @($py.Args) -m venv .venv
}

. .\.venv\Scripts\Activate.ps1

# --- 3. Install dependencies ------------------------------------------------
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

# --- 4. Build. --windowed = no console window. --onefile = single .exe. -----
pyinstaller `
    --name QuitAllWin `
    --windowed `
    --onefile `
    --noconfirm `
    --clean `
    launcher.py

Write-Host ""
Write-Host "Build complete." -ForegroundColor Green
Write-Host "Output: $((Resolve-Path .\dist\QuitAllWin.exe).Path)"

# --- 5. Optional: build the installer if Inno Setup is on PATH ---------------
$iscc = Get-Command iscc -ErrorAction SilentlyContinue
if (-not $iscc) {
    # Inno Setup's installer doesn't add itself to PATH. Try the default location.
    $defaultIscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
    if (Test-Path $defaultIscc) { $iscc = $defaultIscc }
}

if ($iscc) {
    Write-Host ""
    Write-Host "Building installer with Inno Setup..." -ForegroundColor Cyan
    & $iscc "installer\QuitAllWin.iss"
    if ($LASTEXITCODE -eq 0) {
        $setup = Get-ChildItem ".\dist\installer\QuitAllWin-Setup-*.exe" |
                 Sort-Object LastWriteTime -Descending |
                 Select-Object -First 1
        if ($setup) {
            Write-Host "Installer:  $($setup.FullName)" -ForegroundColor Green
        }
    }
} else {
    Write-Host ""
    Write-Host "Inno Setup not found — skipping installer build." -ForegroundColor Yellow
    Write-Host "Install it once with:  winget install --id JRSoftware.InnoSetup"
}
