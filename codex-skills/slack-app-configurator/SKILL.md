---
name: slack-app-configurator
description: Create and run a local GUI for configuring Slack apps with App Configuration Tokens, app names, bot/user OAuth scope checkboxes, Slack app manifests, and Slack CLI setup. Use when the user wants a point-and-click local form to generate, validate, or create a Slack app while minimizing Slack website clicks.
---

# Slack App Configurator

## Quick Start

Start the local GUI from this skill directory:

```bash
python3 scripts/slack_app_configurator.py --open
```

On Windows, start the local GUI from PowerShell:

```powershell
.\scripts\run_windows.ps1
```

Or from Command Prompt:

```cmd
scripts\run_windows.cmd
```

Give the user the printed `http://127.0.0.1:<port>/` URL. The GUI collects:

- App Configuration Token
- app name, bot display name, and optional description
- bot token and user token OAuth scope checkboxes

The app name, bot display name, and description fields intentionally start empty. The default checked scopes match the Hermes Slack guide's current bot/user scope set.

## Workflow

1. Run the GUI script.
2. In the GUI, enter the config token, app name, and selected scopes.
3. Click `Generate manifest` to preview the manifest JSON.
4. Click `Validate manifest` before creating the app.
5. Click `Create app` to run `slack api apps.manifest.create`.
6. Open the returned `oauth_authorize_url` once to approve workspace installation.
7. If you need to validate a generated skill folder, run `python3 scripts/quick_validate.py <path-to-skill>`.

The script runs locally on loopback. It does not save tokens, write token files, or log token values. Slack CLI output is returned to the page with command previews redacted.

## Defaults

Bot scopes:

```text
app_mentions:read
chat:write
files:read
files:write
im:history
im:read
im:write
reactions:write
users:read
```

User scopes:

```text
channels:history
channels:read
chat:write
files:read
files:write
groups:history
groups:read
im:history
im:read
mpim:history
mpim:read
search:read
users:read
```

## Requirements

- `python3`
- Slack CLI available as `slack` for validation, creation, and token rotation actions
- `jq` is not required by the GUI script

Windows users need PowerShell and the official Slack CLI for Windows. Install it with:

```powershell
irm https://downloads.slack-edge.com/slack-cli/install-windows.ps1 | iex
```

Then check:

```powershell
slack version
```

If `slack` is missing, report the script's error and tell the user to install or expose the official Slack CLI in `PATH`.

## Safety Notes

- Treat config tokens, bot tokens, and user tokens as secrets.
- Prefer the GUI's local run buttons over asking the user to paste tokens into chat.
- Do not commit generated manifests if they include private workspace-specific metadata.
- Do not persist tokens in files unless the user explicitly asks for a secure storage flow.
