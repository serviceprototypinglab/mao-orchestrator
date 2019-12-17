FROM python:3.7.4-alpine3.10

WORKDIR /usr/src/app
RUN mkdir data

RUN pip install requests

COPY ./test.py ./

CMD ["python", "./test.py"]
