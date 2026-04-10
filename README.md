# PDF Stamp Redactor / PDF 印章脱敏工具

## 中文

### 项目简介

`PDF Stamp Redactor` 是一个面向 Windows 的桌面小工具，用于检测 PDF 页面中的红色印章区域，并对印章进行马赛克脱敏处理后生成新的 PDF 文件。

### 功能特性

- 图形界面操作，适合直接双击运行
- 自动检测红色印章区域
- 对检测到的印章执行马赛克脱敏
- 支持输出新的 PDF 文件，避免覆盖原文件
- 可选保存调试图片
- 可选在处理完成后自动打开输出目录

### 目录说明

- `stamp_redactor_gui.py`：桌面 GUI 入口
- `redact_stamp.py`：PDF 处理核心逻辑
- `build_exe.ps1`：Windows 打包脚本
- `PDFStampRedactor.spec`：PyInstaller 打包配置
- `dist/PDFStampRedactor.exe`：打包后的可执行文件

### 直接使用 EXE

1. 双击运行 `dist/PDFStampRedactor.exe`
2. 选择输入 PDF 文件
3. 选择输出 PDF 路径
4. 按需勾选“保存调试图片”或“完成后打开输出目录”
5. 点击开始处理
6. 等待进度条完成并查看输出结果

### 从源码运行

建议优先使用项目虚拟环境 `.venv`。

#### 启动图形界面

```powershell
.venv\Scripts\python.exe .\stamp_redactor_gui.py
```

#### 命令行处理 PDF

```powershell
.venv\Scripts\python.exe .\redact_stamp.py input.pdf output_mosaic.pdf
```

#### 带调试输出的命令行示例

```powershell
.venv\Scripts\python.exe .\redact_stamp.py input.pdf output_mosaic.pdf --debug --debug-dir debug
```

### 依赖说明

运行源码或重新打包时，Python 环境需要能导入以下依赖：

- `PySide6`
- `numpy`
- `opencv-python`
- `PyMuPDF`（模块名可能是 `fitz` 或 `pymupdf`）
- `PyInstaller`（仅重新打包时需要）

### 重新打包 EXE

```powershell
.\build_exe.ps1
```

如需指定 Python 解释器：

```powershell
.\build_exe.ps1 -PythonExe C:\path\to\python.exe
```

打包脚本会：

- 优先使用 `.venv\Scripts\python.exe` 作为依赖环境
- 检查 `fitz` 或 `pymupdf` 是否可用
- 在 `.venv` 没有安装 `PyInstaller` 时，自动回退到虚拟环境的基础 Python 执行打包

### 常见问题

#### 1. 打包后的 EXE 提示 `No module named 'fitz'`

原因通常是打包时使用了错误的 Python 环境，导致 `PyMuPDF` 没有被正确收集。

建议：

- 优先使用项目 `.venv` 执行 `.\build_exe.ps1`
- 确认所选解释器可以导入 `fitz` 或 `pymupdf`
- 重新执行打包脚本生成新的 `dist/PDFStampRedactor.exe`

#### 2. 输出文件不能与输入文件相同

工具会阻止直接覆盖输入 PDF，请选择不同的输出路径。

#### 3. 没有检测到印章

当前逻辑主要针对红色、近圆形、面积较明显的印章区域。若印章颜色、形状或扫描质量差异较大，检测效果可能会受影响。

---

## English

### Overview

`PDF Stamp Redactor` is a small Windows desktop utility that detects red stamp regions in PDF pages and applies mosaic redaction to those regions before generating a new PDF file.

### Features

- Simple desktop GUI for end users
- Automatic detection of red stamp regions
- Mosaic redaction for detected stamps
- Writes a new output PDF instead of overwriting the source file
- Optional debug image export
- Optional auto-open of the output folder after completion

### Project Layout

- `stamp_redactor_gui.py`: GUI entry point
- `redact_stamp.py`: core PDF processing logic
- `build_exe.ps1`: Windows build script
- `PDFStampRedactor.spec`: PyInstaller spec file
- `dist/PDFStampRedactor.exe`: packaged executable

### Run the EXE

1. Double-click `dist/PDFStampRedactor.exe`
2. Choose the input PDF
3. Choose the output PDF path
4. Optionally enable debug image saving or auto-open output folder
5. Click the start button
6. Wait for the progress bar to finish and check the result

### Run from Source

Using the project virtual environment `.venv` is recommended.

#### Launch the GUI

```powershell
.venv\Scripts\python.exe .\stamp_redactor_gui.py
```

#### Process a PDF from CLI

```powershell
.venv\Scripts\python.exe .\redact_stamp.py input.pdf output_mosaic.pdf
```

#### CLI example with debug output

```powershell
.venv\Scripts\python.exe .\redact_stamp.py input.pdf output_mosaic.pdf --debug --debug-dir debug
```

### Dependencies

The selected Python environment should be able to import the following packages when running from source or rebuilding:

- `PySide6`
- `numpy`
- `opencv-python`
- `PyMuPDF` (module name may be `fitz` or `pymupdf`)
- `PyInstaller` (required only for packaging)

### Rebuild the EXE

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

### Troubleshooting

#### 1. Packaged EXE reports `No module named 'fitz'`

This usually means the build used the wrong Python environment and PyMuPDF was not collected correctly.

Recommended actions:

- Run `.\build_exe.ps1` with the project `.venv`
- Make sure the selected interpreter can import `fitz` or `pymupdf`
- Rebuild and use the newly generated `dist/PDFStampRedactor.exe`

#### 2. Output file matches the input file

The tool rejects using the same path for input and output. Choose a different output file.

#### 3. No stamp detected

The current logic mainly targets red, roughly circular, and sufficiently large stamp regions. Detection quality may vary if the stamp color, shape, or scan quality differs significantly.
