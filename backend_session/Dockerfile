FROM python:3

WORKDIR /app

ENV PYTHONUNBUFFERED 1
ENV PORT 8082

COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app/

RUN python manage.py migrate
RUN python manage.py generate -s -u 100
CMD python manage.py runserver 0.0.0.0:${PORT}
