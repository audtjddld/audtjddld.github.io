---
title: "Gemini 4 Hydrogen 출시: 3.8 Flash에서 옮길 때 깨지는 설정과 비용, Quarkus 4.0 CR1의 Java 21·Jackson 3 전환"
description: "2026년 11월 13일 기술 브리핑. Google Gemini 4 Hydrogen(gemini-4-hydrogen)의 가격·thinking_level·명시적 캐시 미지원 등 Gemini 3.8 Flash 마이그레이션 주의점과, Java 21 최소 요구·Jackson 3 패키지 변경·세미콜론 쿼리 구분자 제거를 담은 Quarkus 4.0.0.CR1을 1차 출처로 확인해 Java·Kotlin 백엔드 팀의 점검 항목을 정리합니다."
date: 2026-11-13 09:40:00 +0900
categories: [기술뉴스]
tags: [AI, Gemini, Gemini 4 Hydrogen, LLM API, 마이그레이션, LLM 비용, Quarkus, Quarkus 4, Jackson 3, Java 21, Java, Kotlin]
---

"빠르고 싼 모델"이 새로 나오면 보통 모델 ID만 바꾸면 끝날 거라고 생각하기 쉽다. 이번 Gemini 4 Hydrogen은 그렇지 않다. 기존 Flash 계열 요청에 흔히 들어 있던 설정 몇 가지가 무시되거나 오류가 되고, 지금 시점에는 단가도 기존 Flash보다 높다. Java 쪽에서는 Quarkus가 4.0의 첫 릴리스 후보(CR1)를 냈는데, Java 21 최소 요구와 Jackson 3 전환처럼 코드와 빌드를 같이 손봐야 하는 변화가 들어 있다.

**11월 13일 금요일 기준으로 두 가지를 다룬다.** 하나는 미국 시간 11월 12일 공개된 Google Gemini 4 Hydrogen이고, 다른 하나는 한국 시간 11월 12일 새벽(UTC 11월 11일 20:36) GitHub에 올라온 Quarkus 4.0.0.CR1이다. 직접 벤치마크하거나 운영에 적용해 본 결과가 아니라 1차 출처를 읽고 점검 항목을 추린 브리핑이며, 성능 수치는 모두 발표 회사의 자체 수치다.

## 먼저 보는 두 가지 소식

| 소식 | 발표 시점 | 상태 | 영향 받는 쪽 |
| --- | --- | --- | --- |
| Gemini 4 Hydrogen (`gemini-4-hydrogen`) | 2026-11-12 (미국) | Gemini API 정식 제공(GA), 무료 티어 포함 | Gemini Flash 계열을 API로 쓰는 AI 서비스·에이전트 팀 |
| Quarkus 4.0.0.CR1 | 2026-11-12 05:36 (KST) | 사전 릴리스(Release Candidate) | Quarkus 3.x로 운영 중인 Java·Kotlin 백엔드 팀 |

## 1. Gemini 4 Hydrogen: "Flash 후속"이지만 그대로 바꿔 끼우면 안 된다

### 무엇이 나왔나

Google은 11월 12일 Gemini 4 Hydrogen을 공개했다. Google 블로그는 이 모델을 깊은 추론용인 Gemini 4 Carbon·Argon과 달리 "빠른 실행"에 맞춘 모델로 소개하고, Gemini API 문서는 Gemini 3.8 Flash와 그 이전 Gemini 3·2.5 모델에서 옮겨 갈 **권장 업그레이드 대상**으로 명시했다. Gemini API 릴리스 노트 기준으로 같은 날 GA로 제공되기 시작했고, 무료 티어에서도 쓸 수 있다.

문서에서 확인한 핵심 사양은 다음과 같다.

- **모델 ID**: `gemini-4-hydrogen`
- **가격(유료 티어)**: 입력 100만 토큰당 1.50달러, 출력(thinking 토큰 포함) 100만 토큰당 7.50달러. 1M 컨텍스트 전 구간 동일 단가다.
- **컨텍스트**: 입력·thinking·출력이 하나의 1,048,576 토큰 창을 공유한다. 한 번의 동기 응답은 최대 65,536 토큰이고, 그 이상은 background 실행이나 클라이언트 쪽 이어 쓰기(continuation)로 생성한다.
- **thinking_level**: `low`, `medium`, `high`(기본), 그리고 새로 추가된 `xhigh`의 네 단계.
- **캐시**: 명시적 컨텍스트 캐시는 지원하지 않고 암묵적(implicit) 캐시만 쓴다. 문서상 4,096 토큰 이상 프롬프트에서 기본으로 동작하고, 캐시 적중 입력은 95% 할인된다.

