# Windows Desktop Tool

## Ready to use

- Standalone EXE: `dist/PDFStampRedactor.exe`
- GUI source: `stamp_redactor_gui.py`
- Core logic: `redact_stamp.py`

## End-user steps

1. Double-click `dist/PDFStampRedactor.exe`
2. Click `选择文件` and pick the input PDF
3. Click `另存为` and choose the output PDF path
4. Click `开始处理`
5. Wait for the progress bar to finish
6. Open the generated PDF from the output folder

## Notes

- No Python environment is required for end users
- The app can automatically open the output folder after completion
- `保存调试图片` is optional and is off by default

## Rebuild

- The build script prefers the project virtual environment: `.venv\Scripts\python.exe`
- The selected Python environment must be able to import `fitz` or `pymupdf`
- Build command:

```powershell
.\build_exe.ps1
```

- Override the interpreter if needed:

```powershell
.\build_exe.ps1 -PythonExe C:\path\to\python.exe
```
