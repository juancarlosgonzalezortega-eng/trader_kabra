from flask import Flask, render_template, request, redirect
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
app = Flask(__name__)

def get_connection():
    return psycopg2.connect(
        DATABASE_URL, sslmode="require"
    )


@app.route('/')
def index():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT 
            id, 
            usuario,
            empresa,
            monto_cta,
            saldo_inicial,
            saldo_final,
            trades_loss,
            monto_loss,
            trades_win,
            monto_win,
            TO_CHAR(fecha_inicio,'DD/MM/YYYY') as fecha_inicio,
            TO_CHAR(fecha_fin,'DD/MM/YYYY') as fecha_fin
        FROM cuentas_fondeo
        ORDER BY id DESC
    """)

    data = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('index.html', registros=data)


@app.route('/guardar', methods=['POST'])
def guardar():
    datos = (
        request.form['usuario'],
        request.form['empresa'],
        request.form['monto_cta'],
        request.form['saldo_inicial'],
        request.form['saldo_final'],
        request.form['trades_loss'],
        request.form['monto_loss'],
        request.form['trades_win'],
        request.form['monto_win'],
        request.form['fecha_inicio'],
        request.form['fecha_fin']
    )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO cuentas_fondeo
        (usuario, empresa, monto_cta, saldo_inicial, saldo_final, 
         trades_loss, monto_loss, trades_win, monto_win, 
         fecha_inicio, fecha_fin, fecha_actualizacion)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, NOW())
    """, datos)

    conn.commit()
    cursor.close()
    conn.close()

    return redirect('/')
    

if __name__ == '__main__':
    app.run()
