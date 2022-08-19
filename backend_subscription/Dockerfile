FROM python:3

WORKDIR /app

ENV PYTHONUNBUFFERED 1
ENV PORT 8084

ENV BLOG_BACKEND_SESSION_URL http://localhost:8082
ENV BLOG_BACKEND_PUBLICATION_URL http://localhost:8083

COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app/

RUN python manage.py migrate
RUN python manage.py generate -a 10 -t 10
CMD python manage.py runserver 0.0.0.0:${PORT}
