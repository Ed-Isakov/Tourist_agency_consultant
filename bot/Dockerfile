# Используем официальный Python образ
FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# 2. Установка утилит для загрузки и работы с сертификатами
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
       wget \
    && rm -rf /var/lib/apt/lists/*

# 3. Загрузка корневого сертификата в папку, где его ищет libpq/asyncpg
RUN mkdir -p /root/.postgresql \
    && wget "https://storage.yandexcloud.net/cloud-certs/CA.pem" \
         -O /root/.postgresql/root.crt \
    && chmod 0655 /root/.postgresql/root.crt

# Копируем требования в контейнер
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install -r requirements.txt

# Копируем все файлы в контейнер
COPY . .

EXPOSE 5000

CMD ["python", "-u", "main.py"]
