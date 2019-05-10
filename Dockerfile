FROM ubuntu:16.04

MAINTAINER Kyle Hernandez <kmhernan@uchicago.edu>

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get -y update && apt-get install -y --force-yes \
        build-essential \
        autoconf \
        zlibc zlib1g-dev \
        libsqlite3-0 \
        libsqlite3-dev \
        python3.5 \
        python3.5-dev \
        python3-pip \
        wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /opt

## Update pip
RUN pip3 install --upgrade pip

## Install python package
RUN mkdir /opt/bio_qcmetrics_tool
RUN mkdir /opt/bio_qcmetrics_tool/bio_qcmetrics_tool
WORKDIR /opt/bio_qcmetrics_tool
ADD bio_qcmetrics_tool /opt/bio_qcmetrics_tool/bio_qcmetrics_tool/
ADD LICENSE /opt/bio_qcmetrics_tool/
ADD setup.py /opt/bio_qcmetrics_tool/

RUN pip3 install .

WORKDIR /opt
