FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN mkdir data

RUN apt-get update -y --no-install-recommends &&\
apt-get install -y git openssh-server etcd-server etcd-client python3 python3-dev python3-pip python3-setuptools postgresql postgresql-contrib libpq-dev python3-venv --no-install-recommends

COPY . ./

RUN pip3 install -r requirements.txt

ENTRYPOINT ["sh", "-c"]

CMD ["sh env_to_conf.sh && python3 ./async_launcher.py"]
