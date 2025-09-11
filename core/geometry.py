# core/geometry.py

import fitz
from typing import List, Optional, Tuple, Any
from config import PAGE_MARGIN  # (kept if used elsewhere)

LEVEL_GRIDS = {1: (2, 1), 2: (2, 2), 3: (4, 2),4 : (4, 4)}


def rotate_cw(seq: List[Any]) -> List[Any]:
    """
    90° clockwise rotation treating seq as a 2 x (n/2) grid:
    top = seq[:c], bottom = seq[c:], then [b0,t0,b1,t1,...].
    Examples:
      [1,2]             -> [2,1]
      [1,2,3,4]         -> [3,1,4,2]
      [1..8]            -> [5,1,6,2,7,3,8,4]
    """
    n = len(seq)
    if n == 1:
        return seq[:]
    c = n // 2
    top, bot = seq[:c], seq[c:]
    out: List[Any] = []
    for i in range(c):
        out.append(bot[i])
        out.append(top[i])
    return out


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


def process_2d_array(matrix: List[List[Any]], level: int) -> List[List[Any]]:
    if not matrix or not matrix[0]:
        return []

    current = [row[:] for row in matrix]

    # rotate once for level 3, twice for level 4, otherwise none
    rotations_left = 1 if level == 3 else (2 if level == 4 else 0)

    for _ in range(level):
        if len(current[0]) <= 2:
            break

        lefts, rights = [], []
        rotate_now = rotations_left > 0

        for arr in current:
            mid = len(arr) // 2
            L, R = arr[:mid], arr[mid:]
            if rotate_now:
                L = rotate_cw(L)
                R = rotate_cw(R)
            lefts.append(L)
            rights.append(R)

        current = lefts + rights

        if rotate_now:
            rotations_left -= 1

    return current



def split_front_back(arr: List[Any]) -> (List[Any], List[Any]):
    front = [x for i, x in enumerate(arr, start=1) if i % 2 == 1]
    back  = [x for i, x in enumerate(arr, start=1) if i % 2 == 0]
    return front, back


def front_pairs(fronts: List[List[Any]], level: int, signature_pages: int) -> List[Tuple[int, int]]:
    n = len(fronts)
    pairs: List[Tuple[int, int]] = []
    for k in range(n):
        odd  = 1 + 2 * k
        mate = signature_pages - 2 * k
        pairs.append((odd, mate))
    return pairs


def back_pairs(backs: List[List[Any]], level: int, signature_pages: int) -> List[Tuple[int, int]]:
    n = len(backs)
    pairs: List[Tuple[int, int]] = []
    for k in range(n):
        even = 2 + 2 * k
        mate = signature_pages - (2 * k + 1)
        pairs.append((even, mate))
    return pairs


def panels_per_side(level: int) -> int:
    rows, cols = LEVEL_GRIDS[level]
    return rows * cols


def panel_to_sheet_side(panel: int, level: int, *, binding: str = "LTR") -> Tuple[int, str, str]:
    per_side = panels_per_side(level)
    per_sheet = per_side * 2
    sheet = (panel - 1) // per_sheet + 1
    side_is_front = ((panel - 1) % per_sheet) < per_side
    side = "front" if side_is_front else "back"

    # Orientation label follows binding
    if binding.upper() == "RTL":
        orientation = "R→L" if side_is_front else "L→R"
    else:
        orientation = "L→R" if side_is_front else "R→L"

    return sheet, side, orientation


def end_blanks(signature_pages: int, blank_pages: int) -> set[int]:
    if blank_pages <= 0:
        return set()
    start = signature_pages - blank_pages + 1
    return set(range(start, signature_pages + 1))


def a4_rect_landscape() -> fitz.Rect:
    """A4 in landscape (w > h)."""
    r = fitz.paper_rect("a4")
    if r.width < r.height:
        r = fitz.Rect(r.y0, r.x0, r.y1, r.x1)
    return r


def a4_rect_portrait() -> fitz.Rect:
    """A4 in portrait (h > w)."""
    r = fitz.paper_rect("a4")
    if r.height < r.width:
        r = fitz.Rect(r.y0, r.x0, r.y1, r.x1)
    return r


def grid_boxes(rect: fitz.Rect, rows: int, cols: int) -> List[fitz.Rect]:
    """
    Produce rows×cols boxes (row-major: r0c0, r0c1, ...).
    """
    boxes: List[fitz.Rect] = []
    w = (rect.x1 - rect.x0) / cols
    h = (rect.y1 - rect.y0) / rows
    for r in range(rows):
        for c in range(cols):
            boxes.append(
                fitz.Rect(
                    rect.x0 + c * w,
                    rect.y0 + r * h,
                    rect.x0 + (c + 1) * w,
                    rect.y0 + (r + 1) * h,
                )
            )
    return boxes
