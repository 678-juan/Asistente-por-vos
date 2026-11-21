import random
from datetime import datetime, timedelta
from threading import RLock

from flask import Flask, jsonify, request, render_template_string

from .models import PENDING, Reminder


def create_app(database=None, repository=None):
    app = Flask(__name__)
    memory_reminders = {}
    memory_lock = RLock()
    next_id = [1]

    def save_reminder(event, scheduled_at):
        with memory_lock:
            for reminder in memory_reminders.values():
                if (
                    reminder.event.casefold() == event.casefold()
                    and reminder.scheduled_at == scheduled_at
                ):
                    raise ValueError("El recordatorio ya existe.")
            reminder = Reminder(next_id[0], event.strip(), scheduled_at, PENDING)
            next_id[0] += 1
            memory_reminders[reminder.id] = reminder
            return reminder

    def find_by_date(date):
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        with memory_lock:
            return sorted(
                (
                    reminder for reminder in memory_reminders.values()
                    if start <= reminder.scheduled_at < end
                ),
                key=lambda reminder: reminder.scheduled_at,
            )

    def serialize_reminder(reminder):
        return {
            "id": reminder.id,
            "event": reminder.event,
            "scheduled_at": reminder.scheduled_at.isoformat(),
            "status": reminder.status,
        }

    def all_reminders_grouped():
        grouped = {}
        with memory_lock:
            for reminder in memory_reminders.values():
                key = reminder.scheduled_at.strftime("%Y-%m-%d")
                grouped.setdefault(key, []).append(reminder)
        for reminders in grouped.values():
            reminders.sort(key=lambda reminder: reminder.scheduled_at)
        return grouped

    def format_reminders(reminders):
        if not reminders:
            return "No tienes recordatorios para esa fecha."
        details = "; ".join(
            f"{item.event} a las {item.scheduled_at.strftime('%H:%M')}"
            for item in reminders
        )
        return f"Tienes estos recordatorios: {details}."

    @app.get("/")
    def index():
        return render_template_string(INDEX_HTML)

    @app.get("/salud")
    def health():
        return jsonify({"estado": "ok"})

    @app.post("/recordatorios")
    def create_reminder():
        payload = request.get_json(silent=True) or {}
        event = payload.get("event")
        scheduled_at = payload.get("scheduled_at")
        try:
            when = datetime.fromisoformat(str(scheduled_at).replace("Z", "+00:00"))
            if not event or not str(event).strip():
                raise ValueError("El evento no puede estar vacio.")
            reminder = save_reminder(str(event).strip(), when)
            return jsonify(serialize_reminder(reminder)), 201
        except Exception as exc:
            return jsonify({"error": str(exc), "tipo": exc.__class__.__name__}), 400

    @app.post("/comando")
    def voice_command():
        payload = request.get_json(silent=True) or {}
        if not payload:
            payload = request.form.to_dict()
        text = payload.get("text") or payload.get("mensaje") or ""
        now = datetime.now()

        try:
            normalized_text = " ".join(str(text).strip().lower().split())
            fact_phrases = (
                "dato curioso",
                "dato interesante",
                "hecho curioso",
                "hecho interesante",
            )
            if any(phrase in normalized_text for phrase in fact_phrases):
                facts = [
                    "Las abejas pueden reconocer caras humanas.",
                    "Un pulpo tiene tres corazones.",
                    "El corazón de una ballena azul puede pesar alrededor de 180 kilos.",
                    "Los árboles pueden comunicarse mediante redes de hongos bajo el suelo.",
                    "El Sol representa aproximadamente el 99.86 por ciento de la masa del sistema solar.",
                    "Los delfines tienen nombres individuales entre ellos.",
                    "Una taza de café está formada por miles de aromas detectables.",
                    "Los tiburones existen desde antes que los dinosaurios.",
                ]
                fact = random.choice(facts)
                return jsonify({
                    "ok": True,
                    "action": "dato_curioso",
                    "message": fact,
                    "dato": fact,
                })

            from .command_interpreter import CommandInterpreter

            parsed = CommandInterpreter().interpret(text, now)
            if parsed.intent == "QUERY_REMINDERS":
                reminders = find_by_date(parsed.query_date)
                return jsonify({
                    "ok": True,
                    "action": "consulta",
                    "message": format_reminders(reminders),
                    "recordatorios": [serialize_reminder(item) for item in reminders],
                })

            if not parsed.event or not parsed.event.strip():
                raise ValueError("El evento no puede estar vacio.")
            reminder = save_reminder(parsed.event, parsed.scheduled_at)
            return jsonify({
                "ok": True,
                "action": "crear",
                "message": (
                    f"Recordatorio creado: {reminder.event}, "
                    f"para el {reminder.scheduled_at.strftime('%d/%m/%Y a las %H:%M')}."
                ),
                "recordatorios": [serialize_reminder(reminder)],
            })
        except Exception as exc:
            return jsonify({
                "ok": False,
                "error": str(exc),
                "tipo": exc.__class__.__name__,
            }), 400

    @app.get("/dato-curioso")
    def interesting_fact():
        facts = [
            "Las abejas pueden reconocer caras humanas.",
            "Un pulpo tiene tres corazones.",
            "El corazón de una ballena azul puede pesar alrededor de 180 kilos.",
            "Los árboles pueden comunicarse mediante redes de hongos bajo el suelo.",
            "El Sol representa aproximadamente el 99.86 por ciento de la masa del sistema solar.",
            "Los delfines tienen nombres individuales entre ellos.",
            "Una taza de café está formada por miles de aromas detectables.",
            "Los tiburones existen desde antes que los dinosaurios.",
        ]
        return jsonify({"dato": random.choice(facts)})

    @app.get("/recordatorios")
    def list_reminders():
        date_text = request.args.get("date")
        try:
            date = datetime.fromisoformat(date_text) if date_text else datetime.now()
            reminders = find_by_date(date)
            return jsonify([serialize_reminder(item) for item in reminders])
        except Exception as exc:
            return jsonify({"error": str(exc), "tipo": exc.__class__.__name__}), 400

    @app.get("/recordatorios/agrupados")
    def grouped_reminders():
        grouped = all_reminders_grouped()
        return jsonify({
            date: [serialize_reminder(item) for item in reminders]
            for date, reminders in sorted(grouped.items())
        })

    return app


