FROM python:3.5-stretch

MAINTAINER Kyle Hernandez <kmhernan@uchicago.edu>

COPY ./dist /opt

RUN make -C /opt init-pip \
  && ln -s /opt/bin/bio_qcmetrics_tool /bin/bio_qcmetrics_tool

WORKDIR /opt

ENTRYPOINT ["/bin/bio_qcmetrics_tool"]

CMD ["--help"]
