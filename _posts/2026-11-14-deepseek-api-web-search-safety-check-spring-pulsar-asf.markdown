---
title: "DeepSeek API에 웹 검색·파일 파싱·안전성 검사 내장: 비용 구조와 주의점, Spring for Apache Pulsar의 Apache 이관 정리"
description: "2026년 11월 14일 기술 브리핑. DeepSeek이 앱의 웹 검색·딥 씽킹 검색·파일 파싱·URL 읽기·안전성 검사·음성 기능을 API(deepseek-flash)로 공개한 내용과 도구별 과금·피크 시간대·무시되는 파라미터, 그리고 2.0.8을 끝으로 Spring 팀 유지보수가 끝나고 Apache Pulsar 프로젝트로 넘어가는 Spring for Apache Pulsar 이관을 1차 출처로 확인해 Java·Kotlin 백엔드 팀의 점검 항목을 정리합니다."
date: 2026-11-14 09:40:00 +0900
categories: [기술뉴스]
tags: [AI, DeepSeek, deepseek-flash, LLM API, 웹 검색, RAG, LLM 비용, Spring, Apache Pulsar, Spring Boot, Spring Cloud Stream, Java, Kotlin]
---

챗봇에 "검색해서 답하기"를 붙이려면 지금까지는 검색 API 계약, 페이지 크롤링, 본문 추출, 출처 표시, 유해 콘텐츠 필터를 각각 만들어 이어 붙여야 했다. DeepSeek이 이 조각들을 API 파라미터 몇 개로 묶어 내놨다. 편해진 만큼 비용 계산 방식과 "서버가 대신 정하는 부분"이 늘었기 때문에, 붙이기 전에 확인할 것도 생겼다. Java 쪽에서는 Spring for Apache Pulsar가 Spring 팀의 손을 떠나 Apache Pulsar 프로젝트로 이관된다. 당장 깨지는 것은 없지만, 의존성 좌표와 패키지가 바뀌는 예고된 마이그레이션이다.

**11월 14일 토요일 기준으로 두 가지를 다룬다.** 하나는 11월 13일 공개된 DeepSeek API 기능 확장이고, 다른 하나는 11월 10일(미국) Spring 블로그에 올라온 Spring for Apache Pulsar 이관 공지다. Pulsar 쪽은 나흘 전 소식이지만 이 블로그에서 아직 다루지 않았고, Spring Boot 4.2 GA를 앞두고 지금 확인해 둘 내용이라 함께 정리했다. 직접 운영에 적용해 본 결과가 아니라 1차 출처 문서를 읽고 점검 항목을 추린 브리핑이며, 가격은 모두 발표 시점에 공개된 정가 기준이다.

