FROM python:3-slim

WORKDIR /grappa
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD python ./Grappa.py -b $BACKEND -i $ID
EXPOSE 5000