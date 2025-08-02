# Pythonning engil versiyasidan boshlaymiz
FROM python:3.11-slim

# Muhit o'zgaruvchilari (interaktiv bo'lmasin)
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# OS paketlarni yangilash va kerakli paketlarni o‘rnatish
RUN apt-get update \
    && apt-get install -y build-essential libpq-dev netcat gcc curl \
    && apt-get clean

# Ishchi katalogni o‘rnatamiz
WORKDIR /app

# requirements fayllarni o‘rnatamiz
COPY requirements.txt /app/
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Django loyihani konteynerga ko‘chiramiz
COPY . /app/

# statik fayllarni yig‘amiz (run vaqtida ham qilinadi odatda)
# RUN python manage.py collectstatic --noinput

# sog'lomlikni tekshirish uchun tayyor port
EXPOSE 8000

# Gunicorn orqali Django'ni ishga tushiramiz
CMD ["gunicorn", "project_name.wsgi:application", "--bind", "0.0.0.0:8000"]
