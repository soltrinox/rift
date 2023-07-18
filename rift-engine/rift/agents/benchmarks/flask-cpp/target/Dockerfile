FROM cpp

COPY app.py /app

RUN apt-get update && apt-get install -y <dependencies>

EXPOSE 8080

CMD ["cpp", "app.py"]