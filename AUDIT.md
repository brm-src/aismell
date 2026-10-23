# Auditoría de aismell: motor y experiencia de revisión

Base revisada: `ab47cd8`. Implementación y pruebas locales; sin push ni despliegue.

## Conclusión

El problema principal no era la falta de más reglas o de otro modelo. Había inferencias de autoría sin respaldo, reglas que no se ejecutaban como estaban escritas, resultados web distintos del motor y acciones que enviaban información antes de permitir elegir. La herramienta ahora prioriza observaciones editoriales explicables y la edición del original.

No se afirma que aismell sea un detector forense ni un clasificador de última generación. El índice sigue siendo heurístico. “Pocas señales” no significa texto humano; “muchas señales” no demuestra generación automática.

## Hallazgos y cambios

### Motor

- **P1 · Las fechas mencionadas se confundían con la fecha del documento.** Un año antiguo podía rebajar el índice a 0,30. `detect_era()` conserva el año máximo como dato, pero devuelve procedencia desconocida. La época declarada tampoco borra problemas editoriales.
- **P1 · Puntuación sin explicación visible.** Había textos con cero hallazgos y puntuación estadística positiva. Las estadísticas solo aportan peso cuando existe su hallazgo correspondiente. Se retiró la penalización independiente `anchor_starvation`: un regex de dígitos y pronombres no demuestra ausencia de nombres o actores concretos.
- **P1 · Falsos negativos por escapes YAML.** Corregidas 35 reglas: 21 ES y 14 EN. Incluyen 33 reglas con límites sobreescapados y dos reglas adicionales de artefactos/fechas. Se prueban frases y ramas reales, negativos y posiciones; no se reparan silenciosamente en el compilador. El inventario actual contiene 290 reglas ES y 228 EN.
- **P1 · Markdown y ubicaciones.** La cursiva ya no oculta una frase editorial. Código y ejemplos entre comillas conservan su exclusión; las observaciones estructurales mantienen los números de línea originales. Las citas excluidas no fabrican contexto académico.
- **P2 · YAML releído por cada tramo.** Caché estándar `lru_cache(maxsize=2)`, sin dependencia nueva. Una regresión pasó de 20 lecturas YAML a dos para cuatro análisis con tramos, uno por idioma. Las reglas se mantienen durante el proceso; al editarlas hay que reiniciar o vaciar la caché.
- **P1 · Copias desincronizadas.** `bash docs/sync.sh` actualiza navegador, Worker Python, URLs YAML heredadas y la copia del limpiador Unicode. Conserva archivos adicionales no canónicos, en vez de borrarlos. Igualdad de las copias comprobada byte a byte.

### Revisión web

- **P1 · Segundo clasificador inventado en JavaScript.** Eliminados la recombinación del índice, el porcentaje de oraciones calculado contando hallazgos y la supuesta “seguridad del detector”. Web y CLI comparten índice; se muestra como `17/100`, no como probabilidad.
- **P1 · Consultas externas sin consentimiento.** Bibliografía desactivada por defecto, con explicación de los campos y proveedores consultados. Se aplica también a archivos Word. Las consultas pueden cancelarse sin que reaparezcan resultados tardíos.
- **P1 · Reescritura antes de poder elegir.** El primer clic solo abre opciones. Reescritura desmarcada y envío mediante acción separada, límite visible de 3.000 caracteres. Se conserva el original. La limpieza Unicode reutiliza el código existente y ahora es local, sin llamar al servicio.
- **P1 · Semántica costosa e inconsistente.** Revisión experimental opt-in; mismo camino para pegado, texto/PDF importado y Word. Sus notas están separadas del índice y respetan el filtro de prioridad. Se retiró el piso artificial de 0,55 y la penalización por simplemente mantener un tema. El worker tiene límite de espera y la inicialización fallida puede reintentarse. La similitud es un indicio para comparar párrafos, no un detector de autoría.
- **P1 · HTML y enlaces no confiables.** El escape compartido cubre ambas comillas, también en atributos. Los enlaces procedentes de catálogos aceptan solo HTTP(S). Los errores se muestran como texto, no se interpretan como HTML.
- **P1 · DOI web roto.** Una variable `url` sombreada impedía consultar Crossref. Corregida y cubierta con regresión. Además del test aislado, una consulta pública real devolvió `Aspelmeyer (2009) Measured measurement` para `10.1038/nphys1170`.
- **P1 · Informes bibliográficos falsamente verdes.** Un informe con errores o referencias no consultables ya no afirma que todas estén verificadas. Las etiquetas hablan de coincidencias de catálogo, no de validez integral. La similitud de títulos deja de aceptar `Art` como coincidencia de `Artificial intelligence`. Reintentar actualiza filas, resumen y descarga juntos.
- **P1 · Resultados obsoletos y operaciones simultáneas.** Guardia compartida de operación, también para atajos e importación. Editar texto o cambiar opciones invalida el informe. El original no es reemplazado por una respuesta remota.
- **P2 · Hallazgos poco aplicables.** Observaciones breves visibles por defecto y enlace a la frase exacta. La conversión de offsets Python a UTF-16 conserva la selección incluso con emojis antes de la frase. Se compactó el resumen, se eliminó la confianza ficticia y se añadió contador de palabras.
- **P1 · Accesibilidad y móvil.** Etiqueta estable del editor, estado seleccionado del idioma, ayuda accesible en escritorio, estados de expansión y diálogos nativos con foco/Escape/restauración. Solo la acción principal permanece fija en móvil; controles secundarios no se comprimen en una barra de cinco botones. Movimiento reducido y objetivos táctiles comprobados. Eliminado el tooltip que tapaba otros controles.

