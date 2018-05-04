FROM python:3.6.5-alpine3.7

COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

CMD python /app/main.py