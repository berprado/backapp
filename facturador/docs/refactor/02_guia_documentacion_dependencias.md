# Guía para documentar dependencias internas

## Propósito
Uniformar la elaboración de documentos de dependencias en `facturador/docs/refactor`, garantizando trazabilidad entre módulos y consistencia con los archivos ya generados (03+).

## Estructura recomendada

1. **Título**  
   `# Dependencias internas de [ruta/al/modulo.py](ruta/al/modulo.py)`

2. **Visión general**  
   - Resumen breve (1-2 frases) con el rol del módulo dentro del sistema.
   - Enfocarse en responsabilidades normativas y técnicas.

3. **Módulos propios utilizados**  
   - Lista numerada.  
   - Cada elemento debe incluir:
     - Enlace al archivo con formato `[ruta](ruta)`.
     - Descripción del componente usado: funciones, clases, constantes.
     - Rol (una frase) explicando la interacción.
   - Para importaciones diferidas, anotarlo explícitamente entre paréntesis.

4. **Conclusión**  
   - Explicar cómo encaja el módulo dentro de los planes (`00_diagnostico_main.md`, `01_plan_refactorizacion_ui.md`, contingencia, etc.).
   - Referenciar otros documentos clave si aplica.

## Reglas de estilo

- Idioma: español.  
- Usar sólo ASCII salvo que el contenido existente del módulo requiera otros caracteres.  
- Evitar backticks alrededor de nombres de módulos dentro de listas; utilizar etiquetas de enlace.  
- Mantener frases cortas y en voz activa.

## Checklist antes de guardar

- [ ] El título enlaza al módulo correspondiente.  
- [ ] La sección "Visión general" describe el rol normativo/técnico.  
- [ ] Cada dependencia tiene enlace, componentes y rol claros.  
- [ ] Las importaciones diferidas están identificadas.  
- [ ] La conclusión referencia documentos o planes relacionados.  
- [ ] El archivo se ubica en `facturador/docs/refactor/` con el prefijo numérico correlativo.

## Notas adicionales

- Si un módulo **no** utiliza otros componentes internos, indicarlo explícitamente en la sección de dependencias (ej.: "Ningún módulo interno adicional").  
- Cuando existan instrucciones específicas (ej. `contingencia_*.md`, `refactor_cache_*.md`), citarlas en la conclusión para mantener el hilo normativo.  
- Verificar las rutas antes de enlazar para evitar referencias rotas.  
- Mantener el estilo alineado con los documentos `03` a `22` ya publicados.