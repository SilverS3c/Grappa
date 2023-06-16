FROM python:3-slim

WORKDIR /datagenerator
COPY ./requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY ./datagenerator.py datagenerator.py
ENTRYPOINT ["python", "/datagenerator/datagenerator.py"]