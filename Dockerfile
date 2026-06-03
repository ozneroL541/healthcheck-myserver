FROM alpine:latest
RUN apk --no-cache add python3 py3-requests
WORKDIR /app
COPY src/ ./src/
COPY Makefile .
RUN apk --no-cache add make
RUN make install
RUN apk del make
