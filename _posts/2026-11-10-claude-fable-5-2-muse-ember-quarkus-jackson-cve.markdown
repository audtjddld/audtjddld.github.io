---
title: "Claude Fable 5.2·Meta Muse Ember·Quarkus 긴급 LTS 패치: AI 모델 비용과 Jackson 역직렬화 취약점 점검"
description: "2026년 11월 10일 기술 브리핑. Claude Fable 5.2의 가격 인하와 데이터 보존 조건, Meta Muse Ember의 저가 에이전트 모델 출시, Jackson Databind CVE-2026-110879를 포함한 Quarkus 3.33.4.2 긴급 LTS 릴리스를 1차 출처로 확인하고 Java·Kotlin 백엔드와 AI 서비스 팀의 점검 항목을 정리합니다."
date: 2026-11-10 09:40:00 +0900
categories: [기술뉴스]
tags: [AI, Claude, Meta Muse, LLM 비용, Quarkus, Jackson, CVE, Java, Kotlin, 보안]
---

AI 기능을 붙인 백엔드에서 "어떤 모델을 쓸까"는 이제 성능 질문만이 아니라 비용과 데이터 보존 조건의 질문이 됐다. 그리고 JSON 하나를 잘못 받아들이면 서버에서 임의 클래스가 만들어질 수 있는 Jackson 취약점은 아직 끝나지 않은 숙제다.

**11월 10일 화요일, 미국 시간 기준 11월 9일(월)에 나온 발표 세 가지를 정리했다.** 각 항목의 발표 시점을 표에 따로 적었고, Jackson 취약점처럼 발표 자체는 더 이전인 내용은 그렇게 밝혔다. 직접 벤치마크하거나 운영에 적용해 본 결과가 아니라, 1차 출처를 읽고 점검 항목을 추린 브리핑이다. 아래 성능 수치는 모두 각 회사가 공개한 자체 수치다.

## 먼저 보는 세 가지 소식

| 소식 | 공개 시점(KST) | 현재 상태 | 먼저 영향받는 팀 |
| --- | --- | --- | --- |
| Claude Fable 5.2 / Mythos 5.2 | 11월 10일 새벽(미국 11월 9일) | Fable 5.2 일반 공개, Mythos 5.2는 검증 프로그램 대상 | 고난도 코딩·에이전트 작업에 상위 모델을 쓰는 팀, AI 비용·보안 담당 |
| Meta Muse Ember | 11월 9일(미국 기준 발표일) | Meta Model API에서 사용 가능 | 서브 에이전트·추출·라우팅처럼 반복 호출이 많은 AI 서비스 |
| Quarkus 3.33.4.2 긴급 LTS 릴리스 | 11월 9일(공식 블로그 표기일) | 3.33 LTS 스트림 보안 릴리스 | Quarkus 3.33 사용 팀, Jackson 다형성 역직렬화를 쓰는 모든 JVM 서비스 |

Kotlin은 이번 조사에서 최근 48시간 안의 새 릴리스를 확인하지 못했다. 아래 Jackson 항목은 Kotlin 서버(특히 `jackson-module-kotlin`을 쓰는 Spring·Ktor·Quarkus 애플리케이션)에도 그대로 해당한다.

## 1. Claude Fable 5.2: 더 싸고 빨라졌지만, 데이터 보존 조건을 먼저 보자

### 확인된 사실

