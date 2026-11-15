---
title: "Gemini 4 Carbon 출시와 API 마이그레이션 주의점, Spring AI 2.1 RC2 DecisionModel 정리"
description: "2026년 11월 11일 기술 브리핑. Google Gemini 4 Carbon의 가격·토큰 한도·thinking_level 변경과 3.1 Pro에서 옮길 때 HTTP 400이 나는 파라미터, 그리고 GA를 앞둔 Spring AI 2.1.0-RC2의 DecisionModel API·ChatMemory 폐기 예고를 1차 출처로 확인해 Java·Kotlin 백엔드 팀의 점검 항목을 정리합니다."
date: 2026-11-11 09:40:00 +0900
categories: [기술뉴스]
tags: [AI, Gemini, Gemini 4 Carbon, LLM API, 마이그레이션, Spring AI, Java, Kotlin, LLM 비용]
---

새 모델이 나오면 보통 "얼마나 똑똑해졌나"가 먼저 화제가 된다. 하지만 이미 API를 서비스에 붙여 운영하는 백엔드 개발자에게는 "기존 요청이 그대로 통과하나"가 더 급한 질문이다. 이번 Gemini 4 Carbon은 그 질문의 답이 "아니다"인 경우가 있어서 따로 정리할 가치가 있다.

**11월 11일 수요일 기준으로 두 가지를 다룬다.** 하나는 미국 시간 11월 10일에 공개된 Google Gemini 4 Carbon이고, 다른 하나는 11월 5일(UTC) 나온 Spring AI 2.1.0-RC2다. Spring AI 쪽은 엿새 전 소식이지만 이 블로그에서 아직 다루지 않았고, 11월 정식 릴리스를 앞두고 지금 확인해 둘 내용이 있어 함께 정리했다. 직접 벤치마크하거나 운영에 적용해 본 결과가 아니라 1차 출처를 읽고 점검 항목을 추린 브리핑이며, 성능 수치는 모두 발표 회사의 자체 수치다.

## 먼저 보는 두 가지 소식

| 소식 | 공개 시점 | 현재 상태 | 먼저 영향받는 팀 |
| --- | --- | --- | --- |
| Gemini 4 Carbon | 2026-11-10(미국), 한국 시간 11월 11일 새벽 | Gemini API 유료 티어, Gemini for business, Agent Platform에서 사용 가능 | Gemini 3.1 Pro를 쓰는 서비스, 고난도 코딩·에이전트 작업에 상위 모델을 쓰는 팀 |
| Spring AI 2.1.0-RC2 | 2026-11-05(GitHub 릴리스 기준) | 프리릴리스(RC) | Spring AI로 LLM 기능을 만든 Java·Kotlin 팀, 특히 `ChatMemory`를 쓰는 곳 |

## 1. Gemini 4 Carbon: 성능보다 먼저 볼 것은 "깨지는 파라미터"

### 확인된 사실

Google은 [Gemini 4 Carbon 공개 글](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-4-carbon-now-available/)(2026년 11월 10일)에서 Carbon을 개발자·기업·일반 사용자에게 공개했다. 2주 전 사이버보안 방어 조직 대상 Fairwind Program으로 먼저 풀었던 모델이다.

- **포지션:** Google은 대부분의 소프트웨어 엔지니어링·지식 업무에는 기존 Gemini 4 Argon을 권하고, Carbon은 여러 단계의 복잡한 코딩·디버깅이나 열린 형태의 연구처럼 한계를 시험하는 작업용이라고 설명했다. Argon보다 토큰을 더 많이 써서 탐색하고 검증 루프를 길게 돈다고 밝혔다.
- **가격:** 11월 30일까지는 도입 가격으로 입력 100만 토큰당 2달러, 출력 100만 토큰당 10달러(Argon과 같은 가격)이고, 도입 기간이 끝나면 입력 4달러, 출력 20달러가 적용된다고 공지했다.
- **제공 경로:** Google AI Studio의 Gemini API 유료 티어, Gemini for business, Android Studio에서 쓸 수 있고, Google AI Ultra 구독자는 Google Antigravity와 Gemini 앱에서도 쓸 수 있다. 에이전트 여러 개를 한 프롬프트로 조율하는 `/swarm` 기능도 Antigravity에서 미리보기로 공개됐다.
- **자체 발표 지표:** CursorBench 4.0 등 외부 벤치마크에서 1위를 했고 차선 모델보다 작업당 비용이 2배 이상 낮다고 주장했다. 이는 Google이 공개한 결과이며, 우리 업무에서 같은 차이가 난다는 근거는 아니다.

