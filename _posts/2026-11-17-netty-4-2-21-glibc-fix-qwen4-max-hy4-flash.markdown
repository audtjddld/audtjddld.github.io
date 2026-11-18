---
title: "Netty 4.2.21·4.1.141 긴급 수정: 4.2.20의 glibc 2.33 요구 문제 점검법, Qwen4-Max·Hy4 flash 출시와 API 비용 변화"
description: "2026년 11월 17일 기술 브리핑. 11월 2일 보안 릴리스 Netty 4.2.20·4.1.140의 네이티브 트랜스포트가 실수로 glibc 2.33을 요구하게 된 문제를 4.2.21·4.1.141이 되돌린 내용과 Spring WebFlux·Reactor Netty 운영 환경 점검법, 11월 16일 공개된 Alibaba Qwen4-Max와 Tencent Hy4 flash의 사양·가격을 1차 출처로 정리합니다."
date: 2026-11-17 09:50:00 +0900
categories: [기술뉴스]
tags: [Netty, Reactor Netty, Spring WebFlux, glibc, epoll, io_uring, Java, Kotlin, 백엔드 운영, AI, Qwen, Qwen4-Max, Tencent Hy, LLM API]
---

화요일 브리핑의 중심은 Java 쪽이다. 11월 2일 보안 수정 10건을 담고 나온 Netty 4.2.20.Final·4.1.140.Final이 빌드 실수로 **x86_64·aarch64 네이티브 라이브러리의 glibc 요구 버전을 2.33으로 올려 버렸고**, 11월 16일(현지) 나온 4.2.21.Final·4.1.141.Final이 이를 되돌렸다. 보안 패치 때문에 서둘러 올린 팀일수록 확인할 가치가 있다. AI 쪽은 같은 날 나온 중국 빅테크의 새 모델 두 개, Alibaba Qwen4-Max와 Tencent Hy4 flash를 사양과 가격 위주로 짧게 정리한다.

아래 내용은 공식 릴리스 노트·보도자료를 읽고 추린 것이며, 직접 운영 환경에서 재현하거나 벤치마크한 결과가 아니다.

