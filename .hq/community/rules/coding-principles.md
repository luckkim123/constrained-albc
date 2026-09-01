# Coding Principles

Write the least code that solves the stated problem. Stop at the first option that
holds:

1. **Does this need to exist?** Speculative need, skip it and say so in one line.
2. **Already in this codebase?** A helper, type, or pattern that lives here already
   wins. Look before you write.
3. **Standard library?** Use it.
4. **Native platform feature?** A DB constraint over app code, CSS over JS.
5. **An already-installed dependency?** Use it. Never add one for a few lines.
6. **One line?** One line.
7. **Only then** the minimum code that works.

- No interface with one implementation, no factory for one product, no config for a
  value that never changes.
- Deletion beats addition. Boring beats clever.
- A bug report names a symptom. Fix the root cause: one guard in the shared function,
  not a guard in every caller.
- Match the surrounding style even where you would do it differently. Do not
  "improve" adjacent code you were not asked to touch.
- Mark a deliberate shortcut with its ceiling and its upgrade path in a comment.

Never simplify away: input validation at trust boundaries, error handling that
prevents data loss, security measures, accessibility basics, or anything explicitly
requested.
