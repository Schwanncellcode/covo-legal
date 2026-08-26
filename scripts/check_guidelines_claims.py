#!/usr/bin/env python3
"""guidelines.html makes claims about code in two other repositories. Check them.

WHY THIS EXISTS. The page says "we block X" where the backend blocks X, and it
is organised around the report categories the app actually shows. Both of those
are facts about code in repositories this one cannot see at runtime and does not
depend on. Nothing else stops them diverging: change a category in red_flag.py
and this page becomes a published, public, false statement about moderation,
with no failure anywhere.

That is the same argument as covo-frontend's check-notification-routes, which
exists because a rule written in prose ("keep this in step with the backend")
drifted twice while being read by people who believed it.

PUBLIC REPO NOTE: everything this script hardcodes — the six blocking category
names, the nine report reasons — is ALREADY PUBLISHED on guidelines.html. It
quotes nothing from the private repositories that is not on the public page. Keep
it that way: a check that leaks the thing it checks is not an improvement.

Skips with exit 0 if the sibling repos are not checked out, the same way
check-notification-routes does. A check that fails because a sibling directory
moved gets deleted rather than fixed.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GH = os.path.dirname(HERE)
BACKEND = os.path.join(GH, 'covo-backend')
FRONTEND = os.path.join(GH, 'covo-frontend')

RED_FLAG = os.path.join(BACKEND, 'app/core/red_flag.py')
USERS_PY = os.path.join(BACKEND, 'app/routers/users.py')
PROFILE_JS = os.path.join(FRONTEND, 'src/screens/UserProfileScreen.js')
PAGE = os.path.join(HERE, 'guidelines.html')

for path, label in ((RED_FLAG, 'covo-backend'), (PROFILE_JS, 'covo-frontend')):
    if not os.path.exists(path):
        print(f'check_guidelines_claims: skipped ({label} not checked out beside this repo)')
        sys.exit(0)

# Published on guidelines.html, so safe to name here.
EXPECTED_BLOCKING = {
    'drugs', 'weapons', 'violence_threats',
    'hate_speech', 'sexual_exploitation', 'scams_fraud',
}

failures = []


def die(msg):
    print(f'check_guidelines_claims: CANNOT VERIFY — {msg}', file=sys.stderr)
    print('A check that cannot read its source must fail, not pass quietly.', file=sys.stderr)
    sys.exit(2)


page = open(PAGE, encoding='utf-8').read()
body = page.split('<body>', 1)[1].lower() if '<body>' in page else die('guidelines.html has no <body>')

# ---- 1 & 2. categories and severities -------------------------------------
src = open(RED_FLAG, encoding='utf-8').read()
try:
    block = src[src.index('RED_FLAG_KEYWORDS'):src.index('_SEVERITY_RANK')]
except ValueError:
    die('red_flag.py no longer contains RED_FLAG_KEYWORDS ... _SEVERITY_RANK')

# Anchored on indentation: a looser regex mis-parsed this once, reporting six
# categories where there are seven, because a nested list swallowed one.
names = re.findall(r'^    "(\w+)": \{', block, re.M)
sevs = re.findall(r'^        "severity": "(\w+)"', block, re.M)
if not names or len(names) != len(sevs):
    die(f'could not pair categories with severities ({len(names)} names, {len(sevs)} severities)')

cats = dict(zip(names, sevs))
blocking = {k for k, v in cats.items() if v == 'block'}

if blocking != EXPECTED_BLOCKING:
    added = blocking - EXPECTED_BLOCKING
    gone = EXPECTED_BLOCKING - blocking
    if added:
        failures.append(f'blocking categories ADDED and not on the page: {sorted(added)}')
    if gone:
        failures.append(f'page claims we block these, and we no longer do: {sorted(gone)}')

if cats.get('suspicious_intent') != 'flag':
    failures.append(
        "suspicious_intent is no longer flag-only (now "
        f"{cats.get('suspicious_intent')!r}). The page deliberately says NOTHING "
        "about it because every caller discards flag results — if that changed, "
        "the page should describe it."
    )

# ---- 3 & 4. report reasons ------------------------------------------------
ui = open(PROFILE_JS, encoding='utf-8').read()
reasons = re.findall(r"\{ text: '([^']+)', value: '([^']+)' \}", ui)
if len(reasons) < 9:
    die(f'found only {len(reasons)} report reasons in UserProfileScreen.js — has the picker changed shape?')

for label, _value in reasons:
    if label.lower() not in body:
        failures.append(f'report reason "{label}" is offered in the app but appears nowhere on the page')

if os.path.exists(USERS_PY):
    users = open(USERS_PY, encoding='utf-8').read()
    try:
        tm = users[users.index('tier_map = {'):users.index('tier = tier_map')]
    except ValueError:
        die('users.py no longer contains tier_map')
    mapped = set(re.findall(r'"(\w+)":\s*"\w+"', tm))
    offered = {v for _l, v in reasons}
    if mapped != offered:
        failures.append(
            'the app offers report reasons the backend does not grade, or vice versa: '
            f'{sorted(mapped ^ offered)}'
        )

# ---- report ---------------------------------------------------------------
print(
    f'check_guidelines_claims: {len(cats)} categories '
    f'({len(blocking)} blocking), {len(reasons)} report reasons compared'
)

if failures:
    print('', file=sys.stderr)
    print('check_guidelines_claims: guidelines.html no longer matches the code.', file=sys.stderr)
    print('This page is PUBLIC and describes moderation. Wrong is worse than absent.', file=sys.stderr)
    print('', file=sys.stderr)
    for f in failures:
        print(f'  - {f}', file=sys.stderr)
    print('', file=sys.stderr)
    sys.exit(1)

print('check_guidelines_claims: clean — every claim still matches the code.')
