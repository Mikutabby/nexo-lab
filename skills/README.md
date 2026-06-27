# Nexo Skills System

Sistema de plugins para Nexo.

## Archivos

- **nexo-skill** - Gestor de skills (listar, info, ejecutar, crear)
- **nexo-skill-creator** - Crea skills automáticamente desde tareas

## Uso

```bash
# Listar skills
nexo-skill list

# Info de un skill
nexo-skill info <nombre>

# Ejecutar skill
nexo-skill run <nombre> <comando>

# Crear skill
nexo-skill create <nombre>

# Crear desde tarea
nexo-skill-creator "nombre" "descripcion" "pasos"
```

## Estructura de un skill

```
~/.nexo-skills/
  mi-skill/
    skill.json      # Metadata
    scripts/
      mi-script.sh  # Scripts del skill
```

## Ejemplo skill.json

```json
{
  "name": "ejemplo",
  "description": "Skill de ejemplo",
  "version": "1.0.0",
  "commands": {
    "hello": {
      "description": "Dice hola",
      "script": "scripts/hello.sh"
    }
  }
}
```
