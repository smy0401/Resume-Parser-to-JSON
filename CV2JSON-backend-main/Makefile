# ==============================================
# CV2JSON Makefile
# ==============================================

PROJECT_NAME=cv2json
DOCKER_COMPOSE=docker compose
DOCKER_IMAGE=cv2json:latest

# ----------------------------------------------
#  Build Docker image
# ----------------------------------------------
build:
	@echo " Building Docker image..."
	$(DOCKER_COMPOSE) build

# ----------------------------------------------
#  Run service (with live logs)
# ----------------------------------------------
run:
	@echo " Starting CV2JSON service..."
	$(DOCKER_COMPOSE) up

# ----------------------------------------------
#  Stop and clean up
# ----------------------------------------------
down:
	@echo " Stopping containers..."
	$(DOCKER_COMPOSE) down

# ----------------------------------------------
#  Test: Run basic health check after container starts
# ----------------------------------------------
test:
	@echo " Running health check..."
	curl -s http://127.0.0.1:8000/health | jq .

# ----------------------------------------------
#  Rebuild everything from scratch
# ----------------------------------------------
rebuild:
	@echo " Full rebuild..."
	$(DOCKER_COMPOSE) down -v --remove-orphans
	$(DOCKER_COMPOSE) build --no-cache
	$(DOCKER_COMPOSE) up
