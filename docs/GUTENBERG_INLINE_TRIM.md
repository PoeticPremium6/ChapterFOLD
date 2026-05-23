# Gutenberg inline marker trimming

Patch 013 adds a small cleanup layer for Gutenberg books where boilerplate and
real content exist in the same retained spine item.

The spine selector fixes whole-file decisions. This trim fixes inside-file
boilerplate:

- remove text before `*** START OF THE PROJECT GUTENBERG EBOOK ... ***`
- remove text after `*** END OF THE PROJECT GUTENBERG EBOOK ... ***`
- clear headings like `The Project Gutenberg eBook of ...` when they were used
  as section titles

This is designed for odd cases such as `The Real Cyberpunk Fakebook`, where the
selector may keep all spine items to avoid data loss but should still remove the
usage notice from the final output.
