FROM ubuntu:latest
LABEL authors="poulyak"

# Используем официальный Python образ
FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем требования в контейнер
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install -r requirements.txt

# Копируем все файлы в контейнер
COPY . .

# Открываем порт, на котором будет работать FastAPI
EXPOSE 8000

# Запускаем приложение через uvicorn
CMD ["uvicorn", "tour_agent:api.app", "--host", "0.0.0.0", "--port", "8000"]
