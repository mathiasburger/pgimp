FROM ubuntu:16.04
MAINTAINER mathias.burger@gmail.com

RUN apt-get update
RUN apt-get install -y xvfb gimp python python-pip
RUN apt-get install -y python3 python3-pip

RUN pip2 install numpy typing
RUN pip3 install pytest setuptools

ADD requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

VOLUME /src
WORKDIR /src

CMD ["python3"]