Google은 Gemini 3.8 Flash 대비 작업 완료 속도 2.5배, Terminal-Bench 4.1 점수 18.2%에서 57%로 상승, 지어낸 주장(fabricated claims) 5배 이상 감소 같은 수치를 제시했다. 이 블로그에서 재현한 값은 아니고 Google 자체 발표 수치라는 점은 구분해 두자.

### 3.8 Flash에서 옮길 때 실제로 바뀌는 것

공식 마이그레이션 체크리스트에서 백엔드 코드에 직접 영향을 주는 항목만 추리면 이렇다.

1. **`thinking_level: minimal`은 오류가 된다.** Hydrogen은 기본값이 `medium`이 아니라 `high`이고, `minimal`은 거부한다. 지연 시간을 줄이려고 `minimal`을 넣어 둔 코드는 바로 실패한다.
2. **`temperature`, `top_p`, `top_k`는 무시된다.** 오류는 아니지만 서버가 값을 무시하므로, 이 값으로 출력 다양성을 조절해 왔다면 동작이 조용히 달라진다.
3. **명시적 캐시(`cachedContents`, `caches.create`)는 지원하지 않는다.** 요청에서 `cached_content` 필드를 빼야 한다. 긴 시스템 프롬프트를 캐시해 비용을 줄이던 구조라면 암묵적 캐시로 같은 효과가 나는지 다시 측정해야 한다.
4. **도구 호출은 반드시 네이티브로 선언해야 한다.** 도구를 선언하지 않고 시스템 프롬프트로 "JSON으로 도구 호출을 출력하라"고 시키면 `MALFORMED_FUNCTION_CALL`이 돌아올 수 있다고 문서에 적혀 있다. function calling이나 structured output을 쓰라는 안내다.
5. **출력 한도 설정을 다시 보자.** 3.8 Flash는 입력 1M과 출력 64K 예산이 따로였지만 Hydrogen은 하나의 창을 나눠 쓴다. 문서는 낮게 하드코딩한 `max_output_tokens`를 없애거나 65,536으로 올리라고 권한다. `max_output_tokens`는 thinking과 최종 답을 합친 상한이라, 너무 낮으면 생각만 하다 답이 잘릴 수 있다.
6. **멀티턴에서는 상태를 보존해야 한다.** Interactions API에서는 `previous_interaction_id`를 쓰고, `generateContent`로 대화 이력을 직접 관리한다면 이전 모델 턴과 thought signature를 수정 없이 그대로 돌려줘야 한다.

### 비용은 "싸졌다"가 아니라 "지금은 두 배"일 수 있다

여기서 놓치기 쉬운 부분이 있다. Gemini API 가격 페이지 기준으로 Gemini 3.8 Flash는 **2026년 12월 31일까지 입력 0.75달러·출력 3.75달러**이고, **2027년 1월 1일부터 입력 1.50달러·출력 7.50달러**로 오른다. 즉 Hydrogen의 단가는 3.8 Flash의 내년 정가와 같고, 올해 남은 기간의 3.8 Flash 단가와 비교하면 토큰당 두 배다.

게다가 Hydrogen은 기본 thinking_level이 `high`라서, 같은 요청이라도 thinking 토큰이 더 붙을 수 있다. 문서도 thinking 토큰과 grounding 시 내부 시스템 지시·함수 선언까지 모두 과금된다고 명시한다. 반대로 Google은 파트너 초기 테스트에서 3.8 Flash 대비 토큰 사용량이 12~23% 줄었다고 밝혔는데, 이것도 자체 수치이고 워크로드마다 다를 것이다.

**의견:** 결국 "토큰 단가"가 아니라 "작업 하나당 비용"으로 비교해야 하는 모델이다. 단순 분류·라우팅처럼 짧은 판단이 대부분이라면, 문서가 직접 권하듯 Gemini 3.5 Flash-Lite를 유지하는 쪽이 합리적일 수 있다.

### 누가, 어떤 분야에서 영향을 받나