| 소식 | 발표 시점 | 1차 출처 |
| --- | --- | --- |
| DeepSeek, 앱 기능을 API로 공개 | 2026-11-13 | [DeepSeek API 뉴스](https://api-docs.deepseek.com/news/news261113) |
| Spring for Apache Pulsar, Apache Pulsar 프로젝트로 이관 | 2026-11-10 (미국) | [Spring 블로그](https://spring.io/blog/2026/11/10/spring-pulsar-new-home-asf) |

## 1. DeepSeek API: 검색·파일·안전성 검사를 서버가 처리

### 무엇이 바뀌었나

DeepSeek은 자사 앱에서 쓰던 기능을 API로 열었다. 대상 모델은 `deepseek-flash`(현재 DeepSeek-V4.1-Flash-1017이 서빙)이고, Messages(Anthropic 호환), Responses, Chat Completions(OpenAI 호환) 세 가지 엔드포인트에서 모두 쓸 수 있다.

- **웹 검색**: `deepseek_web_search` 도구를 켜면 비사고(non-thinking) 모드에서 웹·이미지 검색 후 인용과 함께 답한다.
- **딥 씽킹 검색**: 사고 모드에서 같은 도구를 켜면 여러 단계 추론 중에 스스로 검색하고 페이지를 읽는다.
- **파일 입력**: PDF, Word, PowerPoint, 이미지 등을 파싱해 대화 컨텍스트에 넣는다.
- **URL 읽기**: `deepseek_read_url`을 켜면 사용자 메시지 속 링크를 서버가 가져와 읽는다.
- **안전성 검사**: `safety_check`를 켜면 입력과 출력을 검토해 위험 시 거절 표시(`stop_reason: "refusal"` 등)를 돌려준다.
- **부가 기능**: 대화 제목 생성, 사용자 날짜·위치·언어 메타데이터, TTS·ASR.

검색(Search), 페이지 가져오기(Fetch), OCR, ASR, TTS는 모델 없이 단독 API로도 호출할 수 있다. 함께 공개된 오픈소스 채팅 데모([deepseek-ai/chat-demo](https://github.com/deepseek-ai/chat-demo))는 각 응답 블록을 화면에 어떻게 그리는지 보여 주는 참고 구현이다.

### 비용 구조: 토큰 + 도구 사용료

[가격 페이지](https://api-docs.deepseek.com/quick_start/pricing)에 따르면 확장 기능은 토큰 요금과 별도로 도구 사용료가 붙는다.

| 항목 | 단위 | 가격 |
| --- | --- | --- |
| 검색(텍스트·이미지) | 1,000회 | $0.75 |
| 웹 페이지 가져오기 | 1,000회 | $0.75 |
| 파일 파싱·OCR | 1,000페이지 | $0.225 |
| TTS | 10,000자 | 정가 $0.45 (한시 50% 할인 $0.225) |
| ASR | 오디오 1시간 | 정가 $0.116 (한시 50% 할인 $0.058) |

`deepseek-flash` 토큰 단가는 피크 기준 입력(캐시 미스) 100만 토큰당 $0.3, 출력 $1.2이고, 비피크는 그 절반이다. 한국 개발자가 특히 봐야 할 부분은 **피크 시간대**다. DeepSeek이 밝힌 피크는 평일 01:00–04:00, 06:00–10:00 UTC로, 한국 시간으로 바꾸면 **평일 10:00–13:00, 15:00–19:00(KST)** 이다. 국내 서비스의 낮 트래픽이 대부분 피크 요금을 내는 셈이다. 주말과 중국 공휴일은 종일 비피크다.

### 서버가 대신 정하는 파라미터

[챗봇 가이드](https://api-docs.deepseek.com/guides/build_a_chatbot)에는 웹 도구나 `safety_check: high`, 제목 생성을 켠 요청에서 **일부 파라미터 값을 무시한다**고 적혀 있다. 예를 들어 Chat Completions에서는 `temperature`, `top_p`, `seed`, `stop`, `n`, `parallel_tool_calls` 등이, Messages에서는 `temperature`, `top_k`, `stop_sequences`, `thinking.budget_tokens` 등이 무시된다. 반면 `max_tokens`는 그대로 적용되는데, 한 라운드 전체가 아니라 **라운드 안의 추론 단계 하나하나의 출력**을 제한한다는 점이 다르다.

또 하나, 검색·URL 읽기 결과 블록은 클라이언트가 **다음 요청에 그대로 돌려줘야** 한다. 대화 이력을 DB에 저장하며 블록을 정리·축약하는 서버라면 이 부분을 놓치기 쉽다.

### 누가, 어떤 분야가 영향을 받나

- **AI 서비스·챗봇 백엔드**: 검색 API + 크롤러 + 본문 추출 + 출처 표시를 직접 엮어 온 팀은 같은 기능을 파라미터로 대체할 선택지가 생겼다. 다만 결과가 서버 쪽에서 조립되므로 어떤 페이지를 왜 읽었는지에 대한 통제권은 줄어든다(의견).
- **비용·인프라**: 요청 단위 비용이 "토큰 수"에서 "토큰 + 검색 횟수 + 페치 횟수"로 바뀐다. 딥 씽킹 검색은 한 요청 안에서 검색과 페치가 여러 번 일어날 수 있어, 요청당 비용 편차가 커질 가능성이 있다. 응답의 `usage.server_tool_use`에 검색·페치 횟수가 따로 오므로 이를 계측 지표로 잡아야 한다.
- **보안·컴플라이언스**: DeepSeek은 공개 서비스라면 안전성 검사를 반드시 켜야 하고, 콘텐츠 검수·모델 등록·AI 생성물 표시 같은 의무는 여전히 개발자 책임이라고 명시했다. 안전성 검사를 켰다고 국내 규제나 사내 정책 대응이 끝나는 것은 아니다. URL 읽기는 사용자 입력 링크를 외부 서버가 가져가는 구조이므로, 사내 문서 링크나 개인정보가 담긴 URL이 넘어가지 않게 입력단에서 거르는 정책도 필요하다(의견).
- **Java·Kotlin 개발 생산성**: OpenAI·Anthropic 호환 엔드포인트라 기존 SDK나 Spring AI 같은 클라이언트로 붙일 수 있지만, `deepseek_web_search` 같은 서버 도구 타입과 `safety_check`, `title` 같은 비표준 필드는 범용 클라이언트가 그대로 지원하지 않을 수 있다. 추가 필드를 요청 본문에 실을 수 있는지 먼저 확인하자(전망).

### 지금 확인할 체크포인트

1. 도구를 켠 요청에서 `temperature`, `seed` 등에 의존한 동작(재현성 테스트, 결정적 응답)이 있는지 확인한다. 값이 조용히 무시된다.
2. 요청당 `usage.server_tool_use`의 검색·페치 횟수를 로그·메트릭으로 남기고, 월 예산 알람을 토큰과 별도로 건다.
3. 배치·요약 같은 비실시간 작업은 KST 기준 평일 저녁 19시 이후나 주말로 옮길 수 있는지 검토한다.
4. 공개 서비스라면 `safety_check`를 켜고 `stop_reason: "refusal"` 응답을 사용자 메시지로 바꾸는 처리를 넣는다.
5. 대화 이력 저장 시 검색·페치 결과 블록을 손대지 않고 다음 요청에 돌려주는지 확인한다.
6. 아직 `deepseek-v4-flash` 같은 이전 모델명을 쓰고 있다면, 이 이름이 이미 V4.1-Flash-1017로 서빙되고 Flash 가격으로 과금된다는 점을 알고 `deepseek-flash`로 정리해 둔다.

## 2. Spring for Apache Pulsar, 2.0.8을 끝으로 Apache Pulsar로 이관

### 무엇이 바뀌었나

Spring 팀은 Spring for Apache Pulsar를 Apache Software Foundation의 Apache Pulsar 프로젝트 하위 프로젝트로 옮긴다고 발표했다. 새 이름은 **Apache Pulsar support for Spring**이다.

- **2.0.8이 Spring 우산 아래의 마지막 릴리스**다. 이후 Spring 팀은 현재·미래 릴리스 트레인 어디에서도 업데이트, 유지보수 패치, 버그 수정을 내지 않는다.
- **Spring Boot 스타터**: Spring 팀이 관리하던 Pulsar 스타터도 유지보수가 끝난다. 2.0.8은 Spring Boot 4.2.0과 함께 계속 쓸 수 있지만, 이후 릴리스는 새 프로젝트가 제공하는 스타터로 바꿔야 한다.
- **Spring Cloud Stream 바인더**: 곧 나올 Spring Cloud Stream 5.1.0까지는 Pulsar 바인더가 포함되고, 그 뒤로는 새 프로젝트에서 받아야 한다.
- 앞으로 업데이트를 받으려면 **의존성 좌표와 패키지 import를 새 프로젝트에 맞춰 바꿔야** 한다고 공지는 밝혔다.

공지 시점에 새 좌표와 패키지 이름의 구체적인 값은 Spring 블로그에 나오지 않았다. Apache Pulsar 쪽 공식 공지를 확인하라고 안내하고 있으니, 좌표를 추측해서 바꾸지 말고 그쪽 문서가 나오면 맞추는 게 안전하다.

### 누가, 어떤 분야가 영향을 받나

- **메시징 기반 백엔드 운영**: `spring-pulsar` 또는 Boot의 Pulsar 스타터, Spring Cloud Stream Pulsar 바인더를 쓰는 서비스가 대상이다. 당장 동작이 바뀌지는 않지만, 2.0.8 이후의 **보안 패치가 어디서 나오느냐**가 바뀐다. 취약점 스캐너가 Pulsar 클라이언트나 관련 의존성을 잡았을 때 Spring Boot 패치 버전만 올려서는 해결되지 않는 상황이 올 수 있다(전망).
- **의존성 관리·빌드**: Spring Boot BOM이 관리하던 버전이 BOM 밖으로 빠지면, Gradle·Maven에서 버전을 직접 지정하거나 새 프로젝트 BOM을 추가해야 할 가능성이 높다(전망). Spring Boot 4.2 이후 버전 업그레이드 때 이 항목이 걸릴 수 있다.
- **Kotlin 프로젝트**: 패키지 import가 바뀌면 Kotlin 코드도 같이 바뀌어야 한다. IDE 일괄 치환으로 끝날 수 있는 작업이지만, 리플렉션·설정 파일(`application.yml`의 속성 접두사 등)에 패키지나 속성 이름이 문자열로 들어간 곳은 컴파일러가 잡아 주지 않는다. 속성 이름이 실제로 바뀌는지는 아직 확인되지 않았으므로 새 문서를 보고 판단해야 한다.

### 지금 확인할 체크포인트

1. `./gradlew dependencies` 또는 `mvn dependency:tree`로 `spring-pulsar`, Pulsar 스타터, `spring-cloud-stream-binder-pulsar`가 들어 있는지 확인한다.
2. 현재 버전이 2.0.8보다 낮다면 우선 2.0.8로 올려 Spring 쪽 마지막 수정까지 받아 둔다.
3. Spring Boot 4.2 GA 이후 업그레이드 계획에 "Pulsar 의존성 좌표·패키지 전환" 항목을 미리 넣는다.
4. Apache Pulsar 프로젝트의 공식 공지와 새 저장소를 구독해, 첫 릴리스의 좌표·패키지·지원하는 Spring Boot 버전을 확인한 뒤 전환한다.

## 정리

두 소식은 방향이 다르지만 백엔드 팀에게 던지는 질문은 비슷하다. **"이 기능의 책임이 어디로 옮겨 갔는가"** 다. DeepSeek은 검색·파싱·안전성 검사를 서버 쪽으로 가져가며 구현 부담을 줄여 주는 대신, 비용 단위와 파라미터 통제권을 바꿨다. Spring for Apache Pulsar는 코드 자체는 그대로지만 유지보수 주체가 바뀌어, 패치를 받는 경로를 다시 확인해야 한다. 둘 다 오늘 당장 고칠 것보다는, 계측과 업그레이드 계획에 한 줄씩 넣어 둘 일에 가깝다.

## 참고 링크

- [The full DeepSeek App experience, now via API](https://api-docs.deepseek.com/news/news261113) (DeepSeek, 2026-11-13)
- [Build a Chatbot](https://api-docs.deepseek.com/guides/build_a_chatbot) (DeepSeek API 문서)
- [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing) (DeepSeek API 문서, 2026-11-14 확인)
- [Announcing a New Home for Spring for Apache Pulsar](https://spring.io/blog/2026/11/10/spring-pulsar-new-home-asf) (Spring 블로그, 2026-11-10)
