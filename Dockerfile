FROM python:3.7

ADD requirements.txt /deploy/
ADD start.sh /deploy/
WORKDIR /deploy

RUN pip install -r requirements.txt

ADD ./rakomqtt /deploy/rakomqtt/
CMD ["./start.sh"]
