# AI for Web Devs 1: Build an Offline LLM Chat App

## First time setup

### Project

- `cp .env.example .env`

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

- [AI vs ML](https://cloud.google.com/learn/artificial-intelligence-vs-machine-learning)
- [Markov Chain](https://en.wikipedia.org/wiki/Markov_chain)
- [What Is ChatGPT Doing … and Why Does It Work?](https://writings.stephenwolfram.com/2023/02/what-is-chatgpt-doing-and-why-does-it-work/)
- [Hugging Face](https://huggingface.co/)
- [LM Studio](https://lmstudio.ai/)
- [OpenWeb UI](https://github.com/open-webui/open-webui)
- [Docker](https://www.docker.com/)
- [Ollama](https://ollama.com/)
- [Flask](https://flask.palletsprojects.com/)
- [Svelte](https://svelte.dev/)
