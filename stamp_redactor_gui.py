from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QProgressBar,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from redact_stamp import redact_pdf_mosaic


class RedactionWorker(QObject):
    progress = Signal(int, int, str)
    log = Signal(str)
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, input_path: Path, output_path: Path, debug_enabled: bool) -> None:
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.debug_enabled = debug_enabled

    def run(self) -> None:
        try:
            result = redact_pdf_mosaic(
                self.input_path,
                self.output_path,
                debug=self.debug_enabled,
                progress_callback=self.progress.emit,
                log_callback=self.log.emit,
            )
            self.finished.emit(str(result))
        except Exception as exc:
            self.failed.emit(str(exc))


class StampRedactorWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PDF 印章脱敏工具")
        self.resize(860, 620)

        self.worker_thread: QThread | None = None
        self.worker: RedactionWorker | None = None

        self.input_edit = QLineEdit()
        self.output_edit = QLineEdit()
        self.debug_checkbox = QCheckBox("保存调试图片")
        self.auto_open_checkbox = QCheckBox("完成后打开输出目录")
        self.auto_open_checkbox.setChecked(True)
        self.progress_bar = QProgressBar()
        self.log_box = QPlainTextEdit()
        self.status_label = QLabel("请选择待处理的 PDF 文件。")
        self.start_button = QPushButton("开始处理")

        self._build_ui()
        self._wire_events()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(14)

        title = QLabel("PDF 印章脱敏工具")
        title_font = QFont("Microsoft YaHei UI", 16)
        title_font.setBold(True)
        title.setFont(title_font)

        subtitle = QLabel("适合小白用户：选择 PDF，点击“开始处理”，程序会输出脱敏后的新文件。")
        subtitle.setWordWrap(True)

        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)

        path_group = QGroupBox("文件设置")
        path_layout = QGridLayout(path_group)
        path_layout.setHorizontalSpacing(10)
        path_layout.setVerticalSpacing(10)

        input_button = QPushButton("选择文件")
        output_button = QPushButton("另存为")
        input_button.clicked.connect(self.choose_input_file)
        output_button.clicked.connect(self.choose_output_file)

        self.input_edit.setPlaceholderText("请选择 PDF 文件")
        self.output_edit.setPlaceholderText("请选择输出路径")

        path_layout.addWidget(QLabel("输入 PDF"), 0, 0)
        path_layout.addWidget(self.input_edit, 0, 1)
        path_layout.addWidget(input_button, 0, 2)
        path_layout.addWidget(QLabel("输出 PDF"), 1, 0)
        path_layout.addWidget(self.output_edit, 1, 1)
        path_layout.addWidget(output_button, 1, 2)
        path_layout.setColumnStretch(1, 1)

        root_layout.addWidget(path_group)

        options_layout = QHBoxLayout()
        options_layout.addWidget(self.debug_checkbox)
        options_layout.addWidget(self.auto_open_checkbox)
        options_layout.addStretch(1)
        root_layout.addLayout(options_layout)

        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        root_layout.addWidget(self.progress_bar)

        log_group = QGroupBox("处理日志")
        log_layout = QVBoxLayout(log_group)
        self.log_box.setReadOnly(True)
        self.log_box.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.log_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        log_layout.addWidget(self.log_box)
        root_layout.addWidget(log_group, stretch=1)

        bottom_layout = QHBoxLayout()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.start_button.setMinimumWidth(120)
        bottom_layout.addWidget(self.status_label, stretch=1)
        bottom_layout.addWidget(self.start_button)
        root_layout.addLayout(bottom_layout)

    def _wire_events(self) -> None:
        self.start_button.clicked.connect(self.start_processing)

    def append_log(self, message: str) -> None:
        self.log_box.appendPlainText(message)

    def choose_input_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 PDF 文件", "", "PDF Files (*.pdf);;All Files (*.*)"
        )
        if not file_path:
            return

        self.input_edit.setText(file_path)
        if not self.output_edit.text().strip():
            source = Path(file_path)
            self.output_edit.setText(str(source.with_name(f"{source.stem}_mosaic.pdf")))
        self.status_label.setText("已选择输入文件。")

    def choose_output_file(self) -> None:
        suggested = self.output_edit.text().strip() or "output_mosaic.pdf"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存处理后的 PDF", suggested, "PDF Files (*.pdf)"
        )
        if file_path:
            if not file_path.lower().endswith(".pdf"):
                file_path += ".pdf"
            self.output_edit.setText(file_path)
            self.status_label.setText("已设置输出文件。")

    def start_processing(self) -> None:
        if self.worker_thread is not None and self.worker_thread.isRunning():
            return

        input_text = self.input_edit.text().strip()
        output_text = self.output_edit.text().strip()

        if not input_text:
            QMessageBox.warning(self, "缺少输入文件", "请先选择需要处理的 PDF 文件。")
            return

        input_path = Path(input_text).expanduser()
        if not input_path.exists():
            QMessageBox.critical(self, "文件不存在", "输入 PDF 文件不存在，请重新选择。")
            return
        if input_path.suffix.lower() != ".pdf":
            QMessageBox.critical(self, "文件格式不支持", "请选择 PDF 文件。")
            return
        if not output_text:
            QMessageBox.warning(self, "缺少输出路径", "请先设置处理后的 PDF 保存位置。")
            return

        output_path = Path(output_text).expanduser()
        if output_path.suffix.lower() != ".pdf":
            output_path = output_path.with_suffix(".pdf")
            self.output_edit.setText(str(output_path))

        try:
            if input_path.resolve() == output_path.resolve():
                QMessageBox.critical(self, "输出路径无效", "输出文件不能和输入文件相同。")
                return
        except FileNotFoundError:
            pass

        if output_path.exists():
            should_overwrite = QMessageBox.question(
                self,
                "覆盖确认",
                "输出文件已存在，是否覆盖？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if should_overwrite != QMessageBox.StandardButton.Yes:
                return

        self.progress_bar.setValue(0)
        self.start_button.setEnabled(False)
        self.status_label.setText("正在处理，请稍候...")
        self.append_log("=" * 40)
        self.append_log(f"Input: {input_path}")
        self.append_log(f"Output: {output_path}")

        self.worker_thread = QThread(self)
        self.worker = RedactionWorker(input_path, output_path, self.debug_checkbox.isChecked())
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.handle_progress)
        self.worker.log.connect(self.append_log)
        self.worker.finished.connect(self.handle_finished)
        self.worker.failed.connect(self.handle_failed)
        self.worker.finished.connect(self.cleanup_worker)
        self.worker.failed.connect(self.cleanup_worker)
        self.worker_thread.start()

    def handle_progress(self, current: int, total: int, message: str) -> None:
        percent = 0 if total == 0 else round(current / total * 100)
        self.progress_bar.setValue(percent)
        self.status_label.setText(message)

    def handle_finished(self, result_path: str) -> None:
        result = Path(result_path)
        self.progress_bar.setValue(100)
        self.status_label.setText("处理完成。")
        self.append_log(f"Done: {result}")
        self.start_button.setEnabled(True)

        if self.auto_open_checkbox.isChecked():
            os.startfile(str(result.parent))

        QMessageBox.information(self, "处理完成", f"输出文件已生成：\n{result}")

    def handle_failed(self, error_message: str) -> None:
        self.status_label.setText("处理失败。")
        self.append_log(f"Error: {error_message}")
        self.start_button.setEnabled(True)
        QMessageBox.critical(self, "处理失败", error_message)

    def cleanup_worker(self) -> None:
        if self.worker_thread is not None:
            self.worker_thread.quit()
            self.worker_thread.wait()
        self.worker_thread = None
        self.worker = None


def main() -> int:
    app = QApplication([])
    app.setFont(QFont("Microsoft YaHei UI", 10))
    window = StampRedactorWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
