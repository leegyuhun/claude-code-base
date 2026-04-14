### GitLab

GitLab Personal Access Token을 채워야 합니다.

```
GitLab → 우상단 프로필 → Preferences → Access Tokens
→ Name: claude-code, Scopes: api, read_api 체크 → Create
```

```bash
cp .mcp.json.example .mcp.json
# 그 다음 .mcp.json에서 YOUR_GITLAB_TOKEN 교체
```

MCP 서버가 활성화되면 Claude Code가 GitLab MR 조회, 생성, 코멘트 등을 직접 처리할 수 있게 됩니다. 
Node.js가 설치돼 있으면 `npx`가 첫 실행 시 자동으로 패키지를 받습니다.


### Redmine 상태 ID 매핑

## status-id 
``` 
New=1, Confirmed=11, Assigned=10, InProgress=2, Resolved=3
Closed=5, NeedsFeedback=7, Rejected=8
```