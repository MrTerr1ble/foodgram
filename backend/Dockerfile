FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --upgrade pip && pip install -r requirements.txt --no-cache-dir

RUN mkdir -p /app/scripts

COPY scripts/entrypoint.sh /app/scripts/entrypoint.sh

RUN chmod +x /app/scripts/entrypoint.sh

COPY . .

ENTRYPOINT ["/bin/bash", "/app/scripts/entrypoint.sh"]

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "foodgram.wsgi"]