FROM python:3

WORKDIR /app

ENV PYTHONUNBUFFERED 1
ENV PORT 8080

ENV BLOG_BACKEND_GATEWAY_URL http://localhost:8081
ENV BLOG_BACKEND_SESSION_URL http://localhost:8082

COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app/

CMD python manage.py runserver 0.0.0.0:${PORT}
