from __future__ import annotations

from core.epub_service import preserve_special_short_line_blocks


def test_special_short_line_block_is_preserved():
    text = """Before.

“Fury said to a
mouse, That he
met in the
house,
‘Let us
both go to
law: I will
prosecute
you.—Come,
I’ll take no
denial; We
must have a
trial:
For really this
morning I’ve
nothing
to do.’

After.
"""

    result = preserve_special_short_line_blocks(text)

    assert '<div class="special-layout-block">' in result
    assert "Fury said to a" in result
    assert "After." in result


def test_short_dialogue_does_not_become_special_block():
    text = """“Yes,” said Alice.

“No,” said the Mouse.

“What?” said the Duck.

“Nothing,” said Alice.
"""

    result = preserve_special_short_line_blocks(text)

    assert '<div class="special-layout-block">' not in result
