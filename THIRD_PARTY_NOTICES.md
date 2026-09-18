# Third-Party Notices

This plugin does not bundle third-party application binaries, proprietary SDKs, credentials, generated media, or vendor source code beyond the vendored skills declared below.

## Vendored skills (verbatim, content-pinned)

The three skills under `skills/` are vendored verbatim from
[full-aigc-skills/minimax-skills](https://github.com/full-aigc-skills/minimax-skills)
(vendored at commit `0b72343a8d5674aa430d42ba8c72d575cadbba8a`):

- `minimax-multimodal-toolkit`
- `minimax-music-gen`
- `minimax-music-playlist`

Upstream license: Apache-2.0. Content integrity is pinned per skill by SHA-256
in `skills.lock.json`; the `check` gate fails on any drift. The upstream skill
`minimax-multimodal-toolkit` relies on the third-party `mmx` CLI
(`npm install -g mmx-cli`); this plugin does not bundle or distribute that CLI.

## Interoperability references

References to MiniMax, Hailuo, 海螺, Codex, ZCode, Kimi, and other product names
identify interoperability targets. Their trademarks and software remain the
property of their respective owners.

MiniMax API access requires the user's own API key configured via the
`MINIMAX_API_KEY` environment variable (or an `mmx` CLI login); nothing here
ships credentials, and no paid call is made without the user's explicit request.
