"""Generate modern AI texts (ES/EN) with free OpenRouter models. Appends to data/gen.jsonl."""
import json, random, sys, time, urllib.request
from pathlib import Path

env = dict(l.strip().split("=", 1) for l in open("/home/brm/.hermes/.env") if "=" in l and not l.startswith("#"))
MODELS = sys.argv[1].split(",")
N = int(sys.argv[2])
random.seed(int(sys.argv[3]) if len(sys.argv) > 3 else 1)
OUT = Path("data/gen.jsonl")

ES = {
    "noticia": "Escribe una noticia de unas {n} palabras sobre {t}.",
    "opinion": "Escribe una columna de opinión de unas {n} palabras sobre {t}.",
    "resena": "Escribe una reseña de unas {n} palabras de {r}.",
    "blog": "Escribe una entrada de blog de unas {n} palabras sobre {t}.",
    "reddit": "Escribe un post para un foro contando en primera persona una experiencia sobre {t}. Unas {n} palabras.",
    "cuento": "Escribe un cuento breve de unas {n} palabras sobre {s}.",
    "wiki": "Escribe un artículo enciclopédico de unas {n} palabras sobre {w}.",
    "correo": "Redacta un correo de unas {n} palabras para {e}.",
    "ensayo": "Escribe un ensayo académico breve de unas {n} palabras sobre {t}.",
    "humano": "Escribe un texto de unas {n} palabras sobre {t}. Que suene natural, como lo escribiría una persona real, sin estructura de manual.",
    "linkedin": "Escribe una publicación de LinkedIn de unas {n} palabras sobre {t}.",
    "discurso": "Escribe un discurso de unas {n} palabras para {e}.",
}
EN = {
    "news": "Write a news article of about {n} words about {t}.",
    "opinion": "Write an opinion column of about {n} words about {t}.",
    "review": "Write a review of about {n} words of {r}.",
    "blog": "Write a blog post of about {n} words about {t}.",
    "reddit": "Write a Reddit post telling a first-person experience about {t}. About {n} words.",
    "story": "Write a short story of about {n} words about {s}.",
    "wiki": "Write an encyclopedia article of about {n} words about {w}.",
    "email": "Write an email of about {n} words to {e}.",
    "essay": "Write a short academic essay of about {n} words about {t}.",
    "human": "Write about {n} words about {t}. Make it sound natural, like a real person wrote it, no textbook structure.",
    "linkedin": "Write a LinkedIn post of about {n} words about {t}.",
    "speech": "Write a speech of about {n} words for {e}.",
}
T_ES = ["el transporte público en Santiago", "la sequía en el norte de México", "el teletrabajo después de la pandemia", "los precios de los arriendos", "la inteligencia artificial en los colegios", "el reciclaje en los barrios", "la salud mental de los universitarios", "el fútbol femenino", "las ferias libres", "la migración venezolana", "el turismo en la Patagonia", "las apps de delivery", "aprender a cocinar de adulto", "criar hijos con pantallas", "el costo de la vida", "los incendios forestales"]
T_EN = ["public transit in mid-sized cities", "remote work after the pandemic", "rent prices", "AI in schools", "community gardens", "student mental health", "women's soccer", "farmers markets", "small-town tourism", "food delivery apps", "learning to cook as an adult", "kids and screen time", "the cost of living", "wildfires", "local newspapers closing", "learning a second language"]
R_ES = ["una novela de misterio ambientada en Valparaíso", "un restaurante de comida peruana", "unos audífonos inalámbricos baratos", "una serie de ciencia ficción", "un hotel en Cartagena", "un disco de rock independiente"]
R_EN = ["a mystery novel set in a coastal town", "a ramen restaurant", "budget wireless earbuds", "a science fiction series", "a boutique hotel", "an indie rock album"]
S_ES = ["un faro abandonado", "una abuela que guarda un secreto", "un niño que encuentra una carta", "un viaje en tren nocturno", "una mudanza", "un perro perdido"]
S_EN = ["an abandoned lighthouse", "a grandmother keeping a secret", "a boy who finds a letter", "a night train", "moving house", "a lost dog"]
W_ES = ["el río Biobío", "la cueca", "el volcán Villarrica", "la empanada de pino", "Gabriela Mistral", "el desierto de Atacama"]
W_EN = ["the Mississippi River", "the harmonica", "Mount Rainier", "sourdough bread", "Emily Dickinson", "the Mojave Desert"]
E_ES = ["pedir una reunión a un cliente", "reclamar por un cobro indebido", "presentar un proyecto al equipo", "la graduación de un colegio", "inaugurar una biblioteca", "agradecer a un profesor"]
E_EN = ["request a meeting with a client", "dispute a wrong charge", "pitch a project to the team", "a high school graduation", "opening a library", "thank a teacher"]


def ask(model, prompt):
    if model.startswith("gem:"):
        body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": random.choice([0.7, 0.9, 1.0]), "maxOutputTokens": 4000}}
        req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{model[4:]}:generateContent?key={env['GEMINI_API_KEY']}",
                                     data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        d = json.load(urllib.request.urlopen(req, timeout=240))
        parts = [p for p in d["candidates"][0]["content"]["parts"] if not p.get("thought")]
        return parts[-1]["text"].strip(), 0
    body = {"model": model, "max_tokens": 2500, "temperature": random.choice([0.7, 0.9, 1.0]),
            "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + env["OPENROUTER_API_KEY"], "Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=180))
    return (d["choices"][0]["message"].get("content") or "").strip(), d.get("usage", {}).get("cost", 0)


import threading
lock = threading.Lock()
done = 0


def worker():
  global done
  while done < N:
      lang = random.choice(["es", "es", "en"])
      tpl = ES if lang == "es" else EN
      genre = random.choice(list(tpl))
      S = (lambda k: random.choice(globals()[k + ("_ES" if lang == "es" else "_EN")]))
      prompt = tpl[genre].format(n=random.choice([250, 400, 600]), t=S("T"), r=S("R"), s=S("S"), w=S("W"), e=S("E"))
      model = random.choice(MODELS)
      try:
          text, cost = ask(model, prompt)
      except Exception as e:
          print("ERR", model, str(e)[:120], flush=True); time.sleep(8); continue
      if cost:
          print("PAID?!", model, cost, flush=True); return
      if len(text.split()) < 120:
          continue
      with lock, OUT.open("a") as f:
          f.write(json.dumps({"text": text, "model": model, "genre": genre, "lang": lang, "prompt": prompt}, ensure_ascii=False) + "\n")
      done += 1
      print(done, model, lang, genre, len(text.split()), flush=True)


ts = [threading.Thread(target=worker) for _ in range(int(sys.argv[4]) if len(sys.argv) > 4 else 6)]
[t.start() for t in ts]; [t.join() for t in ts]
