FROM python:3.6.5 as python-base

# install dependencies
COPY requirements.txt /requirements.txt
RUN pip install --install-option="--prefix=/install" -r /requirements.txt

FROM python:3.6.5-alpine3.7

# only copy necessary folder from previous image
COPY --from=python-base /install /usr/local
COPY *.py /app/

CMD python /app/main.py