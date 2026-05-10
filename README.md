# Vision-Guard: IA Security Core 👁️
Sistema de seguridad perimetral basado en Inteligencia Artificial y Visión Computacional.

## Arquitectura del MVP
Este proyecto integra 4 fases fundamentales:
1. **Motor de Ingesta:** Captura de video en tiempo real usando OpenCV.
2. **Motor de IA:** Detección facial mediante Haar Cascades calibrados para alta sensibilidad.
3. **Persistencia:** Almacenamiento seguro de auditoría y evidencia visual (BLOB) en SQLite.
4. **Dashboard:** Panel de control web reactivo construido con FastAPI y Jinja2.

## Cómo ejecutar el proyecto
Para encender el sistema, se deben ejecutar ambos módulos en terminales separadas:
1. Motor IA: `python vision_core.py`
2. Servidor Web: `uvicorn main:app --reload`
3. Monitoreo: Abrir `http://127.0.0.1:8000` en el navegador con un dashboard muy amigable.
