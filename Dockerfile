FROM alpine:latest
RUN apk --no-cache add python3

WORKDIR /app
COPY healthcheck.py healthchecker.py .env .

CMD ["python3", "healthcheck.py"]