- **AI 서비스 운영**: Flash 계열을 대량 호출하는 팀은 연말 3.8 Flash 가격 인상과 Hydrogen 전환 시점을 같이 계획해야 한다. 지금 당장 옮기면 정확도는 오를 수 있지만 청구서도 오를 수 있다.
- **백엔드 운영·안정성**: `minimal` 거부, 샘플링 파라미터 무시, `MALFORMED_FUNCTION_CALL` 가능성은 모델 ID만 바꾼 배포에서 장애나 품질 저하로 이어질 수 있는 지점이다. Java·Kotlin 서비스에서 요청 본문을 공통 빌더로 만들고 있다면 그 빌더가 점검 대상이다.
- **개발 생산성**: Google은 Antigravity의 Orchestrator가 Carbon과 Hydrogen을 세션 안에서 바꿔 쓰며 Terminal-Bench 4.0에서 Carbon에 가까운 성공률을 내면서 쿼터를 평균 24% 덜 썼다고 밝혔다. "계획은 큰 모델, 실행은 빠른 모델"로 나누는 구조가 공식 패턴으로 자리 잡는 흐름이다(전망).

### 지금 확인할 체크포인트

- [ ] 코드와 설정에서 `thinking_level`에 `minimal`을 쓰는 곳이 있는지 검색한다.
- [ ] 요청에 `temperature`·`top_p`·`top_k`를 넣고 그 효과에 의존하는 기능(예: 다양한 문구 생성)이 있는지 확인한다.
- [ ] `cachedContents`·`cached_content`를 쓰는 경로가 있으면, 암묵적 캐시 적중률과 비용을 스테이징에서 다시 측정한다.
- [ ] 도구 호출을 프롬프트 기반 JSON으로 흉내 내고 있다면 네이티브 function calling이나 structured output으로 바꾼다.
- [ ] 같은 평가 세트를 `low`·`medium`·`high`로 돌려 "품질 기준을 넘는 가장 낮은 단계"를 고른다. 문서도 이 방식을 권한다.
- [ ] 3.8 Flash를 유지한다면 2027년 1월 1일 단가 변경을 예산에 반영한다.

## 2. Quarkus 4.0.0.CR1: Java 17 지원 종료와 Jackson 3, 조용히 바뀌는 HTTP 동작

### 무엇이 나왔나

