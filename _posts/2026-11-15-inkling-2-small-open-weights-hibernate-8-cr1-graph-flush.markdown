---
title: "Inkling 2 Small 오픈 웨이트 공개(Apache 2.0, 594B MoE) 자체 호스팅 조건, Hibernate ORM 8.0 CR1 그래프 기반 flush 점검 포인트"
description: "2026년 11월 15일 기술 브리핑. Thinking Machines Lab의 Inkling 2 Small이 Apache 2.0 오픈 웨이트로 풀리면서 필요한 GPU·체크포인트 선택·라이선스 확인 포인트, 그리고 Jakarta Persistence 4.0을 구현한 Hibernate ORM 8.0.0.CR1의 그래프 기반 flush·멀티테넌시 변화와 JDK 28에서 빠지는 Primitive Patterns 프리뷰를 1차 출처로 정리합니다."
date: 2026-11-15 09:40:00 +0900
categories: [기술뉴스]
tags: [AI, 오픈 웨이트, Inkling 2 Small, Thinking Machines, LLM 자체 호스팅, vLLM, SGLang, Hibernate, Hibernate 8, Jakarta Persistence 4.0, JPA, Spring Data JPA, JDK 28, Java, Kotlin]
---

이번 주말 브리핑은 "가져다 쓸 수 있게 된 것"과 "곧 기본값이 바뀌는 것"을 하나씩 다룬다. AI 쪽은 Thinking Machines Lab의 Inkling 2 Small 가중치가 Apache 2.0으로 공개되면서, 사내 GPU에서 직접 돌리는 선택지가 하나 늘었다. Java 쪽은 Hibernate ORM 8.0이 첫 릴리스 후보(CR1)에 도달했는데, flush 순서를 정하는 방식이 기본값부터 바뀐다. JPA를 쓰는 팀이라면 GA 전에 테스트를 돌려 볼 이유가 충분하다. 덧붙여 JDK 28에서 빠지는 Primitive Patterns 프리뷰도 짧게 정리했다.

직접 운영에 적용해 본 결과가 아니라 1차 출처 문서를 읽고 점검 항목을 추린 브리핑이다. 벤치마크 수치는 모두 발표 주체가 공개한 값이며, 독립 검증된 결과가 아니다.

