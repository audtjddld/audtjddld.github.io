---
title: "Claude Sonnet 4.5 11월 30일 종료와 API 2026-10-21 전환 점검(Java SDK 3.0), JUnit 6.2.0-M1 병렬 실행 기본값 변화"
description: "2026년 11월 16일 기술 브리핑. 2주 앞으로 다가온 claude-sonnet-4-5 종료일과 temperature·top_p·top_k가 400 오류가 되는 Anthropic API 버전 2026-10-21, anthropic-java 3.0.0의 인증 헤더·타입 변화를 Java·Kotlin 백엔드 관점에서 정리하고, 11월 15일 나온 JUnit 6.2.0-M1의 병렬 실행기 기본값·@CsvSource 엄격 파싱·Kotlin assertThrows 변화를 1차 출처로 짚습니다."
date: 2026-11-16 09:40:00 +0900
categories: [기술뉴스]
tags: [AI, Claude, Anthropic, Claude API, LLM 마이그레이션, anthropic-java, Spring AI, JUnit, JUnit 6, 테스트, Java, Kotlin]
---

월요일 브리핑은 "이번 주와 다음 몇 주 안에 실제로 깨질 수 있는 것" 두 가지를 다룬다. AI 쪽은 새 모델 소식 대신 **마감이 정해진 변경**을 골랐다. Claude Sonnet 4.5(`claude-sonnet-4-5-20250929`)가 11월 30일에 종료되는데, 대체 모델로 옮기면서 SDK를 함께 올리면 API 버전 `2026-10-21`의 파괴적 변경까지 한꺼번에 맞게 된다. Java 쪽은 11월 15일 나온 JUnit 6.2.0-M1이다. 마일스톤이지만 병렬 실행기 기본값과 `@CsvSource` 파싱 규칙이 바뀌어, 다음 정식 버전으로 올릴 때 테스트 결과가 달라질 수 있다.

두 소식 모두 새로 발표된 것은 아니거나(Anthropic 종료 공지는 9월 30일, API 버전은 10월 21일) 사전 릴리스(JUnit M1)다. 오늘 새로 터진 뉴스로 소개하는 것이 아니라, 일정상 지금 확인해야 할 항목으로 정리했다. 직접 운영 환경에 적용해 본 결과가 아니라 공식 문서를 읽고 추린 점검 목록이다.

