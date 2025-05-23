# Используем базовый образ Python
FROM python:3.12.0

# Установка Firebird Client Library
RUN apt-get update && apt-get install -y firebird-dev -y tzdata

# Устанавливаем часовой пояс
ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файл вашего приложения в контейнер
COPY . /app

# Устанавливаем зависимости, если таковые имеются

# Если у вас есть файл requirements.txt, используйте его
COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

# Заменяем "python" на конкретный путь к исполняемому файлу Python
CMD ["/usr/local/bin/python", "main.py"]