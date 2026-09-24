# Analizador de Historial de Navegación

**Versión estable: 1.0.0**

Herramienta para **Windows 10 y Windows 11** que preserva y analiza el archivo `History` de perfiles de Google Chrome, calcula SHA-256, reconstruye actividad de navegación y genera resultados HTML consultables.

> Uso previsto: capacitación, análisis técnico e investigación digital sobre sistemas propios o expresamente autorizados. No se presenta como una suite pericial certificada ni sustituye procedimientos formales de adquisición, cadena de custodia o validación metodológica.

## Descarga

ZIP directo:

```text
https://github.com/eelciberseguridad/Lab-ChromeHistory/archive/refs/heads/main.zip
```

Clonar:

```bash
https://github.com/eelciberseguridad/Lab-ChromeHistory.git
```

## Requisitos

- Windows 10 u 11.
- Python 3.10 o superior.
- No requiere dependencias externas.

## Inicio

Extraiga el proyecto y ejecute:

```text
INICIAR.bat
```

El iniciador comprueba Python 3 y ejecuta `analizador_navegacion.py`. Si Python no está instalado, puede abrir la página oficial de descarga.

## Flujo de trabajo

```text
DETECTAR PERFIL
      ↓
ELEGIR PERFIL
      ↓
COMPROBAR QUE CHROME ESTÉ CERRADO
      ↓
COPIAR HISTORY / WAL / SHM
      ↓
VERIFICAR SHA-256
      ↓
ANALIZAR SQLITE EN MODO LECTURA
      ↓
GENERAR RESULTADOS HTML
```

La pantalla principal contiene solamente:

```text
[1] DETECTAR PERFILES COMPATIBLES
[2] CONSULTAR ANÁLISIS GENERADOS
[0] SALIR
```

Al finalizar un análisis:

```text
[1] Consultar resultados de este análisis
[2] Abrir carpeta de este análisis
[3] Volver a la pantalla principal
```

## Adquisición e integridad

La versión 1 detecta perfiles en:

```text
%LOCALAPPDATA%\Google\Chrome\User Data
```

Para el perfil seleccionado intenta preservar:

```text
History
History-wal
History-shm
```

Para cada archivo disponible calcula SHA-256 del origen antes de copiar, de la copia y del origen después de copiar. Si los valores no permanecen consistentes, la herramienta advierte que la adquisición debe repetirse.

La evidencia se almacena en `evidencia/`. El análisis se realiza sobre la copia de `History`, abierta en modo lectura.

## Información analizada

Según las tablas y columnas disponibles, la herramienta puede recuperar:

- URLs y títulos;
- eventos individuales de visita;
- dominio;
- `visit_count` y `typed_count`;
- transición o tipo de navegación;
- origen técnico de visita;
- duración registrada;
- referrer interno y externo;
- términos de búsqueda;
- descargas y sus URLs relacionadas.

Los timestamps de Chromium se convierten a UTC legible. La fecha de ejecución del análisis se muestra en la hora local del equipo.

## Informes generados

Cada análisis crea una carpeta propia dentro de `resultados/` y genera **nueve resultados HTML con numeración fija**:

```text
[1] CENTRO_DE_CONSULTA.html
[2] RESUMEN.html
[3] LINEA_DE_TIEMPO.html
[4] PAGINAS_Y_URLS.html
[5] DOMINIOS.html
[6] TIPOS_DE_NAVEGACION.html
[7] ORIGEN_DE_VISITAS.html
[8] BUSQUEDAS.html
[9] DESCARGAS.html
```

El número **9 siempre corresponde a Descargas**. Los resultados se generan aunque una categoría no tenga registros.

La Versión 1 genera los resultados persistentes en HTML. Al actualizar un análisis anterior, los formatos de salida obsoletos se eliminan de la carpeta de resultados.

## Centro de consulta

`CENTRO_DE_CONSULTA.html` reúne tres bloques.

### 1. Resumen

Muestra:

- eventos de visita;
- URLs registradas;
- dominios distintos;
- búsquedas identificadas;
- descargas registradas;
- período recuperado, desde/hasta;
- dominio con mayor cantidad de eventos;
- fecha con mayor actividad;
- archivo analizado;
- SHA-256;
- tamaño;
- fecha local del análisis.

### 2. Centro de consulta

