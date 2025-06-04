# пример команды make migrate-create msg="Added new table"
migrate-create:
	poetry run alembic revision --autogenerate -m "$(msg)"

migrate-upgrade:
	poetry run alembic upgrade head

migrate-downgrade:
	poetry run alembic downgrade -1

dev-start:
	poetry run uvicorn app.main:app --reload
