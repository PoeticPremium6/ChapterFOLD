from __future__ import annotations

from core.impose_service import signature_sheet_pairs


def _side_tuple(side):
    if isinstance(side, tuple):
        return side
    if isinstance(side, list):
        return tuple(side)
    if hasattr(side, "left_page") and hasattr(side, "right_page"):
        return (side.left_page, side.right_page)
    if hasattr(side, "left") and hasattr(side, "right"):
        return (side.left, side.right)
    raise TypeError(f"Unsupported side object: {side!r}")


def _first_front_back(pairs):
    first = pairs[0]

    if hasattr(first, "front") and hasattr(first, "back"):
        return _side_tuple(first.front), _side_tuple(first.back)

    if isinstance(first, tuple) and len(first) == 2:
        return _side_tuple(first[0]), _side_tuple(first[1])

    if isinstance(first, list) and len(first) == 2:
        return _side_tuple(first[0]), _side_tuple(first[1])

    raise TypeError(f"Unsupported sheet pair object: {first!r}")


def test_ltr_first_16_page_signature_spread_is_outer_to_inner() -> None:
    pairs = signature_sheet_pairs(16, binding_direction="ltr")
    front, back = _first_front_back(pairs)

    assert front == (16, 1)
    assert back == (2, 15)


def test_rtl_first_16_page_signature_spread_is_inner_to_outer() -> None:
    pairs = signature_sheet_pairs(16, binding_direction="rtl")
    front, back = _first_front_back(pairs)

    assert front == (1, 16)
    assert back == (15, 2)
