FROM python:3.8

WORKDIR /app

COPY . .

RUN mkdir -p TMP_PDF
RUN mkdir -p TMP_OUT

RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6 -y
RUN apt-get install poppler-utils -y
RUN apt-get install ghostscript python3-tk -y

RUN pip3 install "camelot-py[base]"
RUN pip3 install -r requirements.txt

CMD ["gunicorn", "-b", "0.0.0.0:5000", "wsgi:app", "--workers=3"]
