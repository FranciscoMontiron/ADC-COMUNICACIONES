import sqlite3
from sqlite3 import Error
import os
import json

def crearConexion():
    """Crea una conexion a la base de datos"""
    try:
        # Crea la base de datos en el directorio actual
        conn = sqlite3.connect('adc_comunicaciones.db')
        return conn
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None

def crearTablas(conn):
    """Crea las tablas necesarias en la base de datos"""
    try:
        cursor = conn.cursor()
        
        # Crea la tabla de señales
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS senales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                f0 REAL NOT NULL,
                amplitud REAL NOT NULL,
                fs REAL NOT NULL,
                bits INTEGER NOT NULL,
                mostrar_alias INTEGER NOT NULL,
                aplicar_filtro INTEGER NOT NULL,
                n_armonicos INTEGER,
                amplitudes_armonicos TEXT,
                snr_db REAL,
                f_portadora REAL,
                indice_mod REAL,
                orden_filtro INTEGER,
                fc_factor REAL,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
    except Error as e:
        print(f"Error al crear las tablas: {e}")

def inicializarBaseDeDatos():
    """Inicializa la base de datos y crea las tablas"""
    # Crea la conexion a la base de datos
    conn = crearConexion()
    
    if conn is not None:
        # Crea las tablas
        crearTablas(conn)
        conn.close()
    else:
        print("Error: No se pudo crear la conexion a la base de datos")

def guardar_senal(tipo, f0, amp, fs, bits, mostrar_alias, aplicar_filtro, n_armonicos=None, amplitudes_armonicos=None, snr_db=None, f_portadora=None, indice_mod=None, orden_filtro=None, fc_factor=None):
    """Guarda la senal en la base de datos"""
    conn = crearConexion()
    if conn is not None:
        cursor = conn.cursor()
        try:
            # Convertir booleanos a enteros para SQLite
            mostrar_alias = 1 if mostrar_alias else 0
            aplicar_filtro = 1 if aplicar_filtro else 0
            
            # Convertir amplitudes_armonicos a JSON si es una lista
            if amplitudes_armonicos is not None and isinstance(amplitudes_armonicos, list):
                amplitudes_armonicos = json.dumps(amplitudes_armonicos)
            
            cursor.execute('''
                INSERT INTO senales (
                    tipo, f0, amplitud, fs, bits, mostrar_alias, aplicar_filtro,
                    n_armonicos, amplitudes_armonicos, snr_db, f_portadora,
                    indice_mod, orden_filtro, fc_factor
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tipo, f0, amp, fs, bits, mostrar_alias, aplicar_filtro,
                n_armonicos, amplitudes_armonicos, snr_db, f_portadora,
                indice_mod, orden_filtro, fc_factor
            ))
            conn.commit()
            return True
        except Error as e:
            print(f"Error al guardar la senal: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    else:
        print("Error: No se pudo crear la conexion a la base de datos")
        return False

def obtener_senal(id_senal):
    """Obtiene una señal de la base de datos por su ID"""
    conn = crearConexion()
    if conn is not None:
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM senales WHERE id = ?', (id_senal,))
            senal = cursor.fetchone()
            
            if senal:
                # Convertir la tupla a diccionario
                columnas = [description[0] for description in cursor.description]
                senal_dict = dict(zip(columnas, senal))
                
                # Convertir amplitudes_armonicos de JSON a lista si existe
                if senal_dict['amplitudes_armonicos']:
                    try:
                        senal_dict['amplitudes_armonicos'] = json.loads(senal_dict['amplitudes_armonicos'])
                    except json.JSONDecodeError:
                        print("Error al decodificar amplitudes_armonicos")
                
                return senal_dict
            return None
        except Error as e:
            print(f"Error al obtener la senal: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    else:
        print("Error: No se pudo crear la conexion a la base de datos")
        return None

if __name__ == '__main__':
    inicializarBaseDeDatos()

    