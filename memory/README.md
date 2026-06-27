# Nexo Memory System

Herramientas de memoria persistente para Nexo.

## Archivos

- **nexo-memory-organize** - Organiza hechos en categorías (11 categorías)
- **nexo-semantic-enhance** - Genera embeddings TF-IDF y búsqueda semántica
- **nexo-memory-enhance** - Agrega tablas de mejora (conversation_summaries, learned_patterns, auto_skills)
- **nexo-memory-improve** - Script combinado de mejora de memoria
- **nexo-skill-creator** - Crea skills automáticamente desde trayectorias de tareas

## Uso

```bash
# Organizar hechos
nexo-memory-organize

# Generar embeddings
nexo-semantic-enhance

# Mejorar memoria
nexo-memory-improve

# Crear skill desde tarea
nexo-skill-creator "nombre" "descripcion" "pasos"
```

## Categorías de hechos

1. **identidad** - Nombre, creador, usuario
2. **hardware** - CPU, RAM, disco, temperatura
3. **red** - IP, puertos, servicios
4. **proyectos** - Repositorios, código
5. **herramientas** - Scripts, utilidades
6. **configuracion** - Settings, preferencias
7. **mejoras** - Optimizaciones, updates
8. **seguridad** - Hardening, permisos
9. **comunicacion** - Telegram, voz
10. **preferencias** - Gustos del usuario
11. **pendientes** - Tareas por hacer
