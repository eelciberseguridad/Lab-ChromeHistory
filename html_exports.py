from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from pathlib import Path


def friendly_utc(value):
    if value in (None, ""):
        return ""
    text = str(value)
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%d/%m/%Y · %H:%M:%S UTC")
    except Exception:
        return text


def friendly_local(value):
    if value in (None, ""):
        return ""
    text = str(value)
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        local = dt.astimezone()
        return local.strftime("%d/%m/%Y · %H:%M:%S") + f" ({local.tzname() or 'hora local'})"
    except Exception:
        return text


LABELS = {
    "fecha_utc": "Fecha y hora UTC",
    "ultima_visita_utc": "Última visita UTC",
    "inicio_utc": "Inicio UTC",
    "fin_utc": "Fin UTC",
    "dominio": "Dominio",
    "title": "Título",
    "url": "URL",
    "visit_count": "Cantidad de visitas",
    "typed_count": "Veces escrita",
    "tipo_navegacion": "Tipo de navegación",
    "origen_visita": "Origen de visita",
    "duracion_segundos": "Duración (s)",
    "url_origen_visita": "URL de origen",
    "external_referrer_url": "Referrer externo",
    "termino": "Término de búsqueda",
    "fuente": "Fuente",
    "target_path": "Archivo de destino",
    "estado_descarga": "Estado",
    "total_bytes": "Tamaño total (bytes)",
    "mime_type": "Tipo MIME",
    "site_url": "Página / sitio",
    "tab_url": "Pestaña",
    "referrer": "Referrer",
    "url_inicial": "URL inicial",
    "url_final": "URL final",
    "eventos": "Eventos",
    "tipo": "Tipo de navegación",
    "origen": "Origen de visita",
}

DATE_FIELDS = {"fecha_utc", "ultima_visita_utc", "inicio_utc", "fin_utc"}

LAYOUTS = {
    "timeline": (
        "LINEA_DE_TIEMPO.html", "Línea de tiempo",
        "Eventos de navegación ordenados cronológicamente.",
        ["fecha_utc", "dominio", "title", "url", "tipo_navegacion", "origen_visita", "duracion_segundos", "url_origen_visita", "external_referrer_url"],
        "fecha_utc", False,
    ),
    "urls": (
        "PAGINAS_Y_URLS.html", "Páginas y URLs",
        "Direcciones registradas en la base de historial.",
        ["ultima_visita_utc", "dominio", "title", "url", "visit_count", "typed_count"],
        "ultima_visita_utc", True,
    ),
    "dominios": (
        "DOMINIOS.html", "Dominios",
        "Dominios identificados y cantidad de eventos asociados.",
        ["dominio", "eventos"], "eventos", True,
    ),
    "tipos_navegacion": (
        "TIPOS_DE_NAVEGACION.html", "Tipos de navegación",
        "Distribución de eventos según el tipo de transición registrado.",
        ["tipo", "eventos"], "eventos", True,
    ),
    "origen_visitas": (
        "ORIGEN_DE_VISITAS.html", "Origen de visitas",
        "Origen técnico asociado a los eventos cuando está disponible.",
        ["origen", "eventos"], "eventos", True,
    ),
    "busquedas": (
        "BUSQUEDAS.html", "Búsquedas",
        "Términos de búsqueda identificados y su contexto asociado.",
        ["fecha_utc", "dominio", "termino", "url", "fuente"],
        "fecha_utc", True,
    ),
    "descargas": (
        "DESCARGAS.html", "Descargas",
        "Transferencias registradas por el navegador y sus datos relacionados.",
        ["inicio_utc", "fin_utc", "dominio", "target_path", "estado_descarga", "total_bytes", "mime_type", "site_url", "tab_url", "referrer", "url_inicial", "url_final"],
        "inicio_utc", True,
    ),
}

