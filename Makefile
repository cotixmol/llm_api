dev:
	uvicorn app:app --reload --env-file .env --port 8002 --log-level debug
