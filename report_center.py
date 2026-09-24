from __future__ import annotations

import json
import unicodedata
from html import escape
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse



def _norm(value):
    text = str(value or "").lower()
    text = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def _internal_tool_url(value):
    try:
        parsed = urlparse(str(value or ""))
        if parsed.scheme.lower() != "file":
            return False
        path = (parsed.path or "").replace("\\", "/").lower()
        return "analizador-historial-navegacion-windows" in path and "/resultados/" in path
    except Exception:
        return False


def generate_html_report(data, output_path):
    m = data["metadata"]
    r = data["resumen"]

    def e(value):
        return escape(str(value or ""))

    def host(value):
        try:
            return urlparse(value or "").netloc.lower()
        except Exception:
            return ""

    # ------------------------------------------------------------------
    # Compact query dataset.
    # Each record is an array instead of a full HTML card. This keeps the
    # report responsive even when the history contains many thousands of rows.
    # [kind, date, datetime, domain, primary, secondary, normalized_search, fields]
    # ------------------------------------------------------------------
    records = []

    clean_timeline = [x for x in data["timeline"] if not _internal_tool_url(x.get("url", ""))]
    clean_searches = [x for x in data["busquedas"] if not _internal_tool_url(x.get("url", ""))]
    clean_urls = [x for x in data["urls"] if not _internal_tool_url(x.get("url", ""))]

    # Recalculate visible totals for older analyses that may contain self-generated file URLs.
    r = dict(r)
    r["visitas"] = len(clean_timeline)
    r["busquedas"] = len(clean_searches)
    r["urls"] = len(clean_urls)

    for x in clean_timeline:
        domain = x.get("dominio", "") or ""
        primary = domain or "Sin dominio"
        secondary = x.get("title", "") or x.get("url", "") or ""
        fields = [
            x.get("fecha_utc", ""),
            x.get("title", ""),
            x.get("tipo_navegacion", ""),
            x.get("origen_visita", ""),
            x.get("duracion_segundos", ""),
            x.get("url_origen_visita", ""),
            x.get("external_referrer_url", ""),
            x.get("url", ""),
        ]
        search_text = " ".join(str(v or "") for v in x.values())
        records.append([
            "e",
            (x.get("fecha_utc", "") or "")[:10],
            x.get("fecha_utc", "") or "",
            domain,
            primary,
            secondary,
            _norm(search_text + " " + domain + " " + primary + " " + secondary),
            fields,
        ])

    for x in clean_searches:
        domain = host(x.get("url", ""))
        primary = x.get("termino", "") or "Búsqueda identificada"
        secondary = domain or x.get("url", "") or ""
        source = "Tabla de términos de búsqueda" if x.get("fuente") == "keyword_search_terms" else "Parámetro de la URL"
        fields = [
            x.get("fecha_utc", ""),
            domain,
            source,
            x.get("url", ""),
        ]
        search_text = " ".join(str(v or "") for v in x.values())
        records.append([
            "s",
            (x.get("fecha_utc", "") or "")[:10],
            x.get("fecha_utc", "") or "",
            domain,
            primary,
            secondary,
            _norm(search_text + " " + domain + " " + primary),
            fields,
        ])

    for x in data["descargas"]:
        domain = ""
        for candidate in [
            x.get("site_url", ""),
            x.get("tab_url", ""),
            x.get("url_final", ""),
            x.get("url_inicial", ""),
            x.get("referrer", ""),
        ]:
            domain = host(candidate)
            if domain:
                break

        primary = x.get("target_path", "") or x.get("current_path", "") or "Descarga"
        secondary = domain or x.get("url_final", "") or x.get("url_inicial", "") or ""
        fields = [
            x.get("inicio_utc", ""),
            x.get("fin_utc", ""),
            domain,
            x.get("estado_descarga", ""),
            x.get("total_bytes", ""),
            x.get("mime_type", ""),
            x.get("site_url", ""),
            x.get("tab_url", ""),
            x.get("referrer", ""),
            x.get("url_inicial", ""),
            x.get("url_final", ""),
        ]
        search_text = " ".join(str(v or "") for v in x.values())
        records.append([
            "d",
            (x.get("inicio_utc", "") or "")[:10],
            x.get("inicio_utc", "") or "",
            domain,
            primary,
            secondary,
            _norm(search_text + " " + domain + " " + primary),
            fields,
        ])

    # URL inventory is kept separate from Activity. A URL row represents an
    # inventory entry whose date is the last_visit_time value.
    for x in clean_urls:
        domain = x.get("dominio", "") or ""
        primary = domain or "Sin dominio"
        secondary = x.get("title", "") or x.get("url", "") or ""
        fields = [
            x.get("ultima_visita_utc", ""),
            x.get("title", ""),
            x.get("url", ""),
            x.get("visit_count", ""),
            x.get("typed_count", ""),
        ]
        search_text = " ".join(str(v or "") for v in x.values())
        records.append([
            "u",
            (x.get("ultima_visita_utc", "") or "")[:10],
            x.get("ultima_visita_utc", "") or "",
            domain,
            primary,
            secondary,
            _norm(search_text + " " + domain + " " + primary + " " + secondary),
            fields,
        ])

    records.sort(key=lambda item: (item[2], item[0]), reverse=True)
    domains = sorted({item[3] for item in records if item[3]})

    # Safe JSON embedding inside HTML.
    records_json = json.dumps(records, ensure_ascii=False, separators=(",", ":"))
    records_json = records_json.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    datalist = "".join(f'<option value="{escape(domain, quote=True)}"></option>' for domain in domains)


    from collections import Counter
    visible_domains = Counter(x.get("dominio", "") for x in clean_timeline if x.get("dominio"))
    top = {"dominio": visible_domains.most_common(1)[0][0], "eventos": visible_domains.most_common(1)[0][1]} if visible_domains else None
    visible_days = Counter((x.get("fecha_utc", "") or "")[:10] for x in clean_timeline if x.get("fecha_utc"))
    busy = {"fecha": visible_days.most_common(1)[0][0], "eventos": visible_days.most_common(1)[0][1]} if visible_days else None
    def friendly_utc(value):
        if not value:
            return "No disponible"
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return dt.strftime("%d/%m/%Y · %H:%M UTC")
        except Exception:
            return str(value)

    period_start = friendly_utc(m.get("primer_evento_utc", ""))
    period_end = friendly_utc(m.get("ultimo_evento_utc", ""))

    def friendly_analysis_time(value):
        if not value:
            return "No disponible"
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            local = dt.astimezone()
            zone = local.tzname() or "hora local"
            return local.strftime("%d/%m/%Y · %H:%M") + f" ({zone})"
        except Exception:
            return str(value)

    analysis_date = friendly_analysis_time(m.get("fecha_analisis_local") or m.get("fecha_analisis_utc", ""))
    analysis_file = Path(m.get("archivo", "History")).name
    top_text = f'{top["dominio"]} — {top["eventos"]} eventos' if top else "No disponible"
    busy_text = f'{busy["fecha"]} — {busy["eventos"]} eventos' if busy else "No disponible"

    css = r"""
:root{--bg:#0b0f14;--surface:#121821;--text:#eef3f7;--muted:#9aa7b5;--cyan:#67c7d8;--cyan2:#2e7f8f;--gold:#c7a66a;--line:#283443}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;color:var(--text);font-family:Segoe UI,Inter,Arial,sans-serif;background:radial-gradient(circle at 10% 0%,rgba(103,199,216,.07),transparent 32%),var(--bg)}
.wrap{max-width:1450px;margin:auto;padding:26px}.hero{background:linear-gradient(135deg,#121a24,#182536);border:1px solid #2b3949;border-radius:20px;padding:28px}.hero-top{display:flex;justify-content:space-between;gap:20px}.hero h1{margin:0;font-size:31px}.sub{color:#aab7c4;margin-top:7px}.brand{text-align:right;color:#e6d8bd;font-weight:700}.email{font-size:13px;color:#9ed8e2;margin-top:6px}
.toolbar{position:sticky;top:0;z-index:20;margin:16px 0;padding:10px;display:flex;gap:8px;flex-wrap:wrap;background:rgba(11,15,20,.95);border:1px solid var(--line);border-radius:14px}button{border:1px solid #334151;background:#141b24;color:#dce6ed;border-radius:9px;padding:9px 12px;cursor:pointer}button:hover{border-color:var(--cyan2);color:var(--cyan)}button:disabled{opacity:.45;cursor:not-allowed}
details.report-section{background:var(--surface);border:1px solid var(--line);border-radius:15px;margin:14px 0;overflow:hidden}details.report-section>summary{cursor:pointer;padding:18px 20px;font-weight:700;font-size:17px;list-style:none;background:#151d27}details.report-section>summary:before{content:"▸";display:inline-block;width:22px;color:var(--cyan)}details.report-section[open]>summary:before{content:"▾"}.content{padding:20px}.desc{color:#b8c5cf;line-height:1.6;margin:0 0 18px}
.metrics{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:14px}.metric{background:linear-gradient(180deg,#102019,#0f1a16);border:1px solid #315844;border-radius:12px;padding:15px}.metric b{display:block;color:#7fd59a;font-size:24px}.metric span{color:#a6b7ad;font-size:10px;font-weight:700}.summary-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.summary-box{background:linear-gradient(180deg,#102019,#0f1a16);border:1px solid #315844;border-radius:11px;padding:14px}.summary-box span{display:block;color:#9cad9f;font-size:10px}.summary-box strong{display:block;color:#7fd59a;font-size:13px;margin-top:6px;overflow-wrap:anywhere}
.period-box{border-color:#315844;background:linear-gradient(180deg,#102019,#0f1a16)}.period-range{display:grid;gap:8px;margin-top:9px}.period-line{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}.period-line b{min-width:42px;color:#91a5af;font-size:10px;text-transform:uppercase}.period-line strong{margin:0;color:#7fd59a;font-size:13px}
.evidence-summary{margin-top:14px;border:1px solid #315844;border-radius:12px;overflow:hidden;background:linear-gradient(180deg,#102019,#0f1a16)}.evidence-title{padding:12px 14px;border-bottom:1px solid #315844;color:#a6b7ad;font-size:10px;font-weight:700;letter-spacing:.35px}.evidence-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr))}.evidence-item{padding:12px 14px;border-top:1px solid rgba(49,88,68,.55);border-right:1px solid rgba(49,88,68,.55)}.evidence-item:nth-child(-n+2){border-top:0}.evidence-item:nth-child(2n){border-right:0}.evidence-item span{display:block;color:#91a59a;font-size:9px;text-transform:uppercase}.evidence-item strong{display:block;margin-top:4px;color:#d7e6dc;font-size:11px;font-weight:500;overflow-wrap:anywhere}
.analysis-info{display:grid;border:1px solid #263545;border-radius:11px;overflow:hidden;background:#101820}.analysis-line{padding:14px 16px;border-top:1px solid #263545;color:#b8c5cf;font-size:13px;line-height:1.55}.analysis-line:first-child{border-top:0}.analysis-line strong{color:#dce8ee;font-weight:600}
.query-panel{background:linear-gradient(180deg,#101820,#0f161e);border:1px solid #2a3948;border-radius:14px;padding:16px;margin-bottom:14px}.query-grid{display:grid;grid-template-columns:minmax(190px,240px) minmax(165px,210px) minmax(220px,1fr) minmax(240px,1fr);gap:10px}.query-grid label{display:block;color:#8fa0ae;font-size:10px;font-weight:700;margin-bottom:5px;text-transform:uppercase;letter-spacing:.25px}.query-grid select,.query-grid input{width:100%;background:#0b1117;border:1px solid #334151;color:var(--text);border-radius:9px;padding:10px 12px}.field-help{display:block;margin-top:5px;color:#8192a0;font-size:10px;line-height:1.35}.type-note{margin:10px 0 0;color:#9dafba;font-size:11px}.query-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.primary{border-color:#39707c;background:#10242c;color:#cce9ee}.query-status{margin-top:12px;padding:10px 12px;border-radius:9px;border:1px solid #283746;background:#0d141b;color:#a9bac6;font-size:12px;white-space:pre-line}.query-status.busy{color:#d5c596;border-color:#5b5034}
.results{display:none}.results.active{display:block}.result-card{background:#0f151d;border:1px solid #283746;border-radius:11px;margin:9px 0;overflow:hidden}.result-head{display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:12px;align-items:center;padding:12px 14px;background:#111922}.kind-badge{color:#a9d2da;border:1px solid #31505b;background:#102129;padding:4px 7px;border-radius:999px;font-size:10px;font-weight:700}.result-title strong{display:block;color:#dce8ee;font-size:13px;overflow-wrap:anywhere}.result-title span{display:block;color:#8fa1af;font-size:11px;margin-top:3px;overflow-wrap:anywhere}.result-head time{color:#91a3af;font-size:10px}.result-fields{display:grid;grid-template-columns:repeat(2,minmax(0,1fr))}.field{padding:9px 12px;border-top:1px solid #263442;border-right:1px solid #263442}.field span{display:block;color:#8293a3;font-size:9px;text-transform:uppercase}.field strong{display:block;color:#d7e2e8;font-size:11px;font-weight:500;margin-top:3px;overflow-wrap:anywhere}.more-wrap{text-align:center;margin:14px 0 4px}.more-wrap button{min-width:180px}.result-note{font-size:11px;color:#8fa1af;text-align:center;margin-top:8px}
.meta{display:grid;grid-template-columns:210px 1fr;gap:9px 14px;font-size:13px}.meta div:nth-child(odd){color:var(--muted)}.tech{white-space:pre-wrap;font-family:Consolas,monospace;font-size:12px;background:#0c1117;border:1px solid var(--line);padding:14px;border-radius:10px;color:#b7c3cf}.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:10px}table{border-collapse:collapse;width:100%;font-size:12px}th{background:#1a2430;color:#b9dce3;text-align:left;padding:11px}td{padding:10px;border-top:1px solid #222d39;word-break:break-word}.limits-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.limit-card{background:#101820;border:1px solid #263545;border-radius:11px;padding:14px}.limit-card strong{display:block;color:#c8dce3;margin-bottom:6px;font-size:13px}.limit-card p{margin:0;color:#aebbc5;font-size:12px;line-height:1.58}.note{border-left:4px solid var(--gold);background:#1a1812;padding:13px;border-radius:8px;color:#d8c8a6}.footer{text-align:center;color:var(--muted);font-size:12px;padding:32px 0}
@media(max-width:1050px){.hero-top{display:block}.brand{text-align:left;margin-top:16px}.metrics{grid-template-columns:repeat(3,1fr)}.summary-grid{grid-template-columns:1fr}.evidence-grid{grid-template-columns:1fr}.evidence-item{border-right:0}.evidence-item:nth-child(2){border-top:1px solid rgba(49,88,68,.55)}.query-grid{grid-template-columns:1fr 1fr}.result-fields{grid-template-columns:1fr}.meta{grid-template-columns:1fr}.limits-grid{grid-template-columns:1fr}}
@media(max-width:650px){.wrap{padding:10px}.metrics{grid-template-columns:repeat(2,1fr)}.query-grid{grid-template-columns:1fr}.content{padding:14px}.result-head{grid-template-columns:1fr}.result-head time{white-space:normal}.query-actions button{flex:1 1 140px}}
@page{size:A4;margin:14mm}@media print{body{background:#fff;color:#111}.toolbar,.query-panel,.more-wrap{display:none!important}details.report-section{border:0}.result-card{break-inside:avoid;background:#fff;color:#111}}
"""

    js = r"""
const TYPE_LABEL={e:'Navegación',s:'Búsqueda',d:'Descarga',u:'URL'};
const FIELD_LABELS={
  e:['Fecha UTC','Título','Tipo de navegación','Origen técnico','Duración (s)','Referrer interno','Referrer externo','URL'],
  s:['Fecha UTC','Dominio','Fuente','URL asociada'],
  d:['Inicio UTC','Fin UTC','Dominio relacionado','Estado','Tamaño (bytes)','Tipo MIME','Página / sitio','Pestaña','Referrer','URL inicial','URL final'],
  u:['Última visita UTC','Título','URL','Visit count','Typed count']
};
const BATCH_SIZE=75;
const CHUNK_SIZE=5000;
let RECORDS=null;
let currentMatches=[];
let renderLimit=BATCH_SIZE;
let queryToken=0;

function getRecords(){
  if(RECORDS!==null)return RECORDS;
  const raw=document.getElementById('query_data')?.textContent || '[]';
  RECORDS=JSON.parse(raw);
  return RECORDS;
}
function normalizeText(value){return (value||'').toString().normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim()}
function normalizeDomain(value){
  let v=normalizeText(value).replace(/^https?:\/\//,'').split('/')[0];
  return v.replace(/^www\./,'');
}
function openSection(id){const el=document.getElementById(id);if(el){el.open=true;setTimeout(()=>el.scrollIntoView({behavior:'smooth',block:'start'}),30)}}
function expandAllSections(){document.querySelectorAll('details.report-section').forEach(d=>d.open=true)}
function collapseAllSections(){document.querySelectorAll('details.report-section').forEach(d=>d.open=false);window.scrollTo({top:0,behavior:'smooth'})}
function filters(){return{type:document.getElementById('q_type')?.value||'activity',date:document.getElementById('q_date')?.value||'',domain:normalizeDomain(document.getElementById('q_domain')?.value||''),text:normalizeText(document.getElementById('q_text')?.value||'')}}
function matchRecord(r,f){
  const kind=r[0],date=r[1]||'',domain=normalizeDomain(r[3]||''),search=r[6]||'';
  const typeOk=f.type==='activity'?['e','s','d'].includes(kind):kind===f.type;
  const terms=f.text?f.text.split(/\s+/).filter(Boolean):[];
  const textOk=!terms.length||terms.every(term=>search.includes(term));
  return typeOk && (!f.date||date===f.date) && (!f.domain||domain.includes(f.domain)) && textOk;
}
function criteriaText(f){const typeNames={activity:'Actividad',e:'Navegación',s:'Búsquedas',d:'Descargas',u:'URLs registradas'};const parts=['Información: '+(typeNames[f.type]||'Actividad')];if(f.date)parts.push('Fecha UTC: '+f.date);if(f.domain)parts.push('Dominio: '+f.domain);if(f.text)parts.push('Texto: '+f.text);return parts.join(' · ')}
function typeBreakdown(rows){
  const counts={e:0,s:0,d:0,u:0};rows.forEach(r=>{if(counts[r[0]]!==undefined)counts[r[0]]++});
  return [['e','Navegación'],['s','Búsquedas'],['d','Descargas'],['u','URLs']].filter(([k])=>counts[k]>0).map(([k,l])=>l+': '+counts[k]).join(' · ');
}
function setActionState(enabled){['export_btn','print_btn'].forEach(id=>{const b=document.getElementById(id);if(b)b.disabled=!enabled})}
function escapeHtml(v){return (v??'').toString().replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;')}
function renderCard(r){
  const labels=FIELD_LABELS[r[0]]||[],values=r[7]||[];
  const fields=labels.map((label,i)=>{const value=values[i];if(value===null||value===undefined||value==='')return '';return `<div class="field"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`}).join('');
  return `<article class="result-card"><div class="result-head"><span class="kind-badge">${escapeHtml(TYPE_LABEL[r[0]]||'Registro')}</span><div class="result-title"><strong>${escapeHtml(r[4])}</strong><span>${escapeHtml(r[5])}</span></div><time>${escapeHtml(r[2])}</time></div><div class="result-fields">${fields}</div></article>`;
}
function renderResults(){
  const root=document.getElementById('query_results');if(!root)return;
  const visible=currentMatches.slice(0,renderLimit);
  root.innerHTML=visible.map(renderCard).join('');
  root.classList.add('active');
  const more=document.getElementById('more_results');
  if(more){more.hidden=renderLimit>=currentMatches.length;more.textContent='Mostrar '+Math.min(BATCH_SIZE,Math.max(0,currentMatches.length-renderLimit))+' más'}
  const note=document.getElementById('render_note');
  if(note){note.textContent=currentMatches.length>visible.length?`Mostrando ${visible.length} de ${currentMatches.length} resultados. La exportación incluye la consulta completa.`:''}
}
function showMore(){renderLimit+=BATCH_SIZE;renderResults()}
function finishQuery(f,token){
  if(token!==queryToken)return;
  renderLimit=BATCH_SIZE;
  renderResults();
  const status=document.getElementById('query_status');
  status?.classList.remove('busy');
  const n=currentMatches.length;
  const count=n===0?'No se encontraron resultados':n===1?'1 resultado encontrado':n+' resultados encontrados';
  const breakdown=n?typeBreakdown(currentMatches):'';
  if(status)status.textContent=count+'\n'+criteriaText(f)+(breakdown?'\n'+breakdown:'');
  setActionState(n>0);
  const consult=document.getElementById('consult_btn');if(consult)consult.disabled=false;
}
function runQuery(){
  const f=filters();
  const status=document.getElementById('query_status');
  const root=document.getElementById('query_results');
  const consult=document.getElementById('consult_btn');
  const token=++queryToken;
  currentMatches=[];renderLimit=BATCH_SIZE;setActionState(false);
  if(root){root.classList.remove('active');root.innerHTML=''}
  if(status){status.textContent='Buscando…';status.classList.add('busy')}
  if(consult)consult.disabled=true;
  const rows=getRecords();
  let index=0;
  function step(){
    if(token!==queryToken)return;
    const end=Math.min(index+CHUNK_SIZE,rows.length);
    for(;index<end;index++){const r=rows[index];if(matchRecord(r,f))currentMatches.push(r)}
    if(index<rows.length){setTimeout(step,0)}else{finishQuery(f,token)}
  }
  setTimeout(step,0);
}
function clearQuery(){
  queryToken++;
  document.getElementById('q_type').value='activity';
  document.getElementById('q_date').value='';
  document.getElementById('q_domain').value='';
  document.getElementById('q_text').value='';
  currentMatches=[];renderLimit=BATCH_SIZE;
  const root=document.getElementById('query_results');if(root){root.innerHTML='';root.classList.remove('active')}
  const more=document.getElementById('more_results');if(more)more.hidden=true;
  const note=document.getElementById('render_note');if(note)note.textContent='';
  const status=document.getElementById('query_status');if(status){status.textContent='Elegí los criterios y presioná Enter o Consultar.';status.classList.remove('busy')}
  const consult=document.getElementById('consult_btn');if(consult)consult.disabled=false;
  setActionState(false);
  updateTypeNote();
  document.getElementById('q_domain')?.focus();
}
function rowObject(r){
  const obj={'Tipo':TYPE_LABEL[r[0]]||'Registro','Registro':r[4]||'','Referencia':r[5]||'','Fecha':r[2]||''};
  const labels=FIELD_LABELS[r[0]]||[],values=r[7]||[];
  labels.forEach((label,i)=>{const value=values[i];if(value!==null&&value!==undefined&&value!=='')obj[label]=value});
  return obj;
}
function exportHeaders(type){
  if(type==='e')return ['Fecha UTC','Dominio','Título','URL','Tipo de navegación','Origen técnico','Duración (s)','Referrer interno','Referrer externo'];
  if(type==='s')return ['Fecha UTC','Dominio','Término de búsqueda','URL asociada','Fuente'];
  if(type==='d')return ['Inicio UTC','Fin UTC','Dominio','Archivo de destino','Estado','Tamaño (bytes)','Tipo MIME','Página / sitio','Pestaña','Referrer','URL inicial','URL final'];
  if(type==='u')return ['Última visita UTC','Dominio','Título','URL','Visit count','Typed count'];
  return ['Tipo','Fecha UTC','Dominio','Descripción','URL principal','Tipo de navegación','Origen técnico','Duración (s)','Fuente de búsqueda','Fin UTC','Estado de descarga','Tamaño (bytes)','Tipo MIME','Página / sitio','Pestaña','Referrer interno','Referrer externo','Referrer de descarga','URL inicial','URL final'];
}
function exportRow(r,type){
  const kind=r[0],v=r[7]||[];
  if(type==='e')return [v[0]||r[2]||'',r[3]||'',v[1]||'',v[7]||'',v[2]||'',v[3]||'',v[4]??'',v[5]||'',v[6]||''];
  if(type==='s')return [v[0]||r[2]||'',r[3]||'',r[4]||'',v[3]||'',v[2]||''];
  if(type==='d')return [v[0]||r[2]||'',v[1]||'',r[3]||'',r[4]||'',v[3]||'',v[4]??'',v[5]||'',v[6]||'',v[7]||'',v[8]||'',v[9]||'',v[10]||''];
  if(type==='u')return [v[0]||r[2]||'',r[3]||'',v[1]||'',v[2]||'',v[3]??'',v[4]??''];

  let description='',url='',navType='',origin='',duration='',searchSource='',endUtc='',downloadState='',bytes='',mime='',site='',tab='',refInternal='',refExternal='',refDownload='',urlInitial='',urlFinal='';
  if(kind==='e'){
    description=v[1]||r[5]||'';url=v[7]||'';navType=v[2]||'';origin=v[3]||'';duration=v[4]??'';refInternal=v[5]||'';refExternal=v[6]||'';
  }else if(kind==='s'){
    description=r[4]||'';url=v[3]||'';searchSource=v[2]||'';
  }else if(kind==='d'){
    description=r[4]||'';url=v[10]||v[9]||v[6]||'';endUtc=v[1]||'';downloadState=v[3]||'';bytes=v[4]??'';mime=v[5]||'';site=v[6]||'';tab=v[7]||'';refDownload=v[8]||'';urlInitial=v[9]||'';urlFinal=v[10]||'';
  }
  return [TYPE_LABEL[kind]||'Registro',r[2]||'',r[3]||'',description,url,navType,origin,duration,searchSource,endUtc,downloadState,bytes,mime,site,tab,refInternal,refExternal,refDownload,urlInitial,urlFinal];
}
function organizedExport(rows,type){
  const ordered=[...rows].sort((a,b)=>(a[2]||'').localeCompare(b[2]||'') || (a[0]||'').localeCompare(b[0]||''));
  return {headers:exportHeaders(type),rows:ordered.map(r=>exportRow(r,type))};
}
function csvOrganized(headers,rows){
  const q=v=>'"'+(v??'').toString().replaceAll('"','""')+'"';
  return ['sep=;',headers.map(q).join(';'),...rows.map(row=>row.map(q).join(';'))].join('\r\n');
}
function exportCurrentCSV(){
  if(!currentMatches.length){alert('No hay resultados para exportar.');return}
  const f=filters();
  const exportType=f.type==='activity'?'activity':f.type;
  const organized=organizedExport(currentMatches,exportType);
  const parts=['historial'];
  const typeName={activity:'actividad',e:'navegacion',s:'busquedas',d:'descargas',u:'urls'}[exportType]||'consulta';
  parts.push(typeName);
  if(f.date)parts.push(f.date);
  if(f.domain)parts.push(f.domain.replace(/[^a-z0-9.-]+/g,'_'));
  if(f.text)parts.push('filtrada');
  const blob=new Blob(['\ufeff'+csvOrganized(organized.headers,organized.rows)],{type:'text/csv;charset=utf-8;'}),url=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=url;a.download=parts.filter(Boolean).join('_')+'.csv';document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(url)
}
function printCurrent(){
  if(!currentMatches.length){alert('No hay resultados para imprimir.');return}
  if(currentMatches.length>1500&&!confirm('La consulta contiene '+currentMatches.length+' resultados. La impresión puede ser extensa. ¿Continuar?'))return;
  const f=filters(),criteria=criteriaText(f),rows=currentMatches.map(rowObject);
  const body=rows.map(r=>'<article>'+Object.entries(r).filter(([k,v])=>v!==''&&v!==null&&v!==undefined).map(([k,v])=>`<div><small>${escapeHtml(k)}</small><strong>${escapeHtml(v)}</strong></div>`).join('')+'</article>').join('');
  const w=window.open('','_blank');if(!w)return;
  w.document.write(`<!doctype html><html><head><meta charset="utf-8"><title>Consulta de historial</title><style>body{font-family:Segoe UI,Arial;margin:28px;color:#111}h1{font-size:22px;margin:0 0 5px}.criteria{font-size:12px;color:#555;margin:0 0 18px}article{border:1px solid #bbb;border-radius:8px;padding:12px;margin:10px 0;page-break-inside:avoid}small{display:block;color:#666;text-transform:uppercase}strong{font-size:12px;font-weight:500;word-break:break-word}article div{margin:0 0 8px}</style></head><body><h1>Consulta de historial</h1><div class="criteria">${escapeHtml(criteria)} · ${currentMatches.length} resultado${currentMatches.length===1?'':'s'}</div>${body}</body></html>`);w.document.close();w.focus();setTimeout(()=>w.print(),150)
}
function updateTypeNote(){
  const value=document.getElementById('q_type')?.value||'activity';
  const notes={activity:'Actividad reúne navegación, búsquedas identificadas y descargas.',e:'Eventos de visita registrados por el navegador.',s:'Términos identificados como búsquedas.',d:'Transferencias registradas por el navegador.',u:'Inventario de URLs. La fecha corresponde a la última visita registrada.'};
  const el=document.getElementById('type_note');if(el)el.textContent=notes[value]||'';
}
function initQueryCenter(){
  const form=document.getElementById('query_form');
  if(form)form.addEventListener('submit',ev=>{ev.preventDefault();runQuery()});
  ['q_type','q_date','q_domain','q_text'].forEach(id=>{const el=document.getElementById(id);if(!el)return;el.addEventListener('keydown',ev=>{if(ev.key==='Enter'){ev.preventDefault();runQuery()}})});
  document.getElementById('q_type')?.addEventListener('change',updateTypeNote);
  updateTypeNote();setActionState(false);
  const preload=()=>{try{getRecords()}catch(err){console.error(err)}};
  if('requestIdleCallback' in window){requestIdleCallback(preload,{timeout:1500})}else{setTimeout(preload,500)};
}
document.addEventListener('DOMContentLoaded',initQueryCenter);
"""

    html = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Informe de Historial de Navegación</title><style>{css}</style></head><body><div class="wrap">
