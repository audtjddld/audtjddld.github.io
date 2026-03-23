---
title: "OpenClaw + LM Studio + Telegram Docker 로컬 AI 챗봇 구축기"
date: 2026-03-23 15:00:00 +0900
categories: [경험 및 정보 공유]
tags: [OpenClaw, LM Studio, Docker, Telegram, 로컬LLM, Rancher Desktop, qwen3]
---

## 왜 로컬 LLM + Telegram 봇인가

ChatGPT나 Claude API를 쓰면 편하긴 한데, 대화 내용이 전부 외부 서버로 나간다. 개인적인 용도로 AI 챗봇을 쓰고 싶은데 프라이버시가 신경 쓰이는 사람이라면 로컬 LLM이 답이다.

그래서 이번에 **LM Studio에서 로컬로 모델을 돌리고**, **OpenClaw를 게이트웨이로 써서 Telegram에서 메시지를 주고받는** 구성을 해봤다. Docker로 감싸서 격리까지 했는데, 삽질을 꽤 했다. 그 과정을 공유한다.

## 아키텍처

```
Telegram 앱 (폰/PC)
    ↕ (Telegram API)
OpenClaw (Docker 컨테이너)
    ↕ (OpenAI-compatible API)
LM Studio (Mac 호스트에서 로컬 실행)
    ↕
qwen3 모델 (GPU/Metal 추론)
```

- **Telegram**: 사용자 인터페이스. 폰이든 PC든 아무 데서나 메시지 보내면 됨
- **OpenClaw**: 멀티채널 AI 게이트웨이. Telegram, Discord, WhatsApp 등 여러 메신저를 LLM에 연결해주는 오픈소스 프로젝트
- **LM Studio**: 로컬 LLM 서버. OpenAI 호환 API를 제공해서 외부 서비스처럼 호출 가능

## 사전 준비

### 1. Docker 환경 (Rancher Desktop)

Mac에서는 Docker Desktop 대신 **Rancher Desktop**을 사용했다. 무료이고 가벼움.

설치 후 Docker context가 제대로 설정되어 있는지 확인:

```bash
docker context ls
```

`rancher-desktop`이 활성화되어 있어야 한다. 만약 `desktop-linux` 같은 다른 context가 선택되어 있으면:

```bash
docker context use rancher-desktop
```

### 2. LM Studio

