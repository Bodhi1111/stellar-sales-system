install:
	python3 -m venv venv && ./venv/bin/pip install -r requirements.txt

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

.PHONY: install docker-up docker-down
