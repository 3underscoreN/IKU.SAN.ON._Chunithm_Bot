FROM python:3.14-slim-trixie

RUN groupadd -r botuser && useradd -u 1000 -r -g botuser botuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install --with-deps chromium

COPY . .
RUN chown -R botuser:botuser /app

USER botuser

CMD ["python", "bot.py"]