# Hello World

## First time setup

### Project

- `cp .env.example .env`

### Ollama

_https://ollama.com/library_

- `docker exec -it mmcg_chat_ollama ollama run {MODEL NAME}`
- `docker exec -it mmcg_chat_ollama ollama run tinydolphin`

## Start the stack

- `docker compose up --build`
