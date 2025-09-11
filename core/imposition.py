# core/imposition.py

import math
import fitz
from typing import List, Dict, Any

# Use ONLY the helpers imported from geometry.py
from core.geometry import (
    a4_rect_portrait,
    grid_boxes,
    process_2d_array,
    paginate_to_matrix,
    split_front_back,
    front_pairs,
    back_pairs,
    panels_per_side,
    panel_to_sheet_side,
)

# Local grids for drawing (box layout)
LEVEL_GRIDS = {1: (2, 1), 2: (2, 2), 3: (4, 2), 4: (4, 4)}



# ------------------------
# Debuggable panel mapping
# ------------------------
def compute_signature_panel_maps(sequence: List[int], level: int, log: List[str]) -> List[List[int]]:
    """
    Build a panel_map per signature using PADDED page counts, and LOG each step.
    Each panel_map is a list of global-panel numbers (taking the left slot of each arranged row).
    """
    per_side  = panels_per_side(level)
    per_sheet = per_side * 2

    panel_maps: List[List[int]] = []
    panel_offset_padded = 0  # global panel numbering starts at 1 and includes blanks

    for i, orig_sig_pages in enumerate(sequence, start=1):
        # pad to full sheets (panels)
        rem = orig_sig_pages % per_sheet
        blank_pages = 0
        padded_sig_pages = orig_sig_pages
        if rem != 0:
            blank_pages = per_sheet - rem
            padded_sig_pages += blank_pages
            log.append(f"[INFO] Signature #{i} padded with {blank_pages} blank pages to {padded_sig_pages} total panels")

        # Number panels globally (start at prior padded panels + 1)
        matrix_start_panel = panel_offset_padded + 1
        matrix = paginate_to_matrix(padded_sig_pages, level, counter=matrix_start_panel)
        log.append(f"[DEBUG] Signature #{i} initial matrix (level={level}, padded={padded_sig_pages}): {matrix}")

        arranged = process_2d_array(matrix, level)
        log.append(f"[DEBUG] Signature #{i} arranged: {arranged}")

        panel_map = [x[0] for x in arranged if x and x[0] is not None]
        panel_maps.append(panel_map)

        # advance offset by PADDED count
        panel_offset_padded += padded_sig_pages

    return panel_maps


# ------------------------
# Drawing helpers
# ------------------------
def _rtl_order_indices(rows: int, cols: int) -> List[int]:
    out: List[int] = []
    for r in range(rows):
        base = r * cols
        for c in range(cols - 1, -1, -1):
            out.append(base + c)
    return out


def _build_imposition_records_from_pairs(
    fronts,
    backs,
    front_pairs_list,
    back_pairs_list,
    *,
    level: int,
    start_global_page_real: int,  # sum of ORIGINAL pages before this signature + 1
    orig_sig_pages: int,          # original (un-padded) pages in this signature
    padded_sig_pages: int,        # padded pages used for panels
    panel_offset_padded: int,     # sum of PADDED panels before this signature
    binding: str = "LTR"          # "LTR" or "RTL"
) -> List[Dict[str, Any]]:
    """
    Emit compact records with fields REQUIRED for drawing:
      - global_page (None for tail blanks)
      - local_panel (1..padded_sig_pages, fixed inside signature)
      - global_panel (panel_offset_padded + local_panel)
      - sheet, side, orientation
    """
    records: List[Dict[str, Any]] = []
    sig_first_global_panel = panel_offset_padded + 1  # 1-based

    def _emit(local_page: int, panel_global_number: int):
        # Convert global panel number to LOCAL (1..padded)
        local_panel = panel_global_number - sig_first_global_panel + 1
        global_panel = panel_global_number

        sheet, side, orientation = panel_to_sheet_side(global_panel, level, binding=binding)
        # global_page ignores blanks; None for tail blanks
        is_blank = local_page > orig_sig_pages
        global_page = None if is_blank else (start_global_page_real + local_page - 1)

        records.append({
            'global_page': global_page,
            'local_panel': local_panel,
            'global_panel': global_panel,
            'sheet': sheet,
            'side': side,
            'orientation': orientation
        })

    # fronts (pairs provide the LOCAL PAGES; panels are the GLOBAL PANEL numbers from arranged)
    for i, panels in enumerate(fronts):
        if i >= len(front_pairs_list):
            break
        p_left  = panels[0] if len(panels) > 0 else None
        p_right = panels[1] if len(panels) > 1 else None
        pg_left, pg_right = front_pairs_list[i]  # local pages
        if p_left  is not None: _emit(pg_left,  p_left)
        if p_right is not None: _emit(pg_right, p_right)

    # backs
    for i, panels in enumerate(backs):
        if i >= len(back_pairs_list):
            break
        p_left  = panels[0] if len(panels) > 0 else None
        p_right = panels[1] if len(panels) > 1 else None
        pg_left, pg_right = back_pairs_list[i]
        if p_left  is not None: _emit(pg_left,  p_left)
        if p_right is not None: _emit(pg_right, p_right)

    # Order by global_page (put blanks last)
    records.sort(key=lambda r: (r['global_page'] is None, r['global_page'] if r['global_page'] is not None else 10**9))
    return records


