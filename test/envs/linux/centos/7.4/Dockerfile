FROM centos:7.4.1708
MAINTAINER mathias.burger@gmail.com

RUN yum update -y

RUN yum install -y centos-release-scl
RUN yum-config-manager --enable centos-sclo-rh-testing

RUN yum install -y xorg-x11-server-Xvfb gimp
RUN yum install -y python27-python python27-python-pip python27-python-devel
RUN yum install -y rh-python36-python rh-python36-python-pip rh-python36-python-devel

RUN cd /tmp && curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py" && python get-pip.py
RUN pip install --upgrade pip
RUN pip install numpy typing
RUN scl enable rh-python36 'pip3 install --upgrade pip'
RUN scl enable rh-python36 'pip3 install pytest setuptools'

RUN yum install -y gcc

ADD requirements.txt /tmp/requirements.txt
RUN scl enable rh-python36 'pip3 install -r /tmp/requirements.txt'

VOLUME /src
WORKDIR /src

CMD ["scl", "enable", "rh-python36", "python3"]
