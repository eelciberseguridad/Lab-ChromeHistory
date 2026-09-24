# Publicar en GitHub

## Repositorio

Nombre recomendado:

```text
ANALIZADOR-HISTORIAL-NAVEGACION-WINDOWS
```

Descripción sugerida:

> Herramienta para Windows que preserva y analiza el historial de navegación de Google Chrome almacenado en SQLite, verifica SHA-256 y genera informes HTML consultables.

## Publicación desde la web

1. Cree un repositorio nuevo con ese nombre.
2. No cree un README adicional.
3. Use **Add file → Upload files**.
4. Suba el contenido de la carpeta `ANALIZADOR-HISTORIAL-NAVEGACION-WINDOWS`.
5. Verifique que `evidencia/` y `resultados/` contengan únicamente `.gitkeep`.
6. Commit sugerido: `Versión 1.0.0 estable`.

## Archivos principales

```text
INICIAR.bat
analizador_navegacion.py
analyzer.py
report_center.py
html_exports.py
README.md
DESCARGA.md
LICENSE
requirements.txt
VERSION.txt
CHANGELOG.md
SECURITY.md
.gitignore
.gitattributes
docs/
evidencia/.gitkeep
resultados/.gitkeep
```

## No publicar evidencia

Antes del commit confirme que no existan archivos `History`, bases SQLite, informes reales ni datos de casos dentro del repositorio. `.gitignore` está preparado para excluir `evidencia/*` y `resultados/*`.
