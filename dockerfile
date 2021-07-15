FROM python:3.6-alpine
RUN apk update
RUN apk add openjdk8-jre

WORKDIR /app/
COPY run.py run.py
ADD scripts scripts
RUN ["pip3", "install", "pyyaml", "plotly", "tqdm"]
CMD ["python3", "run.py"]