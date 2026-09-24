# Datos analizados

Esta referencia explica los principales datos que puede interpretar la herramienta.

## `urls`

Representa registros de URL almacenados por el navegador.

Campos útiles:

- `url`
- `title`
- `visit_count`
- `typed_count`
- `last_visit_time`
- `hidden`

### `visit_count`

Contador asociado a la URL.

No debe interpretarse automáticamente como el número exacto de acciones realizadas por una persona.

### `typed_count`

Contador técnico relacionado con ingreso explícito/interacción desde la interfaz del navegador.

Debe correlacionarse con otros campos.

---

## `visits`

Representa eventos de visita.

Puede aportar:

- fecha;
- URL relacionada;
- visita anterior;
- transición;
- duración;
- referrers;
- metadatos adicionales.

Cada fila puede contribuir a la reconstrucción de la línea de tiempo.

---

## `transition`

Describe el tipo técnico de transición.

Ejemplos interpretados por la herramienta:

- `link`
- `typed`
- `reload`
- `form_submit`
- `generated`
- `auto_bookmark`
- `auto_toplevel`
- `manual_subframe`

No expresa intención humana.

---

## `visit_source`

Cuando existe, puede indicar la fuente técnica del registro.

Ejemplos:

- navegación;
- sincronización;
- extensión;
- importación.

No debe confundirse con el referrer.

---

## Referrer

El programa intenta correlacionar:

- visita anterior interna;
- referrer externo.

Puede aportar contexto sobre relaciones entre eventos.

---

## `visit_duration`

La herramienta convierte el valor almacenado a segundos.

No debe asumirse que representa tiempo efectivo de lectura o atención.

---

## `keyword_search_terms`

Cuando existe, puede aportar términos de búsqueda asociados a una URL.

Además, la herramienta puede reconocer parámetros de búsqueda en URLs de motores compatibles.

---

## `downloads`

Puede contener:

- inicio;
- finalización;
- ruta;
- tamaño;
- estado;
- MIME;
- referrer;
- pestaña;
- sitio.

---

## `downloads_url_chains`

Puede conservar las URLs asociadas a una descarga y sus redirecciones.

---

## Timestamps

Los timestamps de Chromium pueden estar expresados como microsegundos desde:

```text
1601-01-01 00:00:00 UTC
```

La herramienta los convierte a UTC legible.

---

## Interpretación

Una investigación técnica debe diferenciar:

```text
dato encontrado
≠
atribución personal
≠
intención
```

Los registros deben correlacionarse con otras fuentes antes de formular conclusiones.