def draw_booklet_signatures_by_global_panels(
    src_doc: fitz.Document,
    desc_per_signature: List[List[Dict[str, int | str]]],
    pages_per_signature_padded: List[int],   # padded panel counts per signature
    level: int,
    *,
    binding: str = "LTR"  # "LTR" or "RTL"
) -> fitz.Document:
    rows, cols = LEVEL_GRIDS[level]
    per_side = rows * cols
    per_sheet = per_side * 2
    rect = a4_rect_portrait()

    out = fitz.open()
    boxes = grid_boxes(rect, rows, cols)

    # rotation (portrait output)
    if level == 4:
        front_angle = 0
        back_angle  = 0
    else:
        delta = 0 if binding.upper() == "LTR" else 180
        front_angle = ((((level - 1) * 90) + 90) + delta) % 360
        if binding.upper() == "RTL" and level in (1, 2):
            front_angle = (front_angle - 180) % 360
        back_angle  = (front_angle + 180) % 360

    if level==2:
         back_angle = (back_angle - 180) % 360

    # placement orders per binding
    ltr_order = list(range(per_side))          # row-major L→R
    rtl_order = _rtl_order_indices(rows, cols) # row-major R→L
    if binding.upper() == "RTL":
        front_order = rtl_order
        back_order  = ltr_order
    else:
        front_order = ltr_order
        back_order  = rtl_order


    # NEW: for A5 (cols==1), RTL requires vertical flip (top↔bottom)
    vertical_flip = (cols == 1 and binding.upper() == "RTL")

    prev_panel_count = 0  # global panel offset within the OUTPUT

    for sig_idx, (sig_desc, sig_padded) in enumerate(zip(desc_per_signature, pages_per_signature_padded), start=1):
        sheets = math.ceil(sig_padded / per_sheet)
        sig_panel_start = prev_panel_count + 1

        # Map global_panel -> source page index (skip blanks)
        gp_to_src: Dict[int, int] = {}
        for e in sig_desc:
            gp = e.get("global_panel", -1)
            if gp is None or gp == -1:
                continue
            gp_src_val = e.get("global_page", None)
            if gp_src_val is None:
                continue  # tail blank; no source page
            gp_src = int(gp_src_val) - 1
            if gp >= sig_panel_start and 0 <= gp_src < len(src_doc):
                gp_to_src[gp] = gp_src

        # Allocate output pages for this signature (front+back per sheet)
        for _ in range(sheets * 2):
            out.new_page(width=rect.width, height=rect.height)

        for s in range(1, sheets + 1):
            # FRONT
            front_page_idx = len(out) - (sheets * 2) + (s - 1) * 2
            front_page = out[front_page_idx]
            gp_start_front = sig_panel_start + (s - 1) * per_sheet
            for k in range(per_side):
                # vertical flip for single-column RTL: reverse gp assignment along the column
                gp = gp_start_front + (per_side - 1 - k) if vertical_flip else gp_start_front + k
                src_idx = gp_to_src.get(gp)
                if src_idx is None:
                    continue
                box_idx = front_order[k]
                front_page.show_pdf_page(boxes[box_idx], src_doc, src_idx, rotate=front_angle)

            # BACK
            back_page_idx = front_page_idx + 1
            back_page = out[back_page_idx]
            gp_start_back = gp_start_front + per_side
            for k in range(per_side):
                gp = gp_start_back + (per_side - 1 - k) if vertical_flip else gp_start_back + k
                src_idx = gp_to_src.get(gp)
                if src_idx is None:
                    continue
                box_idx = back_order[k]
                back_page.show_pdf_page(boxes[box_idx], src_doc, src_idx, rotate=back_angle)

        prev_panel_count += sheets * per_sheet

    return out