[lmstudio.ai](https://lmstudio.ai)에서 설치하고, 모델을 다운로드한다.

M1 Max 32GB 기준으로 **qwen3-14b Q4_K_M**을 추천한다 (이유는 아래 트러블슈팅에서 설명).

### 3. Telegram Bot 생성

1. Telegram에서 `@BotFather`에게 `/newbot` 명령
2. 봇 이름과 username 설정
3. 발급된 토큰 저장
4. `@userinfobot`에게 메시지 보내서 본인 Telegram ID 확인

## Docker Compose 설정

```yaml
services:
  openclaw:
    image: ghcr.io/openclaw/openclaw:latest
    container_name: openclaw
    volumes:
      - ./config:/home/node/.openclaw
      - ./workspace:/app/workspace
    extra_hosts:
      - "host.docker.internal:host-gateway"
    restart: always
```

주의할 점:
- 이미지는 `ghcr.io/openclaw/openclaw:latest`이다. Docker Hub의 `openclaw/openclaw`가 아님
- `config` 디렉토리를 통째로 마운트해야 한다. 파일 단위로 마운트하면 OpenClaw가 임시 파일을 못 써서 권한 오류 발생

## OpenClaw 설정 (openclaw.json)

OpenClaw는 **환경변수가 아니라 설정 파일**로 구성한다. `config/openclaw.json`:

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "lmstudio/qwen3-14b"
      },
      "models": {
        "lmstudio/qwen3-14b": {
          "alias": "qwen"
        }
      },
      "workspace": "/app/workspace",
      "timeoutSeconds": 600
    },
    "list": [
      {
        "id": "main",
        "default": true,
        "identity": {
          "name": "Assistant",
          "theme": "helpful assistant"
        }
      }
    ]
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "YOUR_TELEGRAM_BOT_TOKEN",
      "allowFrom": ["YOUR_TELEGRAM_USER_ID"],
      "groups": {
        "*": {
          "requireMention": true
        }
      }
    }
  },
  "models": {
    "mode": "merge",
    "providers": {
      "lmstudio": {
        "baseUrl": "http://YOUR_LOCAL_IP:1234/v1",
        "apiKey": "lmstudio",
        "api": "openai-responses",
        "models": [
          {
            "id": "qwen3-14b",
            "name": "Qwen3 14B",
            "reasoning": false,
            "input": ["text"],
            "cost": {
              "input": 0,
              "output": 0,
              "cacheRead": 0,
              "cacheWrite": 0
            },
            "contextWindow": 65536,
            "maxTokens": 4096
          }
        ]
      }
    }
  }
}
```

핵심 포인트:
- `botToken`: BotFather에서 받은 토큰
- `allowFrom`: 본인 Telegram ID만 넣으면 다른 사람은 봇을 못 씀
- `baseUrl`: LM Studio가 돌아가는 Mac의 IP 주소 (뒤에서 설명)
- `contextWindow`: 모델이 처리할 수 있는 토큰 수. 너무 작으면 오류 발생

## 트러블슈팅: 삽질 7가지

### 1. 이미지명이 틀렸다

처음에 `openclaw/openclaw:latest`로 했는데 pull이 안 됐다. 올바른 이미지는:

```
ghcr.io/openclaw/openclaw:latest
```

GitHub Container Registry에 있다.

### 2. 환경변수로 설정하면 안 된다

처음에 docker-compose.yml에 `TELEGRAM_TOKEN`, `LLM_API_BASE` 같은 환경변수를 넣었는데, OpenClaw는 이 방식을 안 쓴다. **반드시 `openclaw.json` 설정 파일**을 사용해야 한다.

설정 검증은 이렇게:

```bash
docker compose run --rm openclaw-cli config validate
```

### 3. Docker context가 잘못 설정되어 있었다

Rancher Desktop을 쓰는데 Docker context가 `desktop-linux`(Docker Desktop)으로 되어 있어서 데몬 연결이 안 됐다.

```bash
docker context use rancher-desktop
```

이걸로 해결.

### 4. host.docker.internal이 안 먹힌다

보통 Docker 컨테이너에서 호스트 머신에 접근할 때 `host.docker.internal`을 쓰는데, **Rancher Desktop에서는 이게 제대로 작동하지 않았다**. DNS는 풀리는데 실제 연결이 안 됨.

해결: Mac의 실제 로컬 IP를 사용했다.

```bash
# Mac IP 확인
ipconfig getifaddr en0
```

이 IP를 `openclaw.json`의 `baseUrl`에 넣으면 된다.

### 5. LM Studio "Serve on Local Network" 설정

LM Studio는 기본적으로 `127.0.0.1`(localhost)에만 바인드된다. Docker 컨테이너에서 접근하려면 **Server 탭에서 "Serve on Local Network" 옵션을 켜야** `0.0.0.0`으로 바인드되어 외부에서 접근 가능해진다.

### 6. 컨텍스트 윈도우 부족

OpenClaw가 시스템 프롬프트를 포함해서 꽤 큰 초기 프롬프트를 보낸다. `contextWindow`를 너무 작게 잡으면 이런 에러가 나온다:

```
The number of tokens to keep from the initial prompt is greater than the context length
```

최소 **65536** 이상으로 설정하는 걸 추천한다. LM Studio 쪽 Context Length 설정도 맞춰줘야 한다.

### 7. qwen3-32b는 32GB Mac에서 무리다

qwen3-32b (Q4 양자화)는 약 18-20GB를 차지한다. 여기에 OS + Docker + OpenClaw + 컨텍스트 메모리까지 합치면 32GB가 꽉 찬다. 실제로 "Channel Error"와 함께 추론이 터졌다.

## 최종 추천: M1 Max 32GB 기준

| 모델 | VRAM(Q4) | 추천도 |
|------|----------|--------|
| qwen3-8b | ~5-6GB | 가벼움, 빠름 |
| **qwen3-14b Q4_K_M** | **~8.5GB** | **최적, 품질/속도 균형** |
| qwen3-32b | ~18-20GB | 무리, 불안정 |

**qwen3-14b Q4_K_M**이 32GB Mac에서 돌리기에 가장 적합하다. GPT-4o-mini 이상, GPT-4o 미만 정도의 품질이고, 응답 속도도 쾌적하다.

## 마무리

이 구성의 장점:
- **프라이버시**: 대화 내용이 외부 서버로 나가지 않음 (Telegram API 통신만 예외)
- **무료**: LM Studio + OpenClaw 모두 무료/오픈소스
- **편의성**: Telegram으로 폰에서도 PC에서도 접근 가능
- **격리**: Docker로 감싸서 호스트 시스템과 분리

삽질은 좀 했지만 한번 세팅해놓으면 편하다. `docker compose up -d` 한 줄이면 끝이고, Mac 부팅할 때 자동으로 올라오게 해놓으면 항상 쓸 수 있다.
