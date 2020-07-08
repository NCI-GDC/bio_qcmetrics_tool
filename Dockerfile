FROM python:3.5-stretch

MAINTAINER Kyle Hernandez <kmhernan@uchicago.edu>

COPY ./dist /opt

WORKDIR /opt

RUN make init-pip \
  && python setup.py install \
  && ln -s /opt/bin/bio_qcmetrics_tool /bin/bio_qcmetrics_tool \
  && chmod +x /bin/bio_qcmetrics_tool


ENTRYPOINT ["/bin/bio_qcmetrics_tool"]

CMD ["--help"]
