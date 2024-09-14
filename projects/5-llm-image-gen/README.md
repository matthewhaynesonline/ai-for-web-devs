# AI for Web Devs 5: Custom Offline LLM with Image Generation

## First time setup

### Project

- `cp .env.example .env`

#### DB / SQLAlchemy

```sh
docker exec -it chat_web flask db init
docker exec -it chat_web flask db migrate -m "Initial migration"
docker exec -it chat_web flask db upgrade
docker exec -it chat_web flask db_seed

# One liner wipe and reset DB
docker exec -it chat_db psql -U app -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"; rm -rf app/migrations; docker exec -it chat_web flask db init; docker exec -it chat_web flask db migrate -m "Initial migration"; docker exec -it chat_web flask db upgrade; docker exec -it chat_web flask db_seed
```

### Ollama

_https://ollama.com/library_

- `docker exec -it chat_ollama ollama run {MODEL NAME}`
- `docker exec -it chat_ollama ollama run tinydolphin`

### Svelte

- `cd components/chat`
- `npm i`

### Link build output to Flask static

- force the output to not include hash (vite config)
- add command to build and watch (package json)
- symlink component output from flask static dir
  - `cd app/static`
  - `mkdir components`
  - `cd components`
  - `ln -s ./../../components/chat/dist/assets ./chat`

## Start the stack

- `docker compose up --build`

## Resources

-
