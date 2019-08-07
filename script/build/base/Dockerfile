FROM centos
MAINTAINER cjw
USER root

#use txyum
RUN rm -rf /etc/yum.repos.d/*
ADD yum.repos.d.tar.gz /etc/

RUN yum update -y && yum upgrade -y && yum install -y \
    epel-release gcc nginx python-setuptools python-devel python-pip net-tools \
    dstat iftop htop which telnet nc wget iproute traceroute \
    expect openssh-clients openssl openssl-devel mysql-devel \
    && yum clean all

RUN pip install --no-cache-dir --trusted-host pypi.douban.com -i http://pypi.douban.com/simple/ requests flask flask-restful gevent protobuf redis sqlalchemy xlrd httpie ujson M2Crypto pycrypto lz4 uWSGI bcrypt cachetools
