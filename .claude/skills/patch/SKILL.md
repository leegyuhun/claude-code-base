---
name: patch
description: YSR EMR 코드베이스에 버그 수정을 적용한다. bug-investigator의 분석 결과를 받아 Delphi 또는 C# 코드를 수정하고, AssemblyInfo.cs 버전 업 및 수정 요약을 작성한다. patch-author 에이전트가 이 스킬을 사용한다.
---

# 코드 패치 스킬

## 수정 원칙

### 최소 범위 수정
필요한 코드만 변경한다. 버그와 직접 관련 없는 코드는 건드리지 않는다. 들여쓰기, 공백, 변수명 정리 등 스타일 수정은 하지 않는다.

### 읽기 우선
수정 전 반드시 전체 파일을 읽는다. 부분 컨텍스트로 수정하면 숨겨진 의존성을 놓칠 수 있다.

### 주석 처리 우선 삭제
로직을 제거할 때는 삭제보다 주석 처리를 먼저 고려한다. YSR은 레거시 시스템으로 숨겨진 의존성이 많다.

## Delphi 수정 패턴

### 주석 스타일
```pascal
// 변경 이유: [이슈 번호] 수정 내용
{ 기존 코드 주석 처리:
  OldCode;
}
```

### 프로시저/함수 수정
- 파라미터 추가 시 기존 호출부 전체 확인 필요 (`Grep`으로 함수명 검색)
- `uses` 절에 유닛 추가 시 순환 참조 방지 — 같은 파일에서 서로 참조하지 않는지 확인

### 버전 관리
Delphi 프로젝트는 `{프로젝트명}.dpr`의 버전을 수동으로 관리하지 않음. C# 쪽만 버전 업.

## C# 수정 패턴

### AssemblyInfo.cs 버전 업 (필수)
C# 프로젝트 파일 수정 시 반드시 함께 업데이트:
```csharp
// 수정 전
[assembly: AssemblyVersion("1.0.0.X")]
[assembly: AssemblyFileVersion("1.0.0.X")]

// 수정 후 (마지막 자리 +1)
[assembly: AssemblyVersion("1.0.0.X+1")]
[assembly: AssemblyFileVersion("1.0.0.X+1")]
```

`AssemblyInfo.cs` 위치: 프로젝트 루트 또는 `Properties/` 하위.

### 주석 스타일
```csharp
// [이슈번호] 수정 이유
// 기존 코드: OldCode();
NewCode();
```

### Null 체크
C# 코드 수정 시 null 참조 예외 가능성을 검토한다. YSR은 nullable 어노테이션을 사용하지 않는 구버전 코드가 많다.

## 수정 후 체크리스트

- [ ] 수정 파일의 전체 코드를 읽고 수정했는가
- [ ] C# 수정 시 `AssemblyInfo.cs` 버전을 올렸는가
- [ ] 같은 기능의 다른 버전 파일(`_D7`, `_BL` 등)도 확인했는가
- [ ] 수정한 함수/클래스를 사용하는 다른 코드가 영향받지 않는가
- [ ] `_workspace/02_patch_summary.md`에 수정 내용을 기록했는가

## 수정 요약 작성

수정 완료 후 `_workspace/02_patch_summary.md` 작성:
- 수정 파일 목록 (경로 + 변경 유형 + 한 줄 요약)
- 각 파일별 변경 상세 (무엇을, 왜)
- 미처리 항목 (수정 못한 것과 사유)
