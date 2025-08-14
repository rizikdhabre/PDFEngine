from core.signature_logic import compute_plan_for_pair

def test_compute_plan():
    p = compute_plan_for_pair(100, 32, 28)
    assert p.total_pages % 4 == 0