<section class="hero"><div class="hero-top"><div><h1>Informe de Historial de Navegación</h1><div class="sub">Análisis técnico de los registros disponibles en la base de historial examinada</div></div><div class="brand">EEL CIBERSEGURIDAD<div class="email">eelciberseguridad@gmail.com</div></div></div></section>
<div class="toolbar"><button onclick="openSection('resumen')">Resumen</button><button onclick="openSection('consulta')">Consulta</button><button onclick="openSection('informacion')">Información</button><button onclick="expandAllSections()">Expandir todo</button><button onclick="collapseAllSections()">Contraer todo</button></div>
<details class="report-section" id="resumen" open><summary>01 · Resumen del análisis</summary><div class="content"><p class="desc">Principales resultados del historial analizado.</p><div class="metrics"><div class="metric"><b>{r['visitas']}</b><span>EVENTOS DE VISITA</span></div><div class="metric"><b>{r['urls']}</b><span>URLS REGISTRADAS</span></div><div class="metric"><b>{r['dominios']}</b><span>DOMINIOS DISTINTOS</span></div><div class="metric"><b>{r['busquedas']}</b><span>BÚSQUEDAS IDENTIFICADAS</span></div><div class="metric"><b>{r['descargas']}</b><span>DESCARGAS REGISTRADAS</span></div></div><div class="summary-grid"><div class="summary-box period-box"><span>PERÍODO RECUPERADO</span><div class="period-range"><div class="period-line"><b>Desde</b><strong>{e(period_start)}</strong></div><div class="period-line"><b>Hasta</b><strong>{e(period_end)}</strong></div></div></div><div class="summary-box"><span>DOMINIO CON MÁS EVENTOS</span><strong>{e(top_text)}</strong></div><div class="summary-box"><span>FECHA CON MÁS ACTIVIDAD</span><strong>{e(busy_text)}</strong></div></div><div class="evidence-summary"><div class="evidence-title">EVIDENCIA E INTEGRIDAD</div><div class="evidence-grid"><div class="evidence-item"><span>Archivo analizado</span><strong>{e(analysis_file)}</strong></div><div class="evidence-item"><span>SHA-256</span><strong>{e(m['sha256'])}</strong></div><div class="evidence-item"><span>Tamaño</span><strong>{m['tamano_bytes']} bytes</strong></div><div class="evidence-item"><span>Fecha de análisis</span><strong>{e(analysis_date)}</strong></div></div></div></div></details>
<details class="report-section" id="consulta" open><summary>02 · Centro de consulta</summary><div class="content"><p class="desc">Consulta los registros disponibles por tipo de información, fecha, dominio o contenido.</p><div class="query-panel"><form id="query_form"><div class="query-grid"><div><label for="q_type">Información</label><select id="q_type"><option value="activity">Actividad</option><option value="e">Navegación</option><option value="s">Búsquedas</option><option value="d">Descargas</option><option value="u">URLs registradas</option></select><span id="type_note" class="field-help"></span></div><div><label for="q_date">Fecha UTC</label><input id="q_date" type="date"><span class="field-help">Vacío: todas las fechas.</span></div><div><label for="q_domain">Dominio</label><input id="q_domain" type="text" list="domain_list" placeholder="Ej.: google.com" autocomplete="off"><datalist id="domain_list">{datalist}</datalist><span class="field-help">Acepta dominio completo o parcial.</span></div><div><label for="q_text">Texto</label><input id="q_text" type="text" placeholder="URL, título, búsqueda, archivo..." autocomplete="off"><span class="field-help">Coincidencias sin distinguir mayúsculas ni acentos.</span></div></div><div class="query-actions"><button id="consult_btn" class="primary" type="submit">Consultar</button><button type="button" onclick="clearQuery()">Limpiar</button><button id="export_btn" type="button" onclick="exportCurrentCSV()" disabled>Exportar CSV</button><button id="print_btn" type="button" onclick="printCurrent()" disabled>Imprimir / Guardar PDF</button></div></form><div id="query_status" class="query-status" role="status" aria-live="polite">Elegí los criterios y presioná Enter o Consultar.</div></div><div id="query_results" class="results"></div><div class="more-wrap"><button id="more_results" type="button" onclick="showMore()" hidden>Mostrar más</button></div><div id="render_note" class="result-note"></div></div></details>
<details class="report-section" id="informacion"><summary>03 · Información del análisis</summary><div class="content"><div class="analysis-info"><div class="analysis-line"><strong>Registros analizados.</strong> Los resultados corresponden a la información presente en la base de historial examinada.</div><div class="analysis-line"><strong>Integridad.</strong> La huella SHA-256 permite comprobar si el archivo analizado permanece sin modificaciones.</div><div class="analysis-line"><strong>Procesamiento local.</strong> El historial y los resultados se procesan en el equipo donde se ejecuta la herramienta.</div></div></div></details>
<div class="footer"><strong>EEL CIBERSEGURIDAD</strong><br>eelciberseguridad@gmail.com<br>Analizador de Historial de Navegación</div></div><script id="query_data" type="application/json">{records_json}</script><script>{js}</script></body></html>"""

    output_path = Path(output_path)
    output_path.write_text(html, encoding="utf-8")
    return output_path
