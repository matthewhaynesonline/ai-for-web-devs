## Running the projects with Mac GPU ( M chip) / running on host machine

The default configuration for the first two projects has Ollama running in a Docker container for convenience. At the time of recording, the laptop running the code was an Intel MacBook, so there was negligible difference in performance between host (native) Ollama vs in a Docker container.

**However, if you have an M chip Mac, you will likely see massive inference performance gains by running Ollama natively on your host machine.** [The native Ollama Mac App](https://ollama.com/download) can utilize Apple silicon GPU, where as the docker container cannot (even if you have an M Chip).

To run Ollama on the host with the projects you will need to do a few manual steps:

1. Download and install the native Ollama app: [https://ollama.com/download](https://ollama.com/download)
2. Make sure you download and test whatever model you want to run (this will be the `MODEL` env var)
   1. For example, after the Ollama mac app is installed and running, type this in your terminal:
   2. `ollama run llama3`
3. Change the `OLLAMA_INSTANCE_URL` to `OLLAMA_INSTANCE_URL=http://docker.for.mac.localhost:11434`
   1. This will tell the python code to make requests to that host, which Docker for Mac uses to proxy requests back out to the host machine
   2. The native Ollama should be running one `127.0.0.1:11434`
4. Comment out the Ollama process in docker compose (and the dependency on it for the web process) as you don't want to waste resource running it if it's not used
   1. Project 3 is setup this way
5. With the native Ollama app running, installed, model loaded and your project env and docker compose updated, start the docker stack

### Model Weights

The other benefit of running the native Ollama app is that the model weights will be cached in a single place and can be reused between projects. The default behavior for the projects is to cache everything within the project to make them self contained, but that behavior could be overridden too.
