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
    tree && yum clean all

RUN pip install --no-cache-dir --trusted-host pypi.douban.com -i http://pypi.douban.com/simple/ \
    requests flask flask-restful gevent==1.1.2 protobuf redis==2.10.6 sqlalchemy \
    xlrd httpie ujson M2Crypto pycrypto lz4 uWSGI bcrypt cachetools redis-py-cluster==1.3.6\
    ConcurrentLogHandler==0.8.7
