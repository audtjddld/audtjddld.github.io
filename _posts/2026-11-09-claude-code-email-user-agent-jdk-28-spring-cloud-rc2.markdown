---
title: "Claude Code 이메일 User-Agent 노출·JDK 28 기능 동결 임박·Spring Cloud RC2: 백엔드 점검"
description: "2026년 11월 9일 기술 브리핑. Claude Code가 계정 이메일을 User-Agent에 넣은 이슈와 임시 대응, JDK 28 EA Build 23과 12월 3일 Rampdown 일정·값 클래스 호환성, Spring Cloud 2026.0.0-RC2 변경을 1차 출처로 확인하고 Java·Kotlin 백엔드 팀의 점검 항목을 정리합니다."
date: 2026-11-09 09:11:34 +0900
categories: [기술뉴스]
tags: [AI, Claude Code, 보안, 개인정보, JDK 28, Java, Kotlin, Spring Cloud]
---

AI 코딩 에이전트에게 웹 조회를 맡겼는데, 그 요청 헤더에 내 계정 이메일이 들어가 있었다면 어디서부터 점검해야 할까? 그리고 3월에 나올 JDK 28을 지금 테스트해야 할 이유는 무엇일까?

**11월 9일 월요일, 지난 주말 사이 백엔드 개발자가 확인할 만한 소식 세 가지를 정리했다.** 오늘 발표된 소식처럼 포장하지 않도록 각 항목의 발표·공개 시점을 표에 따로 적었다. 제품을 직접 벤치마크하거나 운영에 적용한 결과가 아니라, 1차 출처를 읽고 점검 항목을 추린 브리핑이다.

## 먼저 보는 세 가지 소식

| 소식 | 공개 시점(KST) | 현재 상태 | 먼저 영향받는 팀 |
| --- | --- | --- | --- |
| Claude Code 계정 이메일의 User-Agent 노출 이슈 | 11월 6일 07:13, GitHub 이슈 등록 | 임시 차단 모드 배포, 근본 수정은 다음 릴리스 예고 | AI 코딩 에이전트를 쓰는 모든 개발 조직, 보안·개인정보 담당 |
| JDK 28 Early-Access Build 23 | 11월 5일, 다운로드 페이지 표기일 | EA, 12월 3일 Rampdown Phase One 예정 | JDK 업그레이드를 준비하는 플랫폼·라이브러리 팀 |
| Spring Cloud 2026.0.0-RC2 | 11월 5일, 공식 블로그 표기일 | 릴리스 후보, Spring Boot 4.2.0-RC2 기반 | Config Server·Gateway MVC·OpenFeign 사용 팀 |

