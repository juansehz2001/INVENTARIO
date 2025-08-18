import psycopg2

def get_connection():
    try:
        conn = psycopg2.connect(
            dbname="INVENTARIO",     
            user="adminjsh",         
            password="COLORnegro2001",
            host="localhost",
            port="5432"
        )
        print(" Conexión establecida")
        return conn
    except Exception as e:
        print(" Error de conexión:", e)
        return None
