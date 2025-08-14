import fitz
from typing import List, Optional
from core.geometry import a4_rect_landscape, a4_rect_portrait, split_2up, grid_boxes, draw_src, booklet_order_within_signature
from core.signature_logic import Plan

def impose_A5_booklet(src_doc: fitz.Document, plan: Plan, log):
    dst = fitz.Document()
    page_rect = a4_rect_landscape()

    N = len(src_doc)
    total_needed = plan.total_pages
    padded = list(range(N)) + [None] * (total_needed - N)

    cursor = 0
    for S in plan.sequence:
        rel = padded[cursor:cursor + S]
        if len(rel) < S:
            rel += [None] * (S - len(rel))

        order = booklet_order_within_signature(S)
        for (front, back) in order:
            sheet = dst.new_page(width=page_rect.width, height=page_rect.height)
            left_box, right_box = split_2up(page_rect)
            fL = rel[front[0]-1] if 1 <= front[0] <= S else None
            fR = rel[front[1]-1] if 1 <= front[1] <= S else None
            draw_src(sheet, src_doc, fL, left_box)
            draw_src(sheet, src_doc, fR, right_box)

            sheet = dst.new_page(width=page_rect.width, height=page_rect.height)
            left_box, right_box = split_2up(page_rect)
            bL = rel[back[0]-1] if 1 <= back[0] <= S else None
            bR = rel[back[1]-1] if 1 <= back[1] <= S else None
            draw_src(sheet, src_doc, bL, left_box)
            draw_src(sheet, src_doc, bR, right_box)

        cursor += S

    if log is not None:
        log.append(f"Created {len(dst)} A4 landscape pages (duplex spreads) for A5 booklet.")
    return dst

def impose_A6_nup(src_doc: fitz.Document, plan: Plan, log):
    dst = fitz.Document()
    page_rect = a4_rect_portrait()
    boxes = grid_boxes(page_rect, 2, 2)

    N = len(src_doc)
    padded = list(range(N)) + [None] * (plan.total_pages - N)

    i = 0
    while i < len(padded):
        page = dst.new_page(width=page_rect.width, height=page_rect.height)
        for box in boxes:
            if i >= len(padded):
                break
            draw_src(page, src_doc, padded[i], box)
            i += 1

    if log is not None:
        log.append(f"Created {len(dst)} A4 portrait pages with 4-up (A6 panels).")
    return dst

def impose_A7_nup(src_doc: fitz.Document, plan: Plan, log):
    dst = fitz.Document()
    page_rect = a4_rect_landscape()
    boxes = grid_boxes(page_rect, 2, 4)

    N = len(src_doc)
    padded = list(range(N)) + [None] * (plan.total_pages - N)

    i = 0
    while i < len(padded):
        page = dst.new_page(width=page_rect.width, height=page_rect.height)
        for box in boxes:
            if i >= len(padded):
                break
            draw_src(page, src_doc, padded[i], box)
            i += 1

    if log is not None:
        log.append(f"Created {len(dst)} A4 landscape pages with 8-up (A7 panels).")
    return dst
