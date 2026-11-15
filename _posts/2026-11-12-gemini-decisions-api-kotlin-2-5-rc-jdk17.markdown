---
title: "Gemini Decisions API로 라우팅·분류 비용 줄이기, Kotlin 2.5.0-RC의 JDK 17 요구와 value class 변화"
description: "2026년 11월 12일 기술 브리핑. 생성 대신 확률을 돌려주는 Google Gemini Decisions API(gemini-decision-1)의 질문 유형·가격·제약과, 컴파일러 실행에 JDK 17을 요구하기 시작한 Kotlin 2.5.0-RC의 주요 변경을 1차 출처로 확인해 Java·Kotlin 백엔드 팀의 점검 항목을 정리합니다."
date: 2026-11-12 09:40:00 +0900
categories: [기술뉴스]
tags: [AI, Gemini, Gemini Decisions API, LLM 라우팅, LLM 비용, Kotlin, Kotlin 2.5, JDK 17, value class, Spring]
---

LLM을 서비스에 붙이다 보면 실제 호출의 상당수는 긴 글을 쓰는 일이 아니라 "이 요청을 어느 모델로 보낼까", "이 문의가 환불 건인가" 같은 짧은 판단이다. 그런데 이런 판단도 보통은 생성 모델에게 답을 글로 쓰게 하고 그 글을 다시 파싱한다. 어제 Spring AI 2.1 RC2의 DecisionModel API를 다루면서 "판단 작업을 별도 API로 떼어 내는 흐름"을 언급했는데, 하루 만에 Google이 같은 방향의 상용 API를 내놨다.

**11월 12일 목요일 기준으로 두 가지를 다룬다.** 하나는 11월 11일(미국) 공개된 Google Gemini Decisions API이고, 다른 하나는 같은 날 나온 Kotlin 2.5.0-RC다. 직접 벤치마크하거나 운영에 적용해 본 결과가 아니라 1차 출처를 읽고 점검 항목을 추린 브리핑이며, 성능·비용 비교 수치는 모두 발표 회사의 자체 수치다.

## 먼저 보는 두 가지 소식

| 소식 | 공개 시점 | 현재 상태 | 먼저 영향받는 팀 |
| --- | --- | --- | --- |
| Gemini Decisions API (`gemini-decision-1`) | 2026-11-11(미국), 한국 시간 11월 12일 새벽 | Google AI Studio의 Gemini API(`v1beta`)에서 사용 가능, Google Cloud 쪽은 "곧 지원" | 모델 라우팅·의도 분류·정책 검사를 LLM 생성 호출로 처리하는 팀 |
| Kotlin 2.5.0-RC | 2026-11-11 | 릴리스 후보(EAP) | Kotlin으로 서버를 만드는 팀, 특히 JDK 8·11로 빌드하거나 `value class`를 Spring·직렬화와 함께 쓰는 곳 |

## 1. Gemini Decisions API: 답을 "쓰지" 않고 확률로 "고르는" 모델

### 확인된 사실

