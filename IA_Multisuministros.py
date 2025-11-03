# IA_Multisuministros.py
# IA Multisuministros de Costa Rica - Streamlit app (final package)
# Registration from app enabled, designed for Render + local run.

import streamlit as st
import sqlite3, os, io
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from streamlit_lottie import st_lottie
import requests
# === Estilo visual personalizado ===
st.markdown('<link rel="stylesheet" href="assets/style.css">', unsafe_allow_html=True)

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "codigos_multisuministros.db")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "logo.png")

IVA = 0.13
MAX_VENDEDORES = 25

def load_lottie_url(url):
    try:
        r = requests.get(url, timeout=4)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password_hash TEXT,
                    role TEXT
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS productos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo TEXT UNIQUE,
                    descripcion TEXT,
                    precio REAL,
                    impuesto REAL,
                    proveedor TEXT,
                    creado_por TEXT,
                    creado_en TEXT
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS solicitudes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    descripcion TEXT,
                    precio_ingresado REAL,
                    proveedor TEXT,
                    vendedor TEXT,
                    estado TEXT,
                    motivo_ia TEXT,
                    creado_en TEXT,
                    aprobado_por TEXT,
                    aprobado_en TEXT,
                    codigo_asignado TEXT
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS notificaciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT,
                    mensaje TEXT,
                    leido INTEGER DEFAULT 0,
                    creado_en TEXT
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )""")
    conn.commit()
    conn.close()

def seed_defaults():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?,?)", ('tolerancia_precio_pct','0.02'))
    c.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?,?,?)", ('admin', generate_password_hash('admin123'), 'admin'))
    conn.commit()
    conn.close()

init_db()
seed_defaults()

def run_query(q, params=()):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(q, params)
    rows = c.fetchall()
    conn.commit()
    conn.close()
    return rows

def df_from_query(q, params=()):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(q, conn, params=params)
    conn.close()
    return df

def count_vendedores():
    rows = run_query("SELECT COUNT(*) FROM users WHERE role='vendedor'")
    return rows[0][0] if rows else 0

def register_user(username, password, role='vendedor'):
    if role=='vendedor' and count_vendedores()>=MAX_VENDEDORES:
        return False, f"No se pueden crear más vendedores. Límite: {MAX_VENDEDORES}."
    try:
        pw_hash = generate_password_hash(password)
        run_query("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)", (username, pw_hash, role))
        return True, "Usuario creado."
    except Exception as e:
        return False, str(e)

def authenticate(username, password):
    rows = run_query("SELECT password_hash, role FROM users WHERE username=?", (username,))
    if not rows:
        return False, "Usuario no encontrado."
    pw_hash, role = rows[0]
    if check_password_hash(pw_hash, password):
        return True, role
    return False, "Contraseña incorrecta."

def top_similar(descripcion_nueva, top_n=3):
    df = df_from_query("SELECT codigo, descripcion, precio, proveedor FROM productos")
    if df.empty:
        return []
    corpus = df['descripcion'].astype(str).tolist() + [descripcion_nueva]
    vectorizer = TfidfVectorizer().fit_transform(corpus)
    cosine_similarities = linear_kernel(vectorizer[-1], vectorizer[:-1]).flatten()
    top_idx = cosine_similarities.argsort()[::-1][:top_n]
    results = []
    for idx in top_idx:
        score = float(cosine_similarities[idx])
        row = df.iloc[idx]
        results.append({'codigo': row['codigo'], 'descripcion': row['descripcion'], 'precio': row['precio'], 'proveedor': row['proveedor'], 'score': score})
    return results

def push_notification(usuario, mensaje):
    run_query("INSERT INTO notificaciones (usuario, mensaje, leido, creado_en) VALUES (?,?,0,?)", (usuario, mensaje, datetime.now().isoformat()))

# UI
st.set_page_config(page_title="IA Multisuministros de Costa Rica", layout="wide", page_icon="🧾")
st.markdown("""
<style>
.stApp { font-family: Inter, Roboto, Arial, sans-serif; background: #ffffff; color: #0b2740; }
.header-title { font-size:26px; font-weight:700; color:#0b4f8c; }
.header-sub { font-size:13px; color:#6b7280; margin-bottom:6px; }
.card { background: white; border-radius:10px; padding:12px; box-shadow:0 6px 18px rgba(11,79,140,0.06); }
</style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([3,1])
with col1:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=220)
    st.markdown('<div class="header-title">IA Multisuministros de Costa Rica</div>', unsafe_allow_html=True)
    st.markdown('<div class="header-sub">Gestión inteligente de códigos — flujo de solicitudes y aprobaciones.</div>', unsafe_allow_html=True)
with col2:
    l = load_lottie_url("https://assets10.lottiefiles.com/packages/lf20_jcikwtux.json")
    if l:
        st_lottie(l, height=100)

# Sidebar: login + register
st.sidebar.title("Acceso")
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = None
    st.session_state['role'] = None
# === Animación IA en pantalla de inicio ===
from streamlit_lottie import st_lottie
import requests

def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Cargar animación del robot IA
lottie_robot = load_lottieurl("https://assets1.lottiefiles.com/packages/lf20_jcikwtux.json")

# Mostrar animación centrada
st.markdown("<div style='display:flex; justify-content:center;'>", unsafe_allow_html=True)
st_lottie(lottie_robot, height=250, key="robot")
st.markdown("</div>", unsafe_allow_html=True)

# Título estilizado
st.markdown("<h2 style='text-align:center; color:#00A6FF;'>Bienvenido a Multisuministros</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:white;'>Inicia sesión para continuar</p>", unsafe_allow_html=True)

if not st.session_state['logged_in']:
    # === Diseño visual de inicio ===
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("assets/logo.png", use_container_width=True)
    with col2:
        st.image("assets/ia_robot.svg", use_container_width=True)

    st.markdown(
        """
        <div style="text-align:center; margin-top:-20px;">
            <h1 style="color:#004AAD; font-weight:800;">IA Multisuministros de Costa Rica</h1>
            <p style="color:white; font-size:18px;">Gestión inteligente de códigos y solicitudes</p>
        </div>
        """,
        unsafe_allow_html=True
    )

   # === Caja de login ===
st.markdown("<div class='login-box'>", unsafe_allow_html=True)
username = st.text_input(" Usuario", key="login_user")
password = st.text_input(" Contraseña", type="password", key="login_pw")

if st.button("Iniciar sesión"):
    ok, res = authenticate(username.strip(), password.strip())
    if ok:
        st.session_state['logged_in'] = True
        st.session_state['username'] = username.strip()
        st.session_state['role'] = res
        st.success(f"Bienvenido, {st.session_state['username']}")
        st.rerun()
    else:
        st.error("Usuario o contraseña incorrectos.")

elif tab == "Registrarse":
    st.sidebar.markdown("### Registrarse")
    new_user = st.sidebar.text_input("Usuario nuevo", key="reg_user")
    new_pass = st.sidebar.text_input("Contraseña", type="password", key="reg_pw")

    if st.sidebar.button("Crear cuenta"):
        if new_user.strip() and new_pass.strip():
            ok, msg = register_user(new_user.strip(), new_pass.strip(), role='vendedor')
            if ok:
                st.sidebar.success("Cuenta creada. Ahora iniciá sesión.")
            else:
                st.sidebar.error(msg)
        else:
            st.sidebar.error("Completá usuario y contraseña.")
            
    st.markdown("</div>", unsafe_allow_html=True)

    elif tab == "Registrarse":
    st.sidebar.markdown("### Registrarse")
    new_user = st.sidebar.text_input("Usuario nuevo", key="reg_user")
    new_pass = st.sidebar.text_input("Contraseña", type="password", key="reg_pw")

    if st.sidebar.button("Crear cuenta"):
        if new_user.strip() and new_pass.strip():
            ok, msg = register_user(new_user.strip(), new_pass.strip(), role='vendedor')
            if ok:
                st.sidebar.success("Cuenta creada. Ahora iniciá sesión.")
            else:
                st.sidebar.error(msg)
        else:
            st.sidebar.error("Completá usuario y contraseña.")

st.sidebar.markdown("---")
st.sidebar.info("Si tenés problemas, contactá al administrador.")

else:
    st.sidebar.write(f"**Usuario:** {st.session_state['username']}")
    st.sidebar.write(f"**Rol:** {st.session_state['role']}")
    noti_df = df_from_query("SELECT id, mensaje, leido, creado_en FROM notificaciones WHERE usuario=? ORDER BY creado_en DESC", (st.session_state['username'],))
    if not noti_df.empty:
        with st.sidebar.expander("Notificaciones"):
            for _, r in noti_df.iterrows():
                st.write(f"- {r['mensaje']} ({r['creado_en'][:19]})")
            if st.sidebar.button("Marcar todas como leídas"):
                run_query("UPDATE notificaciones SET leido=1 WHERE usuario=?", (st.session_state['username'],))
                st.rerun()
    if st.sidebar.button("Cerrar sesión"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = None
        st.session_state['role'] = None
        st.rerun()

tabs = st.tabs(["Crear solicitud","Buscador","Panel admin","Exportar"])

# Create request tab
with tabs[0]:
    st.header("Crear solicitud de código")
    if not st.session_state['logged_in']:
        st.warning("Iniciá sesión para crear solicitudes.")
    else:
        with st.form("form_request"):
            descripcion = st.text_area("Descripción del producto", max_chars=500)
            precio = st.number_input("Precio (sin símbolos)", min_value=0.0, format="%.2f")
            proveedor = st.text_input("Proveedor (nombre)")
            submitted = st.form_submit_button("Enviar solicitud")
        if submitted:
            with st.modal("Confirmar envío"):
                st.write("¿Estás segura(o) de enviar la solicitud?")
                colA, colB = st.columns([1,1])
                with colA:
                    if st.button("Enviar solicitud"):
                        run_query("""INSERT INTO solicitudes (descripcion, precio_ingresado, proveedor, vendedor, estado, motivo_ia, creado_en)
                                     VALUES (?,?,?,?,?,?,?)""", (descripcion, precio, proveedor, st.session_state['username'], "Pendiente", "Sin verificación", datetime.now().isoformat()))
                        push_notification(st.session_state['username'], "Solicitud enviada (pendiente de aprobación).")
                        st.success("Solicitud enviada. Será revisada por el administrador.")
                        st.rerun()

                with colB:
                    if st.button("Cancelar"):
                        st.info("Envío cancelado. Podés editar la solicitud.")

# Buscador tab
with tabs[1]:
    st.header("Buscador inteligente")
    q = st.text_input("Buscar por descripción o palabra clave")
    proveedor_filter = st.text_input("Filtrar por proveedor (opcional)")
    if st.button("Buscar"):
        df = df_from_query("SELECT codigo, descripcion, precio, proveedor, creado_en FROM productos")
        if df.empty:
            st.info("No hay productos cargados aún.")
        else:
            if proveedor_filter.strip():
                df = df[df['proveedor'].str.contains(proveedor_filter, case=False, na=False)]
            if q.strip():
                corpus = df['descripcion'].astype(str).tolist() + [q]
                vectorizer = TfidfVectorizer().fit_transform(corpus)
                sims = linear_kernel(vectorizer[-1], vectorizer[:-1]).flatten()
                df['score'] = sims
                df = df.sort_values(by='score', ascending=False)
                st.dataframe(df[['codigo','descripcion','precio','proveedor','creado_en','score']].head(50))
            else:
                st.dataframe(df.sort_values(by='creado_en', ascending=False).head(100))

# Admin tab
with tabs[2]:
    st.header("Panel administrador")
    if not st.session_state['logged_in'] or st.session_state['role']!='admin':
        st.warning("Iniciá sesión como admin para acceder a este panel.")
    else:
        st.subheader("Configuración")
        settings = df_from_query("SELECT value FROM settings WHERE key='tolerancia_precio_pct'")
        tol = float(settings.iloc[0,0]) if not settings.empty else 0.02
        new_tol = st.number_input("Tolerancia (ej. 0.02 = 2%)", min_value=0.0, max_value=1.0, value=float(tol), step=0.005, format="%.3f")
        if st.button("Guardar tolerancia"):
            run_query("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", ('tolerancia_precio_pct', str(new_tol)))
            st.success("Tolerancia guardada.")
            st.rerun()
            
        st.subheader("Usuarios")
        st.write(f"Vendedores actuales: {count_vendedores()} / {MAX_VENDEDORES}")
        new_u = st.text_input("Usuario nuevo", key="nu")
        new_p = st.text_input("Contraseña inicial", type="password", key="np")
        if st.button("Crear vendedor"):
            if new_u.strip() and new_p.strip():
                ok,msg = register_user(new_u.strip(), new_p.strip(), role='vendedor')
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
            else:
                st.error("Completá usuario y contraseña.")
        st.subheader("Solicitudes pendientes")
        reqs = df_from_query("SELECT id, descripcion, precio_ingresado, proveedor, vendedor, creado_en FROM solicitudes WHERE estado='Pendiente' ORDER BY creado_en DESC")
        if reqs.empty:
            st.info("No hay solicitudes pendientes.")
        else:
            for _, r in reqs.iterrows():
                st.write('---')
                st.write(f"ID: {r['id']} — Vendedor: {r['vendedor']} — Creada: {r['creado_en'][:19]}")
                st.write(f"Descripción: {r['descripcion']}")
                st.write(f"Precio: ₡{r['precio_ingresado']:.2f} — Proveedor: {r['proveedor']}")
                ca,cb = st.columns([1,1])
                with ca:
                    if st.button(f"Aprobar {r['id']}", key=f"ap{r['id']}"):
                        code = st.text_input(f"Número de código para {r['id']}", key=f"code{r['id']}")
                        if code:
                            run_query("UPDATE solicitudes SET estado='Aprobada', aprobado_por=?, aprobado_en=?, codigo_asignado=? WHERE id=?", (st.session_state['username'], datetime.now().isoformat(), code, r['id']))
                            run_query("INSERT INTO productos (codigo, descripcion, precio, impuesto, proveedor, creado_por, creado_en) VALUES (?,?,?,?,?,?,?)", (code, r['descripcion'], r['precio_ingresado'], 13.0, r['proveedor'], r['vendedor'], datetime.now().isoformat()))
                            push_notification(r['vendedor'], f" Tu código {code} fue aprobado.")
                            st.success("Solicitud aprobada y código creado.")
                            st.rerun()

                        else:
                            st.warning("Ingresá el número de código.")
                with cb:
                    if st.button(f"Rechazar {r['id']}", key=f"rej{r['id']}"):
                        reason = st.text_area(f"Motivo rechazo {r['id']}", key=f"reason{r['id']}")
                        if reason:
                            run_query("UPDATE solicitudes SET estado='Rechazada' WHERE id=?", (r['id'],))
                            push_notification(r['vendedor'], f" Tu solicitud {r['id']} fue rechazada. Motivo: {reason}")
                            st.success("Solicitud rechazada.")
                            st.rerun()

                        else:
                            st.warning("Escribí motivo.")

# Export tab
with tabs[3]:
    st.header("Exportar códigos")
    dfp = df_from_query("SELECT codigo, descripcion, precio, impuesto, proveedor, creado_por, creado_en FROM productos")
    if dfp.empty:
        st.info("No hay productos cargados.")
    else:
        buf = io.StringIO()
        dfp.to_csv(buf, index=False)
        st.download_button("Descargar CSV", buf.getvalue(), file_name="productos_IA_Multisuministros.csv", mime="text/csv")
        st.dataframe(dfp.head(50))

st.markdown("---")
st.markdown("Prototipo — IA Multisuministros de Costa Rica — Para producción: migrar DB a servidor y habilitar HTTPS.")
