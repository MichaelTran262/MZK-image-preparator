FROM python:3.9-buster

USER root

RUN apt update
RUN apt -y install libvips libvips-dev libvips-tools
RUN mkdir /krom_app

COPY . /krom_app

WORKDIR /krom_app

RUN pip install -r requirements.txt

EXPOSE 5000

#CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]