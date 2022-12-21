FROM python:3.8-buster

USER root

RUN apt update
RUN apt -y install libvips libvips-dev libvips-tools
RUN mkdir /app

COPY requirements.txt /

WORKDIR /

RUN pip install -r requirements.txt

#EXPOSE 5000

WORKDIR /app

#CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]