from flask import Flask, render_template, request, redirect, session, url_for
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
import requests

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")

app = Flask(__name__)
app.secret_key = "super_secret_key_123"

ADMIN_USERS = ["juangno", "JKabraFX"]

def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")


### ---------- LOGIN DISCORD ----------
@app.route("/login")
def login():
    discord_auth_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={DISCORD_CLIENT_ID}"
        f"&redirect_uri={DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify email"
    )
    return redirect(discord_auth_url)


### ---------- CALLBACK DISCORD ----------
@app.route("/callback")
def callback():
    code = request.args.get("code")

    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "scope": "identify email"
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post("https://discord.com/api/oauth2/token", data=data, headers=headers)
    r_json = r.json()

    access_token = r_json.get("access_token")

    user_info = requests.get(
        "https://discord.com/api/users/@me",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    session["user"] = {
        "id": user_info["id"],
        "username": user_info["username"],
        "avatar": user_info["avatar"],
        "email": user_info.get("email")
    }

    return redirect("/")


### ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


### ---------- INDEX ----------
@app.route('/')
def index():
    if "user" not in session:
        return render_template("login.html")

    user = session["user"]
    username = user["username"]

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    if username in ADMIN_USERS:
        cursor.execute("""
            SELECT 
                id, usuario, empresa, monto_cta, saldo_inicial,
                saldo_final, trades_loss, monto_loss,
                trades_win, monto_win,
                TO_CHAR(fecha_inicio,'DD/MM/YYYY') as fecha_inicio,
                TO_CHAR(fecha_fin,'DD/MM/YYYY') as fecha_fin
            FROM cuentas_fondeo
            ORDER BY id DESC
        """)
    else:
        cursor.execute("""
            SELECT 
                id, usuario, empresa, monto_cta, saldo_inicial,
                saldo_final, trades_loss, monto_loss,
                trades_win, monto_win,
                TO_CHAR(fecha_inicio,'DD/MM/YYYY') as fecha_inicio,
                TO_CHAR(fecha_fin,'DD/MM/YYYY') as fecha_fin
            FROM cuentas_fondeo
            WHERE usuario = %s
            ORDER BY id DESC
        """, (username,))

    data = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('index.html', registros=data, usuario=username)


### ---------- GUARDAR ----------
@app.route('/guardar', methods=['POST'])
def guardar():
    if "user" not in session:
        return redirect("/")

    username = session["user"]["username"]

    datos = (
        username,
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
    app.run(debug=True)
