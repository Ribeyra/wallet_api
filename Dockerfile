FROM python:3.12-slim

WORKDIR /app

# Установка зависимостей
RUN pip install poetry

# Копируем файлы зависимостей
COPY pyproject.toml poetry.lock* /app/

# Устанавливаем зависимости
RUN poetry config virtualenvs.create false && \
    poetry install --no-root --no-interaction --no-ansi

# Копируем остальные файлы
COPY . /app

ENV PYTHONPATH=/app

# Запускаем приложение
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