EXPECTED_HTML = {
    "CENTRO_DE_CONSULTA.html", "RESUMEN.html", "LINEA_DE_TIEMPO.html",
    "PAGINAS_Y_URLS.html", "DOMINIOS.html", "TIPOS_DE_NAVEGACION.html",
    "ORIGEN_DE_VISITAS.html", "BUSQUEDAS.html", "DESCARGAS.html",
}


def _css():
    return """
:root{
  --bg:#0b0f14;--surface:#111820;--line:#293745;--text:#edf3f6;
  --muted:#94a5b1;--green:#7fd59a;--green2:#315844
}
*{box-sizing:border-box}
html{color-scheme:dark}
body{
  margin:0;
  background:radial-gradient(circle at 10% 0%,rgba(127,213,154,.08),transparent 28%),var(--bg);
  color:var(--text);
  font-family:Segoe UI,Arial,sans-serif
}
.wrap{max-width:1500px;margin:auto;padding:24px}
.hero{
  background:linear-gradient(135deg,#102019,#121c24);
  border:1px solid var(--green2);
  border-radius:18px;
  padding:23px 25px;
  margin-bottom:14px
}
.hero h1{margin:0;font-size:28px}
.hero p{margin:7px 0 0;color:#adbbb4}
.meta{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
.chip{
  border:1px solid var(--green2);
  background:#0d1813;
  color:#a9d9b8;
  padding:6px 9px;
  border-radius:999px;
  font-size:11px
}
.toolbar{
  position:sticky;top:0;z-index:5;
  display:flex;gap:8px;align-items:center;flex-wrap:wrap;
  padding:10px;margin-bottom:14px;
  background:rgba(11,15,20,.96);
  border:1px solid var(--line);
  border-radius:12px
}
.toolbar input{
  min-width:300px;flex:1;
  background:#0b1218;
  border:1px solid #344655;
  color:#e9f0f3;
  border-radius:8px;
  padding:10px 12px
}
.toolbar button{
  border:1px solid #344655;
  background:#121b24;
  color:#e2ebef;
  border-radius:8px;
  padding:9px 12px;
  cursor:pointer;
  font-size:12px
}
.toolbar button:hover{border-color:var(--green2);color:var(--green)}
.status{margin-left:auto;color:#a4b5bf;font-size:12px;white-space:nowrap}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:14px;overflow:hidden}
.table-wrap{overflow:auto;max-height:74vh}
table{border-collapse:separate;border-spacing:0;width:100%;font-size:12px}
th{
  position:sticky;top:0;z-index:2;
  background:#173b2d;color:#e6f3ea;
  text-align:left;padding:11px;white-space:nowrap
}
td{
  padding:9px 11px;
  border-bottom:1px solid #23303c;
  vertical-align:top;
  max-width:520px;
  overflow-wrap:anywhere
}
tr:nth-child(even) td{background:#0f161d}
tr:hover td{background:#15231c}
.empty{text-align:center;padding:35px;color:#8fa0ab}
.footer{text-align:center;color:#7f909b;padding:26px 0;font-size:11px}
.cards{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.card,.detail{
  background:linear-gradient(180deg,#102019,#0f1a16);
  border:1px solid var(--green2);
  border-radius:12px;
  padding:14px
}
.card span,.detail span{display:block;color:#9cad9f;font-size:9px;text-transform:uppercase}
.card strong{display:block;color:var(--green);font-size:22px;margin-top:5px}
.detail strong{display:block;color:#dce8e1;font-size:12px;margin-top:5px;overflow-wrap:anywhere}
.details{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-top:10px}
.period strong{color:var(--green)}
.compat{
  margin:0 0 12px;
  padding:10px 12px;
  border:1px solid #315844;
  border-radius:10px;
  background:#0d1813;
  color:#b7c8bd;
  font-size:11px
}
.compat strong{color:#7fd59a}
@media(max-width:900px){
  .cards{grid-template-columns:repeat(2,1fr)}
  .details{grid-template-columns:1fr}
  .wrap{padding:10px}
  .status{width:100%;margin-left:0}
}
@media(max-width:650px){
  .cards{grid-template-columns:1fr}
  .toolbar input{min-width:100%}
  .toolbar>*{flex:1 1 150px}
}
@media print{
  html{color-scheme:light}
  body{background:#fff;color:#111}
  .toolbar,.compat{display:none!important}
  .wrap{max-width:none;padding:0}
  .hero,.panel,.card,.detail{background:#fff;color:#111;border-color:#bbb}
  .table-wrap{max-height:none;overflow:visible}
  th{position:static;background:#eee;color:#111}
  td,th{font-size:8.5pt;border-color:#ccc}
  tr[hidden]{display:none!important}
}
"""



