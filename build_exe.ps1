param(
    [string]$PythonExe
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$VenvConfig = Join-Path $ProjectRoot ".venv\pyvenv.cfg"
$VenvSitePackages = Join-Path $ProjectRoot ".venv\Lib\site-packages"

function Test-PythonImports {
    param(
        [string]$Interpreter,
        [bool]$RequirePyInstaller = $false,
        [string]$ExtraSitePackages = "",
        [bool]$Quiet = $false
    )

    $pythonCode = "import importlib.util, sys; "

    if ($ExtraSitePackages) {
        $escapedPath = $ExtraSitePackages.Replace("\", "\\")
        $pythonCode += "sys.path.append('$escapedPath'); "
    }

    $pythonCode += "required={'PySide6':'PySide6','cv2':'opencv-python','numpy':'numpy'}; "
    $pythonCode += "fitz_available=importlib.util.find_spec('fitz') is not None; "
    $pythonCode += "pymupdf_available=importlib.util.find_spec('pymupdf') is not None; "
    $pythonCode += "required.update({} if (fitz_available or pymupdf_available) else {'fitz':'PyMuPDF'}); "

    if ($RequirePyInstaller) {
        $pythonCode += "required['PyInstaller']='PyInstaller'; "
    }

    $pythonCode += "missing=[package for module_name, package in required.items() if importlib.util.find_spec(module_name) is None]; "
    $pythonCode += "missing and sys.exit('Missing dependencies in selected interpreter: ' + ', '.join(missing) + '. Install them into this Python environment before packaging.')"

    if ($Quiet) {
        & $Interpreter -c $pythonCode 1>$null 2>$null
    } else {
        & $Interpreter -c $pythonCode
    }
    return $LASTEXITCODE -eq 0
}

function Get-VenvBasePython {
    param([string]$ConfigPath)

    if (-not (Test-Path $ConfigPath)) {
        return $null
    }

    $baseLine = Get-Content $ConfigPath | Where-Object { $_ -like "base-executable = *" } | Select-Object -First 1
    if (-not $baseLine) {
        return $null
    }

    return ($baseLine -replace "^base-executable = ", "").Trim()
}

Push-Location $ProjectRoot
try {
    if (-not $PythonExe) {
        if (Test-Path $VenvPython) {
            $PythonExe = $VenvPython
        } else {
            $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
            if ($null -eq $PythonCommand) {
                throw "Python executable not found. Create the project .venv first or pass -PythonExe explicitly."
            }
            $PythonExe = $PythonCommand.Source
        }
    }

    if (-not (Test-Path $PythonExe)) {
        throw "Python executable not found: $PythonExe"
    }

    $BuildPythonExe = $PythonExe
    $ExtraSitePackages = ""

    if (-not (Test-PythonImports -Interpreter $PythonExe)) {
        throw "Dependency check failed for: $PythonExe"
    }

    if (-not (Test-PythonImports -Interpreter $PythonExe -RequirePyInstaller $true -Quiet $true)) {
        if ($PythonExe -eq $VenvPython -and (Test-Path $VenvSitePackages)) {
            $BasePythonExe = Get-VenvBasePython -ConfigPath $VenvConfig
            if ($BasePythonExe -and (Test-Path $BasePythonExe)) {
                if (Test-PythonImports -Interpreter $BasePythonExe -RequirePyInstaller $true -ExtraSitePackages $VenvSitePackages -Quiet $true) {
                    $BuildPythonExe = $BasePythonExe
                    $ExtraSitePackages = $VenvSitePackages
                } else {
                    throw "Neither $PythonExe nor its base interpreter can package the app. Ensure PyInstaller is installed."
                }
            } else {
                throw "PyInstaller is missing from $PythonExe, and the virtual environment base interpreter could not be resolved."
            }
        } else {
            throw "PyInstaller is missing from $PythonExe. Install it there or pass -PythonExe for an interpreter that has it."
        }
    }

    Write-Host "Dependency Python:" $PythonExe
    Write-Host "Build Python:" $BuildPythonExe
    Write-Host "Working directory:" $ProjectRoot

    if ($ExtraSitePackages) {
        $env:PDFSTAMP_EXTRA_SITE_PACKAGES = $ExtraSitePackages
        Write-Host "Using extra site-packages:" $ExtraSitePackages
    } else {
        Remove-Item Env:PDFSTAMP_EXTRA_SITE_PACKAGES -ErrorAction SilentlyContinue
    }

    & $BuildPythonExe -m PyInstaller --noconfirm --clean PDFStampRedactor.spec
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller build failed with exit code $LASTEXITCODE"
    }

    Write-Host ""
    Write-Host "Build completed:"
    Write-Host "  dist\\PDFStampRedactor.exe"
}
finally {
    Remove-Item Env:PDFSTAMP_EXTRA_SITE_PACKAGES -ErrorAction SilentlyContinue
    Pop-Location
}