[Agent Platform 개발 가이드](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-4-carbon)는 실제 연동에 필요한 규칙을 자세히 적어 두었다. 백엔드 개발자에게 중요한 부분만 추리면 이렇다.

- **모델 ID:** `gemini-4-carbon`. Fairwind Program 승인 프로젝트는 `gemini-4-carbon-cyber-permissive`를 쓴다.
- **통합 토큰 한도:** 입력과 출력(생각 토큰, 함수 호출 포함)을 합쳐 1,048,576토큰을 함께 쓴다. `max_output_tokens`를 생략하면 출력 예산은 기본 65,536토큰이다.
- **긴 출력(long decode):** 한 번의 요청 구간에서 스트리밍은 최대 65,536토큰, 비스트리밍은 32,768토큰까지 만들고, 그 이상은 `continuation_token`으로 이어 붙인다. 최신 Google Gen AI SDK는 이를 자동으로 처리하지만, 가이드는 이 기능이 현재 `v1beta1` API에서만 동작한다고 알려진 이슈로 적었다.
- **HTTP 400이 나는 설정:** `thinking_budget`, `thinking_level="MINIMAL"`, `frequency_penalty`, `presence_penalty`, 1보다 큰 `candidate_count`는 400 오류를 낸다. 3.1 Pro에서는 `thinking_budget`이 thinking level로 대응됐지만 Carbon에서는 오류가 된다고 명시했다.
- **무시되는 설정:** `temperature`, `top_p`, `top_k`는 값을 넣어도 무시된다. 추론 깊이는 `thinking_level`(`LOW`/`MEDIUM`/`HIGH`, 기본 `MEDIUM`)로, 출력 형식은 `response_schema`로 제어하라고 안내한다.
- **캐싱:** 명시적 컨텍스트 캐싱은 지원하지 않는다. 대신 4,096토큰 이상 공통 프롬프트 앞부분에 암묵적 캐싱이 자동 적용되므로, 고정된 내용을 프롬프트 맨 앞에 두라고 권한다.
- **대화 이력 검증:** 이력이 `model` 역할 턴으로 끝나면 안 되고, 모델 응답을 미리 채워 넣는 방식(prefill)은 지원하지 않는다. 함수 응답은 직전 함수 호출의 `id`, 이름, 순서와 맞아야 한다.
- **Java SDK 버전:** `GenerateContent`에서 자동 이어 붙이기를 쓰려면 Java SDK 1.77.0 이상, Interactions API는 1.80.0 이상이 필요하다고 적혀 있다.

### 실무 관점의 해석: 모델 ID만 바꾸면 장애가 날 수 있다

이 글의 판단으로는, Carbon 전환에서 가장 흔하게 부딪힐 문제는 품질이 아니라 **요청 스키마 호환성**이다. 많은 서비스가 공통 설정으로 `temperature=0`이나 `thinking_budget`을 넣어 두고 모델 ID만 환경 변수로 바꿔 끼운다. Carbon에서는 `thinking_budget`이 바로 400 오류가 되고, `temperature`는 조용히 무시된다. 앞의 것은 배포 직후 오류율로 드러나지만, 뒤의 것은 "같은 입력에 같은 답"을 기대하던 테스트나 평가 파이프라인을 소리 없이 흔들 수 있다.

