import math
import fitz
from typing import List, Optional, Any,Dict

from core.geometry import a4_rect_portrait, grid_boxes, draw_src, process_2d_array

# grids: rows >= cols
LEVEL_GRIDS = {1: (2, 1), 2: (2, 2), 3: (4, 2)}

# ---------------------------
# Build panel maps per signature
# ---------------------------

def paginate_to_matrix(num_pages: int, level: int, counter: int = 1) -> List[List[Optional[int]]]:
    """Rows of length 2**level, filled from `counter`… (pad last row with None)."""
    inner_len = 1 << level
    matrix: List[List[Optional[int]]] = []
    page = counter
    last = counter + num_pages - 1
    while page <= last:
        row: List[Optional[int]] = []
        for _ in range(inner_len):
            row.append(page if page <= last else None)
            page += 1
        matrix.append(row)
    return matrix


def compute_signature_panel_maps(sequence: List[int], level: int,log) -> List[List[int]]:
    """
    For each signature size in `sequence`:
      - build its matrix starting at a running counter,
      - call process_2d_array to get the **panel map** (page n → panel #),
      - return list of panel maps (no None).
    """
    rows, cols = LEVEL_GRIDS[level]
    per_side = rows * cols
    per_sheet = per_side * 2
    panel_maps: List[List[int]] = []
    counter = 1

    for i, sig_pages in enumerate(sequence, start=1):
        checkBlanks = sig_pages % per_sheet
        blankPages = 0
        if checkBlanks != 0:
            blankPages = per_sheet - checkBlanks
            sig_pages += blankPages
            log.append(f"[INFO] Signature #{i} padded with {blankPages} blank pages to {sig_pages} total pages")

        start = counter
        end = counter + sig_pages - 1

        # NOTE: no inline blanks here
        matrix = paginate_to_matrix(sig_pages, level, counter=start)
        log.append(f"[DEBUG] Signature #{i} initial matrix (level={level}): {matrix}")

        arranged = process_2d_array(matrix, level)
        panel_map = [x[0] for x in arranged if x and x[0] is not None]
        panel_maps.append(panel_map)

        counter = end + 1

    return panel_maps


def sheets_needed(pages: int, level: int) -> int:
    rows, cols = LEVEL_GRIDS[level]
    per_side = rows * cols
    per_sheet = per_side * 2
    return math.ceil(pages / per_sheet)

def split_signature_into_pages(panel_map: List[int], level: int) -> List[List[int]]:
        rows, cols = LEVEL_GRIDS[level]
        per_side = rows * cols
        return [panel_map[i:i + per_side] for i in range(0, len(panel_map), per_side)]


def describe_split_pages(
    split_pages: List[List[Optional[Any]]],
    level: int,
    *,
    page_offset: int = 0,
    panel_offset: int = 0,
) -> List[Dict[str, int | str]]:
    rows, cols = LEVEL_GRIDS[level]
    per_side = rows * cols
    per_sheet = per_side * 2

    out: List[Dict[str, int | str]] = []
    for chunk_idx, panels in enumerate(split_pages):
        base_local = chunk_idx * per_side
        for pos_in_chunk, global_panel in enumerate(panels):
            local_page = base_local + pos_in_chunk + 1
            global_page = page_offset + local_page

            if global_panel is None:
                out.append({
                    "local_page": local_page,
                    "global_page": global_page,
                    "local_panel": -1,
                    "global_panel": -1,
                    "sheet": -1,
                    "side": "blank",
                    "orientation": "none",
                    "blank": "yes"
                })
                continue

            local_panel = global_panel - panel_offset
            sheet_idx = (global_panel - 1) // per_sheet + 1
            ofs = (global_panel - 1) % per_sheet
            is_front = ofs < per_side
            side = "front" if is_front else "back"
            orientation = "L→R" if is_front else "R→L"

            out.append({
                "local_page": local_page,
                "global_page": global_page,
                "local_panel": local_panel,
                "global_panel": global_panel,
                "sheet": sheet_idx,
                "side": side,
                "orientation": orientation,
                "blank": "no"
            })
    return out