def impose_cut_stack(src_doc: fitz.Document,
                     plan,
                     log: List[str],
                     *,
                     level: int = 1,
                     binding: str = "LTR",
                     emit_blank_tail_signature: bool = False) -> fitz.Document:
    log.append(f"[INFO] Source PDF opened: {len(src_doc)} pages")
    log.append(f"[INFO] Selected level: {level}")
    log.append(f"[INFO] Binding: {binding}")
    log.append(f"[INFO] Plan: {plan.expression}, sequence={plan.sequence}, blanks={plan.blanks}")

    # Stage 1: compute panel_maps (mainly for debugging/visibility)
    panel_maps = compute_signature_panel_maps(plan.sequence, level, log)

    desc_per_signature: List[List[Dict[str, int | str]]] = []
    pages_per_signature_padded: List[int] = []

    # Running offsets
    per_side  = panels_per_side(level)
    per_sheet = per_side * 2
    page_offset_real    = 0  # ORIGINAL pages (no blanks)
    panel_offset_padded = 0  # PADDED panels (includes blanks)

    for i, orig_sig_pages in enumerate(plan.sequence, start=1):
        # derive padded count directly
        rem = orig_sig_pages % per_sheet
        padded_sig_pages = orig_sig_pages if rem == 0 else orig_sig_pages + (per_sheet - rem)

        log.append(f"[INFO] Signature #{i}: real={orig_sig_pages}, padded={padded_sig_pages}")

        # Build arranged and split fronts/backs using GLOBAL panel numbers
        matrix = paginate_to_matrix(padded_sig_pages, level, counter=panel_offset_padded + 1)
        arranged = process_2d_array(matrix, level)
        fronts, backs = split_front_back(arranged)

        # Pairs are computed over PADDED length
        f_pairs = front_pairs(fronts, level, padded_sig_pages)
        b_pairs = back_pairs(backs,  level, padded_sig_pages)

        # Records: ONLY the fields required by draw()
        records = _build_imposition_records_from_pairs(
            fronts, backs, f_pairs, b_pairs,
            level=level,
            start_global_page_real=page_offset_real + 1,   # ignores blanks
            orig_sig_pages=orig_sig_pages,                  # original pages
            padded_sig_pages=padded_sig_pages,              # padded panels
            panel_offset_padded=panel_offset_padded,        # prior panels (incl. blanks)
            binding=binding
        )
        log.append(f"[DEBUG] Records (sig #{i}): {records}")

        desc_per_signature.append(records)
        pages_per_signature_padded.append(padded_sig_pages)

        # advance offsets
        page_offset_real    += orig_sig_pages
        panel_offset_padded += padded_sig_pages

    # Stage 2: render PDF using the compact records
    out = draw_booklet_signatures_by_global_panels(
        src_doc,
        desc_per_signature,
        pages_per_signature_padded,
        level,
        binding=binding
    )

    return out
