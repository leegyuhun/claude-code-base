---
# paths 없음 → 모든 파일 작업 시 항상 로드
---


## !! CP949 인코딩 필수 규칙 (최우선 / HIGHEST PRIORITY)

이 프로젝트의 `.pas`, `.dfm` 파일은 **CP949(EUC-KR) 인코딩**입니다.
프로젝트 내부 파일뿐 아니라 `ComUnit/`, `Common/`, `CommonBL/`, `CommonV7/` 등 **외부 공유 유닛도 동일**합니다.

### 왜 한글이 깨지는가 (근본 원인)

Claude Code 도구들은 내부적으로 UTF-8 기반으로 동작한다.
CP949 파일을 Read 하면 한글이 깨진 문자로 표시되고,
Edit 도구로 저장 시 그 깨진 표현이 올바른 CP949 바이트로 복원된다는 보장이 없다.
즉, "깨진 한글을 new_string에 그대로 복사"해도 바이트 손상이 발생할 수 있다.

### 절대 금지 (NEVER)

- **Write 도구 절대 사용 금지 (NEVER USE Write TOOL)**
  `.pas`/`.dfm` 파일에 Write 도구 사용 시 UTF-8 변환으로 한글 전체 파괴.
  파일 전체 재작성이 필요해도 반드시 **Edit 도구로 청크 단위 수정**.

- **한글이 포함된 줄을 old_string/new_string 범위에 포함시키지 말 것 (CRITICAL)**
  한글 포함 줄이 Edit의 매칭/쓰기 과정에 들어가면 CP949 바이트 손상이 발생한다.
  Edit의 old_string/new_string 경계는 **반드시 한글이 없는 줄 기준**으로 설정할 것.

- **Python subprocess/바이너리 패치 금지**: subprocess로 외부 명령을 호출하거나 바이너리 패치로 `.pas` 파일을 수정하지 말 것. 인코딩 손상 위험. (표준 파일 I/O는 허용 — 아래 참조)

- **CP949 파일에 한글 주석 추가 금지**: Edit 도구는 파일 전체를 UTF-8로 재작성하므로 기존 CP949 한글 바이트가 파괴됨.
  CP949 파일을 수정할 때는 **PowerShell + Encoding 949** 방식만 안전.

- **UTF-8 BOM 파일은 한글 주석 허용**: BOM(`EF BB BF`)으로 시작하는 파일은 Edit 도구로 한글 주석 추가 가능.
  파일 인코딩 확인: `python -c "data=open('file.pas','rb').read(3); print(data.hex())"`
  `efbbbf` → UTF-8 BOM (안전), 그 외 → CP949 (Edit 금지)

- **기존 한글 주석 수정/삭제 금지**: 깨져 보여도(`���`, `�Լ�` 등) 원본 CP949 바이트이므로 절대 건드리지 않음.

### 필수 준수 (ALWAYS)

- **Edit 범위 설정 원칙**: old_string의 시작과 끝을 한글이 없는 줄로 맞출 것.
  한글 포함 줄을 건너뛰어야 한다면, Edit을 여러 번 나눠서 한글 줄을 우회할 것.

- **새 코드 삽입 위치**: 한글 주석 블록과 분리된 위치에 삽입. 한글 줄 바로 위/아래도 가급적 피할 것.

### CP949 파일에 한글 주석을 추가해야 할 때 (MUST USE Python)

Edit/Write 도구는 절대 사용 불가. 반드시 아래 Python 방식으로만 추가할 것.

```python
# Bash 도구로 실행
python -c "
with open('파일경로.pas', 'r', encoding='cp949') as f:
    content = f.read()
content = content.replace('삽입기준_영문텍스트', '삽입기준_영문텍스트 // 한글 주석 내용')
with open('파일경로.pas', 'w', encoding='cp949') as f:
    f.write(content)
"
```

Python 표준 파일 I/O는 CP949 인코딩을 정확히 처리하므로 한글이 깨지지 않음.
사용자가 한글 주석 추가를 요청하면 이 방법을 사용할 것.

PowerShell 방식도 동작하지만 Python을 우선 사용할 것:
```powershell
$enc = [System.Text.Encoding]::GetEncoding(949)
$content = [System.IO.File]::ReadAllText("파일경로.pas", $enc)
$content = $content -replace '(삽입기준_영문텍스트)', '$1 // 한글 주석 내용'
[System.IO.File]::WriteAllText("파일경로.pas", $content, $enc)
```
