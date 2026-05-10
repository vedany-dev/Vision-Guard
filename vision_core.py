import cv2
import sqlite3
from datetime import datetime
import time

class DatabaseManager:
    """Maneja la arquitectura de persistencia con logs de auditoría y Soft-Delete."""
    
    def __init__(self, db_name="vision_guard.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._crear_esquema()

    def _crear_esquema(self):
        query = """
        CREATE TABLE IF NOT EXISTS logs_acceso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            evento TEXT NOT NULL,
            estado TEXT DEFAULT 'Detectado',
            imagen_rostro BLOB,  -- Nueva columna para la foto
            is_deleted INTEGER DEFAULT 0,
            deleted_at TEXT NULL,
            usuario_modificacion TEXT DEFAULT 'SYSTEM'
        )
        """
        self.cursor.execute(query)
        self.conn.commit()

    def registrar_acceso(self, descripcion_evento, foto_bytes=None):
        timestamp_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = "INSERT INTO logs_acceso (timestamp, evento, imagen_rostro) VALUES (?, ?, ?)"
        self.cursor.execute(query, (timestamp_actual, descripcion_evento, foto_bytes))
        self.conn.commit()
        print(f"[AUDITORÍA] Acceso registrado: {timestamp_actual} | Guardado con evidencia visual.")

    def eliminar_registro_logico(self, id_registro, usuario="ADMIN"):
        """Aplica Soft-Delete: oculta el registro sin borrar el dato físicamente."""
        timestamp_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = """
            UPDATE logs_acceso 
            SET is_deleted = 1, deleted_at = ?, usuario_modificacion = ? 
            WHERE id = ? AND is_deleted = 0
        """
        self.cursor.execute(query, (timestamp_actual, usuario, id_registro))
        self.conn.commit()
        print(f"[AUDITORÍA] Registro {id_registro} eliminado lógicamente por {usuario}.")

    def obtener_registros_activos(self):
        """Consulta para el Dashboard: solo trae los registros no eliminados."""
        query = "SELECT id, timestamp, evento FROM logs_acceso WHERE is_deleted = 0 ORDER BY id DESC"
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def cerrar_conexion(self):
        self.conn.close()


class VisionGuardApp:
    """Motor de inteligencia calibrado para alta sensibilidad y captura de evidencia."""
    
    def __init__(self, db_manager):
        self.db = db_manager
        
        # Carga del modelo y verificación de errores
        ruta_modelo = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.clasificador_rostros = cv2.CascadeClassifier(ruta_modelo)
        
        if self.clasificador_rostros.empty():
            print("🚨 [ERROR] OpenCV no pudo cargar el modelo de rostros. Verifica la instalación.")
            
        self.camara = cv2.VideoCapture(0)
        self.ultimo_registro = 0
        self.cooldown_segundos = 3.0 

    def procesar_fotograma(self, frame):
        import os
        # Creamos una carpeta física en tu computadora si no existe
        if not os.path.exists("capturas_evidencia"):
            os.makedirs("capturas_evidencia")

        frame_gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_blur = cv2.GaussianBlur(frame_gris, (5, 5), 0)

        rostros = self.clasificador_rostros.detectMultiScale(
            frame_blur, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30)
        )

        deteccion_activa = False
        foto_bytes = None  

        for (x, y, ancho, alto) in rostros:
            cv2.rectangle(frame, (x, y), (x + ancho, y + alto), (255, 204, 0), 2)
            cv2.putText(frame, "Sujeto Detectado", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 204, 0), 2)
            
            rostro_recortado = frame[y:y+alto, x:x+ancho]
            _, buffer = cv2.imencode('.jpg', rostro_recortado)
            foto_bytes = buffer.tobytes()
            
            # NUEVO: Guardamos el archivo físico en la computadora
            tiempo_archivo = time.strftime("%Y%m%d_%H%M%S")
            ruta_archivo = f"capturas_evidencia/rostro_{tiempo_archivo}.jpg"
            cv2.imwrite(ruta_archivo, rostro_recortado)
            
            deteccion_activa = True
            break

        tiempo_actual = time.time()
        if deteccion_activa and (tiempo_actual - self.ultimo_registro > self.cooldown_segundos):
            print("📸 ¡Rostro detectado! Guardando evidencia visual...")
            self.db.registrar_acceso("Presencia humana detectada.", foto_bytes)
            self.ultimo_registro = tiempo_actual

        return frame

    def ejecutar(self):
        if not self.camara.isOpened():
            print("[ERROR CRÍTICO] No se pudo inicializar el hardware de video.")
            return

        print("=== Iniciando VISION-GUARD MVP ===")
        print("Presiona la tecla 'q' en la ventana de video para apagar el sistema.")

        while True:
            lectura_exitosa, frame = self.camara.read()
            if not lectura_exitosa:
                break

            frame_procesado = self.procesar_fotograma(frame)
            cv2.imshow('Vision-Guard: Monitor de Seguridad', frame_procesado)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.camara.release()
        cv2.destroyAllWindows()
        self.db.cerrar_conexion()
        print("=== Sistema apagado de forma segura ===")


if __name__ == "__main__":
    # Instanciación y ejecución basada en POO
    manejador_db = DatabaseManager()
    sistema_seguridad = VisionGuardApp(manejador_db)
    
    sistema_seguridad.ejecutar()