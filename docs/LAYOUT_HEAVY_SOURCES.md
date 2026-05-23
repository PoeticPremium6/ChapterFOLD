# Layout-heavy / ASCII-heavy source handling

Some Project Gutenberg sources are not ordinary prose. `The Real Cyberpunk Fakebook` is a good example: the text includes ASCII banners, divider blocks, diagrams, old line-break artifacts, and layout-dependent punctuation.

Patch 014 adds a conservative cleanup layer for these sources:

- removes or normalises accidental Unicode/control artifacts;
- turns the common `U+FFFE` hyphen artifact into `-`;
- collapses repeated decorative separator blocks such as `*****` / `=====` into a single `***` line;
- leaves ordinary prose, dictionary-style entries, and most intentional symbols alone.

This is deliberately not a full ASCII-art renderer. The goal is to make layout-heavy EPUBs less noisy in book/PDF output without damaging normal novels or fanfic exports.
