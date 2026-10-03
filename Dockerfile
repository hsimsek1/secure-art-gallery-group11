FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN useradd --create-home gallery
COPY --chown=gallery:gallery . .
RUN mkdir -p /app/instance && chown gallery:gallery /app/instance
USER gallery
EXPOSE 5000
CMD ["waitress-serve", "--host=0.0.0.0", "--port=5000", "--call", "src.backend:create_app"]
