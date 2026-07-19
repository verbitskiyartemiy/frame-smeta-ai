# Демо AI-анализа смет FRAME.
# Сборка:   docker build -t frame-smeta .
# Запуск:   docker run -p 7860:7860 frame-smeta
# Открыть:  http://localhost:7860
FROM python:3.11-slim

WORKDIR /app

# Ставим только лёгкие зависимости демо (без torch/mlflow) — образ компактный.
COPY requirements-app.txt .
RUN pip install --no-cache-dir -r requirements-app.txt

# Код и обработанные реальные данные (коридоры цен строятся из них).
COPY src/ ./src/
COPY data/processed/ ./data/processed/

EXPOSE 7860
CMD ["python", "src/demo_app.py"]
