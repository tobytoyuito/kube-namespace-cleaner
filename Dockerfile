FROM python:3.6 as python-base

# install dependencies
COPY requirements.txt /requirements.txt
RUN pip install --install-option="--prefix=/install" -r /requirements.txt

FROM python:3.6-alpine

LABEL description="Built from https://github.com/tobytoyuito/kube-namespace-cleaner"

# only copy necessary folder from previous image
COPY --from=python-base /install /usr/local
COPY .pylintrc /app/
COPY *.py /app/
#Wanted to do this in python base but I would have to double install dependencies (pylint fails if modules aren't installed).
RUN pylint --rcfile /app/.pylintrc /app

CMD python /app/main.py