| 소식 | 시점 | 1차 출처 |
| --- | --- | --- |
| Claude Sonnet 4.5 종료 | 2026-09-30 공지, **2026-11-30 종료** | [Model deprecations](https://platform.claude.com/docs/en/about-claude/model-deprecations) |
| API 버전 `2026-10-21` (샘플링 파라미터 제거 등) | 2026-10-21 | [API versions](https://platform.claude.com/docs/en/api/versioning), [마이그레이션 가이드](https://platform.claude.com/docs/en/api/migration-2026-10-21) |
| JUnit 6.2.0-M1 | 2026-11-15 19:33 (KST) | [GitHub 릴리스](https://github.com/junit-team/junit-framework/releases/tag/r6.2.0-M1), [릴리스 노트](https://docs.junit.org/6.2.0-M1/release-notes/) |

## 1. Claude Sonnet 4.5 종료 D-14, 그리고 함께 따라오는 API 2026-10-21

### 무엇이 바뀌나 (확인된 사실)

**모델 종료.** Anthropic의 모델 지원 중단 문서에 따르면 `claude-sonnet-4-5-20250929`는 9월 30일 지원 중단(deprecated)으로 바뀌었고, **2026년 11월 30일 종료(retired)** 된다. 권장 대체 모델은 `claude-sonnet-5-5`다. 종료 이후 이 모델로 보낸 요청은 실패한다. 같은 표에서 `claude-opus-4-5-20251101`은 아직 Active지만 종료 예정일이 "2026년 11월 24일 이후"로 적혀 있어, 이 모델도 곧 일정이 잡힐 가능성이 있다.

이 날짜는 Claude API, Claude Platform on AWS, Anthropic이 운영하는 Google Cloud, Microsoft Foundry에 적용된다. Amazon Bedrock과 Google이 운영하는 Google Cloud 경로는 각 플랫폼이 별도 일정을 정한다고 문서에 명시돼 있다.

**API 버전 `2026-10-21`.** 모델을 바꾸는 김에 SDK 메이저 버전을 올리면, 요청 헤더가 `anthropic-version: 2026-10-21`로 바뀐다. 이 버전의 주요 파괴적 변경은 다음과 같다.

- `temperature`, `top_p`, `top_k`를 보내면 **기본값이라도 400 오류**가 난다. 이 파라미터 없이 보내면 기본값(`temperature` 1.0)으로 샘플링된다. Claude 4.7 이후 모델은 원래 기본값만 받으므로 동작이 같지만, Sonnet 4.6처럼 다른 값을 받던 모델에서 `temperature`를 낮춰 일관성을 얻던 요청은 그 효과를 잃고, 대신할 설정은 없다.
- `assistant` 메시지에 `document` 블록을 직접 넣거나, `user` 메시지의 `text` 블록에 비어 있지 않은 `citations`를 넣으면 400 오류가 난다.
- Admin API 응답에서 옛 필드명(`roles`, `group_id`, `workspace_id` 등)이 빠지고 새 이름만 남는다.

**Java SDK 3.0.0.** 마이그레이션 가이드 기준으로 `2026-10-21`을 처음 보내는 Java SDK는 `com.anthropic:anthropic-java` 3.0.0이다. Java·Kotlin 백엔드에서 체감할 변화는 이렇다.

- API 키를 `X-Api-Key`가 아니라 **`Authorization: Bearer`** 헤더로 보낸다. API 자체는 두 헤더 모두 받지만, `X-Api-Key`를 읽거나 넣는 사내 프록시·게이트웨이·로그 마스킹 필터·테스트 스텁은 바꿔야 한다.
- 클라이언트 하나에 자격 증명 하나만 허용한다. 빌더에 `apiKey`와 `authToken`을 함께 설정하면 `build()`에서 `IllegalStateException`이 난다.
- `MessageParam`이 역할별 타입의 유니언이 되면서 `MessageParam.builder()`가 사라지고 `MessageParam.ofUser(...)` 같은 팩토리 메서드를 쓴다. 블록 목록을 받는 빌더 메서드 이름도 바뀌었다(`addUserMessageOfBlockParams` → `addUserMessageOfContentBlockParams` 등).
- `AnthropicBackend.apiKey()` 등 일부 getter가 `Optional`을 반환하고, 인터셉터에서 `anthropic-version`을 덮어쓰려면 `putHeader` 대신 `replaceHeaders`를 써야 한다.
- 레거시 Text Completions API가 Java SDK에서 제거됐고, 라이선스는 MIT에서 Apache 2.0으로 바뀌었다.

참고로 Spring AI 2.1.0-RC2는 Anthropic Java SDK를 3.4.0으로 올렸다([11월 11일 브리핑](/posts/gemini-4-carbon-api-migration-spring-ai-2-1-rc2/)에서 다뤘다). Spring AI를 통해 Claude를 쓰는 팀도 결국 같은 변경을 만나게 된다.

### 누가 영향을 받나

- **`claude-sonnet-4-5-20250929`를 모델 ID로 고정해 둔 서비스**: 챗봇·요약·분류 배치 등. 설정 파일이 아니라 코드 상수나 DB 설정 테이블에 모델 ID가 박혀 있으면 놓치기 쉽다.
- **`temperature=0`을 공통 기본값으로 넣는 래퍼를 둔 팀**: 사내 LLM 게이트웨이나 공통 클라이언트가 모든 요청에 샘플링 파라미터를 붙이고 있다면, SDK를 올리는 순간 전 요청이 400이 될 수 있다.
- **API 키 헤더를 다루는 인프라**: 키를 `X-Api-Key`로 주입·검사·마스킹하는 API 게이트웨이, egress 프록시, 감사 로그 파이프라인.
- **Bedrock 사용자**: `2026-10-21`은 Bedrock에서 Claude 4.7 이후 모델에만 제공된다. 4.6 이하 모델을 Bedrock에서 부르는 코드는 SDK와 API 버전을 지금 그대로 유지하라는 것이 공식 안내다.

### 왜 중요한가 (분석)

*이하는 의견이다.* 모델 교체 자체는 모델 ID 한 줄이지만, 실제 작업량은 "모델 교체 + SDK 메이저 업그레이드 + API 버전 변경"이 겹치면서 커진다. 특히 샘플링 파라미터 제거는 컴파일 단계에서 드러나지 않을 수 있다. 요청을 JSON으로 직접 만들거나 HTTP 클라이언트로 부르는 코드는 런타임에 400을 맞고 나서야 알게 된다. 반대로 SDK 3.x는 해당 필드가 타입에서 사라졌기 때문에 컴파일 오류로 일찍 드러난다. 그래서 SDK를 쓰는 쪽이 오히려 안전한 경로다.

두 작업을 한 번에 할지 나눌지도 판단이 필요하다. 마감이 걸린 것은 모델 종료뿐이므로, 일정이 빠듯하다면 **먼저 현재 SDK(API 버전 `2023-06-01`) 그대로 모델 ID만 `claude-sonnet-5-5`로 바꾸고 품질을 확인한 뒤, SDK 3.x 전환은 별도 배포로 나누는 편**이 장애 원인을 분리하기 쉽다. 다만 Claude 4.7 이후 모델은 기존 API 버전에서도 기본값이 아닌 샘플링 값을 보내면 오류를 낸다고 문서에 적혀 있으므로, 대체 모델로 옮길 때 샘플링 파라미터는 어차피 정리해야 한다.

### 지금 확인할 것

1. **사용량 감사**: Claude Console의 Usage 페이지에서 Export한 CSV로 API 키별·모델별 사용량을 보고, `claude-sonnet-4-5-20250929` 호출이 남아 있는지 확인한다. 공식 문서가 안내하는 방법이다.
2. **코드 전수 검색**: `claude-sonnet-4-5`, `claude-opus-4-5`, `temperature`, `top_p`, `top_k`, `X-Api-Key`, `x-api-key`를 저장소 전체와 설정 저장소(Helm values, Spring 설정, DB 시드)에서 검색한다.
3. **대체 모델로 평가 세트 재실행**: `claude-sonnet-5-5`로 우리 도메인 프롬프트를 돌려 품질·지연·비용을 비교한다. `temperature`를 낮춰 결정성을 얻던 기능(분류, JSON 추출)은 출력 스키마 검증과 재시도 로직이 있는지 함께 본다.
4. **SDK 3.x 전환 시 인프라 동시 점검**: `Authorization: Bearer`로 바뀐 키 헤더를 프록시·게이트웨이·로그 마스킹이 처리하는지, 빌더에 자격 증명이 둘 이상 설정돼 있지 않은지 확인한다.
5. **Opus 4.5 일정 주시**: `claude-opus-4-5-20251101`의 종료 예정일이 "11월 24일 이후"로 잡혀 있으므로, 사용 중이라면 지원 중단 문서를 구독하거나 주기적으로 확인한다.

## 2. JUnit 6.2.0-M1: 병렬 실행기 기본값과 @CsvSource 파싱이 바뀐다

### 무엇이 바뀌었나 (확인된 사실)

JUnit 팀은 11월 15일(UTC 10:33, 한국 시간 19:33) 6.2.0-M1을 사전 릴리스로 냈다. 최신 정식 버전은 여전히 6.1.3이다. 릴리스 노트에서 실무에 영향이 큰 항목을 골랐다.

- **병렬 실행기 기본값 변경**: 병렬 실행을 켜면 `junit.jupiter.execution.parallel.config.executor-service`의 기본값이 `WORKER_THREAD_POOL`이 된다. `ParallelHierarchicalTestExecutorServiceFactory`를 쓰는 테스트 엔진도 같은 기본값을 따른다. 새 병렬 실행기 구현이 기본으로 쓰인다는 뜻이다.
- **병렬 실행 순서 버그 수정**: `@TestFactory`가 반환한 스트림이 예외를 던지면, 이미 만든 동적 테스트가 끝난 다음에 `@AfterEach`가 실행되도록 고쳐졌다. 이전에는 병렬 실행 시 정리 코드가 동적 테스트와 동시에 돌 수 있었다. `@ParameterizedTest`의 인자 소스가 예외를 던질 때도 비슷한 문제가 플랫폼 수준에서 수정됐다.
- **`@CsvSource` 엄격 파싱(파괴적 변경)**: `value[]`의 각 요소를 독립된 CSV 문서로 다룬다. 한 줄의 닫히지 않은 따옴표가 다른 줄에 번지지 않는다. 대신 **주석 문자(기본 `#`)로 시작하는 레코드가 있으면 테스트가 실패**하고, `commentCharacter`는 구분자·따옴표 문자와 달라야 한다.
- **타임아웃 정밀도**: `assertTimeout`, `assertTimeoutPreemptively`, `@Timeout`이 밀리초 미만 정밀도로 시간을 잰다. 타임아웃 값이 양수가 아니거나 2^63 나노초 이상이면 `PreconditionViolationException`이 난다. 타임아웃 실패 메시지에는 스레드 덤프를 켜는 방법에 대한 힌트가 붙는다.
- **Kotlin `assertThrows` 변형 추가**: 예외 타입을 타입 파라미터(reified) 대신 클래스 값으로 받는 오버로드가 생겼다. 예외 클래스를 값으로 넘기는 `@ParameterizedTest`에서 쓰기 어려웠던 문제를 풀기 위한 것이다.
- **확장 API 정리**: `ExtensionContext.Namespace`·`Store`가 deprecated되고 `org.junit.jupiter.api.store` 패키지의 `Namespace`·`Store`로 옮겨 간다. 대부분은 import만 바꾸면 된다고 릴리스 노트에 적혀 있다.
- **기타**: `@Suite` 클래스에 쓰는 `@Disabled`가 추가됐고, `junit-platform-console-standalone`이 `junit-bom`에 포함됐으며, 설정 파라미터가 `META-INF/junit-platform-configuration-metadata.json`으로 기계가 읽을 수 있는 형태로 문서화된다.

### 누가 영향을 받나

- **`junit.jupiter.execution.parallel.enabled=true`로 CI 시간을 줄여 온 팀**: 실행기 구현이 바뀌면 공유 자원(임베디드 DB, 고정 포트, 정적 상태)에 기대던 테스트의 숨은 경쟁 조건이 드러날 수 있다.
- **`@CsvSource`에 `#`로 시작하는 값(해시태그, 색상 코드, 주석처럼 쓴 줄)을 둔 테스트**: 다음 정식 버전으로 올리면 실패로 바뀐다.
- **사내 JUnit 확장을 만든 팀**: `ExtensionContext.Store`·`Namespace`를 쓰는 확장은 deprecation 경고를 받는다.
- **Kotlin 테스트 코드**: 새 `assertThrows` 오버로드는 추가 기능이라 기존 코드를 깨지는 않는다.

### 왜 중요한가 (분석)

*이하는 의견이다.* M1을 프로덕션 빌드에 바로 쓸 이유는 없다. 하지만 병렬 실행기 기본값처럼 "설정을 건드리지 않았는데 동작이 바뀌는" 변경은 정식 버전이 나온 뒤 Spring Boot 같은 BOM을 따라 조용히 들어올 수 있다. Spring Boot가 언제 JUnit 6.2를 관리 버전으로 올릴지는 이 글을 쓰는 시점에 확인하지 못했다. 병렬 실행을 쓰는 팀이라면 별도 브랜치에서 M1으로 CI를 몇 번 돌려 보는 비용이 낮다. 반대로 `@TestFactory`·파라미터화 테스트에서 정리 코드가 일찍 돌던 문제는, 원인을 모르던 간헐적 실패(flaky test)의 정체였을 수도 있다.

### 지금 확인할 것

1. **`@CsvSource` 검색**: 테스트 코드에서 `#`로 시작하는 CSV 레코드가 있는지 찾고, 따옴표로 감싸거나 `commentCharacter`를 바꿔 둔다. 지금 고쳐도 6.1.x에서 문제없이 돈다.
2. **병렬 실행 브랜치 테스트**: 병렬 실행을 켠 프로젝트라면 `org.junit:junit-bom:6.2.0-M1`로 올린 브랜치에서 CI를 여러 번 돌려 실패율을 비교한다.
3. **타임아웃 값 점검**: `@Timeout(0)`이나 음수, 극단적으로 큰 값을 쓰는 곳이 있는지 확인한다.
4. **사내 확장 import 정리**: `ExtensionContext.Store`·`Namespace` 사용처를 `org.junit.jupiter.api.store`로 옮길 준비를 한다.

## 정리

| 분야 | 소식 | 지금 할 일 |
| --- | --- | --- |
| AI 서비스 | Claude Sonnet 4.5 11/30 종료 | 사용량 CSV 감사, `claude-sonnet-5-5`로 평가 재실행 |
| 백엔드·인프라 | API `2026-10-21`, anthropic-java 3.0.0 | 샘플링 파라미터 제거, `Authorization: Bearer` 대응 |
| 개발 생산성(테스트) | JUnit 6.2.0-M1 | `@CsvSource` 주석 문자 점검, 병렬 실행 브랜치 테스트 |

## 출처

- [Model deprecations](https://platform.claude.com/docs/en/about-claude/model-deprecations), Anthropic (Sonnet 4.5 지원 중단 공지 2026-09-30, 종료 2026-11-30)
- [API versions](https://platform.claude.com/docs/en/api/versioning), Anthropic
- [Migrating to API version 2026-10-21](https://platform.claude.com/docs/en/api/migration-2026-10-21), Anthropic
- [JUnit 6.2.0-M1 릴리스](https://github.com/junit-team/junit-framework/releases/tag/r6.2.0-M1), GitHub, 2026-11-15 10:33 UTC
- [JUnit 6.2.0-M1 Release Notes](https://docs.junit.org/6.2.0-M1/release-notes/), JUnit
