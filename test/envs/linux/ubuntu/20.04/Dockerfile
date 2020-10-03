FROM ubuntu:20.04
MAINTAINER mathias.burger@gmail.com

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Berlin

RUN apt-get update
RUN apt-get install -y curl
RUN apt-get install -y python3 python3-pip
RUN apt-get install -y xvfb gimp python2 python-numpy python-typing

RUN cd /tmp && \
  curl http://archive.ubuntu.com/ubuntu/pool/universe/g/gimp/gimp-python_2.10.8-2_amd64.deb --output gimp-python.deb && \
  curl http://archive.ubuntu.com/ubuntu/pool/universe/p/pygtk/python-gtk2_2.24.0-6_amd64.deb --output python-gtk2.deb && \
  apt install python python-cairo python-gobject-2 && \
  dpkg -i python-gtk2.deb && \
  dpkg -i gimp-python.deb && \
  rm gimp-python.deb python-gtk2.deb

RUN pip3 install pytest setuptools
RUN pip2 install numpy typing

ADD requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

VOLUME /src
WORKDIR /src

CMD ["python3"]
