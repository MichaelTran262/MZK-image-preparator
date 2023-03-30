FROM python:3.8-buster

USER root

RUN apt update
RUN apt -y install libvips libvips-dev libvips-tools
RUN mkdir /preparator

COPY . /preparator

WORKDIR /preparator

RUN pip install -r requirements.txt

EXPOSE 5000

#CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]