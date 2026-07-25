# CareClearCrew - Solución de Autorización Médica Autónoma

CareClearCrew es un producto de software de nivel élite, diseñado para automatizar el procesamiento de autorizaciones médicas previas utilizando agentes de inteligencia artificial y tecnología RAG contra políticas de seguros médicos.

## Primeros Pasos

Para una explicación completa del producto, la arquitectura en capas, los más de 100 puntos de control clínicos evaluados, instrucciones detalladas de instalación local, y el despliegue automático en la capa gratuita de Render, consulte la documentación oficial en:

👉 **[EXPLICACION_PROYECTO.md](EXPLICACION_PROYECTO.md)**

Para conocer la historia del desarrollo del producto y el diario de diseño, consulte:

👉 **[DOCUMENTACION.md](DOCUMENTACION.md)**

## Ejecución de la Interfaz del Producto

```bash
pip install uv
cd crews/care_clear_crew
uv sync
uv run streamlit run src/care_clear_crew/app.py
```
