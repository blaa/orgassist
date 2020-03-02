# Container image for development, with the dependencies, dev tools, and the
# code mounted inside instead of copied.
FROM debian:buster

ADD requirements.txt /
ADD requirements-dev.txt /

# Keep lists for easy install during development
RUN apt-get update \
  && apt-get -y install --no-install-recommends python3-pip python3-setuptools python3-wheel \
  && apt-get clean

RUN pip3 install -r requirements.txt -r requirements-dev.txt

VOLUME /app
WORKDIR /app
