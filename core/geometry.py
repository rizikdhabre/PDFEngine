import fitz
from typing import List, Optional, Tuple,Any
from config import PAGE_MARGIN

def rotate_cw(seq: List[Any]) -> List[Any]:
    """
    90° clockwise rotation treating seq as a 2 x (n/2) grid:
    top = seq[:c], bottom = seq[c:], then [b0,t0,b1,t1,...].
    Examples:
      [1,2]           -> [2,1]
      [1,2,3,4]       -> [3,1,4,2]   ([[1,2],[3,4]] -> [[3,1],[4,2]])
      [1,2,3,4,5,6,7,8] -> [5,1,6,2,7,3,8,4]
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

def process_2d_array(matrix: List[List[Any]], level: int) -> List[List[Any]]:
    if not matrix or not matrix[0]:
        return []

    current = [row[:] for row in matrix]
    flag = 0  # 0 = rotation not yet used; 1 = rotation already used

    for step in range(level):
        lefts, rights = [], []
        # Decide once per level whether to rotate this whole pass
        rotate_now = (level == 3 and flag == 0)

        for arr in current:
            mid = len(arr) // 2

            if rotate_now:
                L = rotate_cw(arr[:mid])   # rotate AFTER split
                # print(f"This is lefts step after step {lefts + [L]}")
                R = rotate_cw(arr[mid:])
                # print(f"This is rights step after step {rights + [R]}")
            else:
                L = arr[:mid]
                # print(f"This is lefts step after step {lefts + [L]}")
                R = arr[mid:]
                # print(f"This is rights step after step {rights + [R]}")

            lefts.append(L)
            rights.append(R)

        current = lefts + rights

        # Mark rotation as used so it happens only once total
        if rotate_now:
            flag = 1

    return current


def a4_rect_landscape() -> fitz.Rect:
    """A4 in landscape (w > h)."""
    r = fitz.paper_rect("a4")
    if r.width < r.height:
        r = fitz.Rect(r.y0, r.x0, r.y1, r.x1)  # swap
    return r


def a4_rect_portrait() -> fitz.Rect:
    """A4 in portrait (h > w)."""
    r = fitz.paper_rect("a4")
    if r.height < r.width:
        r = fitz.Rect(r.y0, r.x0, r.y1, r.x1)  # swap
    return r


def split_2up(rect: fitz.Rect) -> Tuple[fitz.Rect, fitz.Rect]:
    """Split into left/right halves."""
    midx = (rect.x0 + rect.x1) / 2.0
    left = fitz.Rect(rect.x0, rect.y0, midx, rect.y1)
    right = fitz.Rect(midx, rect.y0, rect.x1, rect.y1)
    return left, right


def split_tb(rect: fitz.Rect) -> Tuple[fitz.Rect, fitz.Rect]:
    """Split into top/bottom halves."""
    midy = (rect.y0 + rect.y1) / 2.0
    top = fitz.Rect(rect.x0, rect.y0, rect.x1, midy)
    bottom = fitz.Rect(rect.x0, midy, rect.x1, rect.y1)
    return top, bottom


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


def subdivide_boxes(rect: fitz.Rect, depth: int, first_axis: str = "tb") -> List[fitz.Rect]:
    """
    Recursively subdivide 'rect' into 2**depth panels in a folding-friendly order.

    For A7 with your method (fold forward → spine top → rotate CW → spine right),
    we split TOP/BOTTOM first (depth 1), then alternate LR/TB for deeper folds.

    depth = 0 -> [rect]
    depth = 1 -> [top, bottom]
    depth = 2 -> [top-left, top-right, bottom-left, bottom-right]
    depth = 3 -> 8 panels per side, etc.
    """
    if depth <= 0:
        return [rect]

    if first_axis == "tb":
        top, bottom = split_tb(rect)
        # alternate axis next
        return subdivide_boxes(top, depth - 1, "lr") + subdivide_boxes(bottom, depth - 1, "lr")
    else:
        left, right = split_2up(rect)
        return subdivide_boxes(left, depth - 1, "tb") + subdivide_boxes(right, depth - 1, "tb")


def draw_src(page: fitz.Page,
             src_doc: fitz.Document,
             idx: Optional[int],
             box: fitz.Rect,
             rotate: int = 0,
             margin: float = PAGE_MARGIN) -> None:
    """
    Draw zero-based page 'idx' from src_doc into 'box' with optional rotation.
    idx=None -> leave blank. 'rotate' is degrees (0, 90, 180, 270).
    """
    if idx is None:
        return
    if idx < 0 or idx >= len(src_doc):
        return
    inner = fitz.Rect(
        box.x0 + margin, box.y0 + margin,
        box.x1 - margin, box.y1 - margin
    )
    # show_pdf_page(rect, src, pno, clip=None, rotate=0, overlay=True)
    page.show_pdf_page(inner, src_doc, idx, rotate=rotate)
