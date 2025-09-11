from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QLabel, QComboBox, QTextEdit, QHBoxLayout, QMessageBox
)
import fitz

from core.signature_logic import choose_best_plan
from core.imposition import impose_cut_stack


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("A4 → A5/A6/A7/A8 Imposition")
        self.resize(860, 620)

        lay = QVBoxLayout(self)
        
        
        # file row
        row = QHBoxLayout()
        self.label_file = QLabel("No file selected")
        btn_browse = QPushButton("Upload A4 PDF…")
        btn_browse.clicked.connect(self.load_pdf)
        row.addWidget(self.label_file, 1)
        row.addWidget(btn_browse)
        lay.addLayout(row)

        # controls row
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Target:"))
        self.combo_target = QComboBox()
        self.combo_target.addItems([
            "A5 booklet (fold once)",
            "A6 booklet (fold twice)",
            "A7 booklet (fold thrice)",
            "A8 booklet (fold four times)"
        ])
        row2.addWidget(self.combo_target, 1)

        # NEW: Reading direction (affects back rotation)
        row2.addWidget(QLabel("Reading direction:"))
        self.combo_binding = QComboBox()
        self.combo_binding.addItems([
            "LTR (left-to-right(English))",
            "RTL (right-to-left(Hebrew, Arabic))"
        ])
        row2.addWidget(self.combo_binding, 1)

        self.btn_go = QPushButton("Convert / Impose")
        self.btn_go.clicked.connect(self.run_impose)
        row2.addWidget(self.btn_go)
        lay.addLayout(row2)

        # log
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Log will appear here…")
        lay.addWidget(self.log, 1)

        self.src_path = None

    def _unique_path(self, path: str) -> str:
        import os
        base, ext = os.path.splitext(path)
        if not os.path.exists(path):
            return path
        i = 1
        while os.path.exists(f"{base}({i}){ext}"):
            i += 1
        return f"{base}({i}){ext}"

    def load_pdf(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select A4 PDF", "", "PDF Files (*.pdf)")
        if not path:
            return
        self.src_path = path
        self.label_file.setText(path)
        self.log.append(f"Selected: {path}")

    def run_impose(self):
        if not self.src_path:
            QMessageBox.warning(self, "No file", "Please upload an A4 PDF first.")
            return

        try:
            src_doc = fitz.open(self.src_path)
        except Exception as e:
            QMessageBox.critical(self, "Open failed", f"Could not open PDF:\n{e}")
            return

        if len(src_doc) == 0:
            QMessageBox.warning(self, "Empty PDF", "The selected PDF has no pages.")
            return

        target = self.combo_target.currentText()
        binding_choice = self.combo_binding.currentText()
        binding = "RTL" if "RTL" in binding_choice.upper() else "LTR"

        self.log.append("\n---- Imposition (Staged Pipeline) ----")
        best, _ = choose_best_plan(len(src_doc))

        try:
            if "A5" in target:
                out_doc = impose_cut_stack(
                    src_doc, best, self.log,
                    level=1,
                    binding=binding,
                    emit_blank_tail_signature=False
                )
                suffix = "_A5_booklet.pdf"

            elif "A6" in target:
                out_doc = impose_cut_stack(
                    src_doc, best, self.log,
                    level=2,
                    binding=binding,
                    emit_blank_tail_signature=False
                )
                suffix = "_A6_booklet.pdf"

            elif "A7" in target:
                out_doc = impose_cut_stack(
                    src_doc, best, self.log,
                    level=3,
                    binding=binding,
                    emit_blank_tail_signature=False
                )
                suffix = "_A7_booklet.pdf"

            else:
                out_doc = impose_cut_stack(
                    src_doc, best, self.log,
                    level=4,
                    binding=binding,
                    emit_blank_tail_signature=False
                )
                suffix = "_A8_booklet.pdf"


        except Exception as e:
            src_doc.close()
            QMessageBox.critical(self, "Imposition failed", f"An error occurred:\n{e}")
            return

        out_path = self.src_path.rsplit('.', 1)[0] + suffix
        out_path = self._unique_path(out_path)
        try:
            out_doc.save(out_path)
            out_doc.close()
        except Exception as e:
            QMessageBox.critical(self, "Save failed", f"Could not save output:\n{e}")
            return

        self.log.append(f"Saved: {out_path}")
        QMessageBox.information(self, "Done", f"Created:\n{out_path}")
