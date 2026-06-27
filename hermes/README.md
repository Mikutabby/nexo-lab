# Nexo Hermes Integration

Integración de Hermes Agent con el ecosistema Nexo.

## Archivos

- **hermes** - Wrapper para ejecutar Hermes Agent
- **nexo-hermes-integration** - Script de demostración de integración

## Configuración

1. API key en `~/.hermes/.env`:
   ```
   OPENROUTER_API_KEY=tu-api-key
   ```

2. Config en `~/.hermes/config.yaml`:
   ```yaml
   model:
     provider: "openrouter"
     default: "anthropic/claude-opus-4.6"
   ```

## Uso

```bash
# Chat interactivo
hermes chat

# Ver estado
hermes status

# Cambiar modelo
hermes model
```

## Integración con Nexo

Hermes puede:
- Ejecutar comandos del sistema
- Acceder a archivos
- Usar las herramientas de Nexo
- Aprender de interacciones
