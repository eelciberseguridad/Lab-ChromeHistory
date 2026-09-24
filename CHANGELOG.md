# Changelog

## 1.0.0 — 23/09/2026

Primera versión estable para publicación.

- detección automática de perfiles de Google Chrome en Windows;
- adquisición de `History`, `History-wal` y `History-shm` cuando están disponibles;
- verificación SHA-256 antes y después de la copia;
- análisis SQLite en modo lectura;
- extracción de navegación, URLs, dominios, búsquedas y descargas;
- Centro de consulta HTML principal;
- ocho informes HTML complementarios;
- búsqueda, paginación e impresión limpia;
- consulta persistente de análisis anteriores;
- exclusión de evidencia y resultados reales mediante `.gitignore`.

### Versión 1.0.1 — compatibilidad de informes HTML

- corregidos los ocho informes HTML secundarios;
- los registros se escriben directamente dentro de cada tabla HTML;
- los informes ya no dependen de JavaScript para mostrar su contenido;
- búsqueda y paginación quedan como mejora progresiva;
- si JavaScript local no se ejecuta, los datos continúan visibles;
- impresión simplificada con la función nativa del navegador.

### 1.0.2 — consulta directa y reportes simplificados

- eliminado el ENTER posterior a la apertura de informes;
- el menú queda listo inmediatamente para elegir otro informe;
- informes secundarios simplificados;
- eliminado el paginador y el selector de cantidad de filas;
- registros escritos directamente dentro de cada HTML;
- JavaScript utilizado solamente para la búsqueda rápida;
- si JavaScript está bloqueado, los datos permanecen visibles;
- los informes solo se regeneran cuando faltan o son anteriores a analisis.json;
- apertura HTML reforzada con el navegador predeterminado.

### 1.0.3 — cambio de nombre del archivo principal

- `INFORME_FINAL.html` fue reemplazado por `CENTRO_DE_CONSULTA.html`;
- la opción `[1]` pasó de **Informe final** a **Centro de consulta**;
- la interfaz ahora habla de **resultados** y no de **informes** cuando corresponde;
- enlaces internos y documentación actualizados para reflejar la nueva lógica.