def _display(field, value):
    if value is None:
        return ""
    if field in DATE_FIELDS:
        return friendly_utc(value)
    return str(value)


def _table_rows_html(rows, fields):
    chunks = []
    for row in rows:
        cells = [f"<td>{escape(_display(field, row.get(field, '')))}</td>" for field in fields]
        chunks.append('<tr class="data-row">' + "".join(cells) + "</tr>")
    return "".join(chunks)


def _table_html(title, subtitle, rows, fields, metadata):
    source = Path(metadata.get("archivo", "History")).name
    when = friendly_local(
        metadata.get("fecha_analisis_local")
        or metadata.get("fecha_analisis_utc", "")
    )
    headers_html = "".join(
        f"<th>{escape(LABELS.get(field, field.replace('_', ' ').title()))}</th>"
        for field in fields
    )
    rows_html = _table_rows_html(rows, fields)
    empty_style = "display:none" if rows else "display:block"

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title>
<style>{_css()}</style>
</head>
<body>
<div class="wrap">

<section class="hero">
  <h1>{escape(title)}</h1>
  <p>{escape(subtitle)}</p>
  <div class="meta">
    <span class="chip">{len(rows)} registros</span>
    <span class="chip">Fuente: {escape(source)}</span>
    <span class="chip">Análisis: {escape(when)}</span>
  </div>
</section>

<noscript>
  <div class="compat">
    <strong>Contenido disponible:</strong>
    todos los registros están incluidos en este archivo.
  </div>
</noscript>

<div class="toolbar">
  <input id="search" type="search" autocomplete="off"
         placeholder="Buscar en este informe...">
  <button type="button" id="clear">Limpiar</button>
  <button type="button" onclick="window.print()">Imprimir / Guardar PDF</button>
  <span id="status" class="status">{len(rows)} registros</span>
</div>

<div class="panel">
  <div class="table-wrap">
    <table>
      <thead><tr>{headers_html}</tr></thead>
      <tbody id="body">{rows_html}</tbody>
    </table>
    <div id="empty" class="empty" style="{empty_style}">
      No se encontraron registros.
    </div>
  </div>
</div>

<div class="footer">
  EEL CIBERSEGURIDAD · Analizador de Historial de Navegación
</div>
</div>

<script>
(function(){{
  'use strict';

  const input = document.getElementById('search');
  const clearButton = document.getElementById('clear');
  const status = document.getElementById('status');
  const empty = document.getElementById('empty');
  const rows = Array.from(document.querySelectorAll('#body tr.data-row'));

  function normalizeText(value){{
    try {{
      return String(value || '')
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase();
    }} catch (error) {{
      return String(value || '').toLowerCase();
    }}
  }}

  const searchable = rows.map(function(row){{
    return [row, normalizeText(row.textContent)];
  }});

  function filterRows(){{
    const terms = normalizeText(input.value)
      .trim()
      .split(/\s+/)
      .filter(Boolean);

    let visible = 0;

    searchable.forEach(function(item){{
      const row = item[0];
      const haystack = item[1];
      const match = terms.length === 0
        || terms.every(function(term){{ return haystack.indexOf(term) !== -1; }});

      row.hidden = !match;
      if (match) visible += 1;
    }});

    status.textContent = visible + ' registros';
    empty.style.display = visible ? 'none' : 'block';
  }}

  input.addEventListener('input', filterRows);
  input.addEventListener('keydown', function(event){{
    if (event.key === 'Escape') {{
      input.value = '';
      filterRows();
    }}
  }});

  clearButton.addEventListener('click', function(){{
    input.value = '';
    filterRows();
    input.focus();
  }});
}})();
</script>

