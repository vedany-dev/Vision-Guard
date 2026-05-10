from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import sqlite3
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

def obtener_datos():
    # Verificamos si el archivo existe antes de intentar abrirlo
    if not os.path.exists("vision_guard.db"):
        return [], {"total_detecciones": 0, "camaras_activas": 0, "estado_red": "Archivo DB no encontrado"}

    try:
        conn = sqlite3.connect("vision_guard.db")
        cursor = conn.cursor()
        
        # Consulta de logs
        # ¡Agregamos imagen_rostro a la consulta!
        cursor.execute("SELECT id, timestamp, evento, estado, imagen_rostro FROM logs_acceso WHERE is_deleted = 0 ORDER BY id DESC LIMIT 15")
        logs = cursor.fetchall()
        
        # Consulta de estadísticas
        cursor.execute("SELECT COUNT(*) FROM logs_acceso WHERE is_deleted = 0")
        total = cursor.fetchone()[0]
        
        conn.close()
        stats = {"total_detecciones": total, "camaras_activas": 1, "estado_red": "Óptimo"}
        return logs, stats
    except Exception as e:
        print(f"❌ Error crítico en la base de datos: {e}")
        return [], {"total_detecciones": 0, "camaras_activas": 0, "estado_red": f"Error: {e}"}

from fastapi import Response

@app.get("/foto/{log_id}")
async def obtener_foto(log_id: int):
    """Busca los bytes en la DB y los sirve como una imagen real"""
    conn = sqlite3.connect("vision_guard.db")
    cursor = conn.cursor()
    cursor.execute("SELECT imagen_rostro FROM logs_acceso WHERE id = ?", (log_id,))
    resultado = cursor.fetchone()
    conn.close()

    if resultado and resultado[0]:
        # Retornamos los bytes con el tipo de medio correcto (image/jpeg)
        return Response(content=resultado[0], media_type="image/jpeg")
    return Response(status_code=404)

@app.get("/")
async def mostrar_dashboard(request: Request):
    logs, stats = obtener_datos()
    
    # Forma moderna y a prueba de errores para las versiones recientes de FastAPI
    return templates.TemplateResponse(
        request=request, 
        name="dashboard.html", 
        context={
            "request": request, 
            "logs": logs, 
            "stats": stats
        }
    )