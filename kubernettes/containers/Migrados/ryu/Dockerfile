FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install -y --no-install-recommends autoconf automake git g++ libtool python3 python3-pip python3-dev make gcc libffi-dev libssl-dev libxml2-dev libxslt1-dev zlib1g-dev

WORKDIR /root

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt
RUN git clone https://github.com/davidcawork/ryu.git ryu

WORKDIR /root/ryu

RUN python3 setup.py install
COPY ryu_controller.py /root/

CMD ["ryu-manager", "/root/ryu_controller.py"]

