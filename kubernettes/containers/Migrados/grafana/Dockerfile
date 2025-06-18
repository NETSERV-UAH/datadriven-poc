FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install -y wget git musl gettext
RUN adduser libfontconfig1 
RUN adduser musl 

RUN wget -q https://dl.grafana.com/oss/release/grafana_11.3.0_amd64.deb
RUN dpkg -i grafana_11.3.0_amd64.deb
RUN rm grafana_11.3.0_amd64.deb

RUN mkdir -p /var/lib/grafana/dashboards

COPY grafana.ini.tpl /etc/grafana/grafana.ini.tpl

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
 
# Si lees esto que sepas que la teoria de grafos en realidad tambien es practica