def _serialize_reminder(reminder):
    return {
        "id": reminder.id,
        "event": reminder.event,
        "scheduled_at": reminder.scheduled_at.isoformat(),
        "status": reminder.status,
    }


def _serialize_reminders(reminders):
    return [_serialize_reminder(reminder) for reminder in reminders]


def _format_reminders(reminders):
    if not reminders:
        return "No tienes recordatorios para esa fecha."
    details = "; ".join(
        f"{item.event} a las {item.scheduled_at.strftime('%H:%M')}"
        for item in reminders
    )
    return f"Tienes estos recordatorios: {details}."


INDEX_HTML = r"""
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Asistente de recordatorios</title>
  <style>
    :root { font-family: system-ui, sans-serif; color: #172033; background: #eef3fb; }
    body { margin: 0; min-height: 100vh; display: grid; place-items: center; }
    main { width: min(680px, calc(100% - 32px)); background: white; border-radius: 18px;
      padding: 28px; box-sizing: border-box; box-shadow: 0 12px 40px #1d355720; }
    h1 { margin-top: 0; }
    #controls { display: flex; gap: 10px; flex-wrap: wrap; }
    button { border: 0; border-radius: 10px; padding: 12px 16px; cursor: pointer;
      background: #315ee7; color: white; font-weight: 700; }
    button.secondary { background: #e8edf7; color: #172033; }
    button.listening { background: #d64545; animation: pulse 1s infinite; }
    @keyframes pulse { 50% { transform: scale(1.03); } }
    #texto { width: 100%; min-height: 72px; margin: 16px 0 8px; box-sizing: border-box;
      border: 1px solid #ccd6ea; border-radius: 10px; padding: 12px; font: inherit; }
    #respuesta { min-height: 60px; padding: 14px; border-radius: 10px; background: #f5f7fb; }
    #dato { color: #596579; margin-top: 16px; }
    .vista { display: none; }
    .vista.activa { display: block; }
    #volver { margin-bottom: 16px; }
    #lista-fechas { margin-top: 16px; }
    #lista-fechas h2 { margin: 18px 0 8px; }
    .fecha { margin-top: 14px; }
    .fecha h3 { margin: 0 0 6px; font-size: 16px; }
    .fecha ul { margin: 0; padding-left: 20px; }
  </style>
</head>
<body>
  <main>
    <section id="vista-asistente" class="vista activa">
    <h1>Asistente de recordatorios</h1>
    <p>Di una orden, por ejemplo: “Recordarme llamar al médico mañana a las cinco pm”.</p>
    <div id="controls">
      <button id="hablar" type="button">Hablar</button>
      <button id="enviar" type="button" class="secondary">Enviar texto</button>
      <button id="consultar" type="button" class="secondary">Mis recordatorios</button>
    </div>
    <textarea id="texto" aria-label="Comando"></textarea>
    <div id="respuesta">Listo para ayudarte.</div>
    <p id="dato"></p>
    </section>
    <section id="vista-recordatorios" class="vista">
      <button id="volver" type="button" class="secondary">Volver al asistente</button>
      <h1>Mis recordatorios</h1>
      <section id="lista-fechas" aria-label="Recordatorios separados por fecha"></section>
    </section>
  </main>
<script>
const hablar = document.getElementById('hablar');
const texto = document.getElementById('texto');
const respuesta = document.getElementById('respuesta');
const dato = document.getElementById('dato');
const listaFechas = document.getElementById('lista-fechas');
const vistaAsistente = document.getElementById('vista-asistente');
const vistaRecordatorios = document.getElementById('vista-recordatorios');

function mostrarVista(nombre) {
  const mostrarRecordatorios = nombre === 'recordatorios';
  vistaAsistente.classList.toggle('activa', !mostrarRecordatorios);
  vistaRecordatorios.classList.toggle('activa', mostrarRecordatorios);
  if (mostrarRecordatorios) actualizarLista();
}

async function actualizarLista() {
  try {
    const response = await fetch('/recordatorios/agrupados');
    const grupos = await response.json();
    listaFechas.innerHTML = '<h2>Mis recordatorios</h2>';
    const fechas = Object.keys(grupos).sort();
    if (!fechas.length) {
      listaFechas.insertAdjacentHTML('beforeend', '<p>No hay recordatorios creados.</p>');
      return;
    }
    for (const fecha of fechas) {
      const bloque = document.createElement('article');
      bloque.className = 'fecha';
      const titulo = document.createElement('h3');
      titulo.textContent = fecha;
      const lista = document.createElement('ul');
      for (const item of grupos[fecha]) {
        const fila = document.createElement('li');
        const hora = new Date(item.scheduled_at).toLocaleTimeString('es-ES', {
          hour: '2-digit', minute: '2-digit'
        });
        fila.textContent = `${hora} - ${item.event}`;
        lista.appendChild(fila);
      }
      bloque.append(titulo, lista);
      listaFechas.appendChild(bloque);
    }
  } catch (error) {
    listaFechas.textContent = 'No se pudo actualizar la lista.';
  }
}

function decir(mensaje) {
  respuesta.textContent = mensaje;
  if ('speechSynthesis' in window) {
    speechSynthesis.cancel();
    const voz = new SpeechSynthesisUtterance(mensaje);
    voz.lang = 'es-ES';
    speechSynthesis.speak(voz);
  }
}

async function enviarComando() {
  const value = texto.value.trim();
  if (!value) return decir('Escribe o dicta una orden.');
  const enviar = document.getElementById('enviar');
  enviar.disabled = true;
  try {
    const response = await fetch('/comando', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({text: value})
    });
    const result = await response.json();
    decir(result.message || result.error || 'No pude procesar la orden.');
    actualizarLista();
  } catch (error) {
    decir('No pude contactar con el asistente. Comprueba que la pagina esta abierta en http://127.0.0.1:8000.');
  } finally {
    enviar.disabled = false;
  }
}

document.getElementById('enviar').addEventListener('click', enviarComando);
document.getElementById('consultar').addEventListener('click', async () => {
  mostrarVista('recordatorios');
});
document.getElementById('volver').addEventListener('click', () => {
  mostrarVista('asistente');
});
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (!SpeechRecognition) {
  hablar.disabled = true;
  hablar.textContent = 'Voz no disponible';
}

let recognitionActive = null;

hablar.addEventListener('click', () => {
  if (recognitionActive) {
    recognitionActive.stop();
    return;
  }
  const recognition = new SpeechRecognition();
  recognitionActive = recognition;
  recognition.lang = 'es-ES';
  recognition.intermediateResults = false;
  recognition.continuous = false;
  hablar.classList.add('listening');
  hablar.textContent = 'Escuchando...';
  recognition.onresult = event => {
    texto.value = event.results[0][0].transcript;
    enviarComando();
  };
  recognition.onerror = event => {
    const mensajes = {
      network: 'El reconocimiento remoto fallo. Usa Chrome o Edge y escribe el comando mientras tanto.',
      notallowed: 'Debes permitir el uso del microfono en el navegador.',
      denied: 'Debes permitir el uso del microfono en el navegador.',
      noSpeech: 'No detecte ninguna voz. Pulsa Hablar e intenta de nuevo.',
      aborted: 'La escucha fue cancelada.'
    };
    decir(mensajes[event.error] || 'No pude escuchar: ' + event.error);
  };
  recognition.onend = () => {
    recognitionActive = null;
    hablar.classList.remove('listening');
    hablar.textContent = 'Hablar';
  };
  recognition.start();
});
</script>
</body>
</html>
"""


app = create_app()
