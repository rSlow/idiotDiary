FROM python:3.9

RUN mkdir -p /usr/src/app/

WORKDIR /usr/src/app/

COPY . /usr/src/app/

CMD ["python", "start.py"]