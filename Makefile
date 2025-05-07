dev:
	uvicorn app:app --reload --env-file .env --port 8002 --log-level debug

docker-build-local:
	docker build -t gpu_reports:test .

docker-run-local-no-gpu:
	docker run -d --name gpu_reports -p 8002:8002 --env-file .env gpu_reports:test

docker-refresh-local:
	docker build -t gpu_reports:test .
	-@docker rm -f gpu_reports 2>/dev/null || true
	docker run -d --name gpu_reports -p 8002:8002 --env-file .env gpu_reports:test