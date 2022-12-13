FROM python:3.8-buster

RUN apt update
RUN apt -y install libvips libvips-dev libvips-tools

COPY . /app

WORKDIR /app

RUN pip install -r requirements.txt

#EXPOSE 5000
RUN mkdir logs && touch preparator.log

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]