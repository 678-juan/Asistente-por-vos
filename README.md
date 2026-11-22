# Asistente inteligente de recordatorios

Prototipo base en Python 3.11 para reconocer comandos de voz, interpretar
recordatorios y exponerlos mediante una API Flask.

## Requisitos

- Python 3.11 o superior
- Git
- Docker opcional

## Clonar e instalar

En Windows PowerShell:

```powershell
git clone <URL_DEL_REPOSITORIO>
cd Asistente-por-vos

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

En Linux o macOS:

```bash
git clone <URL_DEL_REPOSITORIO>
cd Asistente-por-vos

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Ejecutar localmente

```powershell
python -m flask --app src.app run --host 127.0.0.1 --port 8000
```

Abre `http://127.0.0.1:8000`. Comprueba el estado con:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/salud
```

## Ejecutar las pruebas unitarias

```powershell
python -m pytest tests/unit/ -v
```

El proyecto contiene 22 casos unitarios PU-01 a PU-04. Si una prueba falla,
pytest finaliza con un código distinto de cero.

Con cobertura opcional:

```powershell
pytest tests/unit/ -v --cov=src --cov-report=term-missing
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

## Flujo CI/CD

El workflow `.github/workflows/ci-cd.yml` se ejecuta:

- En `push` hacia `main` o `develop`.
- En `pull_request` hacia `main`.

Etapas:

1. Descarga el repositorio y configura Python 3.11.
2. Instala `requirements.txt` y `requirements-dev.txt`.
3. Ejecuta `pytest tests/unit/ -v`.
4. Si una prueba falla, GitHub Actions detiene el flujo antes del login,
   build, push y despliegue.
5. En un `push`, inicia sesión en GHCR y construye la imagen Docker.
6. Ejecuta un contenedor y prueba `http://127.0.0.1:8000/salud`.

Para hacer push de la imagen a GHCR, el repositorio debe permitir permisos de
Actions con **Read and write permissions**:

1. Abre **Settings** del repositorio en GitHub.
2. Entra a **Actions** y luego **General**.
3. En **Workflow permissions**, selecciona **Read and write permissions**.
4. Guarda los cambios.