비용도 단가만 보면 안 된다. Google 스스로 Carbon이 Argon보다 토큰을 더 쓴다고 했고, 생각 토큰도 모두 과금된다. 도입 가격은 11월 30일에 끝나므로, 12월부터 단가가 두 배가 되는 것을 전제로 예산을 잡아야 한다. 분류·요약처럼 가벼운 작업까지 Carbon으로 보내면 비용이 빠르게 늘어날 것이다. Google 가이드도 그런 작업에는 `LOW`를 권한다.

마지막으로, 긴 출력 기능이 `v1beta1`에서만 동작한다는 점은 엔드포인트를 `v1`으로 고정해 둔 서비스에 영향이 있다. 다만 대부분의 채팅·추출 작업은 65,536토큰 안에서 끝난다고 가이드가 밝힌 만큼, 긴 출력이 꼭 필요한 작업인지부터 따져 보는 편이 낫다.

### 지금 확인할 항목

1. 공통 LLM 호출 설정에 `thinking_budget`, `MINIMAL`, `frequency_penalty`, `presence_penalty`, `candidate_count`가 들어 있는지 검색한다. Carbon으로 보낼 경로에서는 제거하거나 모델별로 설정을 나눈다.
2. `temperature`에 기대는 테스트·평가 코드가 있다면 Carbon에서는 그 값이 무시된다는 전제로 다시 설계한다.
3. 명시적 캐시(`cached_content`)를 쓰고 있다면 Carbon 경로에서 제거하고, 고정 시스템 프롬프트를 앞에 모아 암묵적 캐싱을 받을 수 있게 프롬프트 순서를 정리한다.
4. 대화 이력을 만드는 코드가 마지막 턴을 모델 응답으로 끝내거나 prefill을 쓰는지 확인한다.
5. 12월 1일부터 적용될 정가(입력 4달러, 출력 20달러)와 생각 토큰을 포함해 월 비용을 다시 추정하고, 작업 난이도에 따라 Argon·Carbon·`thinking_level`을 나누는 라우팅을 검토한다.

## 2. Spring AI 2.1.0-RC2: DecisionModel API와 ChatMemory 폐기 예고

### 확인된 사실

