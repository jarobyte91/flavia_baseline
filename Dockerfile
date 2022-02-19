# FROM python:slim
#FROM ubuntu:latest
FROM continuumio/miniconda3:latest
# RUN apt-get update
# RUN apt-get install build-essential libpoppler-cpp-dev pkg-config python3-dev -y
RUN conda install -c conda-forge pdftotext -y
RUN useradd quotes
WORKDIR /home/quotes
COPY quotes_baseline quotes_baseline
WORKDIR quotes_baseline
RUN pip install -r requirements.txt
# RUN python -m venv venv
# RUN venv/bin/pip/ install -r requirements.txt
COPY boot.sh boot.sh
RUN chmod +x boot.sh
USER quotes
EXPOSE 8040
ENTRYPOINT ["./boot.sh"]

