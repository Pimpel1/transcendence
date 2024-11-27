FROM docker.elastic.co/logstash/logstash:7.10.2

USER root

COPY ./logstash.conf /usr/share/logstash/pipeline/logstash.conf
COPY ./logstash.yml /usr/share/logstash/config/logstash.yml
COPY ./ssl/logstash.crt /usr/share/logstash/config/logstash.crt
COPY ./ssl/logstash.key /usr/share/logstash/config/logstash.key
COPY ./ssl/elasticsearch.crt /usr/share/logstash/config/elasticsearch.crt

RUN chown -R logstash:logstash /usr/share/logstash/config
RUN chmod 644 /usr/share/logstash/config/logstash.crt \
    /usr/share/logstash/config/elasticsearch.crt
RUN chmod 600 /usr/share/logstash/config/logstash.key

USER logstash
WORKDIR /usr/share/logstash
EXPOSE 5044

CMD ["bin/logstash", "-f", "pipeline/logstash.conf"]
