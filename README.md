# covo-legal

The static pages Covo has to publish somewhere public, and the two Stripe
Connect sends people back to. Six files, no build step, no framework — they
are served as they are.

| file | what it is |
|---|---|
| `index.html` | the landing page the others hang off |
| `privacy.html` | privacy policy — linked from the App Store listing and from Settings |
| `terms.html` | terms of service — same two places |
| `support.html` | the support URL App Store Connect requires |
| `connect-complete.html` | where Stripe returns a business account after onboarding finishes |
| `connect-refresh.html` | where Stripe returns one whose onboarding link expired |

## Why this is its own repo

These are a requirement of shipping, not a part of the app: the App Store
listing links to the privacy policy and the support page by URL, and Stripe
Connect is configured with the two return URLs. They outlive any particular
build of the client, and the client cannot serve them — an app that has been
rejected is an app whose privacy policy still has to be reachable.

They lived for months in a folder with no git behind it, which is exactly the
wrong home for the two documents Covo is legally answerable for.

## Changing the policy pages

`privacy.html` and `terms.html` are commitments to users, not copy. Change them
deliberately, keep the "last updated" line honest, and remember that the App
Store review team reads the URL, not the file.

## The hook, and why it is not automatic

`hooks/pre-commit` runs `scripts/check_guidelines_claims.py`, which verifies that
`guidelines.html` still describes what `covo-backend` and `covo-frontend`
actually do. **Git does not clone hook configuration.** After cloning this repo:

```sh
git config core.hooksPath hooks
```

Without that line the hook is inert and nothing tells you. The check itself
skips with exit 0 when the sibling repos are not checked out beside this one, so
it is safe on a machine that only has this repo.

`guidelines.html` is the one page here that makes checkable claims about code it
cannot see. It says "we block X" where the backend blocks X, and it is organised
around the report categories the app shows. Change a category in `red_flag.py`
and, without this check, the only signal is a public page quietly describing
moderation that no longer happens.
