# Language Protocol

Three axes, decided separately:

| Axis | Language |
|:---|:---|
| Reasoning | English |
| Code, identifiers, comments, commit messages | English |
| Text the human reads | Korean |

The third axis is the one vendor workers get wrong. You are invoked through a shell
wrapper, so you do **not** inherit the calling session's output style -- if your
output reaches the user unedited, it must already be Korean. When your output is
consumed by the calling session rather than the user, English is correct and the
session translates.

Keep full orthography for whatever language you write. Never substitute an ASCII
lookalike for an accented character.

No emoji in text the human reads: it corrupts copied text. Headings and bold instead.
