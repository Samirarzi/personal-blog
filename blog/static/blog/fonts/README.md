# Self-hosted fonts for Samir's blog

These font families match the typography declared by the reference site
[jadi.space](https://jadi.space/) on 2026-10-31. The font files are supplied
locally so the site does not depend on a font CDN at runtime.

## Included faces

| Family | Weight | File |
| --- | --- | --- |
| Roboto Slab | 400 / regular | `roboto-slab-latin-400.woff2` |
| Roboto Slab | 700 / bold | `roboto-slab-latin-700.woff2` |
| Fira Code | 300 / light | `fira-code-latin-300.woff2` |
| Fira Code | 400 / regular | `fira-code-latin-400.woff2` |
| Fira Code | 700 / bold | `fira-code-latin-700.woff2` |

These are Latin subsets suitable for the current English interface. A future
Persian interface would need an appropriate additional typeface and coverage.
No font files are modified or renamed.

## Provenance and licenses

Roboto Slab is by Christian Robertson and the Roboto Slab Project Authors.
Google Fonts identifies this family as Apache License 2.0 in its
[authoritative metadata](https://github.com/google/fonts/blob/main/apache/robotoslab/METADATA.pb).
Keep `RobotoSlab-LICENSE.txt` with the distributed assets. Its original text is
from [Google Fonts](https://github.com/google/fonts/blob/main/apache/robotoslab/LICENSE.txt).

Fira Code is by the Fira Code Project Authors and is licensed under the
SIL Open Font License 1.1. Keep `FiraCode-LICENSE.txt` with the distributed
assets. Its original text is from the
[Fira Code project](https://github.com/tonsky/FiraCode/blob/master/LICENSE).

The unmodified WOFF2 files use the reference site's Latin webfont distribution:

- https://jadi.space/fonts/roboto-slab-latin-400.woff2
- https://jadi.space/fonts/roboto-slab-latin-700.woff2
- https://jadi.space/fonts/fira-code-latin-300.woff2
- https://jadi.space/fonts/fira-code-latin-400.woff2
- https://jadi.space/fonts/fira-code-latin-700.woff2

Preserve these licenses and the attribution below when moving the files.

## Attribution

Roboto Slab: Copyright 2018 The Roboto Slab Project Authors
(https://github.com/googlefonts/robotoslab).

Fira Code: Copyright (c) 2014 The Fira Code Project Authors
(https://github.com/tonsky/FiraCode).

## Typography roles

Use `"Roboto Slab", Georgia, serif` for body copy and article prose, normally
weight 400 and line-height 1.675. Use weight 700 for emphasized prose.

Use `"Fira Code", "Lucida Console", Monaco, monospace` for the header,
navigation, headings, metadata, code and small interface details. The reference
uses 400 for h1/h2, 300 for smaller headings, and 700 for the site logo. Its
default body font size is 16px; desktop h1 is 38px and h2 is 32px.

Use `font-display: swap` and serve the assets from `/static/blog/fonts/`.
Keep mobile input text at least 16px even when matching compact desktop metadata.
