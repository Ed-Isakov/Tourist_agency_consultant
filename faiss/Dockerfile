# Используем официальный Python образ
FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем требования в контейнер
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы в контейнер
COPY . .

# Открываем порт, на котором будет работать FastAPI
EXPOSE 5000

# Запускаем приложение через uvicorn
CMD ["uvicorn", "faiss_service:app", "--host", "0.0.0.0", "--port", "5000"]
