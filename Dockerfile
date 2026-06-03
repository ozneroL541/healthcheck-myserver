FROM alpine:latest
RUN apk --no-cache add python3 py3-requests
WORKDIR /app
COPY healthcheck.py healthchecker.py Makefile .
RUN make install
