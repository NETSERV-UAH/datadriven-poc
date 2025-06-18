FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install -y curl wget python3 python3-pip

RUN curl -O https://dl.influxdata.com/influxdb/releases/influxdb2_2.7.5-1_amd64.deb
RUN dpkg -i influxdb2_2.7.5-1_amd64.deb
RUN rm influxdb2_2.7.5-1_amd64.deb
RUN pip3 install influxdb-client

RUN mkdir -p /var/lib/influxdb /etc/influxdb

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