[Spring AI GitHub 릴리스 노트](https://github.com/spring-projects/spring-ai/releases)에 따르면 2.1.0-RC2는 2026년 11월 5일 프리릴리스로 나왔다. 새 기능 목록에서 눈에 띄는 것은 다음과 같다.

- **DecisionModel API 도입:** 릴리스 노트에 `Introduce DecisionModel API`가 들어갔고, Ollama 구현(`OllamaDecisionModel`), `SystemOneDecisionModel`, 도구 검색용 `DecisionToolIndex`, 판단 기반 RAG 문서 후처리기도 함께 추가됐다. 자유 텍스트 생성이 아니라 분류·선택처럼 정해진 판단을 다루는 쪽의 API로 보인다. 다만 이 글에서는 레퍼런스 문서의 상세 사용법까지는 확인하지 못했다.
- **도구 호출 스트리밍:** 도구 호출 인자의 변경분(delta)을 스트리밍하는 기능이 추가됐다.
- **MCP 신규 프로토콜:** MCP 2026-07-28("modern") 프로토콜 개정판의 서버 측 지원이 들어갔다.
- **벡터 저장소:** Chroma, MariaDB, MongoDB Atlas, Typesense, Neo4j에 upsert와 미리 계산한 임베딩으로 검색하는 기능이 추가됐다.
- **비용 집계:** Anthropic과 Bedrock의 프롬프트 토큰 수에 캐시된 토큰을 포함하도록 바뀌었다. Anthropic Java SDK는 3.4.0으로 올라갔다.

한 단계 앞선 2.1.0-RC1(2026년 10월 23일)에서는 **`ChatMemory`를 폐기(deprecate)하고 세션 메모리로 대체**하는 변경이 들어갔다. 릴리스 노트는 세션 메모리를 "턴 단위 압축을 하는 이벤트 로그"로 설명한다. 같은 RC1에는 도구 호출 확인(confirmation) 기능, Kotlin 2.4.21 업그레이드도 포함됐다.

### 실무 관점의 해석: RC 단계는 "테스트를 돌려 볼 마지막 시점"

RC 이후에는 보통 API 변경 없이 버그 수정만 들어간다. 그래서 Spring AI 2.1을 쓸 계획이라면 정식 버전을 기다리기보다 지금 RC2로 테스트를 한 번 돌려 보는 것이 이 글의 권장이다. 특히 `ChatMemory` 기반으로 대화 기록을 관리하는 서비스는 2.1부터 폐기 경고가 뜨게 되므로, 당장 바꾸지는 않더라도 세션 메모리로 옮길 범위를 미리 파악해 두면 다음 업그레이드가 수월하다. 폐기는 삭제가 아니므로 곧바로 컴파일이 깨지는 것은 아니다.

캐시 토큰을 프롬프트 토큰에 포함하도록 바뀐 점도 운영팀이 알아야 한다. 토큰 사용량으로 비용 대시보드나 알림을 만들어 두었다면, 업그레이드 후 집계 숫자가 달라 보일 수 있다. 실제 청구가 바뀐 것이 아니라 집계 방식이 바뀐 것일 수 있으니 업그레이드 시점을 대시보드에 기록해 두는 편이 좋다.

DecisionModel은 1번 Gemini 소식과도 이어진다. 분류·라우팅처럼 답이 정해진 판단을 별도 API로 다루면, 비싼 상위 모델은 어려운 생성 작업에만 쓰고 판단 작업은 가벼운 모델로 돌리는 구성을 코드 수준에서 나누기 쉬워진다. 이것은 방향에 대한 의견이며, 실제 효과는 각 서비스에서 평가해야 한다.

### 지금 확인할 항목

1. 코드에서 `ChatMemory`, `MessageWindowChatMemory`, `ChatMemoryRepository` 사용처를 검색해 세션 메모리로 옮길 범위를 파악한다.
2. 스테이징 브랜치에서 Spring AI BOM을 2.1.0-RC2로 올려 테스트를 돌리고, 폐기 경고와 실패를 정리한다. RC 버전을 받기 위해 별도 저장소 설정이 필요한지도 빌드에서 확인한다.
3. Anthropic·Bedrock 토큰 사용량을 모니터링하고 있다면 업그레이드 전후 집계 방식 차이를 기록한다.
4. 벡터 저장소에 직접 계산한 임베딩을 넣고 있다면 새 upsert·임베딩 검색 API로 우회 코드를 줄일 수 있는지 검토한다.

## 정리

| 분야 | 이번 소식이 바꾸는 것 | 우선 행동 |
| --- | --- | --- |
| AI 서비스·비용 | Carbon 도입 가격이 11월 30일 종료, 생각 토큰 과금, 명시적 캐시 미지원 | 12월 정가 기준 비용 재추정, 작업별 모델·thinking_level 분리 |
| 백엔드 운영 | Carbon에서 일부 파라미터가 400 오류, 긴 출력은 `v1beta1` 전용 | 공통 호출 설정 점검, 모델별 설정 분리 |
| 개발 생산성 | Spring AI 2.1 RC2에 DecisionModel·도구 호출 스트리밍·MCP 신규 프로토콜 | RC2로 테스트, `ChatMemory` 이전 범위 파악 |

## 참고 원문

- [Gemini 4 Carbon is now available](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-4-carbon-now-available/), Google, 2026-11-10(미국)
- [Gemini 4 Carbon is now available for developers](https://blog.google/innovation-and-ai/technology/developers-tools/gemini-4-carbon-developers/), Google, 2026-11-10(미국)
- [Gemini 4 Carbon 개발 가이드](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-4-carbon), Google Cloud Gemini Enterprise Agent Platform 문서
- [Spring AI Releases (v2.1.0-RC2, v2.1.0-RC1)](https://github.com/spring-projects/spring-ai/releases), spring-projects/spring-ai, 2026-11-05 / 2026-10-23
