FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY requirements-ml.txt .
RUN pip install --no-cache-dir --timeout=120 -r requirements-ml.txt

ARG INSTALL_TEST_DEPS=false
COPY requirements-dev.txt .
RUN if [ "$INSTALL_TEST_DEPS" = "true" ]; then pip install --no-cache-dir pytest==8.2.2 pytest-asyncio==0.23.7; fi

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
