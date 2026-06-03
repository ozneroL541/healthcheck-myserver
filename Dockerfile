FROM alpine:latest
RUN apk --no-cache add python3 py3-requests
WORKDIR /app
COPY Makefile src/ .
RUN make install
