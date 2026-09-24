# Lab-ChromeHistory

Herramienta para **Windows** que preserva y analiza el historial de Google Chrome almacenado en SQLite.

Permite revisar actividad de navegación, URLs, dominios, búsquedas y descargas desde resultados HTML fáciles de consultar.

## ¿Qué hace?

- Detecta perfiles de Google Chrome.
- Copia `History`, `History-wal` y `History-shm` cuando están disponibles.
- Calcula hashes **SHA-256** para controlar la integridad.
- Analiza la copia del historial en modo lectura.
- Convierte las fechas de Chromium a un formato legible.
- Genera resultados HTML para consultar la información recuperada.

## Requisitos

- Windows 10 u 11.
- Python 3.10 o superior.
- No requiere librerías externas.

## Descargar

Repositorio:

```text
https://github.com/eelciberseguridad/Lab-ChromeHistory
```

Clonar:

```bash
git clone https://github.com/eelciberseguridad/Lab-ChromeHistory.git
```

O descargá el repositorio desde aca:

[![Descargar Lab-ChromeHistory](https://img.shields.io/badge/⬇️_DESCARGAR-Lab--ChromeHistory-238636?style=for-the-badge&logo=github&logoColor=white)](https://github.com/eelciberseguridad/Lab-ChromeHistory/archive/refs/heads/main.zip)

## Cómo usarlo

1. Cerrá Google Chrome.
2. Ejecutá:

```text
INICIAR.bat
```

3. Elegí:

```text
[1] DETECTAR PERFILES COMPATIBLES
```

4. Seleccioná el perfil que querés analizar.
5. La herramienta preservará una copia y generará los resultados.
6. Para volver a consultar análisis anteriores utilizá:

```text
[2] CONSULTAR ANÁLISIS GENERADOS
```

## Resultados

Cada análisis genera:

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

### Centro de consulta

`CENTRO_DE_CONSULTA.html` es la vista principal.

Permite consultar el historial por:

- tipo de información;
- fecha;
- dominio;
- texto;
- búsquedas;
- descargas.

También permite imprimir o guardar resultados como PDF.

## Carpetas

```text
evidencia/
```

Contiene las copias utilizadas para el análisis.

```text
resultados/
```

Contiene cada análisis y sus archivos HTML.

## Importante

Usá la herramienta únicamente sobre equipos, perfiles y datos propios o expresamente autorizados.

Una URL, una búsqueda o una descarga registrada por el navegador debe interpretarse dentro de su contexto. El historial por sí solo no identifica necesariamente a la persona que realizó una acción.

Los datos recopilados podrian contener informacion sencible y deben ser preservados con el cuidado necesario. 

Este sistema ayuda, pero no suplanta a herramientas de adquisicion de evidencia profesionales.

## Licencia

MIT.

## Autor

**EEL Ciberseguridad**  
`eelciberseguridad@gmail.com`