Quarkus 팀은 4.0의 첫 번째 릴리스 후보인 4.0.0.CR1을 GitHub에 사전 릴리스로 올렸다. 아직 Quarkus 블로그의 공식 발표 글은 없고, 이 글은 GitHub 릴리스 노트와 공식 위키의 [Migration Guide 4.0](https://github.com/quarkusio/quarkus/wiki/Migration-Guide-4.0)을 기준으로 정리했다. 마이그레이션 가이드는 CR1 이후에도 갱신될 수 있으니 실제 업그레이드 때는 최신본을 다시 확인해야 한다.

CR1 릴리스 노트에는 새 Graceful Shutdown API, Hibernate ORM 리플렉션 없는 상태 접근(Hibernate Accessor)과 Hibernate Validator 9.2.0.Beta1 업그레이드, Spring `@ConfigurationProperties`를 SmallRye Config로 지원하는 변경, `quarkus dev --remote` 옵션, OIDC 쿠키 분할 개선 등이 포함됐다.

### 업그레이드 전에 알아야 할 큰 변화

마이그레이션 가이드에서 대부분의 팀에 해당할 만한 항목을 골랐다.

1. **Java 21이 최소 버전이다.** Java 17은 더 이상 지원하지 않고, 권장 버전은 Java 25다. 컨테이너 이미지 기본값도 UBI 10으로 바뀌었다.
2. **Jackson 2에서 Jackson 3으로 올라간다.** `com.fasterxml.jackson.databind`는 `tools.jackson.databind`로, `com.fasterxml.jackson.core`는 `tools.jackson.core`로 패키지가 바뀐다. 애너테이션(`com.fasterxml.jackson.annotation`)은 그대로다. Quarkus가 제공하는 CDI 빈도 `ObjectMapper`가 아니라 `JsonMapper`가 되고, `ObjectMapperCustomizer`는 `JsonMapperBuilderCustomizer`로 이름과 API가 바뀐다. 이제 변경 가능한 매퍼 대신 `JsonMapper.Builder`를 받는다.
3. **세미콜론이 더 이상 쿼리 파라미터 구분자가 아니다.** `a=1;b=2`는 이제 파라미터 두 개가 아니라 값이 `1;b=2`인 파라미터 `a` 하나로 해석된다. 예전 동작이 필요하면 `quarkus.http.use-semicolon-as-query-param-delimiter=true`(관리 인터페이스는 `quarkus.management.use-semicolon-as-query-param-delimiter=true`)를 설정한다.
4. **오래전 폐기 예고된 설정이 실제로 삭제됐다.** 예를 들어 `quarkus.hibernate-orm.database.generation`은 `quarkus.hibernate-orm.schema-management.strategy`로, `quarkus.log.console.enable`은 `quarkus.log.console.enabled`로 바뀌어야 한다. 가이드는 `quarkus update` 사용을 강력히 권하며, 표시된 항목은 이 명령이 자동으로 처리한다.
5. **Avro 역직렬화가 클래스를 검증한다.** Apache Avro 1.12.2로 올라가면서 신뢰되지 않은 클래스를 역직렬화하면 `SecurityException`이 난다. Avro 생성 클래스만 쓰는 앱은 바꿀 것이 없다.
6. **Spring 호환 설정에서 인터페이스 바인딩이 사라졌다.** `@ConfigurationProperties`를 인터페이스에 붙이면 빌드가 실패한다. 클래스로 바꾸거나 `@io.smallrye.config.ConfigMapping`을 써야 한다.

### 누가, 어떤 분야에서 영향을 받나

- **인프라·플랫폼**: Java 17 런타임이나 UBI 8·9 기반 이미지를 표준으로 쓰는 조직은 Quarkus 4로 가기 전에 런타임과 베이스 이미지부터 올려야 한다.
- **백엔드 코드베이스**: Jackson 3 패키지 변경은 커스텀 직렬화기, `JsonNode`를 직접 다루는 코드, 테스트 유틸까지 넓게 걸린다. 같은 저장소에 Jackson 2에 묶인 다른 라이브러리가 있으면 두 버전이 함께 classpath에 올라오는지도 봐야 한다.
- **보안·API 게이트웨이**: 세미콜론 처리 변경은 파라미터 해석이 프록시나 게이트웨이와 어긋나는 문제를 줄이는 방향으로 보이지만(의견), 기존 클라이언트가 `;`로 파라미터를 보내고 있었다면 조용히 다른 값이 들어간다. 오류가 나지 않아 발견이 늦어지기 쉬운 유형이다.
- **Kotlin 사용자**: Jackson 3 전환은 Kotlin 모듈과 데이터 클래스 직렬화에도 영향을 주므로, Kotlin으로 작성한 Quarkus 서비스도 같은 점검 대상이다.

### 지금 확인할 체크포인트

- [ ] 빌드·CI·런타임 이미지의 JDK가 21 이상인지 확인한다.
- [ ] `com.fasterxml.jackson.databind`·`com.fasterxml.jackson.core` import와 `ObjectMapperCustomizer` 구현체 수를 세어 작업량을 가늠한다.
- [ ] 액세스 로그에서 쿼리 문자열에 `;`가 들어오는 요청이 있는지 확인한다.
- [ ] 별도 브랜치에서 `quarkus update`로 CR1을 적용해 삭제된 설정과 컴파일 오류 목록을 미리 뽑아 본다. 운영 적용은 정식 릴리스 이후로 미루는 것이 일반적이다.

## 정리

두 소식의 공통점은 "버전 숫자만 올리면 되는 업그레이드가 아니다"라는 점이다. Gemini 4 Hydrogen은 성능 향상과 함께 요청 파라미터와 캐시 방식, 비용 구조가 바뀌었고, Quarkus 4.0은 JDK·Jackson·HTTP 해석 같은 기반이 함께 바뀐다. 둘 다 지금 당장 운영에 넣기보다, 이번 주에 점검 목록을 만들고 스테이징에서 평가해 볼 시점이다.

## 참고 원문

- [Introducing Gemini 4 Hydrogen](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-hydrogen/), Google 블로그, 2026-11-12
- [Gemini API 릴리스 노트](https://aistudio.google.com/docs/changelog), 2026-11-12 항목
- [What's new in Gemini 4 Hydrogen (마이그레이션 체크리스트)](https://aistudio.google.com/docs/whats-new-gemini-4-hydrogen), Gemini API 문서
- [Gemini API 가격](https://ai.google.dev/gemini-api/docs/pricing), Gemini 4 Hydrogen·Gemini 3.8 Flash 항목
- [Quarkus 4.0.0.CR1 릴리스](https://github.com/quarkusio/quarkus/releases/tag/4.0.0.CR1), GitHub, 2026-11-11 20:36 UTC
- [Quarkus Migration Guide 4.0](https://github.com/quarkusio/quarkus/wiki/Migration-Guide-4.0), Quarkus 위키
