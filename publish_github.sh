#!/usr/bin/env bash
set -euo pipefail

REPO="iamrichmack111/exerx-eye"
REMOTE="git@github.com:iamrichmack111/exerx-eye.git"
SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="${TMPDIR:-/tmp}/exerx-eye-publish-$USER"

for cmd in git rsync python3 npm npx; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "ERROR: missing required command: $cmd"; exit 1; }
done

if [[ ! -f "$SOURCE/app.py" || ! -f "$SOURCE/requirements.txt" ]]; then
  echo "ERROR: publish_github.sh must stay inside the ExerxEye project folder."
  exit 1
fi

echo "==> Publishing only to $REMOTE"
rm -rf "$WORK"
git clone "$REMOTE" "$WORK"

rsync -a --delete \
  --exclude='.git' \
  --exclude='.venv' \
  --exclude='node_modules' \
  --exclude='playwright-report' \
  --exclude='test-results' \
  --exclude='instance/*.db' \
  --exclude='instance/.secret' \
  "$SOURCE/" "$WORK/"

cd "$WORK"
git remote set-url origin "$REMOTE"

current_remote="$(git remote get-url origin)"
[[ "$current_remote" == "$REMOTE" ]] || { echo "ERROR: wrong remote: $current_remote"; exit 1; }

echo "==> Python setup"
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

echo "==> Playwright setup"
npm install
npx playwright install chromium

echo "==> Generate correct 1440x900 README screenshots"
rm -f screenshots/*.png
npx playwright test tests/screenshots.spec.cjs --project=chromium

.venv/bin/python - <<'PY'
from pathlib import Path
from struct import unpack

expected = [
    Path('screenshots/01-exercise-library.png'),
    Path('screenshots/02-exercise-library-dark.png'),
    Path('screenshots/03-login.png'),
    Path('screenshots/04-signup.png'),
]

for p in expected:
    if not p.exists() or p.stat().st_size < 10_000:
        raise SystemExit(f'Bad or missing screenshot: {p}')
    with p.open('rb') as f:
        if f.read(8) != b'\x89PNG\r\n\x1a\n':
            raise SystemExit(f'Not a PNG: {p}')
        f.read(4)
        if f.read(4) != b'IHDR':
            raise SystemExit(f'Invalid PNG: {p}')
        width, height = unpack('>II', f.read(8))
    if (width, height) != (1440, 900):
        raise SystemExit(f'Wrong dimensions for {p}: {width}x{height}')
    print(f'OK {p}: {width}x{height}')
PY

echo "==> Update README badges and gallery"
.venv/bin/python - <<'PY'
from pathlib import Path
import re

p = Path('README.md')
text = p.read_text(encoding='utf-8') if p.exists() else '# ExerxEye\n'
text = re.sub(
    r'\n?<!-- EXERXEYE-GITHUB:START -->.*?<!-- EXERXEYE-GITHUB:END -->\n?',
    '\n',
    text,
    flags=re.S,
)

block = '''<!-- EXERXEYE-GITHUB:START -->
[![CI + Playwright](https://github.com/iamrichmack111/exerx-eye/actions/workflows/ci.yml/badge.svg)](https://github.com/iamrichmack111/exerx-eye/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-Web_App-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Playwright](https://img.shields.io/badge/Tested_with-Playwright-2EAD33?logo=playwright)](https://playwright.dev/)
![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)
![PWA](https://img.shields.io/badge/PWA-Ready-5A0FC8?logo=pwa)
![Dark Mode](https://img.shields.io/badge/Dark_Mode-Ready-111111)

## Screenshots

### Exercise Library — Light
<img src="screenshots/01-exercise-library.png" alt="ExerxEye exercise library in light mode" width="900">

### Exercise Library — Dark
<img src="screenshots/02-exercise-library-dark.png" alt="ExerxEye exercise library in dark mode" width="900">

### Login
<img src="screenshots/03-login.png" alt="ExerxEye login screen" width="900">

### Signup
<img src="screenshots/04-signup.png" alt="ExerxEye signup screen" width="900">
<!-- EXERXEYE-GITHUB:END -->'''

lines = text.strip().splitlines()
if lines and lines[0].startswith('#'):
    title = lines[0]
    rest = '\n'.join(lines[1:]).strip()
    text = title + '\n\n' + block + ('\n\n' + rest if rest else '') + '\n'
else:
    text = '# ExerxEye\n\n' + block + '\n\n' + text.strip() + '\n'
p.write_text(text, encoding='utf-8')
PY

for entry in '.venv/' 'node_modules/' 'playwright-report/' 'test-results/' 'instance/*.db' 'instance/.secret'; do
  grep -qxF "$entry" .gitignore 2>/dev/null || echo "$entry" >> .gitignore
done

echo "==> Commit and push main"
git add .
git commit -m "release: ExerxEye with Playwright screenshots CI badges and release" || true
git push -u origin main

git fetch --tags origin >/dev/null 2>&1 || true
n=0
while git rev-parse -q --verify "refs/tags/v10.0.$n" >/dev/null 2>&1; do
  n=$((n + 1))
done
tag="v10.0.$n"
echo "==> Create tag $tag"
git tag -a "$tag" -m "ExerxEye $tag"
git push origin "$tag"

if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  echo "==> Description and repository topics"
  gh repo edit "$REPO" \
    --description "ExerxEye — Flask fitness and workout tracker with workout generation, weekly planning, progress analytics, exports, PWA support, dark mode, animations and Playwright CI." \
    --add-topic flask \
    --add-topic python \
    --add-topic fitness \
    --add-topic workout-tracker \
    --add-topic sqlite \
    --add-topic playwright \
    --add-topic pwa \
    --add-topic dark-mode

  gh release create "$tag" \
    --repo "$REPO" \
    --title "ExerxEye ${tag#v} — Organized Motion + Features" \
    --notes "ExerxEye with organized Home / Explore / Train / Track navigation, workout generation, weekly planning, progress analytics, username accounts, dark mode, exports, installable PWA support, animations, correctly rendered 1440x900 Playwright screenshots, README badges and CI/CD."
  echo "Release created: $tag"
else
  echo "NOTE: gh is not authenticated. Main and tag $tag were pushed; GitHub description/topics/release creation was skipped."
fi

echo
echo "DONE — published to $REMOTE"
echo "Screenshots:"
ls -lh screenshots/*.png
