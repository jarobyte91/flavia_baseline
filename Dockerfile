# FROM python:slim
# FROM ubuntu:latest
FROM continuumio/miniconda3:latest
# RUN apt-get update
# RUN apt-get install build-essential libpoppler-cpp-dev pkg-config python3-dev -y
RUN conda install -c conda-forge pdftotext -y
RUN useradd quotes
WORKDIR /home/quotes
COPY boot.sh requirements.txt app.py wsgi.py runtime.txt Procfile ./
# RUN chmod +x boot.sh
# RUN python -m venv venv
# RUN venv/bin/pip/ install -r requirements.txt
RUN pip install -r requirements.txt
RUN pip install gunicorn
USER quotes
# EXPOSE 8040
# ENTRYPOINT ["./boot.sh"]
# CMD python app.py
CMD gunicorn --bind 0.0.0.0:$PORT wsgi 
