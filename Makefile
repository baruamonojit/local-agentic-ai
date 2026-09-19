APP_NAME = opensource-agent
PORT = 8501

.PHONY: help build run stop logs clean

help:
	@echo "Available commands:"
	@echo "  make build   - Build the Docker image"
	@echo "  make run     - Run the container locally (connected to host Ollama)"
	@echo "  make stop    - Stop and remove the running container"
	@echo "  make logs    - View real-time container logs"
	@echo "  make clean   - Remove container and untagged image"

build:
	docker build -t $(APP_NAME) .

run:
	docker run -d \
		--name $(APP_NAME) \
		--network=host \
		-e OLLAMA_BASE_URL="http://127.0.0.1:11434" \
		--env-file .env \
		$(APP_NAME)
	@echo "App is running at http://localhost:$(PORT)"
	@echo "App is running at http://localhost:$(PORT)"

stop:
	-docker stop $(APP_NAME)
	-docker rm $(APP_NAME)

logs:
	docker logs -f $(APP_NAME)

clean: stop
	-docker rmi $(APP_NAME)