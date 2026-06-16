# Hermes Agent Slack Integration Guide

Hermes Agent에서 Slack Web API를 안전하게 호출하기 위한 한국어 가이드입니다. GitHub Pages나 브라우저에서 `index.html`을 열면 App Configuration Token, Slack CLI 기반 앱 생성, 봇/유저 토큰 권한 스코프, 토큰 보관 원칙, 실행 명령 예시를 한 번에 확인할 수 있습니다.

## 구성

- `index.html`: 정적 단일 페이지 가이드
- `codex-skills/slack-app-configurator/`: App Configuration Token으로 Slack 앱 manifest를 만들고, 앱 생성 후 Agent용 Slack 작업 스킬 지침까지 만들어 주는 Codex skill
- 외부 빌드 과정 없음
- Slack 토큰은 문서에 저장하지 않음
- 앱 생성은 `slack api apps.manifest.create`와 manifest JSON 예시 중심으로 안내

## Codex skill 설치

이 repo를 클론한 뒤 스킬 폴더를 로컬 Codex skill 경로로 복사합니다.

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R codex-skills/slack-app-configurator "${CODEX_HOME:-$HOME/.codex}/skills/"
python3 "${CODEX_HOME:-$HOME/.codex}/skills/slack-app-configurator/scripts/slack_app_configurator.py" --open
```

Windows에서는 PowerShell에서 스킬 폴더로 이동한 뒤 실행합니다.

```powershell
.\scripts\run_windows.ps1
```

GUI는 입력한 앱 ID와 유저 토큰을 포함하는 개인용 Slack 작업 스킬 생성 지침을 만들 수 있습니다. 생성된 개인 스킬은 본인 로컬 머신 전용으로 쓰고, GitHub나 공유 드라이브에 올리지 마세요.

스킬 폴더를 검증하려면 함께 포함된 검증 스크립트를 실행합니다.

```bash
python3 codex-skills/slack-app-configurator/scripts/quick_validate.py codex-skills/slack-app-configurator
```

## 로컬 확인

```bash
python3 -m http.server 4173
```

브라우저에서 `http://localhost:4173`을 열어 확인합니다.

## 참고 문서

- [Slack Apps](https://api.slack.com/apps)
- [App manifests](https://docs.slack.dev/app-manifests/configuring-apps-with-app-manifests/)
- [apps.manifest.create](https://docs.slack.dev/reference/methods/apps.manifest.create/)
- [slack api](https://docs.slack.dev/tools/slack-cli/reference/commands/slack_api/)
- [conversations.list](https://docs.slack.dev/reference/methods/conversations.list)
- [conversations.history](https://docs.slack.dev/reference/methods/conversations.history)
- [chat.postMessage](https://docs.slack.dev/reference/methods/chat.postMessage)
