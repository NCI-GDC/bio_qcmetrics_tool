ARG REGISTRY=docker.osdc.io/ncigdc
ARG BASE_CONTAINER_VERSION=2.3.0

FROM ${REGISTRY}/python3.11-builder:${BASE_CONTAINER_VERSION} as builder

COPY ./ /opt

WORKDIR /opt

RUN pip install tox && tox -e build

ARG REGISTRY=docker.osdc.io/ncigdc
ARG BASE_CONTAINER_VERSION=2.3.0

FROM ${REGISTRY}/python3.11:${BASE_CONTAINER_VERSION}

COPY --from=builder /opt/dist/*.whl /opt/
COPY requirements.txt /opt/

WORKDIR /opt

RUN pip install --no-deps -r requirements.txt \
	&& pip install --no-deps *.whl \
	&& rm -f *.whl requirements.txt

CMD ["bio_qcmetrics_tool --help"]
