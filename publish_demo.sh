#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"
EXPECTED="git@github.com:iamrichmack111/exerx-eye.git"
CURRENT="$(git remote get-url origin 2>/dev/null || true)"
case "$CURRENT" in
  git@github.com:iamrichmack111/exerx-eye.git|https://github.com/iamrichmack111/exerx-eye.git) ;;
  *) echo "Wrong origin: $CURRENT"; echo "Expected: $EXPECTED"; exit 1 ;;
esac

python3 - <<'PY'
from pathlib import Path
p=Path('README.md')
text=p.read_text(encoding='utf-8') if p.exists() else '# ExerxEye\n'
start='<!-- EXERXEYE-DEMO:START -->'
end='<!-- EXERXEYE-DEMO:END -->'
block='''<!-- EXERXEYE-DEMO:START -->
## HQ narrated demo

ExerxEye includes a 1080p product-demo pipeline narrated with Piper **en_US-ryan-high**. The **HQ Piper Demo** workflow captures the real Flask UI with Playwright, renders an H.264/AAC MP4 with FFmpeg, uploads it as a workflow artifact, and attaches it to the latest GitHub Release.

[View the latest ExerxEye release](https://github.com/iamrichmack111/exerx-eye/releases/latest)
<!-- EXERXEYE-DEMO:END -->'''
if start in text and end in text:
    a=text.index(start); b=text.index(end)+len(end)
    text=text[:a]+block+text[b:]
else:
    text=text.rstrip()+'\n\n'+block+'\n'
p.write_text(text,encoding='utf-8')
PY

touch .gitignore
for x in '.demo-cache/' '.demo-venv/' 'demo/captures/' 'demo/render/'; do
  grep -qxF "$x" .gitignore || echo "$x" >> .gitignore
done

git add demo/ .github/workflows/demo.yml publish_demo.sh README.md .gitignore
git commit -m "feat: add 1080p HQ Piper narrated demo workflow" || true
git push origin main

gh workflow run demo.yml
sleep 3
RUN_ID="$(gh run list --workflow demo.yml --limit 1 --json databaseId --jq '.[0].databaseId')"
echo "Demo workflow started: $RUN_ID"
echo "Watching build..."
gh run watch "$RUN_ID" --exit-status

echo
echo "Demo build complete. Latest release:"
gh release view --json tagName,url --jq '"\(.tagName)  \(.url)"'
