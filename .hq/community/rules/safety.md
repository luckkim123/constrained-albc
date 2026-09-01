# Safety

## Destructive operations

Every destructive operation goes through a recoverable path.

- **Delete** to the trash (`trash`, `gio trash`; inside a git repo, `git rm` plus a
  commit). Never a permanent erase. No trash available: confirm a copy exists
  elsewhere *and* get explicit approval that this is permanent.
- **Move** is `mv`, then `find`/`ls` the destination to confirm the files landed,
  and only then remove the source. Never in the same breath -- sync lag loses files.
- **Before overwriting or deleting, look at the target.** A file you have not read is
  a file you cannot judge as safe to lose.

The rule is *avoid irreversible loss*, not *always use trash*. Take the safest path
the environment offers.

## Secrets

Never read, echo, or embed: `.env` files, `*.pem`, `*.key`, anything matching
`credentials*` or `*secret*`, `~/.ssh/**`, `~/.aws/**`, `~/.config/gcloud/**`. If a
task appears to require one, stop and say which credential it needs and why.

Never hardcode a secret. Never log one. Parameterize SQL; validate input at the trust
boundary.

## Scope

Confirm before anything hard to reverse or outward-facing -- a push, a deploy, a
message to a third party. Approval for one such action does not extend to the next.
