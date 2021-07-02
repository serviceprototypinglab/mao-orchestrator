FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    openssh-client \
    python3 \
    python3-dev \
    python3-pip \
    python3-setuptools \
    postgresql-client \
 && rm -rf /var/lib/apt/lists/*

RUN useradd -m user
RUN mkdir -p /home/user/.ssh
RUN mkdir /home/user/data

COPY . /home/user

WORKDIR /home/user/

RUN pip3 install --no-cache-dir -r requirements.txt

RUN chown -R user:user /home/user

USER user

ENTRYPOINT ["sh", "-c"]

CMD ["sh env_to_conf.sh && python3 ./async_launcher.py"]
