import math
from dataclasses import dataclass
from typing import List, Tuple, Optional
from config import SIG_PAIRS

@dataclass
class Plan:
    pair: Tuple[int, int]
    count_hi: int
    count_lo: int
    total_pages: int
    blanks: int
    expression: str
    sequence: List[int]

def compute_plan_for_pair(n_pages: int, a: int, b: int) -> Plan:
    large, small = (a, b) if a > b else (b, a)

    lo_fit = n_pages // small
    used = lo_fit * small
    r = n_pages - used

    delta = large - small
    if r <= 0:
        count_hi = 0
        count_lo = lo_fit
    else:
        x = math.ceil(r / delta)
        if x > lo_fit:
            count_hi = x
            count_lo = 0
        else:
            count_hi = x
            count_lo = lo_fit - x

    total = count_hi * large + count_lo * small
    remainder4 = total % 4
    if remainder4 != 0:
        total += (4 - remainder4)

    blanks = total - n_pages

    parts = []
    if count_hi > 0:
        parts.append(f"{count_hi}*{large}")
    if count_lo > 0:
        parts.append(f"{count_lo}*{small}")
    expression = " + ".join(parts) if parts else f"0*{large}"

    # sequence
    seq = []
    if count_hi > 0 and count_lo > 0:
        hi_remaining = count_hi
        lo_remaining = count_lo
        while hi_remaining > 0 and lo_remaining > 0:
            seq.append(large)
            hi_remaining -= 1
            seq.append(small)
            lo_remaining -= 1
        seq.extend([large] * hi_remaining)
        seq.extend([small] * lo_remaining)
    elif count_hi > 0:
        seq = [large] * count_hi
    elif count_lo > 0:
        seq = [small] * count_lo

    return Plan(pair=(large, small), count_hi=count_hi, count_lo=count_lo,
                total_pages=total, blanks=blanks, expression=expression, sequence=seq)

def choose_best_plan(n_pages: int):
    plans = [compute_plan_for_pair(n_pages, a, b) for (a, b) in SIG_PAIRS]
    plans.sort(key=lambda p: (p.blanks, p.total_pages))
    return plans[0], plans