| 소식 | 발표 시점 | 1차 출처 |
| --- | --- | --- |
| Inkling 2 Small 오픈 웨이트 공개 (모델 출시는 11/5) | 2026-11-12 가중치 공개, 11-14 Modal 제공 시작 | [모델 카드](https://thinkingmachines.ai/model-card/inkling-2-small/), [Modal 변경 로그](https://modal.com/changelog/inkling-2-small-is-now-available-on-modal) |
| Hibernate ORM 8.0.0.CR1 | 2026-11-12 (미국) | [In Relation To](https://in.relation.to/2026/11/12/orm-80-cr1/), [호환성 페이지](https://hibernate.org/orm/releases/8.0/) |
| Primitive Patterns 프리뷰 철회 | 2026-11-11 (미국) | [Inside Java](https://inside.java/2026/11/11/withdraw-primitive-patterns-preview/) |

## 1. Inkling 2 Small: Apache 2.0 오픈 웨이트, 하지만 "작은" 모델은 아니다

### 무엇이 바뀌었나

Thinking Machines Lab은 11월 5일 Inkling 2 Small을 자사 파인튜닝 플랫폼 Tinker로 먼저 내놓았고, 이후 Hugging Face에 가중치를 공개했다. 모델 카드 기준 확인되는 사실은 다음과 같다.

- **라이선스**: Apache 2.0. 상업적 사용·수정·재배포가 가능한 가장 관대한 축의 라이선스다.
- **구조**: 48층 디코더 전용 트랜스포머에 희소 MoE. 토큰마다 384개 전문가 중 8개로 라우팅되며, 전체 594B 파라미터 중 활성 파라미터는 17B다.
- **입출력**: 텍스트·이미지 입력, 텍스트 출력. 컨텍스트는 최대 1M 토큰을 지원한다고 밝혔다.
- **정밀도**: NVFP4로 사전학습부터 사후학습까지 진행했고, NVFP4 체크포인트를 기본으로 권장한다. MXFP8 체크포인트도 있지만 평가 점수 차이는 1~2%p 수준이라 실용적 의미는 없다고 설명한다.
- **하드웨어**: NVFP4는 합산 VRAM 500GB 이상(예: B300 2장 또는 H200 4장), MXFP8은 800GB 이상(B300 4장 또는 H200 8장)이 필요하다.
- **서빙 프레임워크**: SGLang, vLLM, TokenSpeed, Unsloth, Hugging Face.
- **접근 경로**: Tinker API, 서드파티 추론 사업자. Modal은 11월 14일 공유 엔드포인트를 11월 27일까지 프리뷰로 연다고 공지했다.

모델 카드의 자체 비교표에서는 BrowseComp(압축 사용 시 90.2%), SWE-Atlas-QnA(74.2%) 등 검색·도구 사용과 일부 에이전트 과제에서 같은 "Flash급" 오픈 웨이트 모델 중 상위 점수를 제시한다. 반면 Terminal Bench v4.0(13.1%)처럼 비교 모델보다 낮은 항목도 같은 표에 그대로 실려 있다. 고르게 강한 모델이라기보다 강점과 약점이 뚜렷한 모델로 읽는 편이 맞다.

### 누가 영향을 받나

- **데이터 외부 반출이 어려운 조직**: 금융·공공·의료처럼 외부 API로 데이터를 보내기 어려운 곳에서 상업 이용 제한이 없는 오픈 웨이트 후보가 하나 늘었다.
- **이미 H200/B300급 클러스터를 운영하는 팀**: 활성 파라미터가 17B라 토큰당 연산량은 크지 않지만, 594B 전체를 메모리에 올려야 한다. "Small"이라는 이름만 보고 단일 GPU 서버를 떠올리면 안 된다.
- **에이전트·RAG 서비스 개발자**: 도구 호출·검색형 벤치마크 점수가 강점으로 제시된 만큼, 사내 검색 에이전트의 자체 호스팅 후보로 검토해 볼 만하다.

### 왜 중요한가 (분석)

*이하는 의견이다.* 오픈 웨이트 경쟁에서 라이선스는 점점 더 중요한 차별점이 되고 있다. 같은 주에 공개된 다른 오픈 모델 중에는 특정 국가(한국 포함)를 이용 지역에서 제외하는 커뮤니티 라이선스를 붙인 사례도 있었다. 이런 상황에서 Apache 2.0은 법무 검토 부담을 크게 줄여 준다. 다만 일부 보도에 따르면 공개 시점에 저장소에는 별도 LICENSE 파일이 없고 모델 카드 메타데이터에만 라이선스가 표기돼 있었다고 한다. 조달 절차가 엄격한 조직이라면 이 점부터 확인하자. 인프라 측면에서는 FP4 네이티브 학습 모델이 실사용 단계에 들어왔다는 점이 눈에 띈다. Blackwell 세대 GPU를 보유한 팀과 Hopper만 있는 팀 사이에서 같은 모델의 운영 비용 차이가 더 벌어질 수 있다.

### 지금 확인할 것

1. **보유 GPU로 돌릴 수 있는지**: NVFP4는 500GB, MXFP8은 800GB 합산 VRAM이 기준이다. 여기에 KV 캐시 여유분까지 따로 계산해야 한다. 1M 컨텍스트를 실제로 쓰려면 메모리가 훨씬 더 든다.
2. **API로 먼저 평가하기**: 클러스터를 구성하기 전에 Tinker나 서드파티 엔드포인트(Modal 프리뷰는 11/27까지)로 우리 도메인 과제를 먼저 돌려 보는 편이 싸다. 호스팅 서비스가 실제로 제공하는 컨텍스트 길이는 서비스마다 다를 수 있으니 따로 확인해야 한다.
3. **라이선스 증빙**: 모델 카드의 Apache 2.0 표기와 Hugging Face 저장소 상태를 캡처해 법무 검토 자료로 남겨 둔다.
4. **안전장치는 애플리케이션 계층에**: 모델 카드도 콘텐츠 필터링, 레이트 리밋, 모니터링을 애플리케이션 단에 별도로 두라고 권고한다. 의료·법률·안전 관련 의사결정 영역에는 추가 검증 없이 배치하지 말라는 내용도 명시돼 있다.

## 2. Hibernate ORM 8.0.0.CR1: flush 순서를 "그래프"로 계산한다

### 무엇이 바뀌었나

Hibernate 팀은 11월 12일 8.0의 첫 릴리스 후보를 냈다. 공지에서 확인되는 핵심은 다음과 같다.

- **Jakarta Persistence 4.0, Jakarta Data 1.1 구현**: `StatelessSession`과 비슷한 무상태 작업을 표준화한 `EntityAgent` API가 들어왔다. 결과를 반환하는 쿼리와 데이터를 바꾸는 문장(statement)은 API가 분리되고, 프로그래밍 방식 SQL 결과 매핑과 타입 안전한 옵션 등도 추가됐다.
- **그래프 기반 flush 조정(기본 활성화)**: 대기 중인 엔티티·컬렉션 변경을 매핑의 관계 제약을 바탕으로 의존성 그래프로 만들고, 그 그래프로 실행 순서를 정한다. 기존의 순서 휴리스틱 방식을 대체하며, 전환 기간에는 `hibernate.flush.queue.type=legacy`로 예전 방식을 쓸 수 있다.
- **연관관계 처리**: subselect fetch가 컬렉션뿐 아니라 to-one 연관관계도 지원한다. `hibernate.bidirectionality_management=true`를 켜면 flush 준비 단계에서 소유 측 기준으로 양방향 참조를 맞춘다. 단, 로딩되지 않은 역방향 컬렉션을 이 동기화만을 위해 초기화하지는 않는다. `@Filter`와 `@SQLRestriction`은 `@ManyToOne`, `@OneToOne`에 직접 선언할 수 있게 됐다.
- **멀티테넌시**: 판별자(discriminator) 기반 멀티테넌시가 PostgreSQL, Db2, SQL Server, CockroachDB의 행 수준 보안(RLS)과 연동된다. 커스텀 `@SQLUpdate`, `@SQLDelete`에는 현재 테넌트 식별자 파라미터를 넣을 수 있다.
- **호환성**: Java 17, 21, 25, 27을 지원하고 Jakarta EE 12 계열이다. 호환성 페이지에는 Quarkus 4.0과 짝을 이룬다고 나와 있다.

### 누가 영향을 받나

- **JPA/Hibernate 기반 백엔드 전반**: Spring Data JPA 사용자도 결국 Hibernate 버전을 따라간다. 다만 Spring Boot가 어느 버전에서 Hibernate 8을 기본으로 관리할지는 이 글을 쓰는 시점에 확인하지 못했다. 참고로 곧 GA될 Spring Boot 4.2의 RC2는 Hibernate 7.4.x를 관리한다.
- **한 트랜잭션에서 insert·update·delete·컬렉션 변경을 섞는 서비스**: Hibernate 팀이 특히 테스트를 요청한 패턴이다. 제약조건 위반이나 데드락을 피하려고 `flush()` 호출 위치를 손으로 조정해 둔 코드가 대표적인 점검 대상이다.
- **SaaS 멀티테넌트 서비스**: DB의 RLS를 ORM 테넌트 판별과 묶을 수 있게 되면서, 애플리케이션 버그로 테넌트 데이터가 섞이는 위험을 DB 계층에서 한 번 더 막을 수 있다.

### 왜 중요한가 (분석)

*이하는 의견이다.* flush 순서는 평소에는 신경 쓸 일이 없다가, 문제가 터지면 "왜 이 순서로 SQL이 나갔지?"를 추적하느라 시간을 가장 많이 쓰는 영역이다. 의존성 그래프 방식은 이론적으로 순서 실패를 줄이고 배칭 최적화의 기반이 된다. 하지만 지금까지의 동작에 기대어 작성된 코드, 예를 들어 특정 순서를 전제로 한 트리거나 유니크 제약 교체 로직은 SQL 실행 순서가 달라지면서 다르게 동작할 수 있다. 기본값이 바뀌는 변화이므로 CR 단계에서 통합 테스트를 돌려 보는 비용이 GA 이후 장애 대응 비용보다 훨씬 싸다.

### 지금 확인할 것

1. **브랜치에서 CR1으로 통합 테스트 돌리기**: `org.hibernate.orm:hibernate-core:8.0.0.CR1`로 올리고, SQL 로그로 flush 순서가 달라진 지점을 비교한다.
2. **문제가 생기면 legacy로 분리 확인**: `hibernate.flush.queue.type=legacy`로 재현되는지 확인해, 원인이 새 flush 조정기인지 다른 변경인지 나눈다. 재현되는 사례는 업스트림에 제보할 가치가 있다.
3. **양방향 연관관계 동기화 옵션 검토**: 연관관계 편의 메서드로 양쪽을 맞추던 코드가 있다면 `hibernate.bidirectionality_management`를 켰을 때의 동작 차이를 확인한다.
4. **마이그레이션 가이드 정독**: 공식 Migration Guide를 읽고, 사용 중인 deprecated·incubating API가 영향을 받는지 확인한다.

## 3. 짧게: JDK 28에서 Primitive Patterns 프리뷰 제거

OpenJDK Amber 팀은 11월 11일, "패턴·instanceof·switch에서의 기본형(primitive) 타입" 기능 개발을 중단한다고 밝혔다. 여섯 번째 프리뷰가 될 예정이던 JEP 초안은 철회되고, 이 기능은 JDK 28에서 제거된다. 프리뷰 기능이므로 `--enable-preview`로 실험하던 코드만 영향을 받는다. 그래도 JDK 28로 올릴 때는 컴파일이 깨진다. 관련 배경은 [amber-spec-experts 메일링 스레드](https://mail.openjdk.org/archives/list/amber-spec-experts@openjdk.org/thread/UYEK3PGOHN6R56AHJTSLPGAY363K666S/)에서 이어진다. *의견:* 프리뷰 기능을 프로덕션 코드에 쓰면 안 되는 이유를 다시 보여 준 사례다. 사내 코드베이스에서 `--enable-preview` 사용처를 한 번 검색해 두면 좋다.

## 정리

- **AI 서비스·인프라**: Inkling 2 Small은 상업 이용이 자유로운 오픈 웨이트라는 점이 가장 큰 의미다. 다만 500GB 이상 VRAM이 기본 전제이므로, API로 먼저 평가한 뒤 자체 호스팅 여부를 판단하자.
- **백엔드 운영(JPA)**: Hibernate 8은 flush 순서 결정 방식이 기본값부터 바뀐다. GA 전에 CR1으로 통합 테스트를 돌리고, legacy 옵션으로 비교 기준을 확보하자.
- **Java 언어**: Primitive Patterns 프리뷰를 쓰던 코드는 JDK 28에서 깨진다. 프리뷰 기능 사용처를 점검하자.
