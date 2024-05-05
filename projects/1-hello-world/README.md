# Hello World

## First time setup

### Project

- `cp .env.example .env`

### Ollama

_https://ollama.com/library_

- `docker exec -it mmcg_chat_ollama ollama run {MODEL NAME}`
- `docker exec -it mmcg_chat_ollama ollama run tinydolphin`

## Svelte

- `cd components/mmcg_chat`
- `npm i`

### Link build output to Flask static

- force the output to not include hash (vite config)
- add command to build and watch (package json)
- symlink component output from flask static dir
  - `cd app/static`
  - `mkdir components`
  - `cd components`
  - `ln -s ./../../components/mmcg_chat/dist/assets ./mmcg_chat`

## Start the stack

- `docker compose up --build`
