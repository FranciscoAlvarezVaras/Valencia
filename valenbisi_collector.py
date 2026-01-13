import requests
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import time
import os
import logging
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Configuración de la base de datos (con variables de entorno)
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'dbname': os.getenv('DB_NAME', 'valenbisi'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

# URL de la API de Valenbisi
API_URL = "https://valencia.opendatasoft.com/api/explore/v2.1/catalog/datasets/valenbisi-disponibilitat-valenbisi-dsiponibilidad/records?limit=100"

def wait_for_db(max_retries=30, delay=2):
    """Espera hasta que la base de datos esté disponible"""
    logger.info("Esperando conexión a la base de datos...")
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            conn.close()
            logger.info("✓ Conexión a base de datos establecida")
            return True
        except psycopg2.OperationalError as e:
            if attempt < max_retries - 1:
                logger.warning(f"Intento {attempt + 1}/{max_retries} - Base de datos no disponible, reintentando en {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"✗ No se pudo conectar a la base de datos después de {max_retries} intentos")
                raise
    return False

def fetch_data():
    """Obtiene datos de la API de Valenbisi"""
    try:
        logger.info(f"Consultando API: {API_URL}")
        response = requests.get(API_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        results = data.get('results', [])
        if not results:
            logger.warning("No se recibieron datos de la API")
            return []
        
        result = []
        timestamp = datetime.now()
        
        for station in results:
            try:
                # Extraer coordenadas
                geo_point = station.get('geo_point_2d', {})
                latitude = geo_point.get('lat')
                longitude = geo_point.get('lon')
                
                # Los campos ahora están directamente en el resultado
                result.append((
                    station.get('number'),  # station_id
                    station.get('address'),  # station_name
                    latitude,  # latitude
                    longitude,  # longitude
                    station.get('available'),  # available_bikes
                    station.get('free'),  # available_slots
                    station.get('open'),  # station_status (T/F)
                    station.get('total'),  # total_capacity
                    timestamp
                ))
            except Exception as e:
                logger.error(f"Error procesando estación: {e}")
                continue
        
        logger.info(f"✓ Datos obtenidos: {len(result)} estaciones")
        return result
    
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Error al consultar API: {e}")
        raise
    except Exception as e:
        logger.error(f"✗ Error inesperado obteniendo datos: {e}")
        raise

    except Exception as e:
        logger.error(f"✗ Error inesperado obteniendo datos: {e}")
        raise

# Configuración MongoDB
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://root:examplepassword@mongo:27017/')
from pymongo import MongoClient, UpdateOne

def store_data_mongo(records):
    """Almacena datos en MongoDB"""
    try:
        client = MongoClient(MONGO_URI)
        db = client.valenbisi
        
        # Preparar operaciones para latest_status (Upsert)
        latest_ops = []
        # Preparar documentos para series temporales
        history_docs = []
        
        for r in records:
            # Desempaquetar tupla
            (station_id, name, lat, lon, bikes, slots, status, capacity, timestamp) = r
            
            doc = {
                "station_id": station_id,
                "name": name,
                "location": {"type": "Point", "coordinates": [lon, lat]},
                "available_bikes": bikes,
                "available_slots": slots,
                "status": status,
                "total_capacity": capacity,
                "timestamp": timestamp
            }
            
            # Operación para última actualización
            latest_ops.append(
                UpdateOne(
                    {"station_id": station_id},
                    {"$set": doc},
                    upsert=True
                )
            )
            
            history_docs.append(doc)
            
        # Ejecutar operaciones
        if latest_ops:
            db.latest_status.bulk_write(latest_ops)
        
        if history_docs:
            db.station_status.insert_many(history_docs)
            
        logger.info(f"✓ Insertados {len(records)} registros en MongoDB")
        client.close()
        
    except Exception as e:
        logger.error(f"✗ Error guardando en MongoDB: {e}")
        # No lanzar excepción para no detener el flujo principal si Mongo falla


def store_data(records):
    """Almacena los datos en PostgreSQL y MongoDB"""
    if not records:
        logger.warning("No hay datos para almacenar")
        return
    
    # 1. Almacenar en PostgreSQL
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        sql = """
            INSERT INTO valenbisi_raw
            (station_id, station_name, latitude, longitude, available_bikes, 
             available_slots, station_status, total_capacity, timestamp)
            VALUES %s
        """
        
        execute_values(cursor, sql, records)
        conn.commit()
        
        logger.info(f"✓ Insertados {len(records)} registros en PostgreSQL")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        logger.error(f"✗ Error de base de datos Postgres: {e}")
        raise
    except Exception as e:
        logger.error(f"✗ Error inesperado almacenando datos en Postgres: {e}")
        raise

    # 2. Almacenar en MongoDB
    store_data_mongo(records)

def main():
    """Función principal del collector"""
    logger.info("=" * 60)
    logger.info("VALENBISI DATA COLLECTOR - Iniciando")
    logger.info("=" * 60)
    
    # Esperar a que la base de datos esté lista
    wait_for_db()
    
    # Intervalo de recolección (5 minutos = 300 segundos)
    interval = int(os.getenv('COLLECTION_INTERVAL', 300))
    logger.info(f"Intervalo de recolección: {interval} segundos")
    
    iteration = 0
    while True:
        iteration += 1
        logger.info(f"\n{'='*60}")
        logger.info(f"Iteración #{iteration} - {datetime.now()}")
        logger.info(f"{'='*60}")
        
        try:
            # Obtener datos de la API
            data = fetch_data()
            
            # Almacenar en la base de datos
            if data:
                store_data(data)
            
            logger.info(f"✓ Ciclo completado exitosamente")
            
        except Exception as e:
            logger.error(f"✗ Error en el ciclo de recolección: {e}")
            logger.info("Continuando con el siguiente ciclo...")
        
        # Esperar antes del próximo ciclo
        logger.info(f"Esperando {interval} segundos hasta el próximo ciclo...")
        time.sleep(interval)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n✓ Collector detenido por el usuario")
    except Exception as e:
        logger.error(f"\n✗ Error fatal: {e}")
        sys.exit(1)
