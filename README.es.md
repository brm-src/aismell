# aismell

> Olfatea olor a IA en tu texto. Bilingüe ES/EN. CLI. Offline. Con opiniones.

🇬🇧 [Read in English](README.md)

```
texto.md  •  47 oraciones  •  smell: 31% (moderado)

Hallazgos línea por línea
  🔴 L4   No se trata solo de productividad, sino de transformación.
        estructura paralela negativa típica de IA [es.no_solo_sino]
        → di la idea positiva sin el contraste de relleno

  🔴 L12  ...vale la pena destacar que profundizamos en...
        muletilla AI clásica [es.vale_pena_destacar]
        → solo destácalo
```

## Qué hace

`aismell` lee tu texto y te marca línea por línea qué huele a modelo de lenguaje. Sin promesas falsas de "engañar a GPTZero". Tu post, email, PR o ensayo suena a *ti* o suena a IA — esta herramienta te ayuda a ver cuál de las dos.

Funciona offline, con regex y heurísticas (sin llamadas a APIs por defecto), en español e inglés.

## Por qué otro de estos

La mayoría de los "humanizadores de IA" son estafa. Cambian sinónimos al azar o agregan typos para esquivar detectores. Ese juego es deshonesto e inútil.

`aismell` es lo contrario:
- **No reescribe por ti.** Te muestra qué se lee a IA, línea por línea.
- **Es auditable.** Cada patrón vive en un YAML que puedes leer y contribuir.
- **Es offline por defecto.** Tu texto no sale de tu máquina.
- **No promete burlar detectores.** Promete que tu texto no se sienta a piloto automático.

El enfoque honesto es editorial, no adversario. Úsalo antes de publicar.

## Instalación

```bash
git clone https://github.com/brm-src/aismell.git
cd aismell
pip install -e .
```

O sin instalar:
```bash
git clone https://github.com/brm-src/aismell.git
~/aismell/bin/aismell --help
```

Necesita Python 3.9+ y PyYAML.

## Uso

```bash
# analiza un archivo (detecta idioma solo)
aismell post.md

# desde stdin
cat borrador.txt | aismell

# solo hallazgos de alta confianza
aismell --strict post.md

# un solo número 0-100 (útil para CI / pre-commit)
aismell --score-only post.md

# forzar idioma
aismell --lang es post.md

# sin colores
aismell --no-color post.md
```

Sale con código `0` si está limpio, `1` si encuentra cosas. Sirve para hooks de git.

## Qué detecta

Tres capas.

**1. Patrones de frase.** Cosas que la IA dice y los humanos casi nunca: *"vale la pena destacar"*, *"se erige como"*, *"un testimonio de"*, *"espero que esto te sirva"*. ~50 patrones por idioma.

**2. Patrones de estructura.** Pistas más allá de las palabras: paralelismos negativos (*"no se trata solo de X, sino de Y"*), copula avoidance (*"se erige como"* en vez de *"es"*), cierres genéricos (*"el futuro se ve brillante"*), aperturas serviles.

**3. Ritmo y densidad.** Varianza de largo de oración, densidad de em-dashes, ratio de bullets, frecuencia de regla de tres. Cálculo global, no por línea.

Los scores se normalizan a 0–100. Sobre 60 es IA fuerte, 30–60 es mezcla, bajo 30 está mayormente limpio.

## Qué *no* hace

- No llama a ningún LLM (en el futuro habrá flag `--rewrite` opt-in).
- No reescribe tu texto.
- No es un detector forense. Falsos positivos pasan — humanos también usan estas frases. El punto es hacerlas visibles para que tú decidas.

## Los patrones son datos

Cada regla vive en `patterns/es.yaml` o `patterns/en.yaml`. Formato:

```yaml
- id: es.vale_pena_destacar
  kind: phrase            # phrase | regex
  severity: 3             # 1 (sospecha) | 2 (probable) | 3 (casi seguro)
  pattern: vale la pena destacar
  message: muletilla AI clásica
  suggestion: solo destácalo
```

Agrega un patrón, abre un PR. No necesitas tocar código para reglas nuevas.

## Roadmap

- [ ] Más patrones (siempre)
- [ ] Flag `--rewrite` con backend LLM opcional (offline por defecto sigue siendo default)
- [ ] Output plano para `grep`
- [ ] Config para pre-commit
- [ ] Modo `--diff` con sugerencias antes/después

## Créditos

Este proyecto se apoya en los patrones documentados en [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) y [blader/humanizer](https://github.com/blader/humanizer). Ambos son MIT, y este también.

## Licencia

MIT. Ver [LICENSE](LICENSE).
