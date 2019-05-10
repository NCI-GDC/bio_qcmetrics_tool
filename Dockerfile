FROM python:3.5

MAINTAINER Kyle Hernandez <kmhernan@uchicago.edu>

# Copy over source
COPY . /opt/bio_qcmetrics_tool/
WORKDIR /opt/bio_qcmetrics_tool

## Install python package
RUN pip install .
