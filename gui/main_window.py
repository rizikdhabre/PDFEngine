from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QLabel, QComboBox, QTextEdit, QHBoxLayout, QMessageBox
)
import fitz

from core.signature_logic import choose_best_plan
from core.imposition import impose_A5_booklet, impose_A6_nup, impose_A7_nup

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("A4 → A5/A6/A7 Imposition (Best Signature Fit)")
        self.resize(860, 620)

        lay = QVBoxLayout(self)

        row = QHBoxLayout()
        self.label_file = QLabel("No file selected")
        btn_browse = QPushButton("Upload A4 PDF…")
        btn_browse.clicked.connect(self.load_pdf)
        row.addWidget(self.label_file, 1)
        row.addWidget(btn_browse)
        lay.addLayout(row)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Target:"))
        self.combo_target = QComboBox()
        self.combo_target.addItems(["A5 booklet (2-up spreads)", "A6 n-up (4-up)", "A7 n-up (8-up)"])
        row2.addWidget(self.combo_target, 1)
        self.btn_go = QPushButton("Convert / Impose")
        self.btn_go.clicked.connect(self.run_impose)
        row2.addWidget(self.btn_go)
        lay.addLayout(row2)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Log will appear here…")
        lay.addWidget(self.log, 1)

        self.src_path = None

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

        n_pages = len(src_doc)
        if n_pages == 0:
            QMessageBox.warning(self, "Empty PDF", "The selected PDF has no pages.")
            return

        best, all_plans = choose_best_plan(n_pages)

        self.log.append("---- Signature Planning (All Options) ----")
        self.log.append(f"Total pages in source: {n_pages}")
        for p in all_plans:
            self.log.append(
                f"Pair [{p.pair[0]}, {p.pair[1]}] -> {p.expression} = {p.total_pages} pages ({p.blanks} blank)"
            )

        self.log.append("\n---- Best Fit ----")
        self.log.append(f"Best signature pair: [{best.pair[0]}, {best.pair[1]}]")
        self.log.append(f"Combination: {best.expression} = {best.total_pages} pages")
        self.log.append(f"Blank pages (added at end): {best.blanks}")
        self.log.append("Sequence array (in order for printing):")
        self.log.append(str(best.sequence))

        target = self.combo_target.currentText()
        self.log.append("\n---- Imposition ----")
        if "A5 booklet" in target:
            out_doc = impose_A5_booklet(src_doc, best, self.log)
            suffix = "_A5_booklet_spreads.pdf"
        elif "A6" in target:
            out_doc = impose_A6_nup(src_doc, best, self.log)
            suffix = "_A6_4up.pdf"
        else:
            out_doc = impose_A7_nup(src_doc, best, self.log)
            suffix = "_A7_8up.pdf"

        out_path = self.src_path.rsplit('.', 1)[0] + suffix
        try:
            out_doc.save(out_path)
            out_doc.close()
        except Exception as e:
            QMessageBox.critical(self, "Save failed", f"Could not save output:\n{e}")
            return

        self.log.append(f"Saved: {out_path}")
        QMessageBox.information(self, "Done", f"Created:\n{out_path}")
