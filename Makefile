.PHONY: infra-up infra-down api web

infra-up:
	docker compose -f infra/compose/docker-compose.yml up -d

infra-down:
	docker compose -f infra/compose/docker-compose.yml down

api:
	cd apps/api && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

web:
	cd apps/web && npm run dev