| 소식 | 시점(KST) | 1차 출처 |
| --- | --- | --- |
| Netty 4.2.21.Final / 4.1.141.Final | 2026-11-17 04:29 (GitHub 릴리스) | [4.2.21 공지](https://netty.io/news/2026/11/16/4-2-21-Final.html), [4.1.141 공지](https://netty.io/news/2026/11/16/4-1-141-Final.html), [GitHub 릴리스](https://github.com/netty/netty/releases/tag/netty-4.2.21.Final) |
| (참고) Netty 4.2.20.Final 보안 릴리스 | 2026-11-02 | [4.2.20 공지](https://netty.io/news/2026/11/02/4-2-20-Final.html) |
| Alibaba Qwen4-Max | 2026-11-16 | [Alibaba Cloud 보도자료](https://www.alibabacloud.com/en/press-room/alibaba-unveils-qwen4-max) |
| Tencent Hy4 flash | 2026-11-16 | [Tencent 보도자료](https://www.tencent.com/tencent-launches-hy4-flash-to-power-high-speed-cost-efficient-ai-deployment-for-everyday-workflows/) |

## 1. Netty 4.2.21·4.1.141: 보안 릴리스가 끌고 온 glibc 2.33 요구를 되돌리다

### 무엇이 바뀌었나 (확인된 사실)

- **배경**: 11월 2일 나온 4.2.20.Final은 "bug-fix and security release"로, `netty-buffer` 범위 밖 읽기, `netty-codec-http2`·`netty-codec-mqtt`의 무제한 메모리 사용, `netty-codec-http`의 제어 문자 처리, `netty-handler`·`netty-codec-quic`의 세션 재개를 통한 mTLS 인증 우회 등 10건의 보안 수정을 담았고, 프로젝트는 업그레이드를 강하게 권고했다. (공지 시점에는 CVE 번호가 `CVE-2026-XXXXX`로 비어 있었다.)
- **문제**: 4.2.21 공지에 따르면 4.2.20과 4.1.140은 빌드 실수로 **x86_64·aarch64용 glibc 요구 버전이 2.33으로 올라가 있었다.** 4.2.21.Final과 4.1.141.Final에서 요구 버전이 이전 수준으로 돌아갔다(#18365, #18390).
- **그 밖의 변경**: 4.2.21에는 `Bzip2Decoder` 오류 후 디코딩 중단, HTTP 응답 reason phrase의 모든 제어 문자·DEL 거부, HTTP/3의 잘못된·연결 전용 헤더 거부, SPDY 24비트 길이 초과 프레임 거부, `MqttDecoder`의 `maxBytesInMessage` 변경 허용 같은 입력 검증 강화와, TLS 핸드셰이크 실패 이벤트 처리, 몇몇 classloader 누수 수정이 들어 있다. 이번 릴리스 자체는 "bug-fix release"로 공지됐고 새 보안 수정 목록은 없다.
- **일정**: 두 공지 모두 Netty 4.1이 **2027년 7월 1일 EOL**이라고 다시 적고 있다.

### 누가 영향을 받나

glibc는 OS가 제공하는 C 라이브러리라서, 영향은 "Netty 네이티브 트랜스포트(`netty-transport-native-epoll`, `io_uring` 등 `.so`가 든 classifier 아티팩트)를 쓰는 Linux x86_64·aarch64 환경 중 glibc가 2.33보다 낮은 곳"으로 좁혀진다. 참고로 배포판 기본 glibc는 대략 Amazon Linux 2가 2.26, RHEL·Rocky·Alma 8이 2.28, Ubuntu 20.04·Debian 11이 2.31로 2.33보다 낮고, RHEL 9(2.34)·Ubuntu 22.04(2.35)·Debian 12(2.36)는 그 이상이다. 정확한 값은 각 환경에서 직접 확인해야 한다. musl을 쓰는 Alpine이나 macOS·Windows, 순수 NIO 트랜스포트만 쓰는 애플리케이션은 이 이슈와 무관하다.

Netty를 직접 쓰지 않아도 Spring WebFlux·Spring Cloud Gateway(Reactor Netty), gRPC-Java, Lettuce(Redis), 각종 비동기 HTTP 클라이언트처럼 Netty를 전이 의존성으로 끌고 오는 스택이 많다. Spring Boot 같은 BOM이 어느 패치 버전에서 4.2.20/4.2.21을 관리 버전으로 잡는지는 이 글을 쓰는 시점에 확인하지 못했다.

### 왜 중요한가 (분석)

*이하는 의견이다.* 보안 공지를 보고 4.2.20으로 올린 뒤 "배포는 됐는데 성능이 이상하다"거나 "특정 서버에서만 기동이 실패한다"는 증상이 있었다면 이 건을 먼저 의심할 만하다. 네이티브 라이브러리 로딩에 실패했을 때 애플리케이션이 NIO로 조용히 폴백할지, 예외로 멈출지는 프레임워크와 설정에 따라 다르다. 조용히 폴백하는 쪽은 장애로 드러나지 않고 지연·CPU 사용량 변화로만 나타날 수 있어 더 놓치기 쉽다. 컨테이너 이미지는 최신 베이스라도 노드 OS의 glibc가 아니라 **이미지 안의 glibc**를 쓴다는 점도 기억해 둘 만하다.

반대로 4.2.20을 피해 4.2.19 이하에 머무는 것은 보안 수정 10건을 포기하는 선택이다. 4.2.21이 보안 수정을 유지한 채 glibc 문제만 되돌린 버전이므로, 현재로서는 4.2.20을 건너뛰고 4.2.21(4.1 계열은 4.1.141)로 가는 것이 자연스러운 경로로 보인다.

### 지금 확인할 것

1. **실제 Netty 버전 확인**: `./gradlew dependencyInsight --dependency io.netty:netty-transport-native-epoll` 또는 `mvn dependency:tree -Dincludes=io.netty`로 전이 의존성까지 포함한 버전을 본다. 4.2.20.Final·4.1.140.Final이면 대상이다.
2. **런타임 glibc 확인**: 운영 컨테이너·서버 안에서 `ldd --version`을 실행한다. 2.33 미만이면서 위 버전을 쓰고 있다면 우선순위를 올린다.
3. **네이티브 트랜스포트 실제 사용 여부**: 애플리케이션 로그에서 epoll/io_uring 로딩 실패 메시지를 찾거나, 진단 엔드포인트에서 `Epoll.isAvailable()`·`Epoll.unavailabilityCause()` 값을 확인한다.
4. **버전 고정**: BOM이 따라오기 전이라면 `io.netty:netty-bom:4.2.21.Final`(또는 `4.1.141.Final`)을 의존성 관리에 명시해 4.2.20을 건너뛴다. 4.1 계열은 EOL(2027-07-01) 전에 4.2 이전 계획도 함께 잡는다.

## 2. Alibaba Qwen4-Max: 2.4T MoE, 활성 71B, 100만 토큰 컨텍스트

### 무엇이 바뀌었나 (확인된 사실)

Alibaba는 11월 16일 Qwen 계열 최상위 모델 **Qwen4-Max**를 공개했다. 보도자료 기준 사양과 주장은 다음과 같다.

- 총 2.4조(2.4T) 파라미터 MoE, 토큰당 활성 파라미터 **710억(71B)** 으로 같은 규모의 Qwen3.8-Max보다 활성 파라미터가 25% 적다. 네이티브 비전과 **100만 토큰 컨텍스트**를 지원한다.
- 자체 벤치마크 Work360에서 Qwen3.8-Max보다 전반적으로 나으면서, High 추론 모드에서 토큰을 35% 덜 쓰고 작업당 평균 비용을 약 60% 줄였다고 밝혔다. Code Arena에서는 6위라고 했다.
- QwenCloud의 Token Plan과 API, QwenWork·QwenStudio에서 바로 쓸 수 있다. 공개된 가격 중 하나는 **암묵적 캐시 적중 입력 100만 토큰당 0.075달러**다.
- Qwen4 시리즈의 **소형 오픈 웨이트 모델을 곧 공개**하겠다고 했다. Qwen4-Max 자체의 가중치 공개는 보도자료에 없다.

### 누가, 어디에 영향을 받나

- **AI 서비스·백엔드**: 긴 문서·에이전트 작업에서 비용을 따지는 팀에게 선택지가 하나 늘었다. 다만 Work360은 Alibaba 자체 벤치마크이고, 비용 절감 수치도 회사 발표다.
- **보안·컴플라이언스**: 호스팅 전용 모델이라 데이터가 QwenCloud로 나간다. 국내 서비스라면 데이터 처리 위치와 약관 검토가 기술 평가보다 먼저다.

*의견:* 실무에서 당장 의미가 큰 쪽은 Max보다 "곧 나올 Qwen4 오픈 웨이트 소형 모델"일 가능성이 높다. 사내 GPU에서 돌릴 모델 후보를 관리하는 팀이라면 이 공개를 지켜볼 만하다.

## 3. Tencent Hy4 flash: 활성 12B, 저가형 1M 컨텍스트 모델

같은 날 Tencent는 **Hy4 flash**를 발표했다. 보도자료 기준 총 2,240억 파라미터(이 중 640억이 Engram 파라미터), 활성 120억, 멀티모달 입력과 최대 100만 토큰 컨텍스트를 지원한다. 가격은 100만 토큰당 입력 약 0.070달러, 출력 약 0.281달러, 캐시 입력 약 0.003달러로 Hy 계열 중 가장 싸다고 했다. Tencent Cloud TokenHub 등에서 제공되며 OpenRouter 연동은 "곧", 11월 30일까지 TokenHub 표준 가격 50% 할인을 내걸었다. 일상 작업은 Hy4 flash, 장기 소프트웨어 엔지니어링 같은 복잡한 작업은 11월 4일 나온 Hy4를 쓰라고 권하며, Hy4 flash도 오픈소스로 공개할 계획이라고 밝혔다.

*의견:* 분류·요약·문서 처리처럼 호출량이 많은 작업에서 "1M 컨텍스트 + 초저가"가 표준 가격대가 되어 가는 흐름이다. 다만 할인가는 한시적이므로 비용 추정은 표준가로 하는 것이 안전하다.

### AI 쪽 지금 확인할 것

1. **비용 비교는 표준가·캐시 조건으로**: 발표 가격은 캐시 적중·프로모션 조건이 섞여 있다. 자사 트래픽의 캐시 적중률을 넣어 다시 계산한다.
2. **자체 평가셋으로 검증**: 공개 벤치마크 대신 실제 프롬프트 몇십 건으로 품질·지연을 비교한다.
3. **데이터 경계 확인**: 해외 호스팅 API로 개인정보·사내 코드를 보내도 되는지 사내 정책을 먼저 확인한다.

## 정리

| 분야 | 소식 | 지금 할 일 |
| --- | --- | --- |
| 백엔드 운영·인프라 | Netty 4.2.21·4.1.141 (4.2.20·4.1.140 glibc 2.33 요구 회귀 수정) | 전이 의존성 버전·`ldd --version` 확인, 4.2.21로 고정 |
| 보안 | Netty 4.2.20 보안 수정 10건 유지 | 4.2.19 이하에 머물지 말고 4.2.21로 |
| AI 서비스·비용 | Qwen4-Max, Hy4 flash | 표준가 기준 비용 재계산, 자체 평가셋 비교, 데이터 경계 검토 |

## 출처

- [Netty 4.2.21.Final released](https://netty.io/news/2026/11/16/4-2-21-Final.html), Netty, 2026-11-16 (GitHub 릴리스 2026-11-17 04:29 KST)
- [Netty 4.1.141.Final released](https://netty.io/news/2026/11/16/4-1-141-Final.html), Netty, 2026-11-16
- [Netty 4.2.20.Final released](https://netty.io/news/2026/11/02/4-2-20-Final.html), Netty, 2026-11-02
- [Alibaba Unveils Qwen4-Max](https://www.alibabacloud.com/en/press-room/alibaba-unveils-qwen4-max), Alibaba Cloud, 2026-11-16
- [Tencent Launches Hy4 flash](https://www.tencent.com/tencent-launches-hy4-flash-to-power-high-speed-cost-efficient-ai-deployment-for-everyday-workflows/), Tencent, 2026-11-16