Permite combinar:

- **Información:** Actividad, Navegación, Búsquedas, Descargas o URLs registradas.
- **Fecha UTC.**
- **Dominio.**
- **Texto:** título, URL, búsqueda, archivo u otro valor visible.

La consulta puede iniciarse con **Consultar** o presionando **Enter**. La búsqueda de texto no distingue mayúsculas ni acentos y acepta varias palabras.

Para historiales extensos, el procesamiento se realiza por bloques y se muestran 75 resultados inicialmente. **Mostrar más** incorpora resultados adicionales sin renderizar todo el historial de una vez.

La consulta puede exportarse a CSV o imprimirse/guardarse como PDF.

### 3. Información del análisis

Indica de forma breve que:

- los resultados corresponden a los registros presentes en la base examinada;
- SHA-256 aporta un control de integridad;
- el procesamiento del historial se realiza localmente.

## Informes complementarios

Los ocho resultados complementarios mantienen la misma estética general del proyecto. Incluyen:

- buscador;
- búsqueda con Enter;
- búsqueda sin distinguir mayúsculas ni acentos;
- paginación de 50, 100 o 250 registros;
- contador de resultados;
- acceso al Centro de consulta;
- impresión/guardado PDF mediante una vista limpia.

## Consulta de análisis anteriores

La opción principal **[2] CONSULTAR ANÁLISIS GENERADOS** muestra los análisis disponibles. Al elegir uno se abre siempre la misma lista fija de nueve resultados.

Puede abrir varios resultados consecutivamente.

- `M` dentro del listado de resultados vuelve a la lista de análisis.
- `M` en la lista de análisis vuelve a la pantalla principal.

## Interpretación técnica

Algunos campos requieren contexto:

- una URL registrada no identifica automáticamente a la persona que utilizó el equipo;
- `visit_count` es un contador almacenado por el navegador y no debe asumirse como conteo exacto de acciones humanas;
- `typed_count` es un indicador técnico y debe correlacionarse con otros datos;
- `visit_duration` no equivale necesariamente a tiempo efectivo de lectura;
- una búsqueda identificada no demuestra intención por sí sola;
- una descarga registrada no demuestra que el archivo haya sido abierto o ejecutado;
- la ausencia de un registro no prueba que la actividad nunca haya ocurrido.

## Privacidad del repositorio

No publique evidencia real. `.gitignore` excluye el contenido de:

```text
evidencia/
resultados/
```

y conserva únicamente sus archivos `.gitkeep`.

## Estructura

```text
ANALIZADOR-HISTORIAL-NAVEGACION-WINDOWS/
├── INICIAR.bat
├── analizador_navegacion.py
├── analyzer.py
├── report_center.py
├── html_exports.py
├── README.md
├── DESCARGA.md
├── LICENSE
├── requirements.txt
├── VERSION.txt
├── CHANGELOG.md
├── SECURITY.md
├── .gitignore
├── .gitattributes
├── docs/
│   ├── DATOS_ANALIZADOS.md
│   └── GUIA_GITHUB.md
├── evidencia/
│   └── .gitkeep
└── resultados/
    └── .gitkeep
```

## Licencia

MIT. Consulte `LICENSE`.

## Autor

**EEL Ciberseguridad**  
Abogado – Especialista en Entornos Digitales y Ciberseguridad  
Correo: `eelciberseguridad@gmail.com`

## Compatibilidad de los resultados HTML

Los resultados secundarios contienen sus registros directamente en el documento HTML. La información es visible aunque el navegador limite la ejecución de JavaScript local. JavaScript se utiliza solo para la búsqueda rápida.


## Consulta de resultados

Cada análisis genera nueve resultados HTML:

```text
[1] Centro de consulta
[2] Resumen
[3] Línea de tiempo
[4] Páginas y URLs
[5] Dominios
[6] Tipos de navegación
[7] Origen de visitas
[8] Búsquedas
[9] Descargas
```

Al seleccionar un resultado se abre en el navegador y la consola queda inmediatamente preparada para elegir otro número. No es necesario presionar `ENTER` después de cerrarlo.

Los resultados secundarios contienen los registros directamente dentro del HTML. JavaScript se utiliza únicamente para la búsqueda rápida. Si el navegador no ejecuta scripts locales, los datos continúan visibles.
