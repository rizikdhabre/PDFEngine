import fitz
from typing import Tuple, List
from config import PAGE_MARGIN

def a4_rect_landscape() -> fitz.Rect:
    r = fitz.paper_rect('a4')
    if r.width < r.height:
        r = fitz.Rect(r.y0, r.x0, r.y1, r.x1)
    return r

def a4_rect_portrait() -> fitz.Rect:
    r = fitz.paper_rect('a4')
    if r.height < r.width:
        r = fitz.Rect(r.y0, r.x0, r.y1, r.x1)
    return r

def split_2up(rect: fitz.Rect) -> Tuple[fitz.Rect, fitz.Rect]:
    midx = (rect.x0 + rect.x1) / 2
    left = fitz.Rect(rect.x0, rect.y0, midx, rect.y1)
    right = fitz.Rect(midx, rect.y0, rect.x1, rect.y1)
    return left, right

def grid_boxes(rect: fitz.Rect, rows: int, cols: int):
    boxes = []
    w = (rect.x1 - rect.x0) / cols
    h = (rect.y1 - rect.y0) / rows
    for r in range(rows):
        for c in range(cols):
            boxes.append(fitz.Rect(rect.x0 + c*w, rect.y0 + r*h,
                                   rect.x0 + (c+1)*w, rect.y0 + (r+1)*h))
    return boxes

def draw_src(page: fitz.Page, src_doc: fitz.Document, idx: int, box: fitz.Rect, margin: int = PAGE_MARGIN):
    if idx is None or idx < 0 or idx >= len(src_doc):
        return
    inner = fitz.Rect(box.x0 + margin, box.y0 + margin, box.x1 - margin, box.y1 - margin)
    page.show_pdf_page(inner, src_doc, idx)

def booklet_order_within_signature(sig_pages: int):
    S = sig_pages
    left, right = 1, S
    sheets = []
    while left < right:
        front = (right, left)
        left += 1; right -= 1
        back = (left, right)
        left += 1; right -= 1
        sheets.append((front, back))
    return sheets
