<p align="right">
  <a href="./README.md">中文</a> | English
</p>

# PDF Stamp Redactor

## Overview

`PDF Stamp Redactor` is a Windows desktop utility that detects red stamp regions in PDF pages, applies mosaic redaction to those regions, and generates a new PDF file.

## Features

- Simple GUI for desktop use
- Automatic detection of red stamp regions
- Mosaic redaction for detected stamps
- Writes a new output PDF instead of overwriting the source file
- Optional debug image export
- Optional auto-open of the output folder after completion

## Project Layout

- `stamp_redactor_gui.py`: GUI entry point
- `redact_stamp.py`: core PDF processing logic
- `build_exe.ps1`: Windows build script
- `PDFStampRedactor.spec`: PyInstaller spec file
- `dist/PDFStampRedactor.exe`: packaged executable

## Run the EXE

1. Double-click `dist/PDFStampRedactor.exe`
2. Choose the input PDF
3. Choose the output PDF path
4. Optionally enable debug image saving or auto-open output folder
5. Click the start button
6. Wait for the progress bar to finish and check the result

## Run from Source

Using the project virtual environment `.venv` is recommended.

### Launch the GUI

```powershell
.venv\Scripts\python.exe .\stamp_redactor_gui.py
```

### Process a PDF from CLI

```powershell
.venv\Scripts\python.exe .\redact_stamp.py input.pdf output_mosaic.pdf
```

### CLI example with debug output

```powershell
.venv\Scripts\python.exe .\redact_stamp.py input.pdf output_mosaic.pdf --debug --debug-dir debug
```

## Dependencies

The selected Python environment should be able to import the following packages when running from source or rebuilding:

- `PySide6`
- `numpy`
- `opencv-python`
- `PyMuPDF` (module name may be `fitz` or `pymupdf`)
- `PyInstaller` (required only for packaging)

## Rebuild the EXE

```powershell
.\build_exe.ps1
```

To override the Python interpreter:

```powershell
.\build_exe.ps1 -PythonExe C:\path\to\python.exe
```

The build script will:

- Prefer `.venv\Scripts\python.exe` as the dependency environment
- Verify that `fitz` or `pymupdf` is available
- Fall back to the virtual environment's base Python for packaging when `.venv` does not contain `PyInstaller`

## Troubleshooting

### 1. Packaged EXE reports `No module named 'fitz'`

This usually means the build used the wrong Python environment and PyMuPDF was not collected correctly.

Recommended actions:

- Run `.\build_exe.ps1` with the project `.venv`
- Make sure the selected interpreter can import `fitz` or `pymupdf`
- Rebuild and use the newly generated `dist/PDFStampRedactor.exe`

### 2. Output file matches the input file

The tool rejects using the same path for input and output. Choose a different output file.

### 3. No stamp detected

The current logic mainly targets red, roughly circular, and sufficiently large stamp regions. Detection quality may vary if the stamp color, shape, or scan quality differs significantly.
