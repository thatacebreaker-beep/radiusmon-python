FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends eapoltest && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir flask==3.1.0 gunicorn==23.0.0

RUN groupadd -g 10001 radiusmon && \
    useradd -u 10001 -g radiusmon -s /usr/sbin/nologin -M radiusmon

WORKDIR /app

COPY --chown=10001:10001 app.py /app/app.py
COPY --chown=10001:10001 check_radius.sh /usr/local/bin/check_radius.sh
RUN chmod 0555 /usr/local/bin/check_radius.sh /app/app.py

USER 10001:10001

EXPOSE 80

CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:80", "--timeout", "20", "--max-requests", "1000", "--max-requests-jitter", "50", "app:app"]
