FROM python:3

WORKDIR /app

ENV PYTHONUNBUFFERED 1
ENV PORT 8083

ENV BLOG_BACKEND_SESSION_URL http://localhost:8082

COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app/

RUN python manage.py migrate
RUN python manage.py generate -t 100 -T 5 -s 15 -p 1000 -S 3 -P 100 -C 10
CMD python manage.py runserver 0.0.0.0:${PORT}