def draw_booklet_signatures_by_global_panels(
    src_doc: fitz.Document,
    desc_per_signature: List[List[Dict[str, int | str]]],
    pages_per_signature: List[int],
    level: int,
) -> fitz.Document:
    rows, cols = LEVEL_GRIDS[level]
    per_side = rows * cols
    per_sheet = per_side * 2
    rect = a4_rect_portrait()

    out = fitz.open()
    boxes = grid_boxes(rect, rows, cols)

    # >>> rotation fix (CCW): make level 1 look "<-", level 3 look "->"
    front_angle = (((level-1) * 90) + 90) % 360     # fronts
    back_angle  = (front_angle + 180) % 360     # backs
    # <<<

    prev_panel_count = 0  # how many panels allocated by previous signatures

    for sig_idx, (sig_desc, sig_pages) in enumerate(zip(desc_per_signature, pages_per_signature), start=1):
        # sheets and the global-panel range reserved for THIS signature
        sheets = sheets_needed(sig_pages, level)
        sig_panel_start = prev_panel_count + 1  # first global panel number for this signature

        # Build a lookup only from this signature's description
        gp_to_src = {}
        for e in sig_desc:
            gp = e.get("global_panel", -1)
            if gp is None:
                continue
            gp = int(gp)
            gp_src_val = e.get("global_page", None)
            if gp_src_val is None:
                continue
            gp_src = int(gp_src_val) - 1
            if gp >= sig_panel_start and 0 <= gp_src < len(src_doc):
                gp_to_src[gp] = gp_src

        # Create pages for this signature only
        for _ in range(sheets * 2):
            out.new_page(width=rect.width, height=rect.height)

        # Draw this signature (no bleed-over to the next)
        for s in range(1, sheets + 1):
            # front page for this sheet
            front_page_idx = len(out) - (sheets * 2) + (s - 1) * 2
            front_page = out[front_page_idx]
            gp_start_front = sig_panel_start + (s - 1) * per_sheet
            for k in range(per_side):
                gp = gp_start_front + k
                src_idx = gp_to_src.get(gp)
                if src_idx is None:
                    continue
                front_page.show_pdf_page(boxes[k], src_doc, src_idx, rotate=front_angle)

            # back page for this sheet
            back_page_idx = front_page_idx + 1
            back_page = out[back_page_idx]
            gp_start_back = gp_start_front + per_side
            for k in range(per_side):
                gp = gp_start_back + k
                src_idx = gp_to_src.get(gp)
                if src_idx is None:
                    continue
                back_page.show_pdf_page(boxes[k], src_doc, src_idx, rotate=back_angle)

        # advance reserved panel space for the next signature
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

    total_sheets = sum(sheets_needed(s, level) for s in plan.sequence)
    log.append(f"[INFO] Total sheets (all signatures): {total_sheets}")

    panel_maps = compute_signature_panel_maps(plan.sequence, level, log)

    desc_per_signature = []
    pages_per_signature = []

    for i, panel_map in enumerate(panel_maps, start=1):
        page_offset = sum(plan.sequence[:i - 1])
        panel_offset = page_offset

        log.append(f"[INFO] Drawing signature #{i} with {len(panel_map)} pages...")
        log.append(f"[DEBUG] Panel map: {panel_map}")

        newarrayy = split_signature_into_pages(panel_map, level)
        log.append(f"[DEBUG] Split into pages {newarrayy}")

        desc = describe_split_pages(newarrayy, level,
                                    page_offset=page_offset,
                                    panel_offset=panel_offset)
        orig_sig_pages = plan.sequence[i - 1]  
        for rec in desc:
            if rec["local_page"] > orig_sig_pages:
                rec["global_page"] = None
                rec["blank"] = "yes"
            else:
                rec["blank"] = "no"
        log.append(f"[DEBUG] Page descriptions: {desc}")

        desc_per_signature.append(desc)
        pages_per_signature.append(len(panel_map))

    

    out = draw_booklet_signatures_by_global_panels(
        src_doc,
        desc_per_signature,
        pages_per_signature,
        level
    )

    return out