### Servicio

- **P1 · Logs con contenido privado.** Las rutas de error ya no escriben mensajes upstream arbitrarios que puedan contener texto o respuesta del modelo.
- **P1 · Consentimiento truthy.** Solo el booleano literal `rewrite: true` autoriza inferencia en `/strip-marks`; la cadena `"false"` no la activa.
- **P1 · DOI distintos tratados como iguales.** El ranking conserva puntuación significativa y exige coincidencia exacta del DOI, sin compensarla con similitud del título.
- **P1 · Pérdida de fórmulas/código en el posprocesamiento.** Se conserva contenido técnico o con formato en vez de quitar asteriscos y backticks indiscriminadamente. Las descripciones de cambios corresponden a los cambios efectuados.

## Verificación ejecutada

```sh
/usr/bin/python -m pytest tests worker/analyzer/test -q
npm --prefix worker test
node --check docs/app.js
node --check docs/embedding-analysis.js
node --check worker/src/index.js
bash -n docs/sync.sh
git diff --check
```

- **178 pruebas Python pasan**, incluidas 13 regresiones de navegador con Playwright instalado y Pyodide real. Dos advertencias preexistentes de `ElementTree` en anotación DOCX.
- **41 pruebas del Worker pasan.** Las pruebas de modelos remotos usan dobles controlados; no son llamadas reales ni prueba de calidad de reescritura.
- Flujo real: pegar, analizar, localizar frase Unicode, editar/invalidate, limpiar caracteres localmente, importar Markdown y Word, descargar y abrir el ZIP Word comentado, cancelar bibliografía y usar diálogos con teclado.
- Capturas de escritorio, móvil y opciones; comprobaciones en anchos 390, 360 y 320 px: sin desbordamiento horizontal ni botones visibles de altura inferior a 44 px. Sin errores JavaScript de página en ese recorrido. Inspección visual final de escritorio y móvil.
- Comparación de rendimiento orientativa, **una muestra sintética de 120 oraciones en este equipo**, misma puntuación y tres hallazgos: antes 2,262 s; después 0,3018 s con caché fría y 0,0987 s caliente. No es un benchmark de exactitud ni una garantía de rendimiento general.
- Nueve pares de fuentes/copias comparados byte a byte, incluidos motor, patrones y limpieza Unicode.

El detector mecánico de UI se ejecutó una vez. Se corrigieron el borde excesivo del informe y la transición de ancho innecesaria. Sus otros avisos eran contextuales: el panel delega padding a sus hijos, la animación indica una operación en curso y las frases de privacidad explican límites concretos. No equivalen a una certificación WCAG.

## Límites que quedan explícitos

- Falta un corpus independiente y representativo ES/EN por género, con anotación editorial humana. Sin esa evaluación no hay fundamento para publicar precisión, confianza estadística ni superioridad frente a otros motores.
- La revisión semántica completa con descarga del modelo no se ejercitó en esta auditoría; se verificaron su aislamiento, opt-in, filtro y que no altere el índice. Sus umbrales son experimentales.
- La reescritura online no se invocó contra producción ni se usó una API pagada. Un prompt que pide conservar hechos no garantiza que el modelo los conserve.
- Las búsquedas de catálogos no confirman que una fuente respalde una afirmación, ni validan automáticamente edición, autor y todos los metadatos. Una ausencia de coincidencia no prueba invención.
- El primer arranque web necesita descargar Pyodide y sus recursos. “Local” describe dónde se procesa el texto, no una instalación inicialmente desconectada.
- El motor determinista todavía se ejecuta en el hilo principal. La caché reduce el trabajo repetido, pero documentos muy grandes pueden bloquear la interfaz; no se afirma que este techo esté eliminado.
- No se auditaron ajustes privados de retención, cuotas ni protección de abuso de la cuenta Cloudflare. El código de aplicación no sustituye esa configuración.
- No se modificó producción. Los cambios y la vista de prueba son locales hasta aprobación de publicación.

## Referencias usadas

- Código y pruebas del repositorio, base `ab47cd8`.
- [Ficha oficial de multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small): prefijo `query:` para tareas distintas de recuperación; no documenta un clasificador de autoría ni justifica los umbrales editoriales.
- [Guía de Turnitin sobre su informe](https://guides.turnitin.com/hc/en-us/articles/28457596598925-AI-writing-detection-in-the-classic-report-view): explica la menor fiabilidad y el riesgo de falsos positivos en rangos bajos. No se extrapola su rendimiento a aismell.
