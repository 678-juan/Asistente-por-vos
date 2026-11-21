# Asistente inteligente de recordatorios

Prototipo base en Python 3.11 para reconocer comandos de voz, interpretar
recordatorios y exponerlos mediante una API Flask.

## Ejecucion local

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
python -m flask --app src.app run --port 8000
```

## Pruebas

```bash
pytest tests/unit/ -v
pytest tests/unit/ --cov=src --cov-report=term-missing
```

## Docker

```bash
docker build -t asistente-recordatorios .
docker run --rm -p 8000:8000 asistente-recordatorios
```

Comprobar el estado:

```bash
curl http://127.0.0.1:8000/salud
```