Anthropic은 [공식 발표](https://www.anthropic.com/claude-fable-and-mythos-5-2)(2026년 11월 9일, 미국)에서 Claude Fable 5.2와 Claude Mythos 5.2를 공개했다. 핵심은 다음과 같다.

- **같은 기반 모델, 다른 안전장치:** Fable과 Mythos는 같은 기반 모델이다. Fable에는 사이버보안·생물학 분야 오남용을 막는 분류기가 붙어 있어 모든 사용자에게 공개되고, Mythos는 사이버보안·생명과학 검증 프로그램을 통과한 조직만 쓸 수 있다.
- **가격과 속도:** 표준 가격은 입력 100만 토큰당 8달러, 출력 100만 토큰당 40달러다. 5.1 세대보다 출력 생성이 최대 30% 빠르다고 밝혔다. 토큰 생성을 최대 2.5배 빠르게 하는 선택형 fast mode는 입력 16달러, 출력 40달러의 두 배인 80달러다.
- **API 모델 ID:** Claude Platform에서는 `claude-fable-5-2`로 쓸 수 있고, AWS·Google Cloud·Microsoft Azure 등 주요 클라우드에서도 제공된다고 밝혔다. [AWS 블로그](https://aws.amazon.com/blogs/machine-learning/introducing-claude-fable-5-2-on-aws/)는 Amazon Bedrock에서 `global.anthropic.claude-fable-5-2` 형태의 ID로 호출하는 예시를 공개했다.
- **권장 사용처:** Anthropic은 대부분의 코딩·지식 업무는 Opus 5.5로 시작하고, 가장 어렵고 열린 형태의 기술 작업에서 Fable·Mythos로 올리라고 권한다. Fable 5.2를 하위 모델이 자문하는 Advisor나, 쉬운 일을 작은 모델에 나눠 주는 Orchestrator로 쓰는 구성도 제시했다.
- **사이버보안 차단:** Fable 5.2의 안전 분류기는 침투 테스트, 익스플로잇 생성 같은 고위험 사이버 작업 대부분을 막는다. 차단되면 다른 모델의 응답으로 대체된다. 5.1 대비 불필요한 차단은 초기 테스트 기준 약 55% 줄었다고 밝혔다.
- **데이터 보존:** 여러 요청에 걸친 패턴을 보는 안전 모니터링 때문에, Enterprise Frontier Safeguards(현재 비공개 베타)를 쓰지 않는 고객에게는 **안전 모니터링 목적의 30일 보존**이 적용된다고 명시했다. AWS 블로그도 Bedrock에서 기본적으로 최대 30일 보존과 사람의 안전 검토가 필요하며, 호출 전에 계정·프로젝트에 `aws_review` 보존 모드를 설정해야 한다고 안내한다.
- **API 변경:** 추론 내용을 빼내려는 증류(distillation) 시도를 막기 위해 "preserved thinking" 기능을 모든 계정에 확대 적용한다고 밝혔고, 개발자는 관련 문서를 보고 연동을 갱신하라고 안내했다.

### 실무 관점의 해석: 모델 교체는 설정 한 줄이 아니다

가격이 20% 내려갔다는 소식만 보면 모델 ID만 바꾸면 될 것 같지만, 이 글의 의견은 다르다. 백엔드 팀이 먼저 볼 것은 **데이터 보존 조건**이다. 지금까지 ZDR(zero data retention) 조건으로 계약하거나 사내 규정상 프롬프트를 외부에 남기지 않기로 한 서비스라면, Fable 5.2로 바꾸는 순간 30일 보존 대상이 될 수 있다. 개인정보나 고객 코드가 프롬프트에 들어가는 서비스라면 법무·보안 검토가 먼저다.

둘째는 **비용 구조**다. 토큰 단가는 내렸지만 Fable급 모델은 여전히 상위 가격대이고, Anthropic 스스로도 일상 작업에는 Opus 5.5를 권한다. 모든 호출을 Fable로 보내기보다, 어려운 계획·검토 단계만 Fable에 맡기고 반복 작업은 작은 모델로 나누는 라우팅 설계가 비용 면에서 현실적이다. 이것이 아래 Muse Ember 소식과 연결되는 지점이다.

셋째, 보안팀이 AI로 취약점 분석을 하려 한다면 Fable 5.2는 그 용도의 요청 대부분을 막는다. 이 용도는 Mythos 5.2 검증 프로그램이나 Enterprise 고객용 Claude Security 쪽 경로를 따로 검토해야 한다.

### 지금 확인할 항목

1. 우리 서비스가 Claude를 어떤 데이터 보존 조건으로 쓰고 있는지 확인하고, Fable 5.2 전환 시 30일 보존이 계약·사내 정책과 충돌하지 않는지 검토한다.
2. Bedrock을 쓴다면 `aws_review` 보존 모드 설정이 필요한지 [AWS 안내](https://aws.amazon.com/blogs/machine-learning/introducing-claude-fable-5-2-on-aws/)를 기준으로 확인한다.
3. 추론(thinking) 블록을 다음 요청에 다시 넣거나 편집하는 코드가 있다면 preserved thinking 확대 적용으로 동작이 달라지지 않는지 공식 문서로 확인한다. 응답의 첫 블록이 항상 텍스트라고 가정한 파싱 코드도 점검한다.
4. 모델을 바꾸기 전에 자체 평가 세트로 품질과 호출당 비용을 비교한다. 발표된 벤치마크는 Anthropic 자체 결과이며 우리 업무에서 같은 차이가 난다는 보장은 없다.

## 2. Meta Muse Ember: 에이전트의 '잔일'을 맡길 저가 모델

### 확인된 사실

Meta는 [공식 블로그](https://research.meta.ai/blog/muse-ember)(2026년 11월 9일)에서 자사에서 가장 작고 효율적인 모델 Muse Ember를 공개했다.

- **목적:** 도구 호출, 코딩 하위 작업, 라우팅, 정보 추출, 긴 문서 파싱처럼 에이전트가 하루 종일 반복하는 작업용이다.
- **가격과 사양:** 모델 ID는 `muse-ember-1.0`이다. 20만 토큰 이하 프롬프트 기준 입력 100만 토큰당 0.10달러, 캐시된 입력 0.004달러, 출력 0.50달러다. 20만 토큰을 넘는 프롬프트는 입력 0.30달러, 출력 1.50달러로 올라간다. 컨텍스트 창은 100만 토큰, 최대 출력은 51만 2천 토큰이며 Responses API를 지원한다.
- **제공 경로:** Muse Code와 Meta Model API에서 제공되며, Muse 모델 제품군은 Google Cloud와 Oracle Cloud에서도 쓸 수 있다고 밝혔다.
- **자체 비교:** Meta는 Artificial Analysis 지표 기준으로 Claude Haiku 5.5, GPT-6 Luna보다 비용 대비 성능이 좋다고 주장했다. 다만 같은 발표 표에서도 실제 오픈소스 저장소 변경의 병합 가능성을 보는 FrontierCode 2.0-AA는 Haiku 5.5(34.9)가 Muse Ember(27.2)보다 높았다. 모든 항목에서 앞서는 것은 아니라는 뜻이다.

### 실무 관점의 해석: 큰 모델 하나보다 '역할 분담' 설계가 중요해진다

Anthropic이 Fable을 Orchestrator로, Meta가 Ember를 "대량 처리 담당"으로 소개한 것은 같은 방향을 가리킨다. 이 글의 의견으로는, AI 기능을 운영하는 백엔드 팀의 비용 최적화 포인트가 모델 선택에서 **작업 분해와 라우팅**으로 옮겨가고 있다. 로그 요약, 문서 필드 추출, 티켓 분류처럼 정답 형식이 정해진 작업은 저가 모델로 보내고, 판단이 어려운 단계만 상위 모델로 올리는 식이다.

다만 출력 토큰 단가가 낮다고 총비용이 반드시 줄지는 않는다. 재시도 횟수, 검증 실패율, 긴 프롬프트 구간(20만 토큰 초과) 요금이 실제 비용을 좌우한다. 그리고 새 공급자를 추가하면 데이터 처리 위치, 보존 정책, 장애 시 대체 경로까지 따로 검토해야 한다.

### 지금 확인할 항목

1. 현재 AI 호출 중 형식이 정해진 반복 작업(분류·추출·요약)의 비율과 비용을 먼저 집계한다.
2. 이 작업들로 작은 평가 세트를 만들어 저가 모델 후보를 비교한다. 정확도뿐 아니라 JSON 형식 준수율, 재시도율, 지연 시간을 함께 본다.
3. 공급자를 늘릴 계획이라면 모델 호출을 추상화한 계층(예: Spring AI의 `ChatClient`)에서 공급자별 타임아웃과 대체 경로를 설정할 수 있는지 확인한다.

## 3. Quarkus 3.33.4.2 긴급 LTS 릴리스와 Jackson CVE-2026-110879

### 확인된 사실

Quarkus 팀은 [공식 블로그](https://quarkus.io/blog/quarkus-3-33-4-2-released/)(2026년 11월 9일)에서 3.33 LTS 스트림의 긴급 릴리스 3.33.4.2를 냈다. 수정된 항목은 다음과 같다.

- **CVE-2026-107912:** Quarkus Vert.x HTTP 관리 인터페이스에서, 관리용 루트 경로와 권한 규칙을 잘못 결합해 인가를 우회할 수 있는 문제.
- **CVE-2026-110879:** Jackson Databind의 `PolymorphicTypeValidator` 우회. 이전 CVE-2026-54512의 수정이 불완전했던 부분이다.
- **CVE-2026-111497:** Brotli4J를 통해 들어온 Brotli 디코더의 힙 범위 밖 쓰기로, 원격 코드 실행으로 이어질 수 있는 문제.
- 그 밖에 Quarkus BOM이 관리하는 Jackson Avro·CBOR·Protobuf·Smile 데이터 포맷 모듈의 CVE도 Jackson 2.21.8로 함께 해결됐다.

Quarkus 팀은 3.33을 쓰고 있다면 안전한 업그레이드라고 밝혔고, `quarkus update --stream=3.33` 명령을 안내했다.

이 중 Jackson 취약점은 Quarkus만의 문제가 아니다. [GitHub 보안 권고 GHSA-m8xf-2cr7-77ph](https://github.com/FasterXML/jackson-databind/security/advisories/GHSA-m8xf-2cr7-77ph)는 2026년 10월 20일에 공개됐고 심각도는 Critical이다. 요점은 이렇다.

- **무엇이 문제인가:** 클래스 이름을 타입 ID로 쓰는 다형성 역직렬화에서, Jackson이 바깥 클래스만 검사하고 그 안의 제네릭 인자나 배열 원소 타입으로 지정된 클래스는 제대로 검사하지 않았다. 그래서 직접 지정하면 거부될 클래스를 제네릭 인자 안에 숨겨 인스턴스화할 수 있었다.
- **어떤 설정이 해당되나:** Jackson 3.x 기본 `JsonMapper`에서 `@JsonTypeInfo(use = Id.CLASS)` 같은 클래스 이름 기반 다형성을 쓰는 경우, Jackson 2.x·3.x에서 default typing을 켜고 `allowIfBaseType(Map.class)` 같은 바깥 타입 허용 규칙을 쓰는 경우가 포함된다. 권고문은 Spring Data Redis 4.0.7의 `RedisSerializer.json()`과 레거시 `GenericJackson2JsonRedisSerializer()`, Spring Security의 레거시 Jackson 2 모듈도 이 경로를 노출한다고 적었다.
- **영향 버전과 수정 버전:** `com.fasterxml.jackson.core:jackson-databind`는 2.10.0~2.18.11, 2.19.0~2.21.7, 2.22.0~2.22.3이 영향을 받고, **2.18.12, 2.21.8, 2.22.4**에서 고쳐졌다. Jackson 3(`tools.jackson.core:jackson-databind`)은 3.0.0~3.1.7, 3.2.0~3.2.3이 영향을 받고 **3.1.8, 3.2.4**에서 고쳐졌다. 이전 CVE의 수정판으로 알려진 2.18.8, 2.21.4, 3.1.4도 남은 경로를 허용한다고 명시돼 있다.
- **임시 대응:** 업그레이드할 수 없다면 신뢰할 수 없는 데이터에 클래스 이름 기반 다형성을 끄고, 하위 타입 허용 규칙을 좁히고, 공격자가 직렬화된 캐시·세션 값을 쓸 수 없게 하고, 불필요한 의존성을 제거하라고 권고한다.

### 실무 관점의 해석: "우리는 default typing 안 쓰는데요"를 확인하는 법

Jackson 역직렬화 취약점은 늘 "설정에 따라 다르다"로 끝나서 넘어가기 쉽다. 하지만 이번 권고는 애플리케이션이 직접 매퍼를 설정하지 않아도 **Redis 직렬화 편의 API**를 통해 해당 경로가 열릴 수 있다고 적었다. Spring 기반 서비스에서 Redis 캐시나 세션 저장소에 JSON 직렬화를 쓰고, 그 Redis에 다른 시스템이나 사람이 값을 쓸 수 있다면 점검 우선순위를 높여야 한다는 것이 이 글의 판단이다.

또 Jackson은 대부분 프레임워크 BOM이 버전을 정해 주기 때문에, 직접 의존성에 Jackson이 없어도 영향을 받을 수 있다. Quarkus는 이번에 LTS 패치로 올렸지만, Spring Boot 등 다른 프레임워크의 BOM이 어느 Jackson 버전을 가져오는지는 각 프로젝트에서 직접 확인해야 한다. 이 글에서는 Spring Boot 각 버전의 반영 여부를 따로 확인하지 못했다.

### 지금 확인할 항목

1. 빌드 결과에 실제로 들어간 Jackson 버전을 확인한다. Gradle은 `./gradlew dependencyInsight --dependency jackson-databind`, Maven은 `mvn dependency:tree -Dincludes=com.fasterxml.jackson.core,tools.jackson.core`로 볼 수 있다.
2. 수정 버전(2.18.12, 2.21.8, 2.22.4, 3.1.8, 3.2.4) 미만이라면 프레임워크 BOM 업데이트를 우선 검토하고, 바로 못 올리면 Jackson BOM 버전을 명시적으로 올리는 방안을 테스트한다.
3. 코드에서 `activateDefaultTyping`, `enableDefaultTyping`, `@JsonTypeInfo(use = JsonTypeInfo.Id.CLASS)`, `Id.MINIMAL_CLASS`, `allowIfBaseType(`, `GenericJackson2JsonRedisSerializer`, `RedisSerializer.json()`을 검색해 해당 경로가 있는지 확인한다.
4. Quarkus 3.33 LTS를 쓴다면 3.33.4.2로 올리고, 관리 인터페이스(management interface)를 켜 둔 경우 그 경로가 외부에 노출되지 않는지 네트워크 설정도 함께 확인한다.

## 정리

| 분야 | 이번 소식이 바꾸는 것 | 우선 행동 |
| --- | --- | --- |
| AI 서비스·비용 | 상위 모델 단가 인하와 저가 에이전트 모델 출시로 모델 라우팅 설계의 여지가 커짐 | 자체 평가 세트로 품질·비용 비교, 작업별 모델 분리 검토 |
| 보안·개인정보 | Fable 5.2의 30일 보존 조건, Jackson 다형성 역직렬화 우회 | 보존 조건 검토, Jackson 실제 버전과 다형성 설정 점검 |
| 백엔드 운영 | Quarkus 3.33 LTS 긴급 패치 | 3.33.4.2 적용, 관리 인터페이스 노출 확인 |

## 참고 원문

- [Introducing Claude Fable 5.2 and Claude Mythos 5.2](https://www.anthropic.com/claude-fable-and-mythos-5-2), Anthropic, 2026-11-09(미국)
- [Introducing Claude Fable 5.2 on AWS](https://aws.amazon.com/blogs/machine-learning/introducing-claude-fable-5-2-on-aws/), AWS Machine Learning Blog
- [Introducing Our Smallest, Most Efficient Model: Muse Ember](https://research.meta.ai/blog/muse-ember), Meta, 2026-11-09
- [Quarkus 3.33.4.2 released - LTS emergency release](https://quarkus.io/blog/quarkus-3-33-4-2-released/), Quarkus, 2026-11-09
- [GHSA-m8xf-2cr7-77ph (CVE-2026-110879)](https://github.com/FasterXML/jackson-databind/security/advisories/GHSA-m8xf-2cr7-77ph), FasterXML, 2026-10-20
- [Jackson Release 2.21.8](https://github.com/FasterXML/jackson/wiki/Jackson-Release-2.21.8), FasterXML, 2026-10-17