Kotlin은 이번 조사에서 최근 48시간 안의 새 릴리스를 확인하지 못했다. [공식 릴리스 문서](https://kotlinlang.org/docs/releases.html) 기준 최신 안정판은 10월 8일의 2.4.21이고, 2.5.0은 2026년 12월 예정으로 안내돼 있다. 아래 JDK·Spring 점검 항목은 JVM 위에서 도는 Kotlin 서버에도 그대로 해당한다.

## 1. Claude Code가 계정 이메일을 User-Agent에 넣은 이슈

### 확인된 사실

[anthropics/claude-code 이슈 #107757](https://github.com/anthropics/claude-code/issues/107757)은 Claude Code가 웹 요청의 `User-Agent` 헤더에 로그인한 사용자의 이메일을 넣어 외부 사이트로 보냈다는 신고다. 보고자는 2.1.318 버전 환경을 적었고, 글 작성 시점에 이슈는 열린 상태다.

원인과 대응은 두 곳에서 설명됐다.

- **원인:** [Hacker News 토론](https://news.ycombinator.com/item?id=50385272)에서 Claude Code 작업자라고 밝힌 사용자는, `@author` 태그 등에 이름을 지어내는 문제를 줄이려고 로그인 사용자의 계정 이메일을 모델 컨텍스트에 넣었다고 설명했다. 일부 사이트가 자동화 클라이언트에 연락처를 요구하는데, 모델이 `curl` 같은 명령을 직접 작성할 때 그 이메일을 연락처로 넣는 경우가 있었다는 것이다.
- **임시 대응:** 같은 설명과 이슈 댓글에 따르면 2.1.317 이후 버전에는 기본으로 켜진 내장 모드 `cc-plugin-privacy`가 들어 있고, 이메일이 포함된 웹 도구 호출이나 curl 형태 명령을 실행하기 전에 확인하거나 막는다. 다만 Claude가 스크립트를 직접 작성해 실행하는 경우처럼 **모든 경로를 막지는 못한다**고 스스로 밝혔다. 또 stable 채널은 당시 2.1.311이라 2.1.317 이상으로 올리라고 안내했다.
- **근본 수정 예고:** 계정 이메일을 모델 컨텍스트에서 빼는 변경을 다음 릴리스에 넣겠다고 했다. 이 글을 쓰는 시점에 그 릴리스의 배포 여부는 확인하지 못했다.

이슈 댓글에는 2.1.317~2.1.319에서 이 모드가 문서상 거부해야 할 명령을 거부하지 않았다는 사용자 재현 보고도 여러 건 있다. 이는 개별 사용자의 보고이며, 공식 확인된 결함 목록은 아니다.

### 실무 관점의 해석: 모델에게 준 정보는 결국 밖으로 나갈 수 있다

이번 사례의 핵심은 특정 도구의 버그보다 **"에이전트 컨텍스트에 들어간 값은 에이전트가 만드는 모든 출력으로 흘러갈 수 있다"**는 점이다. 이메일만의 문제가 아니다. 저장소 경로, 프로젝트·고객사 이름, 환경 변수, `git log`의 커밋 작성자 정보도 같은 경로로 외부 요청에 실릴 수 있다. 실제로 이슈 댓글에서도 계정 컨텍스트를 지워도 `.gitconfig`나 커밋 이력에서 이메일을 다시 얻을 수 있다는 지적이 나왔다.

또 하나는 **문자열 패턴으로 막는 가드의 한계**다. 명령 문자열에 이메일과 `User-Agent`가 함께 있을 때만 잡는 방식은, 모델이 파일에 스크립트를 쓴 뒤 실행하거나 다른 헤더를 쓰면 빠져나갈 수 있다. 그래서 보안 관점에서는 프롬프트나 훅 수준의 방어보다 **네트워크 이그레스 제한, 격리된 실행 환경, 컨텍스트에 넣을 정보의 최소화**가 더 근본적인 통제라는 것이 이 글의 의견이다.

영향이 큰 곳은 회사 계정으로 에이전트를 쓰면서 개인 이메일로 로그인한 개발자, 고객사 이름이 저장소에 드러나는 외주·에이전시 조직, 그리고 GDPR 같은 개인정보 규정을 따지는 팀이다. 규정 위반 여부는 각 조직과 계약에 따라 판단할 문제이며, 이 글에서 단정하지 않는다.

### 지금 확인할 항목

1. 팀에서 쓰는 Claude Code 버전을 확인하고 2.1.317 이상인지, 이메일을 컨텍스트에서 뺀 후속 릴리스가 나왔는지 [이슈](https://github.com/anthropics/claude-code/issues/107757)에서 확인한다.
2. 로컬 세션 기록이나 프록시 로그에서 에이전트가 만든 요청의 `User-Agent`·쿼리스트링에 계정 이메일이나 프로젝트명이 들어간 적이 있는지 검색한다.
3. 에이전트가 외부로 나갈 수 있는 도메인을 허용 목록으로 제한할 수 있는지 검토한다. 컨테이너나 VM 같은 격리 환경을 쓰면 실행 범위를 더 명확히 나눌 수 있다.
4. 에이전트용 Git 설정에 공개해도 되는 커밋 이메일(예: GitHub의 noreply 주소)을 쓰고, 연락처를 요구하는 외부 API에는 사람이 명시적으로 정한 업무용 주소만 쓰도록 규칙을 둔다.
5. 다른 AI 코딩 도구도 같은 위험이 있는지 확인한다. 이번 이슈는 Claude Code에서 보고됐지만, 컨텍스트에 개인정보를 넣는 구조라면 어떤 도구에도 생길 수 있는 문제다.

## 2. JDK 28: 기능 동결까지 약 3주, 값 클래스 호환성을 지금 시험하자

### 확인된 사실

[JDK 28 프로젝트 페이지](https://openjdk.org/projects/jdk/28/)의 일정은 다음과 같다. **Rampdown Phase One은 2026년 12월 3일**, Rampdown Phase Two는 2027년 1월 14일, 정식 출시는 **2027년 3월 9일**이다. 현재 목표로 지정된 JEP는 Value Objects(Preview, JEP 401), Structured Concurrency(JEP 543), Ahead-of-Time Code Compilation(JEP 544), ZGC 시작·워밍업 개선(JEP 545), ZGC 적응형 힙 크기(JEP 546), Simple JSON API(Incubator, JEP 540), PEM 인코딩(JEP 542), Shenandoah 세대별 모드 기본화(JEP 535), JVM의 엄격한 필드 초기화(Preview, JEP 539), macOS/x64 포트 제거 예고(JEP 541) 등 10개다.

[JDK 28 Early-Access 페이지](https://jdk.java.net/28/)에는 11월 5일자 **Build 23**이 올라와 있다. EA 빌드는 피드백 수집용이며 GA 빌드와 같은 수준으로 테스트되지 않고, 보안 수정이 빠져 있을 수 있다고 명시돼 있다.

10월 27일 OpenJDK Quality Outreach가 낸 [JDK 28 값 클래스 안내](https://inside.java/2026/10/27/quality-heads-up/)는 이번 주에 새로 나온 글은 아니지만, 동결 전에 다시 볼 가치가 있다. 요지는 다음과 같다.

- 프리뷰 기능을 켜면 `Integer`·`Long` 등 래퍼 클래스, `Optional` 계열, `LocalDate`·`Instant` 등 `java.time` 주요 타입을 포함한 **JDK 클래스 30개가 값 클래스가 된다.** 코드를 다시 컴파일하지 않아도 JDK 28에서 프리뷰를 켜고 실행하면 적용된다.
- 값 객체는 식별성이 없으므로 `==`가 필드 값 비교가 되고, 이들 객체에 `synchronized`를 걸면 컴파일 오류나 `IdentityException`이 발생하며, `WeakHashMap`과 `java.lang.ref` API에 쓸 수 없다.
- 그래서 프리뷰를 끈 상태와 켠 상태 **두 가지로 CI를 돌려 보라**고 권한다. 예상 밖 동작은 valhalla-dev 메일링 리스트로 보고해 달라고 한다.

### 실무 관점의 해석: 당장 쓰지 않아도 라이브러리가 먼저 영향을 받는다

대부분의 서비스는 프리뷰 기능을 운영에 켜지 않으므로 3월 GA 직후 바로 동작이 바뀌지는 않는다. 그런데도 지금 볼 이유가 있다. **프리뷰 단계는 동작이 이상할 때 고쳐 달라고 요청할 수 있는 시기이고, 이후 정식 기능이 되면 라이브러리와 프레임워크가 먼저 대응해야 하기 때문이다.**

박싱된 값에 락을 걸거나, `Integer`·`LocalDate`를 키로 약한 참조 캐시를 만들거나, 래퍼 객체의 동일성(`==`)에 의존하는 코드는 오래된 사내 공통 라이브러리에 남아 있기 쉽다. 이런 코드는 컴파일 성공이나 단순한 기동 확인으로 잡히지 않는다. Structured Concurrency 정식화와 AOT 코드 컴파일도 같은 일정으로 들어오므로, 가상 스레드 기반 동시성 코드나 기동 시간 최적화를 고민하는 팀이라면 EA 빌드에서 함께 시험해 볼 만하다.

### 지금 확인할 항목

1. CI에 JDK 28 EA 빌드 작업을 추가하고, 가능하면 `--enable-preview` 유무 두 가지로 돌린다. 운영 배포에는 EA 빌드를 쓰지 않는다.
2. 사내 공통 모듈에서 래퍼·`java.time` 타입에 대한 `synchronized`, `==` 비교, `WeakHashMap` 키 사용을 검색한다.
3. Kotlin 서버라면 코루틴과 Java Structured Concurrency 중 어떤 동시성 모델을 표준으로 삼을지 팀 기준을 정리해 둔다. 성능 우열은 측정 없이 단정하지 않는다.
4. 사용하는 프레임워크·라이브러리의 JDK 28 지원 계획을 이슈 트래커에서 확인한다.

## 3. Spring Cloud 2026.0.0-RC2: Config Server와 Gateway MVC 변화

### 확인된 사실

[11월 5일 공식 발표](https://spring.io/blog/2026/11/05/spring-cloud-2026-0-0-RC2-has-been-released/)에 따르면 Spring Cloud 2026.0.0-RC2(코드명 Paddington)는 Spring milestone 저장소에 공개됐고, **Spring Boot 4.2.0-RC2를 기반으로 한다.** 각 모듈은 5.1.0-RC2로 올라갔다. 발표문이 꼽은 변경은 다음과 같다.

- **Spring Cloud Config:** Google Cloud Storage를 Config Server 백엔드로 지원하고, 일반 텍스트·바이너리 파일을 `Resource`로 가져올 수 있게 됐다.
- **Spring Cloud Gateway:** Server Web MVC 쪽에 `LocalResponseCache` 필터가 추가됐다.
- **Spring Cloud OpenFeign:** `@SpringQueryMap`의 중첩 객체를 중첩 쿼리 파라미터로 보낸다.

### 실무 관점의 해석: 작은 항목이 요청 형식과 캐시 동작을 바꾼다

GCS 백엔드는 GCP를 쓰는 팀이 Git 저장소 대신 버킷으로 설정을 관리할 선택지가 생겼다는 뜻이다. 다만 버킷 접근 권한과 버전 관리 방식을 새로 설계해야 한다.

더 조심해서 볼 항목은 OpenFeign이다. **중첩 객체를 쿼리 파라미터로 보내는 형식이 바뀌면, 호출받는 쪽 API가 기대하는 파라미터 이름과 어긋날 수 있다.** 기존 동작에 맞춰 만든 서버가 있다면 업그레이드 전후 실제 요청 URL을 비교해 봐야 한다. 이 해석은 발표문의 한 줄 설명과 이슈 번호(#1448)를 근거로 한 것으로, 정확한 직렬화 형식은 해당 이슈에서 다시 확인하자.

Gateway MVC의 응답 캐시 필터는 서블릿 기반 게이트웨이에서도 응답 캐시를 쓸 수 있게 해 준다. 다만 캐시를 켜면 인증 정보가 섞인 응답이나 개인화된 응답이 다른 사용자에게 나가지 않도록 캐시 키와 대상 경로를 꼼꼼히 정해야 한다.

### 지금 확인할 항목

1. Boot 4.2 RC2 검증 환경을 이미 만들었다면 Spring Cloud BOM도 2026.0.0-RC2로 맞춰 함께 시험한다. RC는 운영에 바로 쓰지 않는다.
2. `@SpringQueryMap`에 중첩 객체를 넘기는 Feign 클라이언트를 찾아, 업그레이드 전후 실제 요청 URL을 로그로 비교한다.
3. Gateway MVC에 응답 캐시를 적용한다면 인증·개인화 응답을 캐시 대상에서 빼는 규칙부터 정한다.

Boot 4.2 RC2의 Redis·프록시 헤더 변경은 [어제 정리한 글](/posts/spring-boot-ai-rc2-gpt-6-cyber-backend-brief/)에서 이어서 볼 수 있다.

## 정리: 이번 주에는 "무엇이 밖으로 나가는가"와 "무엇이 조용히 바뀌는가"를 보자

- **AI 도구를 쓰는 모든 팀:** 에이전트가 만든 외부 요청에 계정·프로젝트 정보가 실리지 않는지 확인하고, 문자열 가드보다 이그레스 제한과 격리를 우선한다.
- **Java·Kotlin 플랫폼 팀:** 12월 3일 JDK 28 기능 동결 전에 EA 빌드로 값 클래스 영향을 시험한다.
- **Spring Cloud 사용 팀:** OpenFeign 쿼리 형식과 Gateway 응답 캐시처럼 요청·응답이 조용히 달라질 수 있는 지점부터 회귀 테스트로 남긴다.

세 소식의 공통점은 **눈에 띄는 오류 없이 동작이 달라질 수 있다**는 것이다. 이번 주에는 업그레이드 자체보다 이런 변화를 잡아낼 로그와 테스트를 먼저 준비하는 편이 현실적이다.

## 출처와 확인 기준

정리 기준일은 **2026년 11월 9일 KST**다. 아래 1차 출처 본문을 확인했고, 발표일과 정리일을 구분했다. 이슈와 문서는 이후 바뀔 수 있다.

1. **anthropics/claude-code 이슈 #107757 — Privacy violation in User-Agent header**, 등록 2026년 11월 6일 07:13 KST, 정리 시점 열린 상태: <https://github.com/anthropics/claude-code/issues/107757>
2. **Hacker News — Claude Code sends your email address to websites**, Claude Code 작업자의 원인·대응 설명 포함: <https://news.ycombinator.com/item?id=50385272>
3. **OpenJDK — JDK 28 프로젝트 페이지**, 일정과 대상 JEP: <https://openjdk.org/projects/jdk/28/>
4. **OpenJDK JDK 28 Early-Access Builds**, Build 23 표기일 2026년 11월 5일: <https://jdk.java.net/28/>
5. **Inside.java — Quality Outreach Heads-up: JDK 28 Value Classes**, 원문 표기일 2026년 10월 27일: <https://inside.java/2026/10/27/quality-heads-up/>
6. **Spring Blog — Spring Cloud 2026.0.0-RC2 (aka Paddington) Has Been Released**, 원문 표기일 2026년 11월 5일: <https://spring.io/blog/2026/11/05/spring-cloud-2026-0-0-RC2-has-been-released/>
7. **Kotlin release process**, 최신 안정판·예정 일정 확인용, 이번 호의 새 발표로 취급하지 않음: <https://kotlinlang.org/docs/releases.html>
