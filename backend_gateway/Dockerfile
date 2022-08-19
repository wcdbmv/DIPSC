FROM python:3

WORKDIR /app

ENV PYTHONUNBUFFERED 1
ENV PORT 8081

ENV BLOG_BACKEND_SESSION_URL http://localhost:8082
ENV BLOG_BACKEND_PUBLICATION_URL http://localhost:8083
ENV BLOG_BACKEND_SUBSCRIPTION_URL http://localhost:8084
ENV BLOG_BACKEND_STATISTICS_URL http://localhost:8085

COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app/

CMD python manage.py runserver 0.0.0.0:${PORT}
