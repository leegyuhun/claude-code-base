#!/usr/bin/env bash
# pretooluse-bash-guard.sh
# Claude Code PreToolUse Hook — Bash 위험 명령 차단
#
# 입력: stdin JSON {"tool_input": {"command": "..."}}
# 출력: Exit 0 (허용) / Exit 2 (차단 + 메시지)

set -uo pipefail

INPUT=$(cat)
COMMAND=$(python3 -c "
import sys, json
try:
    d = json.loads(sys.stdin.read())
    print(d.get('tool_input', {}).get('command', ''))
except:
    print('')
" <<< "$INPUT" 2>/dev/null || echo "")

[ -n "$COMMAND" ] || exit 0

block() {
  echo ""
  echo "🚫 [bash-guard] $1"
  echo ""
  echo "  차단된 명령어: $COMMAND"
  echo ""
  exit 2
}

# ── 규칙 1: 디렉토리 체이닝 차단 ────────────────────────────────────
if echo "$COMMAND" | grep -qE '^\s*cd\s+[^\s&;]+\s*&&'; then
  block "디렉토리 체이닝(cd /path && ...)은 금지됩니다.
  → 절대 경로로 직접 명령을 실행하세요."
fi

# ── 규칙 2: master 브랜치 직접 push 차단 ────────────────────────────
if echo "$COMMAND" | grep -qE 'git push(\s+[^\s]+)?\s+master(\s|$)'; then
  block "master 브랜치 직접 push는 금지됩니다.
  → 브랜치 전략: Release → master PR을 통해 병합하세요."
fi

# ── 규칙 3: Release 브랜치 직접 push 차단 ───────────────────────────
if echo "$COMMAND" | grep -qE 'git push(\s+[^\s]+)?\s+Release(\s|$)'; then
  block "Release 브랜치 직접 push는 금지됩니다.
  → 브랜치 전략: 정기 배포 브랜치(2026_정기_N차) → Release PR을 통해 병합하세요."
fi

# ── 규칙 4: force push 차단 ─────────────────────────────────────────
if echo "$COMMAND" | grep -qE 'git push.+(-f\b|--force\b|--force-with-lease\b)'; then
  block "Force push는 공유 브랜치의 히스토리를 손상시킵니다.
  → 대안: 충돌을 해소하거나 새 커밋을 생성하세요."
fi

# ── 규칙 5: hard reset 차단 ─────────────────────────────────────────
if echo "$COMMAND" | grep -qE 'git reset\s+--hard'; then
  block "git reset --hard는 로컬 변경 사항을 영구적으로 삭제합니다.
  → 대안: 'git stash'로 임시 보관하거나 'git revert'를 사용하세요."
fi

# ── 규칙 6: 브랜치 명명 규칙 검증 (YSR 패턴) ───────────────────────
if echo "$COMMAND" | grep -qE 'git (checkout -b|switch -c)\s+'; then
  BRANCH=$(echo "$COMMAND" | grep -oE '(checkout -b|switch -c)\s+\S+' | awk '{print $NF}' | head -1)
  if [ -n "$BRANCH" ]; then
    # 허용 패턴 (하나라도 매칭 시 통과)
    ALLOWED=0
    # 패턴 1: Redmine 이슈 — {연도}_{분류}_#{이슈번호}
    echo "$BRANCH" | grep -qE '^[0-9]{4}_[^_]+_#[0-9]+$' && ALLOWED=1
    # 패턴 2: Sprint — {base}_sprint-{NN}
    echo "$BRANCH" | grep -qE '_sprint-[0-9]+$' && ALLOWED=1
    # 패턴 3: Hotfix — {base}_hotfix_{영문소문자-숫자-하이픈}
    echo "$BRANCH" | grep -qE '_hotfix_[a-z0-9-]+$' && ALLOWED=1

    if [ "$ALLOWED" -eq 0 ]; then
      block "브랜치 명명 규칙 위반: '$BRANCH'
  허용 패턴:
    ✓ {연도}_{분류}_#{이슈번호}        예: 2026_정기5차_#207500
    ✓ {base}_sprint-{NN}              예: main_delphi_sprint-01
    ✓ {base}_hotfix_{영문소문자-설명}  예: main_delphi_hotfix_login-fix
  허용되지 않는 패턴:
    ✗ 위 3가지에 해당하지 않는 임의 브랜치명"
    fi
  fi
fi

exit 0