</body>
</html>"""



def _summary_html(data):
    m, r = data.get("metadata", {}), data.get("resumen", {})
    source = Path(m.get("archivo", "History")).name
    when = friendly_local(m.get("fecha_analisis_local") or m.get("fecha_analisis_utc", ""))
    cards = [
        ("Eventos de visita", r.get("visitas", 0)),
        ("URLs registradas", r.get("urls", 0)),
        ("Dominios distintos", r.get("dominios", 0)),
        ("Búsquedas", r.get("busquedas", 0)),
        ("Descargas", r.get("descargas", 0)),
    ]
    cards_html = "".join(
        f'<div class="card"><span>{escape(label)}</span><strong>{escape(str(value))}</strong></div>'
        for label, value in cards
    )
    return f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Resumen del análisis</title><style>{_css()}</style></head><body><div class="wrap">
<section class="hero"><h1>Resumen del análisis</h1><p>Principales resultados e información de integridad.</p><div class="meta"><span class="chip">Fuente: {escape(source)}</span><span class="chip">Análisis: {escape(when)}</span></div></section>
<div class="toolbar"><button type="button" onclick="window.print()">Imprimir / Guardar PDF</button><a href="CENTRO_DE_CONSULTA.html">Centro de consulta</a></div>
<div class="cards">{cards_html}</div><div class="details"><div class="detail period"><span>Período recuperado · Desde</span><strong>{escape(friendly_utc(m.get('primer_evento_utc', '')) or 'No disponible')}</strong></div><div class="detail period"><span>Período recuperado · Hasta</span><strong>{escape(friendly_utc(m.get('ultimo_evento_utc', '')) or 'No disponible')}</strong></div><div class="detail"><span>Archivo analizado</span><strong>{escape(source)}</strong></div><div class="detail"><span>Tamaño</span><strong>{escape(str(m.get('tamano_bytes', '')))} bytes</strong></div><div class="detail"><span>SHA-256</span><strong>{escape(m.get('sha256', ''))}</strong></div><div class="detail"><span>Fecha de análisis</span><strong>{escape(when)}</strong></div></div>
<div class="footer">EEL CIBERSEGURIDAD · Analizador de Historial de Navegación</div></div></body></html>'''


def remove_legacy_outputs(output_dir):
    output_dir = Path(output_dir)
    for pattern in ("*.xlsx", "*.csv", "*.txt"):
        for path in output_dir.glob(pattern):
            try:
                path.unlink(missing_ok=True)
            except Exception:
                pass
    for path in output_dir.glob("*.html"):
        if path.name not in EXPECTED_HTML:
            try:
                path.unlink(missing_ok=True)
            except Exception:
                pass


def write_html_outputs(data, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    remove_legacy_outputs(output_dir)
    (output_dir / "RESUMEN.html").write_text(_summary_html(data), encoding="utf-8")
    metadata = data.get("metadata", {})
    for key, (filename, title, subtitle, fields, sort_field, reverse) in LAYOUTS.items():
        rows = list(data.get(key, []) or [])
        rows.sort(
            key=lambda row: row.get(sort_field, 0)
            if isinstance(row.get(sort_field, 0), (int, float))
            else str(row.get(sort_field, "") or ""),
            reverse=reverse,
        )
        (output_dir / filename).write_text(
            _table_html(title, subtitle, rows, fields, metadata), encoding="utf-8"
        )
    return output_dir