Google은 [Gemini Decisions API 공개 글](https://blog.google/innovation-and-ai/technology/developers-tools/gemini-decisions-api/)(2026년 11월 11일)에서 정해진 선택지 중에서 고르는 작업 전용 엔드포인트와 전용 모델 Gemini Decision 1(`gemini-decision-1`)을 발표했다. 핵심만 추리면 이렇다.

- **동작 방식:** 답을 토큰 단위로 생성하지 않고, 후보 선택지를 한 번의 순전파(forward pass)로 점수 매겨 확률과 0~1 사이 신뢰도(confidence)를 돌려준다.
- **질문 유형 세 가지:** 예/아니오 판단(`noul`), 2~255개 선택지 중 고르기(`choice`), 0부터 시작하는 순서형 루브릭 점수(`score`). 한 요청에 서로 다른 유형을 섞어 최대 1,000개의 독립 질문을 함께 보낼 수 있다.
- **입력:** 텍스트, 이미지, 오디오, 영상, PDF를 하나의 공유 입력으로 묶어 넣을 수 있고 최대 256K 토큰이다. `input` 필드는 Interactions API와 같은 `Content` 블록 형식을 쓴다.
- **가격:** 입력 100만 토큰당 0.10달러, 출력 토큰은 과금하지 않는다. 공유 입력은 질문 수와 관계없이 요청당 한 번만 과금되고, 질문마다 그 질문의 지시문·선택지 토큰만 추가된다. AI Studio에서 프로토타이핑용 무료 티어도 쓸 수 있다고 밝혔다.
- **지연 시간(자체 수치):** 모델 연산 중앙값 50~100ms, 종단 간 150~250ms이며, 16K 토큰 이하 입력에서는 질문 수를 1개에서 100개로 늘려도 거의 일정하다고 설명했다. 같은 벤치마크 묶음에서 Gemini 3.5 Flash-Lite를 Interactions API로 쓰는 것보다 5배 가까이 싸다고도 주장했다.
- **Google 내부 사례:** Gemini Notebook이 요청마다 모델 등급과 thinking level을 고르는 라우터로 쓰고 있으며 일상 질의 지연을 최대 40% 줄였다고 소개했다. Google 검색에서는 MCP 도구에 대한 적대적 행위 탐지 계층으로 쓴다고 밝혔다.
- **제공 범위:** 공식 예제는 `v1beta` API 버전을 지정한 Python SDK이고, 문서 가이드는 Python, JavaScript, REST로 안내된다. OpenRouter, LangChain, Vercel, LiteLLM, Pydantic AI 등 연동이 순차적으로 나오고 있으며 **Gemini in Google Cloud 지원은 "곧(coming soon)"** 이라고만 적혀 있다.

### 실무 관점의 해석: "작은 판단"을 생성 호출에서 떼어 낼 기회

여기서부터는 의견이다. 백엔드에서 LLM 비용과 지연이 커지는 원인 중 하나는 본 작업 전후로 붙는 작은 판단 호출이다. 요청 분류, 도구 선택, 금칙어·정책 검사, 검색 결과가 질문에 답이 되는지 거르는 작업 같은 것들이다. 이런 호출을 생성 모델로 처리하면 출력 파싱 실패, 포맷 흔들림, 생각 토큰 과금이 따라온다. 확률을 숫자로 돌려주는 API는 이 문제를 구조적으로 줄여 준다.

특히 신뢰도 점수가 오는 점이 운영에 유리하다. 예를 들어 "신뢰도 0.9 이상이면 자동 처리, 그 아래면 상위 모델이나 사람에게 넘긴다" 같은 규칙을 코드로 명확하게 둘 수 있다. 다만 임계값은 각 서비스의 데이터로 정해야 하고, Google이 말한 보정(calibration) 품질이 우리 도메인에서도 유지되는지는 직접 검증해야 한다.

한계도 분명하다.

- **열린 답이 필요한 작업에는 맞지 않는다.** 선택지를 미리 정의할 수 있는 판단에만 쓸 수 있다.
- **`v1beta`와 지역·계약 조건.** 현재 공식 안내는 AI Studio의 Gemini API 기준이다. 사내 정책상 Google Cloud(Vertex 계열) 계약으로만 Gemini를 써야 하는 회사라면 아직 바로 도입하기 어렵다.
- **Java 공식 예제가 아직 없다.** 발표 글이 안내하는 가이드는 Python·JavaScript·REST다. Java·Kotlin 서버에서는 당분간 REST로 직접 호출하거나, Spring AI 같은 프레임워크의 판단 API가 이 엔드포인트를 지원하는지 확인해야 한다. 어제 정리한 Spring AI 2.1 RC2의 DecisionModel이 Gemini Decisions API 구현체를 제공한다는 근거는 이 글을 쓰는 시점에 확인하지 못했다.
- **비교 수치는 자체 발표다.** "5배 저렴", "40% 지연 감소"는 Google의 벤치마크와 내부 사례 기준이다.

### 지금 확인할 항목

1. 지금 LLM 호출 로그에서 출력이 짧은 분류·라우팅·검사 호출이 얼마나 되는지, 그 호출들의 토큰 비용과 지연을 따로 집계해 본다.
2. 후보 하나를 골라 AI Studio 무료 티어로 기존 생성 호출과 결과를 나란히 비교하고, 신뢰도 분포를 보고 자동 처리 임계값을 정한다.
3. 사내 데이터 처리 정책상 AI Studio(Gemini API)를 쓸 수 있는지, 아니면 Google Cloud 지원을 기다려야 하는지 먼저 확인한다.
4. Java·Kotlin 서비스라면 REST 호출용 얇은 클라이언트를 둘지, 프레임워크 지원을 기다릴지 결정한다. 공식 엔드포인트가 `v1beta`이므로 버전을 설정값으로 분리해 두는 편이 안전하다.

## 2. Kotlin 2.5.0-RC: 컴파일러 실행 JDK 17 요구가 "오류"로 올라갔다

### 확인된 사실

JetBrains의 [What's new in Kotlin 2.5.0-RC](https://kotlinlang.org/docs/whatsnew-eap.html) 문서에 따르면 2.5.0-RC는 2026년 11월 11일 공개됐다. 서버 개발자에게 영향이 큰 항목만 골랐다.

- **컴파일러 실행 최소 JDK 17:** 컴파일러를 JDK 8로 돌리던 하한을 JDK 17로 올리는 다음 단계로, 17 미만 JDK에서 컴파일러를 실행하면 이제 **오류**가 난다. 임시로 `-Xallow-pre-17-runtime-jdk` 옵션으로 피할 수 있지만, 이 옵션은 Kotlin 2.5.20 또는 2.6.0에서 제거되고 그때부터 JDK 17이 필수라고 명시했다. 이 요구는 "컴파일러를 실행하는 JDK"에 대한 것이다.
- **Java 28 바이트코드 생성 지원:** Kotlin/JVM 컴파일러가 Java 28 바이트코드를 담은 클래스를 만들 수 있게 됐다.
- **안정화된 언어 기능:** 개선된 컴파일 타임 상수, 선택 파라미터용 버전별 오버로드를 만드는 `@IntroducedAt`, **기본으로 켜지는 미사용 반환값 검사기**, 그리고 기본값이 된 이름 기반 구조 분해(`only-syntax` 모드)가 Stable이 됐다. 이 모드에서 기존 `val (x, y)`는 위치 기반 그대로이고, 새 문법 `(val x, val y)`가 이름 기반으로 동작한다.
- **실험 기능:** 컴패니언 객체 없이 타입 이름으로 접근하는 컴패니언 확장·`companion {}` 블록(JVM에서는 `@JvmStatic` 없이 정적 멤버로 생성), 여러 프로퍼티를 가진 **full value class**가 실험 기능으로 들어왔다.
- **`value class` 의미 변경 예고:** full value class가 생기면서 `value class`가 더 이상 곧 inline을 뜻하지 않게 된다. 문서는 이 구분이 **Spring과 직렬화 라이브러리에 중요하다**고 직접 적었다. 앞으로 inline value class는 `inline` 수식어나 `@JvmInline value class`로 명시해야 하며, Kotlin 2.5.20은 표시 없는 단일 필드 value class에 경고를, 2.6.0 또는 2.7.0은 오류를 낼 계획이다. 미리 대비하려면 `-Xinline-value-class-migration=warning` 또는 `=strict` 옵션을 쓸 수 있다.
- **타입 추론 성능 개선:** 복잡한 제네릭 코드에서 생기던 과도한 제약을 줄였는데, 빌더 추론 등 일부 경계 사례에서 추론 타입이나 선택되는 오버로드가 달라질 수 있다고 경고했다. 이전 동작은 `-XXLanguage:-EliminateSecondKindIncorporation`으로 되돌릴 수 있다.

### 실무 관점의 해석

여기서부터는 의견이다. RC 단계의 변경 중 운영 중인 서버 팀이 가장 먼저 부딪힐 부분은 언어 기능보다 **빌드 환경**이다. 애플리케이션을 Java 11 대상으로 배포하더라도, CI 러너나 Gradle 데몬이 JDK 11로 Kotlin 컴파일러를 실행하고 있다면 2.5로 올리는 순간 빌드가 실패할 수 있다. 위 요구 사항은 실행 JDK에 대한 것이고, 바이트코드 대상(`jvmTarget`)을 올리라는 뜻은 아니므로 두 설정을 구분해서 보는 것이 중요하다. 다만 빌드 툴체인 구성에 따라 실제 동작이 다를 수 있으니 자기 프로젝트에서 확인해야 한다.

두 번째는 `value class`다. Spring 서비스에서 ID나 금액을 `@JvmInline value class`로 감싸 쓰는 경우는 이미 표시가 있으니 영향이 적다. 반면 `@JvmInline` 없이 `value class`만 써 온 코드가 있다면 2.5.20부터 경고가 뜨고 이후 오류가 될 예정이다. 직렬화·JPA·Spring 바인딩에서 inline 여부에 따라 동작이 다른 만큼, 지금 미리 명시해 두는 것이 이후 업그레이드를 조용히 넘기는 방법이다.

세 번째로 미사용 반환값 검사가 기본으로 켜진다. 경고를 오류로 다루는(`allWarningsAsErrors`) 빌드라면 업그레이드 직후 빌드가 깨질 수 있다. 버려지는 반환값이 실제 버그인 경우도 있으니, 무조건 끄기보다 한 번 훑어보는 것을 권한다.

Spring Boot 문서는 현재 Kotlin 2.2.x 이상을 요구하고 버전을 의존성 관리로 맞춰 준다. Spring이 2.5를 관리 버전으로 채택하는 시점은 이 글에서 확인하지 못했으므로, RC는 별도 브랜치에서 시험하는 용도로만 쓰는 편이 안전하다.

### 지금 확인할 항목

1. CI와 로컬에서 Kotlin 컴파일러를 실행하는 JDK 버전을 확인한다. Gradle 데몬 JDK, 툴체인 설정, Maven 실행 JDK를 각각 본다.
2. 저장소에서 `value class`를 검색해 `@JvmInline`이 빠진 선언을 찾고, `-Xinline-value-class-migration=warning`으로 경고를 미리 받아 본다.
3. 경고를 오류로 다루는 빌드라면 미사용 반환값 검사 결과를 먼저 확인한다.
4. 별도 브랜치에서 Kotlin 버전만 2.5.0-RC로 올려 테스트를 돌리고, 타입 추론 변경으로 컴파일 오류나 다른 오버로드 선택이 생기는지 본다.

## 정리

| 분야 | 이번 소식이 바꾸는 것 | 우선 행동 |
| --- | --- | --- |
| AI 서비스·비용 | 분류·라우팅을 생성 없이 확률로 처리하는 전용 API, 출력 토큰 무과금 | 짧은 판단 호출 비용 집계, 후보 하나로 비교 실험 |
| 보안·정책 | 신뢰도 기반으로 자동 처리와 사람 검토를 나누기 쉬워짐, Google Cloud 지원은 아직 | 사내 데이터 정책상 AI Studio 사용 가능 여부 확인 |
| 빌드·인프라 | Kotlin 2.5부터 JDK 17 미만으로 컴파일러 실행 시 오류 | CI·Gradle 데몬 JDK 점검 |
| 백엔드 코드 | `value class`의 inline 의미 명시화 예고, 미사용 반환값 검사 기본 활성화 | `@JvmInline` 누락 선언 정리, RC로 테스트 |

## 참고 원문

- [Gemini Decisions API: Fast, calibrated multimodal decisions](https://blog.google/innovation-and-ai/technology/developers-tools/gemini-decisions-api/), Google, 2026-11-11(미국)
- [What's new in Kotlin 2.5.0-RC](https://kotlinlang.org/docs/whatsnew-eap.html), Kotlin Documentation, 2026-11-11
- [Kotlin Support](https://docs.spring.io/spring-boot/reference/features/kotlin.html), Spring Boot Reference Documentation
