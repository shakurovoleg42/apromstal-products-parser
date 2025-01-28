# Используем Python 3.10 как базовый образ
FROM python:3.12-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем все файлы из текущей директории в контейнер
COPY . .

# Устанавливаем зависимости из requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем Python-скрипт
CMD ["python", "parser.py"]
