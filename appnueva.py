# app.py — DIMEX Dashboard (Ultra UI Edition)
# -------------------------------------------------------
# Requisitos base:
#   pip install streamlit pandas numpy plotly scikit-learn
# Extras opcionales recomendados (gráficos y animaciones):
#   pip install streamlit-lottie pillow
#
# Nota: Sin API ni chatbot. Mantiene la paleta verde DIMEX.

# ==== IMPORTS ==========================================================
import streamlit as st 
import textwrap                  # Framework de UI web rápida en Python
import pandas as pd                      # Manejo de datos tabulares
import numpy as np                       # Utilidades numéricas
import plotly.express as px              # Gráficas de alto nivel
import plotly.graph_objects as go        # Gráficas/objetos de bajo nivel (gauge, etc.)
from pathlib import Path                 # Manejo de rutas cross-OS
import json                              # (reservado) leer/guardar JSON
import io                                # (reservado) buffers en memoria
import base64                            # Para exportar CSV embebido como data URI
from datetime import datetime 
from streamlit_shadcn_ui import card, button
from dotenv import load_dotenv
import os
from openai import OpenAI
import google.generativeai as genai
import base64
import plotly.graph_objects as go


def load_base64_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()
avatar = load_base64_image("dimi_avatar.png")

import base64

def get_base64_image(path):
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# ===== SISTEMA DE LOGIN SIMPLE =====
# ========== LOGIN DE DIMEX (GLASS + AESTHETIC) ==========

import streamlit as st

USERS = {
    "ceo": {"password": "ceo", "rol": "CEO"},
    "director": {"password": "director", "rol": "Director"},
    "ejecutivo": {"password": "ejecutivo", "rol": "Ejecutivo"},
}

PERMISOS = {
    "CEO": ["full"],
    "Director": ["kpis", "mapa", "ranking", "alertas"],
    "Ejecutivo": ["kpis", "alertas", "tabla"],
}

if "auth" not in st.session_state:
    st.session_state.auth = False
    st.session_state.rol = None


def login_screen():
    st.markdown("""
    <style>

    body {
        background: linear-gradient(135deg,#10B98120,#05966920);
        animation: fadeIn 1s ease-in-out;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px);}
        to { opacity: 1; transform: translateY(0);}
    }


    @keyframes slideUp {
        from { opacity: 0; transform: translateY(25px);}
        to { opacity: 1; transform: translateY(0);}
    }

    .login-title {
        text-align: center;
        font-size: 28px;
        font-weight: 700;
        color: #065f46;
        margin-bottom: 10px;
    }

    .login-sub {
        text-align: center;
        font-size: 14px;
        color: #0f172a;
        opacity: 0.75;
        margin-bottom: 25px;
    }

    </style>
    """, unsafe_allow_html=True)

    logo_base64 = get_base64_image("dimi_principal.png")

    st.markdown(f"""
    <div class='login-card'>

    <div style="text-align:center; margin-bottom:1px;">
        <img src="data:image/png;base64,{logo_base64}" width="400">
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='login-title'>Acceso</div>", unsafe_allow_html=True)
    st.markdown("<div class='login-sub'>Panel ejecutivo de riesgo y colocación</div>", unsafe_allow_html=True)

    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Iniciar sesión", use_container_width=True):
        if user in USERS and USERS[user]["password"] == password:
            st.session_state.auth = True
            st.session_state.rol = USERS[user]["rol"]
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")

    st.markdown("</div>", unsafe_allow_html=True)


# BLOQUEO
if not st.session_state.auth:
    login_screen()
    st.stop()

rol = st.session_state.rol
permisos_usuario = PERMISOS[rol]







# ==== CARGA DE VARIABLES DE ENTORNO / CLIENTE OPENAI ==================

# Limpia cualquier variable global de Windows que interfiera
if "OPENAI_API_KEY" in os.environ:
    del os.environ["OPENAI_API_KEY"]

# Cargar .env (forzar a machacar cualquier otra key)
load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    client = None  # Para evitar crasheos si no hay key



# PRIMER INTENTO: modelo estable 1.0

# ==== INTENTAR CARGAR EXTRAS (LOTTIE) =================================
try:
    from streamlit_lottie import st_lottie  # Librería para animaciones Lottie
    LOTTI_AVAILABLE = True                   # Flag: hay lottie disponible
except Exception:
    LOTTI_AVAILABLE = False                  # Si falla la importación, lo dejamos apagado

# ==== INTENTAR CARGAR SCIKIT-LEARN ====================================
try:
    from sklearn.tree import DecisionTreeClassifier  # Árbol para drivers de riesgo
    SKLEARN_AVAILABLE = True                         # Flag: sklearn disponible
except ImportError:
    SKLEARN_AVAILABLE = False                        # Si no está instalado, desactivar drivers

# -------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA (título, layout, sidebar)
# -------------------------------------------------------------------
st.set_page_config(
    page_title="DIMEX | Dashboard de Riesgo Sucursales",  # Título de la pestaña
    layout="wide",                                        # Ancho completo
    initial_sidebar_state="collapsed"                     # Sidebar cerrada por defecto
)

# -------------------------------------------------------------------
# PALETA / THEME (colores corporativos y escalas)
# -------------------------------------------------------------------
DIMEX_GREEN = "#059669"
DIMEX_GREEN_LIGHT = "#10B981"
DIMEX_GREEN_DARK = "#047857"

DIMEX_TEAL = "#0d9488"
DIMEX_BLUE_GRAY = "#64748b"
DIMEX_SOFT_GRAY = "#e2e8f0"
DIMEX_BG = "#f9fafb"

COLOR_CLUSTER_1 = "#10B981"   # verde desarrollo
COLOR_CLUSTER_2 = "#3b82f6"   # azul estrella
COLOR_CLUSTER_3 = "#ef4444"   # rojo riesgo
 # Escala riesgo (verde-amarillo-rojo)

# -------------------------------------------------------------------
# ESTILOS GLOBALES + ANIMACIONES (inyecta CSS en la página)
# -------------------------------------------------------------------

def pretty_layout(fig):
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(
            family="Segoe UI, sans-serif",
            color="#0f172a",
            size=13
        ),
        margin=dict(l=40, r=40, t=60, b=40),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Segoe UI"
        ),
        transition_duration=300
    )
    return fig

def inject_global_styles():
    # Usamos st.markdown con unsafe_allow_html para insertar <style> global
    st.markdown("""
        <style>
        /* Estado base (con transición suave) */
        .kpi {
            transition: transform 0.25s cubic-bezier(.22,.61,.36,1),
                        box-shadow 0.25s cubic-bezier(.22,.61,.36,1);
            transform-origin: center;
        }

        /* Hover tipo lupa (zoom suave) */
        .kpi:hover {
            transform: scale(1.05) translateY(-2px);
            box-shadow:
                0 20px 40px rgba(5,150,105,0.25),
                0 0 16px rgba(16,185,129,0.35);
        }
                /* Hover suave para el chip de salud */
        .health-chip {
            transition: transform 0.25s cubic-bezier(.22,.61,.36,1),
                        box-shadow 0.25s cubic-bezier(.22,.61,.36,1);
        }

        .stTabs [data-baseweb="tab-list"] {
        flex-wrap: wrap !important;
        row-gap: 10px;
        }
        
                
        .health-chip:hover {
            transform: scale(1.05) translateY(-1px);
            box-shadow:
                0 14px 28px rgba(16,185,129,0.25),
                0 0 12px rgba(5,150,105,0.35);
        }
        .hoverable {
        transition: transform 0.25s cubic-bezier(.22,.61,.36,1),
                        box-shadow 0.25s cubic-bezier(.22,.61,.36,1);
        }
        .hoverable:hover {
            transform: scale(1.05) translateY(-2px);
            box-shadow:
                0 20px 40px rgba(5,150,105,0.25),
                0 0 16px rgba(16,185,129,0.35);
        }

        </style>
            
        
    
                

    <style>
        /* ===== TÍTULOS DE SECCIÓN DIMEX UI ===== */

        .section-title {
            font-family: 'Inter', 'Segoe UI', system-ui, sans-serif !important;
            font-size: 22px !important;
            font-weight: 600 !important;
            color: #0f172a !important;
            text-align: center !important;
            padding-bottom: 6px !important;
            margin-top: 6px !important;
            margin-bottom: 14px !important;
            letter-spacing: -0.3px;
        }

        /* Para títulos h3, h4, h5 nativos de Streamlit */
        h3, h4, h5 {
            font-family: 'Inter', 'Segoe UI', system-ui, sans-serif !important;
            text-align: center !important;
            font-weight: 600 !important;
            color: #0f172a !important;
        }
    </style>

    <style>

        /* ============================================
       OCULTAR TODO EL CHAT-INPUT PERO DEJAR SU ESPACIO
       ============================================ */

        /* El contenedor completo sigue ocupando lugar, pero no se ve */
        .stChatInputContainer {
        visibility: hidden !important;
        height: 5px !important;        /* ← ajusta este valor a tu gusto */
        padding: 0 !important;
        margin: 0 auto !important;
        }

        /* El textarea dentro también se oculta */
        .stChatInputContainer textarea {
        visibility: hidden !important;
        }

        /* Quita bordes/sombras (aunque no se vean) */
        .stChatInputContainer div {
        box-shadow: none !important;
        border: none !important;
        background: transparent !important;
        }

    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        f"""
        <style>
            /* Tipografía tipo Creative Point */
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap');
            html, body, [class*="css"] {{
             font-family: "Poppins", system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
                }}

                /* Cards shadcn suavizadas */
                .scui-card, .scui-card * {{
                border-radius: 10px !important;
                }}
                .scui-card{{
                box-shadow: 0 12px 28px rgba(5,150,105,.12) !important;
                border: 1px solid rgba(5,150,105,.12) !important;
                }}

                /* Botones shadcn */
                .scui-button{{
             border-radius: 12px !important;
                box-shadow: 0 10px 22px rgba(5,150,105,.20) !important;
                }}

        /* --- Variables CSS a partir de la nueva paleta DIMEX --- */
        :root {{
            --dimex-green: #059669;          /* Verde principal DIMEX */
            --dimex-green-soft: #10B981;     /* Verde claro, acentos suaves */
            --dimex-green-dark: #047857;     /* Verde oscuro corporativo */
            
            --dimex-teal: #0d9488;           /* Teal premium */
            --dimex-blue-gray: #64748b;      /* Azul gris profesional */
            --dimex-gray-soft: #e2e8f0;      /* Gris claro para bordes y backgrounds */
            --dimex-bg: #f9fafb;             /* Fondo suave limpio */

            /* Riesgo, éxito, advertencias — por si los usas en gauges */
            --risk: #dc2626;                 /* Rojo riesgo */
            --ok: #10B981;                   /* Verde éxito */
            --warn: #f59e0b;                 /* Amarillo advertencia */

            --ink: #0f172a;                  /* Color de texto principal (azul noche) */
        }}


        /* --- Layout base del contenedor central de Streamlit --- */
        .block-container {{
            padding-top: 0.6rem;             /* margen arriba para respirar */
            padding-bottom: 1.2rem;          /* margen abajo */
            max-width: 1300px !important;    /* limita ancho máximo */
        }}

       
                    /* === Tabs container centrado === */
            .stTabs [data-baseweb="tab-list"] {{
                justify-content: center !important;
                gap: 32px !important;            /* Más separación */
            }}

            /* === Tabs estilo pill grande === */
            .stTabs [data-baseweb="tab"] {{
                padding: 12px 26px !important;   /* MÁS grande */
                border-radius: 999px !important;

                background: rgba(16,185,129,0.07) !important;
                border: 1px solid rgba(16,185,129,0.22) !important;

                font-size: 40px !important;       /* ← AUMENTA FUENTE */
                font-weight: 600 !important;
                color: #0f172a !important;

                display: flex;
                align-items: center;
                gap: 10px;                        /* Espacio icono-texto */

                transition: all .22s ease;
            }}

            /* Hover premium */
            .stTabs [data-baseweb="tab"]:hover {{
                background: rgba(16,185,129,0.12) !important;
                transform: translateY(-2px) scale(1.02);
                box-shadow: 0 8px 20px rgba(16,185,129,0.20);
            }}

            /* === TAB ACTIVO === */
            .stTabs [data-baseweb="tab"][aria-selected="true"] {{
                background: linear-gradient(180deg,#059669,#10b981) !important;
                color: white !important;
                border: none !important;
                box-shadow: 0 10px 28px rgba(16,185,129,0.35);

                font-size: 17px !important;      /* Más grande el activo */
                padding: 14px 30px !important;
            }}

            /* Íconos dentro del tab */
            .stTabs [data-baseweb="tab"] svg {{
                width: 20px !important;          /* Aumenta tamaño icono */
                height: 20px !important;
            }}


            /* Hover suave */
            .stTabs [data-baseweb="tab"]:hover{{
                background: rgba(16,185,129,0.12) !important;
                transform: translateY(-1px);
                box-shadow: 0 6px 16px rgba(16,185,129,0.15);
            }}

            /* Tab ACTIVO */
            .stTabs [data-baseweb="tab"][aria-selected="true"]{{
                background: linear-gradient(180deg,#059669,#10b981) !important;
                color: white !important;
                border: none !important;
                box-shadow: 0 8px 18px rgba(16,185,129,0.30);
            }}


       

        /* --- Tarjetas KPI --- */
        .kpi {{
            border-radius: 14px;
            border: 1px solid rgba(226,232,240,0.9);
            background: linear-gradient(180deg, rgba(236,253,245,0.95), rgba(240,253,244,0.7));
            box-shadow: 0 2px 8px rgba(16,185,129,0.12);
            padding: 12px 14px;
        }}

        /* --- Barra de salud (llenado animado) --- */
        @keyframes fillWidth {{
            0% {{ width: 0%; }}
            100% {{ width: var(--health-width, 0%); }}
        }}
        .health-bar {{
            height: 10px;
            border-radius: 999px;
            background: #d1fae5;
            overflow: hidden;
            position: relative;
        }}
        .health-bar > span {{
            display: block;
            height: 100%;
            background: linear-gradient(90deg, var(--dimex-green), #34d399);
            animation: fillWidth 1s ease forwards;  /* animación de entrada */
            box-shadow: inset 0 0 8px rgba(255,255,255,0.8);
        }}

        /* --- Botón DIMEX genérico --- */
        -        /* === BOTONES NATIVOS DIMEX (st.button, st.download_button, etc.) === */

        .stButton > button,
        .stDownloadButton > button {{
            border-radius: 999px !important;                     /* pill */
            border: 1px solid rgba(148,163,184,0.55) !important;
            background: #ffffff !important;
            padding: 9px 22px !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            color: #0f172a !important;
            box-shadow: 0 4px 14px rgba(15,23,42,0.08) !important;
            transition: transform .14s ease,
                        box-shadow .18s ease,
                        background .18s ease,
                        border-color .18s ease,
                        color .18s ease !important;
        }}

        .stButton > button:hover,
        .stDownloadButton > button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 12px 26px rgba(16,185,129,0.30) !important;
            border-color: rgba(16,185,129,0.85) !important;
            background: linear-gradient(90deg,#ecfdf5,#f0fdfa) !important;
            color: #064e3b !important;
        }}

        .stButton > button:active,
        .stDownloadButton > button:active {{
            transform: translateY(0px) scale(.98);
            box-shadow: 0 6px 18px rgba(16,185,129,0.25) !important;
        }}


        /* --- Botones flotantes (FAB) --- */
        .fab-wrap {{
            position: fixed;
            right: 22px;
            bottom: 22px;
            z-index: 1000;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .fab {{
            width: 54px; height: 54px;
            border-radius: 999px;
            background: radial-gradient(circle at 30% 20%, #34d399, var(--dimex-green));
            display: grid; place-items: center;
            color: white; font-weight: 800;
            border: 1px solid rgba(16,185,129,0.6);
            box-shadow: 0 10px 28px rgba(16,185,129,0.38);
            cursor: pointer;
            transition: transform .15s ease, box-shadow .15s ease, filter .2s ease;
            user-select: none;
        }}
        .fab:hover {{
            transform: translateY(-2px) scale(1.03);
            box-shadow: 0 16px 36px rgba(16,185,129,0.45);
            filter: saturate(1.08);
        }}

        /* --- Badges suaves de aviso --- */
        .badge-soft {{
            display:inline-block;padding:4px 8px;border-radius:999px;
            background:rgba(254,249,195,0.9);border:1px solid #fde68a;color:#92400e;
            font-size:12px;
        }}

        /* --- Header sticky (cinta superior) --- */
        .dimex-header {{
            position: sticky; top: 0;
            z-index: 500;
            backdrop-filter: blur(8px);
            background: linear-gradient(90deg, rgba(255,255,255,0.85), rgba(255,255,255,0.6));
            border-bottom: 1px solid rgba(148,163,184,0.25);
            margin-bottom: .4rem;
        }}

        /* --- Espaciador para que el sticky no tape contenido --- */
        .top-spacer {{ height: 6px; }}

        /* --- DataFrame con bordes redondeados --- */
        .stDataFrame {{ border-radius: 12px; overflow: hidden; }}

        </style>
        """,
        unsafe_allow_html=True  # Permitimos HTML/CSS crudo
    )
    st.markdown("""
<style>
    /* 🔧 Forzar estilo limpio en el árbol predictor */
    .arbol-html-card * {
        font-family: "Poppins", system-ui, sans-serif !important;
        white-space: normal !important;
        overflow-wrap: break-word !important;
        font-size: 13px !important;
        color: #111827 !important;
    }

    .arbol-html-card {
        background: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
</style>
""", unsafe_allow_html=True)


# Inyectar los estilos al arrancar
inject_global_styles()

# -------------------------------------------------------------------
# CONSTANTES DE COLUMNAS (nombres que vienen en tu Excel)
# -------------------------------------------------------------------
COL_SUCURSAL     = "Región"                           # Nombre de columna de región/sucursal
COL_SALDO        = "Saldo Insoluto Actual"            # Saldo total actual
COL_SALDO_VENC   = "Saldo Insoluto Vencido Actual"    # Saldo vencido
COL_SALDO_VIG    = "Saldo Insoluto Vigente Actual"    # Saldo vigente
COL_COLOCACION   = "Colocación promedio mensual"      # Colocación mensual promedio
COL_ICV          = "ICV"                               # Índice de calidad de venta
COL_MORA         = "Mora Temprana"                     # Proporción de mora temprana
COL_PERDIDAS     = "Pérdidas Tempranas"                # Pérdidas
COL_RECUP        = "Tasa de recuperación Actual"       # Recuperación
COL_FPD          = "FPD"                               # First Payment Default
COL_MARGEN_NETO  = "Margen Financiero Neto Actual"     # Margen financiero
COL_SCORE_RAW    = "Score_Final_S10"                   # Score bruto del modelo
COL_CLUSTER      = "Cluster_Final_S10"                 # Cluster final

# Ruta local al archivo de datos (ajústala a tu archivo)
DATA_PATH = Path(r"Reto_final_limpio_estesi_con_clusters_S10.xlsx")

# -------------------------------------------------------------------
# ESTADO DE CHAT DE DIMI (en memoria de sesión)
# -------------------------------------------------------------------
if "dimi_history" not in st.session_state:
    st.session_state["dimi_history"] = []  # lista de mensajes [{role, content}]
# -------------------------------------------------------------------
# IA DIMI: conecta filtros actuales con modelo de OpenAI
# -------------------------------------------------------------------
def dimi_answer(user_msg: str, df_context: pd.DataFrame) -> str:
    """DIMI nivel analista senior, con contexto completo y comparaciones globales."""

    if client is None:
        msg = "No hay API KEY configurada."
        st.session_state["dimi_history"].append({"role": "assistant", "content": msg})
        return msg

    # === SUMMARY DEL FILTRO ACTUAL ===========================================
    resumen_segmento = {
        "num_sucursales": int(len(df_context)),
        "colocacion_total": float(df_context[COL_COLOCACION].sum()),
        "mora_prom": float(df_context[COL_MORA].mean()),
        "recuperacion_prom": float(df_context[COL_RECUP].mean()),
        "fpd_prom": float(df_context[COL_FPD].mean()),
        "risk_prom": float(df_context["Risk_Score"].mean()),
        "margen_neto_total": float(df_context[COL_MARGEN_NETO].sum()),
    }

    # === SUMMARY GLOBAL POR CLUSTER ==========================================
    cluster_stats = (
        df_full.groupby(COL_CLUSTER)
        .agg(
            num_suc=(COL_SUCURSAL, "count"),
            colocacion=(COL_COLOCACION, "sum"),
            mora=(COL_MORA, "mean"),
            recup=(COL_RECUP, "mean"),
            fpd=(COL_FPD, "mean"),
            risk=("Risk_Score", "mean"),
        )
        .reset_index()
        .to_dict(orient="records")
    )

    # === PERCENTILES GLOBALES ================================================
    percentiles = {
        "mora_p75": float(df_full[COL_MORA].quantile(0.75)),
        "recup_p25": float(df_full[COL_RECUP].quantile(0.25)),
        "risk_p75": float(df_full["Risk_Score"].quantile(0.75)),
        "risk_p25": float(df_full["Risk_Score"].quantile(0.25)),
    }

    # === TOP SUCURSALES GLOBAL ===============================================
    top_sucursales_global = (
        df_full.sort_values("Risk_Score", ascending=False)
        .head(10)[[COL_SUCURSAL, "Risk_Score", COL_MORA, COL_RECUP, COL_FPD]]
        .to_dict(orient="records")
    )

    # === PROMPT NIVEL ANALISTA SENIOR ========================================
    system_prompt = f"""
        🧠 Identidad del agente
        Eres DIMI, analista senior de riesgo de DIMEX, especializado en portafolios de crédito a jubilados y pensionados. Tu rol es explicar, interpretar y detectar riesgos en el portafolio según los datos que recibe de Streamlit (df filtrado).
        Tu tono es siempre:
        Ejecutivo
        Claro
        Directo
        Narrativo
        Con enfoque para toma de decisiones
        Nunca eres técnico solo por ser técnico: traduces datos a acciones.
        📊 Diccionario maestro de variables (con significado)
        Estas son TODAS las columnas del dataset, con lo que significan en contexto DIMEX:
        1. Identificación
        Región → Nombre de la sucursal/región de operación.
        2. Saldos y cartera
        Saldo Insoluto Actual → Saldo total vigente + vencido del portafolio activo.
        Saldo Insoluto Vencido Actual → Saldo en mora (clientes con retraso).
        Saldo Insoluto Vigente Actual → Saldo sano (al corriente).
        3. Flujo y rentabilidad
        Capital Dispersado Actual → Capital otorgado en créditos activos.
        Interés Generado Actual → Intereses devengados.
        Servicio Deuda Actual → Pago esperado de clientes.
        Comisión Pagada Actual → Comisiones por originación.
        Margen Financiero Actual → Ingresos financieros directos.
        Margen Financiero Neto Actual → Ingresos menos costos asociados (indicador clave de rentabilidad).
        Tasa Efectiva Sucursal (Anual) → Tasa real a la que está rentando la sucursal.
        4. Castigos / saneamiento
        Quitas+Castigos Actual → Reducciones o castigos aplicados (indicador de deterioro).
        5. Versiones normalizadas
        (Usadas para modelaje y comparaciones)
        Capital Dispersado Actual_norm
        Saldo Insoluto Actual_norm
        Capital Dispersado Actual_log
        Saldo Insoluto Actual_log
        6. Ratios
        Ratio_Dispersion → (Capital dispersado) / (Saldo insoluto). Mide dinámica de colocación vs cartera.
        7. KPIs operativos
        Colocación promedio mensual → Ventas mensuales promedio por sucursal.
        Mora Temprana → Proporción de clientes con atraso 1–30 días (indicador clave de calidad).
        Pérdidas Tempranas → Créditos tempranamente perdidos / castigados.
        Tasa de recuperación Actual → Proporción recuperada sobre cartera vencida.
        FPD → First Payment Default: % de clientes que fallan en el primer pago.
        ICV → Índice de calidad de la venta (riesgo de originación).
        8. Rangos categóricos (bajo/medio/alto)
        Para cada KPI existe una versión:
        Rango_X
        Rango_X_Bajo
        Rango_X_Medio
        Rango_X_Alto
        Indican terciles o clusters operativos.
        9. Score y clúster
        Score_Final_S10 → Score numérico del modelo de riesgo.
        Cluster_Final_S10 → Segmentación Inteligente por riesgo:
        Estrella / Desarrollo / Excelente / Riesgo / Medio / Regular / Alto / Bajo (según dataset).
        🔎 Cómo debe razonar DIMI
        Cuando el usuario pregunte, DIMI:
        1) Siempre analiza sobre el df filtrado
        El df filtrado viene de Streamlit, ya acotado por cluster, sucursal, o filtros rápidos.
        2) Siempre compara el segmento filtrado vs. el universo completo
        (Si el usuario me manda también el resumen global).
        3) Siempre contextualiza si un KPI es:
        alto
        bajo
        crítico
        normal
        fuera de tendencia
        arriba/abajo de p75/p25
        4) Convierte datos a narrativa ejecutiva
        Ejemplo: “No solo está alta la mora. El 28% del portafolio filtrado supera el percentil 75 de la red, lo cual indica un deterioro acelerado en originación y cobranza”.
        5) Detecta focos rojos
        Mora Temprana ↑
        Recuperación ↓
        FPD ↑
        Margen ↓
        Clusters de Riesgo Alto ↑
        Castigos ↑
        6) Sugiere acciones operativas REALES
        Auditorías a sucursales específicas
        Ajustes de originación
        Reforzar cobranza
        Identificar sesgos de venta
        Revisar ICV
        Revisar prácticas de sucursales “joya”
        📘 Cómo debe responder DIMI en cada modo
        🟩 Modo explicación simple
        Lenguaje fácil
        Sin tecnicismos
        Storytelling simple
        🟧 Modo análisis ejecutivo
        Explica tendencias
        Resume riesgos por nivel
        Relaciona KPIs entre sí
        Recomienda acciones
        🟥 Modo comité / reporte
        Formato:
        Contexto
        Hallazgos
        Comparativo Red
        Riesgos
        Oportunidades
        Recomendaciones
        Conclusión ejecutiva
        ❌ Cosas que JAMÁS debe hacer
        Inventar valores que no están en el df.
        Asumir clusters que no existen.
        Modificar definiciones de KPIs.
        Hallazgos que contradicen datos.
        Repetir texto sin análisis.
        🧮 Reglas analíticas internas del agente
        Usa estos criterios:
        Riesgo (Risk_Score)
        <33 — bajo
        33–66 — moderado
        66 — alto
        Mora temprana
        p75 → alerta
        50–75 → monitoreo
        < p25 → bueno
        Recuperación
        < p25 → crítica
        25–50 → débil
        p75 → sobresaliente
        FPD
        10% → foco rojo
        5–10% → seguir monitoreando
        < 5% → sano
        ICV
        Bajo → mala originación
        Medio → control
        Alto → buena colocación con calidad
        📈 Patrones y relaciones que DIMI conoce
        Mora ↑ + Recuperación ↓ → Distrito crítico
        Mora ↑ + FPD ↑ → originación deficiente
        Margen Neto ↓ + Riesgo ↑ → cartera costosa y deteriorada
        Colocación ↑ + ICV bajo → crecimiento tóxico
        FPD ↑ solo → mal score de originación
        Recup ↑ + Mora ↑ → cobranza reactiva, no preventiva
        Clusters de riesgo alto ↑ → casos prioritarios
        🧩 Formato para responder preguntas técnicas
        Si piden:
        cálculo de KPI → devuelve fórmula en pandas
        cómo graficar → devuelve snippet
        cómo segmentar → explica reglas
        cómo interpretar clusters → expone cada uno
        🎯 Objetivo central del agente
        Ayudar a DIMEX a:
        entender cartera
        detectar riesgos
        priorizar sucursales
        explicar por qué
        proponer acciones aterrizadas
        generar insights para comité
        Tu misión final: Traducir datos en decisiones.

AQUÍ ESTÁ TU CONTEXTO:

SEGMENTO FILTRADO:
{json.dumps(resumen_segmento, ensure_ascii=False)}

CLUSTERS GLOBALES:
{json.dumps(cluster_stats, ensure_ascii=False)}

PERCENTILES GLOBALES:
{json.dumps(percentiles, ensure_ascii=False)}

TOP SUCURSALES GLOBAL:
{json.dumps(top_sucursales_global, ensure_ascii=False)}
"""

    # === MENSAJES ============================================================
    messages = [{"role": "system", "content": system_prompt}]
    messages += st.session_state["dimi_history"]
    messages.append({"role": "user", "content": user_msg})

    # === LLAMADA AL MODELO ===================================================
    response = client.chat.completions.create(
        model="gpt-4.1-nano",  # o gpt-5-nano (sin temperature)
        messages=messages,
        temperature=0.2,
    )

    answer = response.choices[0].message.content

    # Guarda historial
    st.session_state["dimi_history"].append({"role": "user", "content": user_msg})
    st.session_state["dimi_history"].append({"role": "assistant", "content": answer})

    return answer

# -------------------------------------------------------------------
# CARGA Y PREPARACIÓN DE DATOS (lee Excel, valida y crea métricas)
# -------------------------------------------------------------------
@st.cache_data
def load_data(path: Path):
    if not path.exists():                                   # Si no existe el archivo...
        st.error(f"No se encontró el archivo en la ruta: {path}")  # Mensaje de error
        st.stop()                                           # Detiene la app

    df = pd.read_excel(path)                                # Carga el Excel en DataFrame

    # Columnas requeridas para que todo funcione
    required = [
        COL_SUCURSAL, COL_SALDO, COL_SALDO_VENC, COL_SALDO_VIG,
        COL_COLOCACION, COL_ICV, COL_MORA, COL_PERDIDAS,
        COL_RECUP, COL_FPD, COL_MARGEN_NETO, COL_SCORE_RAW, COL_CLUSTER
    ]
    missing = [c for c in required if c not in df.columns]  # Detecta faltantes
    if missing:
        st.error(f"Faltan columnas requeridas en el Excel: {missing}")  # Avisa cuáles
        st.stop()

    # Forzar tipos numéricos (coerce pone NaN si no se puede convertir)
    numeric_cols = [
        COL_SALDO, COL_SALDO_VENC, COL_SALDO_VIG,
        COL_COLOCACION, COL_ICV, COL_MORA, COL_PERDIDAS,
        COL_RECUP, COL_FPD, COL_MARGEN_NETO, COL_SCORE_RAW
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Elimina filas con NaN críticos que romperían la vista
    df.dropna(
        subset=[COL_SUCURSAL, COL_SALDO, COL_COLOCACION, COL_ICV,
                COL_MORA, COL_RECUP, COL_FPD, COL_SCORE_RAW, COL_CLUSTER],
        inplace=True
    )

    # Normaliza Score_Final_S10 a 0–100 como Health_Index y define Risk_Score inverso
    score_min = df[COL_SCORE_RAW].min()
    score_max = df[COL_SCORE_RAW].max()
    if score_max == score_min:
        df["Health_Index"] = 50.0                          # Caso degenerado: valor fijo
    else:
        df["Health_Index"] = (df[COL_SCORE_RAW] - score_min) / (score_max - score_min) * 100.0
    df["Risk_Score"] = 100.0 - df["Health_Index"]         # Riesgo es inverso a salud

    # Asegura tipos string en claves categóricas
    df[COL_SUCURSAL] = df[COL_SUCURSAL].astype(str)
    df[COL_CLUSTER]  = df[COL_CLUSTER].astype(str)

    return df                                              # Devuelve DataFrame listo

# Carga única (cacheada) del dataset completo
df_full = load_data(DATA_PATH)

# -------------------------------------------------------------------
# FORMATOS Y HELPERS DE TEXTO
# -------------------------------------------------------------------
def get_risk_level(avg_risk):             # Traduce score promedio de riesgo a etiqueta y texto
    if avg_risk < 33:
        return "bajo", "El portafolio filtrado se encuentra en una zona de control, con riesgo bajo y buen desempeño general."
    if avg_risk < 66:
        return "moderado", "El portafolio filtrado muestra señales mixtas: algunas sucursales sanas conviven con focos de riesgo que conviene priorizar."
    return "alto", "El portafolio filtrado concentra una proporción relevante en sucursales de alto riesgo; se recomienda focalizar medidas inmediatas de cobranza."

def fmt_currency(v):                      # Formatea MXN sin decimales con separador de miles
    return f"${v:,.0f}" if pd.notnull(v) else "$0"

def fmt_percent(v):
    if pd.isnull(v):
        return "N/D"
    if v > 1.5:
        v = v / 100.0
    return f"{v*100:.1f}%"

def fmt_ratio(v):                         # Alias semántico (usa fmt_percent)
    return fmt_percent(v)

def get_cluster_color(cluster):           # Mapea texto del cluster a color de fondo
    text = str(cluster).lower()
    if "desarrollo" in text:
        return "#fef9c3"  # amarillo claro
    if "estrella" in text:
        return "#dcfce7"  # verde claro
    if any(w in text for w in ["riesgo", "alto"]):
        return "#fee2e2"
    if any(w in text for w in ["regular", "medio"]):
        return "#fef9c3"
    if any(w in text for w in ["excelente", "bueno", "bajo"]):
        return "#dcfce7"
    return "#e5e7eb"



# -------------------------------------------------------------------
# FILTRADO (aplica filtros seleccionados en UI)
# -------------------------------------------------------------------
@st.cache_data
def apply_filters(df, filters, quick):
    df_f = df.copy()                                      # Trabaja sobre copia
    if filters["cluster"] != "Todos":                     # Filtro por cluster
        df_f = df_f[df_f[COL_CLUSTER] == filters["cluster"]]
    if filters["sucursal"] != "Todas":                    # Filtro por sucursal
        df_f = df_f[df_f[COL_SUCURSAL] == filters["sucursal"]]
    if quick["alto_riesgo"]:                              # Filtro rápido: umbral de riesgo
        df_f = df_f[df_f["Risk_Score"] >= quick["umbral_riesgo"]]
    if quick["mora_alta"]:                                # Filtro rápido: mora > p75 global
        q_mora = df[COL_MORA].quantile(0.75)
        df_f = df_f[df_f[COL_MORA] >= q_mora]
    if quick["recup_baja"]:                               # Filtro rápido: recup < p25 global
        q_rec = df[COL_RECUP].quantile(0.25)
        df_f = df_f[df_f[COL_RECUP] <= q_rec]
    return df_f

# -------------------------------------------------------------------
# THEME PARA PLOTLY (estandariza altura, márgenes y fondos)
# -------------------------------------------------------------------
def apply_plotly_theme(fig, height=340):
    fig.update_layout(
        height=height,
        margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor="rgba(255,255,255,1)",    # blanco pleno para contraste limpio
        plot_bgcolor="rgba(255,255,255,0.98)",  # casi blanco, elegante
        font=dict(size=13, family="Poppins"),   # tipografía moderna
        legend=dict(
            borderwidth=0,
            bgcolor="rgba(255,255,255,0.0)"
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Poppins"
        )
    )

    fig.update_xaxes(showline=True, linewidth=1, linecolor='rgba(148,163,184,0.3)', mirror=True, zeroline=False)
    fig.update_yaxes(showline=True, linewidth=1, linecolor='rgba(148,163,184,0.3)', mirror=True, zeroline=False)

    return fig

# -------------------------------------------------------------------
# COMPONENTES VISUALES REUSABLES (cards, KPIs, gráficos)
# -------------------------------------------------------------------
def card_container(open_tag=True):                        # Abre/cierra un <div> con clase card
    if open_tag:
        st.markdown("<div class='dimex-card'>", unsafe_allow_html=True)
    else:
        st.markdown("</div>", unsafe_allow_html=True)


def rentabilidad_vs_riesgo(df):
    if df.empty:
        st.info("Sin datos.")
        return

    df2 = df.copy()

    fig = px.scatter(
        df2,
        x="Score_Final_S10",
        y="Margen Financiero Neto Actual",
        trendline="ols",
        color="Cluster_Final_S10",
        color_discrete_sequence=px.colors.qualitative.Set2,
        labels={
            "Score_Final_S10": "Riesgo",
            "Margen Financiero Neto Actual": "Margen Neto (MXN)"
        },
    )

    apply_plotly_theme(fig, 350)
    st.plotly_chart(fig, use_container_width=True, key="rr_line")


def top_sucursales_criticas(df):
    if df.empty:
        st.info("Sin datos.")
        return

    p75_risk = df["Risk_Score"].quantile(0.75)
    p25_margen = df[COL_MARGEN_NETO].quantile(0.25)

    crit = df[(df["Risk_Score"] >= p75_risk) &
              (df[COL_MARGEN_NETO] <= p25_margen)]

    if crit.empty:
        st.warning("No hay sucursales críticas según el criterio estadístico.")
        return

    crit = crit.sort_values("Risk_Score", ascending=False).head(15)

    fig = px.bar(
        crit,
        x="Risk_Score",
        y=COL_SUCURSAL,
        orientation="h",
        color="Risk_Score",
        color_continuous_scale="Reds",
        title="Top 15 Sucursales Críticas",
    )

    apply_plotly_theme(fig, 370)
    st.plotly_chart(fig, use_container_width=True, key="acciones_criticas")


def top_sucursales_potenciales(df):
    if df.empty:
        st.info("Sin datos.")
        return

    p30_risk = df["Risk_Score"].quantile(0.30)
    p70_margen = df[COL_MARGEN_NETO].quantile(0.70)

    pot = df[(df["Risk_Score"] <= p30_risk) &
             (df[COL_MARGEN_NETO] >= p70_margen)]

    if pot.empty:
        st.warning("No hay sucursales con alto potencial.")
        return

    pot = pot.sort_values(COL_MARGEN_NETO, ascending=False).head(15)

    fig = px.bar(
        pot,
        x=COL_MARGEN_NETO,
        y=COL_SUCURSAL,
        orientation="h",
        color="Risk_Score",
        color_continuous_scale="Greens",
        title="Top 15 Sucursales con Potencial",
    )

    apply_plotly_theme(fig, 370)
    st.plotly_chart(fig, use_container_width=True, key="acciones_potenciales")


def alertas_kpi(df):
    if df.empty:
        st.info("Sin datos para alertas.")
        return

    alertas = []

    # Mora
    mora_alta = df[df["Mora Temprana"] > df["Mora Temprana"].quantile(0.80)]
    if not mora_alta.empty:
        alertas.append(f"🔴 {len(mora_alta)} sucursales con *mora temprana crítica* (>p80).")

    # Recuperación
    baja_recup = df[df["Tasa de recuperación Actual"] < df["Tasa de recuperación Actual"].quantile(0.20)]
    if not baja_recup.empty:
        alertas.append(f"🟠 {len(baja_recup)} sucursales con *recuperación insuficiente* (<p20).")

    # FPD
    fpd_alto = df[df["FPD"] > df["FPD"].quantile(0.75)]
    if not fpd_alto.empty:
        alertas.append(f"🟡 {len(fpd_alto)} sucursales con *FPD elevado* (>p75).")

    if not alertas:
        st.success("Todo en orden. No se detectaron alertas principales.")
        return
    
    for a in alertas:
        st.markdown(f"**{a}**")



def render_tab_acciones_prioritarias(df):

    st.markdown("""
        <div style="display:flex; justify-content:center; margin-bottom:16px;">
            <span style="
                display:inline-block;
                background:rgba(220,38,38,0.10);
                padding:6px 16px;
                border-radius:10px;
                font-size:26px;
                font-weight:700;
                color:#b91c1c;
                border:1px solid rgba(220,38,38,0.20);
            ">
                Acciones Prioritarias
            </span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 🔥 Matriz de priorización (Riesgo × Rentabilidad)")
    matriz_priorizacion(df)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🔴 Top sucursales críticas")
        top_sucursales_criticas(df)

    with col2:
        st.markdown("### 🟢 Top sucursales con potencial")
        top_sucursales_potenciales(df)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    st.markdown("### ⚠️ Alertas automáticas del portafolio")
    alertas_kpi(df)


def matriz_priorizacion(df):
    if df.empty:
        st.info("Sin datos para matriz de priorización.")
        return

    risk_med = df["Risk_Score"].median()
    margen_med = df[COL_MARGEN_NETO].median()

    fig = px.scatter(
        df,
        x="Risk_Score",
        y=COL_MARGEN_NETO,
        color="Cluster_Final_S10",
        size=COL_COLOCACION,
        hover_name=COL_SUCURSAL,
        color_discrete_sequence=px.colors.qualitative.Set2,
        labels={
            "Risk_Score": "Riesgo",
            COL_MARGEN_NETO: "Margen Neto (MXN)"
        },
        title="Matriz de Prioridad",
    )

    fig.add_vline(x=risk_med, line_dash="dash", line_color="#475569")
    fig.add_hline(y=margen_med, line_dash="dash", line_color="#475569")

    apply_plotly_theme(fig, 420)
    st.plotly_chart(fig, use_container_width=True, key="acciones_matriz")



def margen_vs_volumen_cluster(df):
    if df.empty:
        st.info("Sin datos.")
        return

    grp = df.groupby("Cluster_Final_S10").agg({
        "Margen Financiero Neto Actual": "sum",
        "Saldo Insoluto Actual": "sum"
    }).reset_index()

    fig = px.bar(
        grp,
        x="Cluster_Final_S10",
        y="Margen Financiero Neto Actual",
        color="Saldo Insoluto Actual",
        text_auto=".2s",
        color_continuous_scale="Greens",
        title="Margen Neto por Cluster (color = Volumen)",
        labels={"Margen Financiero Neto Actual": "Margen Neto (MXN)"}
    )

    apply_plotly_theme(fig, 340)
    st.plotly_chart(fig, use_container_width=True, key="rr_bar_cluster")


def mora_vs_margen(df):
    if df.empty:
        st.info("No hay datos para calcular relación.")
        return

    fig = px.scatter(
        df,
        x="Mora Temprana",
        y="Margen Financiero Neto Actual",
        color="Cluster_Final_S10",
        trendline="ols",
        size="Saldo Insoluto Actual",
        color_discrete_sequence=px.colors.qualitative.Set2,
        labels={
            "Mora Temprana": "Mora (%)",
            "Margen Financiero Neto Actual": "Margen Neto (MXN)"
        },
        title="Relación Mora – Margen (Tradeoff calidad-ganancia)"
    )

    apply_plotly_theme(fig, 350)
    st.plotly_chart(fig, use_container_width=True, key="rr_mora_margen")



def render_tab_riesgo_rentabilidad(df):

    st.markdown("""
        <div style="display:flex; justify-content:center; margin-bottom:16px;">
            <span style="
                display:inline-block;
                background:rgba(16,185,129,0.10);
                padding:6px 16px;
                border-radius:10px;
                font-size:26px;
                font-weight:700;
                color:#047857;
                border:1px solid rgba(16,185,129,0.20);
            ">
                Riesgo & Rentabilidad
            </span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📈 Mapa de Riesgo vs Rentabilidad (Score vs Margen)")

    mapa_riesgo_rentabilidad(df)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 💰 Rentabilidad por Score de Riesgo")
        rentabilidad_vs_riesgo(df)

    with col2:
        st.markdown("### 🧮 Curva Margen / Volumen por Cluster")
        margen_vs_volumen_cluster(df)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    st.markdown("### 🧊 Relación Mora – Rentabilidad")
    mora_vs_margen(df)






def distribucion_riesgo1(df):
    if df.empty:
        st.info("No hay datos suficientes.")
        return

    fig = px.histogram(
        df,
        x="Risk_Score",
        nbins=22,
        opacity=0.9,
        color_discrete_sequence=[DIMEX_GREEN],
        marginal="violin"
    )

    fig.update_traces(
        marker_line_width=1,
        marker_line_color="rgba(0,0,0,0.15)",
        hovertemplate="Score: %{x}<br>Cantidad: %{y}<extra></extra>",
    )

    fig.update_layout(
        title=dict(
            text="",
            x=0.5,
            font=dict(size=20, color=DIMEX_GREEN_DARK)
        )
    )

    pretty_layout(fig)
    st.plotly_chart(fig, use_container_width=True, key=f"distribucion_riesgo1{hash(df.head().to_string())}")

def drivers_correlacion_heatmap(df):
    if df.empty:
        st.info("Sin datos para correlaciones.")
        return
    
    vars_interes = [
        "Mora Temprana", "Pérdidas Tempranas", "FPD",
        "Tasa de recuperación Actual", "ICV",
        "Margen Financiero Neto Actual", "Colocación promedio mensual",
        "Score_Final_S10"
    ]

    df_corr = df[vars_interes].corr()

    fig = px.imshow(
        df_corr,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="Greens",
        title="Correlación entre variables clave y Score de Riesgo"
    )

    apply_plotly_theme(fig, height=450)
    st.plotly_chart(fig, use_container_width=True, key="drivers_heatmap")


def drivers_por_cluster(df):
    if df.empty:
        st.info("Sin datos para drivers por cluster.")
        return

    vars_drivers = [
        "Mora Temprana",
        "Pérdidas Tempranas",
        "FPD",
        "Tasa de recuperación Actual",
    ]

    df_grp = df.groupby("Cluster_Final_S10")[vars_drivers].mean().reset_index()

    fig = px.bar(
        df_grp,
        x="Cluster_Final_S10",
        y=vars_drivers,
        barmode="group",
        color_discrete_sequence=px.colors.qualitative.Set2,
        title="Drivers promedio por cluster"
    )

    apply_plotly_theme(fig, height=420)
    st.plotly_chart(fig, use_container_width=True, key="drivers_cluster")


def curvas_deterioro(df):
    if df.empty:
        st.info("Sin datos para curvas de deterioro.")
        return

    fig = px.scatter(
        df,
        x="Score_Final_S10",
        y="Mora Temprana",
        trendline="ols",
        color="Cluster_Final_S10",
        labels={
            "Score_Final_S10": "Score de riesgo",
            "Mora Temprana": "Mora temprana (%)"
        },
        title="Relación entre Score de Riesgo y Mora Temprana"
    )

    apply_plotly_theme(fig, height=400)
    st.plotly_chart(fig, use_container_width=True, key="curva_mora")

    fig2 = px.scatter(
        df,
        x="Score_Final_S10",
        y="FPD",
        trendline="ols",
        color="Cluster_Final_S10",
        title="Relación entre Score y FPD"
    )

    apply_plotly_theme(fig2, height=400)
    st.plotly_chart(fig2, use_container_width=True, key="curva_fpd")

    fig3 = px.scatter(
        df,
        x="Score_Final_S10",
        y="Pérdidas Tempranas",
        trendline="ols",
        color="Cluster_Final_S10",
        title="Relación entre Score y Pérdidas Tempranas"
    )

    apply_plotly_theme(fig3, height=400)
    st.plotly_chart(fig3, use_container_width=True, key="curva_perdidas")

def mapa_riesgo_rentabilidad(df):
    if df.empty:
        st.info("No hay datos para el mapa riesgo–rentabilidad.")
        return

    risk_med   = df["Risk_Score"].median()
    margen_med = df[COL_MARGEN_NETO].median()

    fig = px.scatter(
        df,
        x="Risk_Score",
        y=COL_MARGEN_NETO,
        size=COL_COLOCACION,
        color=COL_CLUSTER,
        hover_name=COL_SUCURSAL,
        hover_data={
            COL_COLOCACION: ":.0f",
            COL_MORA: ":.3f",
            COL_RECUP: ":.3f",
            COL_FPD: ":.3f",
            "Risk_Score": ":.1f",
        },
        labels={
            "Risk_Score": "Score de riesgo",
            COL_MARGEN_NETO: "Margen financiero neto (MXN)"
        },
        size_max=40,
        template="plotly_white"
    )

    fig.add_vline(x=risk_med, line_width=1, line_dash="dash", line_color="rgba(15,23,42,0.5)")
    fig.add_hline(y=margen_med, line_width=1, line_dash="dash", line_color="rgba(15,23,42,0.5)")

    fig.add_annotation(
        x=risk_med * 0.4,
        y=margen_med * 1.3 if margen_med > 0 else margen_med + abs(margen_med)*0.3,
        text="Joyas de la cartera", showarrow=False,
        font=dict(size=11, color="#166534")
    )
    fig.add_annotation(
        x=risk_med * 1.6 if risk_med > 0 else risk_med + 10,
        y=margen_med * 1.3 if margen_med > 0 else margen_med + abs(margen_med)*0.3,
        text="Focos rojos de alto valor", showarrow=False,
        font=dict(size=11, color="#b91c1c")
    )
    fig.add_annotation(
        x=risk_med * 1.6 if risk_med > 0 else risk_med + 10,
        y=margen_med * 0.7,
        text="Sucursales a cuestionar", showarrow=False,
        font=dict(size=11, color="#92400e")
    )
    fig.add_annotation(
        x=risk_med * 0.4,
        y=margen_med * 0.7,
        text="Potencial de desarrollo", showarrow=False,
        font=dict(size=11, color="#0f172a")
    )

    apply_plotly_theme(fig, height=360)

    st.plotly_chart(fig, use_container_width=True, key=f"riesgo_rent_{hash(df.head().to_string())}")




def mapa_riesgo_rentabilidad_drivers(df):
    if df.empty:
        st.info("No hay datos disponibles.")
        return
    
    fig = px.scatter(
        df,
        x="Score_Final_S10",
        y="Margen Financiero Neto Actual",
        size="Saldo Insoluto Actual",
        color="Cluster_Final_S10",
        hover_name="Región",
        title="Mapa de Drivers: Riesgo vs Margen Financiero",
        labels={
            "Score_Final_S10": "Score de riesgo",
            "Margen Financiero Neto Actual": "Margen Neto (MXN)"
        },
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    apply_plotly_theme(fig, height=450)
    st.plotly_chart(fig, use_container_width=True, key="mapa_drivers_riesgo_rent")



def distribucion_riesgo(df):
    if df.empty:
        st.info("No hay datos suficientes.")
        return

    fig = px.histogram(
        df,
        x="Risk_Score",
        nbins=22,
        opacity=0.9,
        color_discrete_sequence=[DIMEX_GREEN],
        marginal="violin"
    )

    fig.update_traces(
        marker_line_width=1,
        marker_line_color="rgba(0,0,0,0.15)",
        hovertemplate="Score: %{x}<br>Cantidad: %{y}<extra></extra>",
    )

    fig.update_layout(
        title=dict(
            text="",
            x=0.5,
            font=dict(size=20, color=DIMEX_GREEN_DARK)
        )
    )

    pretty_layout(fig)
    st.plotly_chart(fig, use_container_width=True, key=f"distribucion_riesgo_{hash(df.head().to_string())}")




def mapa_riesgo_rentabilidad1(df):
    if df.empty:
        st.info("No hay datos.")
        return

    risk_med = df["Risk_Score"].median()
    margen_med = df[COL_MARGEN_NETO].median()

    fig = px.scatter(
        df,
        x="Risk_Score",
        y=COL_MARGEN_NETO,
        color=COL_CLUSTER,
        color_discrete_map={
            "Desarrollo": COLOR_CLUSTER_1,
            "Estrella": COLOR_CLUSTER_2,
            "Riesgo": COLOR_CLUSTER_3
        },
        size=COL_COLOCACION,
        hover_name=COL_SUCURSAL,
        size_max=38,
    )

    # Cuadrantes
    fig.add_vline(x=risk_med, line_color=DIMEX_BLUE_GRAY, line_dash="dot")
    fig.add_hline(y=margen_med, line_color=DIMEX_BLUE_GRAY, line_dash="dot")

    fig.update_traces(
        marker=dict(
            opacity=0.85,
            line=dict(width=1, color="white")
        ),
        hovertemplate="<b>%{hovertext}</b><br>Riesgo: %{x}<br>Margen: %{y}<extra></extra>"
    )

    fig.update_layout(
        title=dict(
            text="📉 Riesgo vs Rentabilidad",
            x=0.5,
            font=dict(size=20, color=DIMEX_GREEN_DARK)
        )
    )


    pretty_layout(fig)
    st.plotly_chart(fig, use_container_width=True, key=f"mapa_riesgo_rentabilidad1{hash(df.head().to_string())}")

def concentracion_clusters(df):
    if df.empty:
        st.info("No hay información.")
        return

    agg = df.groupby(COL_CLUSTER)["Risk_Score"].mean().reset_index()

    fig = px.bar(
        agg,
        x=COL_CLUSTER,
        y="Risk_Score",
        color="Risk_Score",
        color_continuous_scale=["#bbf7d0", DIMEX_GREEN],
    )

    fig.update_traces(
        marker_line_width=1.2,
        marker_line_color=DIMEX_GREEN_DARK,
        hovertemplate="Cluster: %{x}<br>Riesgo Promedio: %{y:.1f}<extra></extra>",
    )

    fig.update_layout(
        title=dict(
            text="",
            x=0.5,
            font=dict(size=20, color=DIMEX_GREEN_DARK)
        )
    )

    pretty_layout(fig)
    st.plotly_chart(fig, use_container_width=True)




  # Renderiza un KPI
def kpi_card(title, value_str, subtitle=None, color=DIMEX_GREEN_DARK):
    st.markdown(
        f"""
        <div class="kpi" style="
            background: linear-gradient(180deg, #F0FDF4, #ECFDF5);
            border-radius: 16px;
            min-width: 260px;
            border: 1px solid rgba(5,150,105,0.25);
            box-shadow: 0 8px 24px rgba(5,150,105,0.12);
            padding: 20px 18px;
            text-align: left;
            transition: transform .25s ease, box-shadow .25s ease;
        ">
            <p style="margin:0; font-size:18px; font-weight:500; color:#065F46;">
                {title}
            </p>
            <p style="margin:6px 0 0 0; font-size:28px; font-weight:800; color:{color};">
                {value_str}
            </p>
            <p style="margin:4px 0 0 0; font-size:16px; color:#6B7280;">
                {subtitle or ""}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

def gauge_riesgo(score):
    # --- Determinar color dinámico del puntero ---
    if score < 40:
        bar_color = "#059669"   # Verde DIMEX
    elif score < 70:
        bar_color = "#facc15"   # Amarillo
    else:
        bar_color = "#f87171"   # Rojo

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={'font': {'size': 62, 'color': '#0f172a'}},

        title={
            'text': "<b>Nivel de Riesgo</b>",
            'font': {'size': 28, 'color': '#065F46'}
        },

        gauge={
            'axis': {
                'range': [0, 100],
                'tickwidth': 1,
                'tickcolor': "#6b7280"
            },

            # --- FRANJAS DE COLOR (como ya tenías) ---
            'steps': [
                {'range': [0, 40], 'color': 'rgba(5,150,105,0.25)'},      # Verde suave
                {'range': [40, 70], 'color': 'rgba(250,204,21,0.25)'},     # Amarillo suave
                {'range': [70, 100], 'color': 'rgba(248,113,113,0.25)'}    # Rojo suave
            ],

            # --- Color dinámico de la barra ---
            'bar': {
                'color': bar_color,
                'thickness': 0.3
            },

            'borderwidth': 2,
            'bordercolor': '#065F46',
        }
    ))

    fig.update_layout(
        margin=dict(l=30, r=30, t=70, b=0),
        height=420
    )

    return fig

def bubble_risk_map(df, x_metric, y_metric, size_metric): # Mapa de burbujas riesgo
    if df.empty:
        st.info("No hay datos para mostrar en el mapa de burbujas.")
        return
    fig = px.scatter(
        df,
        x=x_metric["col"],                                # Columna eje X
        y=y_metric["col"],                                # Columna eje Y
        size=size_metric["col"],                          # Tamaño burbuja
        color="Risk_Score",                               # Color por riesgo
        color_continuous_scale=SEMAFORO_SCALE,            # Escala semáforo
        hover_name=COL_SUCURSAL,                          # Tooltip principal
        hover_data={                                      # Tooltip adicional (formateos)
            COL_COLOCACION: ":.0f",
            COL_MORA: ":.3f",
            COL_RECUP: ":.3f",
            COL_FPD: ":.3f",
            COL_ICV: ":.3f",
            "Risk_Score": ":.1f",
            COL_MARGEN_NETO: ":.0f",
            COL_CLUSTER: True,
        },
        labels={                                          # Etiquetas de ejes
            x_metric["col"]: x_metric["label"],
            y_metric["col"]: y_metric["label"],
            "Risk_Score": "Score de riesgo",
        },
        size_max=42,                                      # Tamaño máximo de burbuja
        template="plotly_white"                           # Tema base Plotly
    )
    fig.update_traces(marker=dict(line=dict(width=1.5, color="rgba(15,23,42,0.9)")))  # Borde burbuja
    apply_plotly_theme(fig, height=360)
    fig.update_layout(coloraxis_colorbar=dict(title="Riesgo", ticks="outside"))
    st.plotly_chart(fig, use_container_width=True)

def ranking_barras(df, min_risk, top_n):                 # Ranking horizontal por riesgo
    if df.empty:
        st.info("No hay datos para ranking.")
        return
    df_rank = df[df["Risk_Score"] >= min_risk]           # Filtra por umbral
    if df_rank.empty:
        st.info("No hay sucursales con score de riesgo por encima del umbral seleccionado.")
        return
    df_rank = df_rank.sort_values("Risk_Score", ascending=False).head(top_n)  # Top N
    fig = px.bar(
        df_rank.sort_values("Risk_Score"),                # Orden para barras apiladas
        x="Risk_Score",
        y=COL_SUCURSAL,
        color="Risk_Score",
        color_continuous_scale=SEMAFORO_SCALE,
        orientation="h",
        labels={"Risk_Score": "Score de riesgo"},
        template="plotly_white"
    )
    apply_plotly_theme(fig, height=350)
    fig.update_layout(xaxis_title="Score de riesgo (0-100)", yaxis_title="Sucursal",
                      coloraxis_colorbar=dict(title="Riesgo", ticks="outside"))
    st.plotly_chart(fig, use_container_width=True, key="ranking_barras")


def concent_riesgo_cluster(df):
    if df.empty:
        st.info("No hay datos para mostrar.")
        return

    grp = (
        df.groupby("Cluster_Final_S10")["Saldo Insoluto Actual"]
        .sum()
        .reset_index()
        .sort_values("Saldo Insoluto Actual", ascending=False)
    )

    fig = px.bar(
        grp,
        x="Cluster_Final_S10",
        y="Saldo Insoluto Actual",
        text_auto=".2s",
        color="Cluster_Final_S10",
        color_discrete_sequence=px.colors.qualitative.Set2,
        title="Concentración de saldo por cluster",
    )

    apply_plotly_theme(fig, height=380)
    st.plotly_chart(fig, key="mapa_riesgo")


def concent_por_decil(df):
    if df.empty:
        st.info("No hay datos disponibles.")
        return

    df2 = df.copy()

    try:
        df2["Decil"] = pd.qcut(
            df2["Score_Final_S10"],
            q=10,
            labels=False,
            duplicates="drop"
        ) + 1
    except ValueError:
        st.warning("No se pudieron generar deciles (valores repetidos o pocos datos).")
        return

    grp = (
        df2.groupby("Decil")["Saldo Insoluto Actual"]
        .sum()
        .reset_index()
    )

    fig = px.line(
        grp,
        x="Decil",
        y="Saldo Insoluto Actual",
        markers=True,
        color_discrete_sequence=["#047857"],
        title="Concentración por decil de riesgo (1=menor, 10=mayor)"
    )

    apply_plotly_theme(fig, height=350)
    st.plotly_chart(fig, use_container_width=True, key="plot_decil_riesgo")



    grp = (
        df2.groupby("Decil")["Saldo Insoluto Actual"]
        .sum()
        .reset_index()
    )

    fig = px.line(
        grp,
        x="Decil",
        y="Saldo Insoluto Actual",
        markers=True,
        color_discrete_sequence=["#047857"],
        title="Concentración por decil de riesgo (1=menor, 10=mayor)"
    )

    apply_plotly_theme(fig, height=350)


def mapa_riesgo_volumen(df):
    if df.empty:
        st.info("Sin datos.")
        return

    fig = px.scatter(
        df,
        x="Score_Final_S10",
        y="Saldo Insoluto Actual",
        size=df["Margen Financiero Neto Actual"].abs(),
        color="Cluster_Final_S10",
        hover_name="Región",
        title="Mapa de concentración: Riesgo vs Volumen",
        labels={
            "Score_Final_S10": "Score de riesgo",
            "Saldo Insoluto Actual": "Saldo Insoluto (MXN)"
        },
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    apply_plotly_theme(fig, height=420)
    st.plotly_chart(fig, use_container_width=True, key="mapa_riesgo_volumen")




def heatmap_concentracion(df):
    if df.empty:
        st.info("No hay información para heatmap.")
        return

    df["Decil"] = pd.qcut(
        df["Score_Final_S10"],
        q=10,
        labels=False,
        duplicates="drop"
    ) + 1

    pivot = df.pivot_table(
        values="Saldo Insoluto Actual",
        index="Cluster_Final_S10",
        columns="Decil",
        aggfunc="sum",
        fill_value=0
    )

    fig = px.imshow(
        pivot,
        color_continuous_scale="Greens",
        aspect="auto",
        title="Heatmap de concentración: Cluster × Decil"
    )

    apply_plotly_theme(fig, height=450)
    st.plotly_chart(fig, use_container_width=True, key="heatmap_concentracion")



def tarjetas_concentracion(df):
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Saldo total cartera", f"${df['Saldo Insoluto Actual'].sum():,.0f}")

    with col2:
        st.metric("Margen financiero neto", f"${df['Margen Financiero Neto Actual'].sum():,.0f}")

    with col3:
        top_cluster = df.groupby("Cluster_Final_S10")["Saldo Insoluto Actual"].sum().idxmax()
        st.metric("Cluster más concentrado", top_cluster)



def radar_riesgo_multifactor(df_segment):                # Radar comparativo por KPIs
    if df_segment.empty:
        st.info("No hay datos para el radar de riesgo.")
        return
    mode = st.radio("Vista del radar", ["Por cluster", "Por sucursal (Top 5 riesgo)"],
                    horizontal=True, key="radar_mode")    # Selector de modo

    # Definición de métricas y si son "inversas" (alto es bueno) o no
    metrics = {
        "Mora temprana": {"col": COL_MORA, "inverse": False},
        "%FPD": {"col": COL_FPD, "inverse": False},
        "Recuperación": {"col": COL_RECUP, "inverse": True},
        "ICV": {"col": COL_ICV, "inverse": False},
    }
    # Calcula percentiles globales para puntuar comparativamente
    global_risk_scores = {}
    for name, meta in metrics.items():
        col = meta["col"]
        s = df_full[col].copy()
        s = pd.to_numeric(s, errors="coerce").dropna()
        if s.empty:
            continue
        pct = s.rank(method="average", pct=True)          # Percentil 0..1
        global_risk_scores[name] = (1 - pct) if meta["inverse"] else pct

    # Genera series por cluster o por top sucursales
    if mode.startswith("Por cluster"):
        entities = df_segment[COL_CLUSTER].unique().tolist()[:6]
        series_list = []
        for cl in entities:
            sub = df_segment[df_segment[COL_CLUSTER] == cl]
            values = []
            for name, meta in metrics.items():
                if name not in global_risk_scores:
                    values.append(0.0)
                    continue
                g_pct = global_risk_scores[name]
                common_idx = sub.index.intersection(g_pct.index)
                values.append(float(g_pct.loc[common_idx].mean()) if len(common_idx) else 0.0)
            series_list.append({"label": cl, "values": values})
    else:
        top_suc = df_segment.sort_values("Risk_Score", ascending=False)[COL_SUCURSAL].unique().tolist()[:5]
        series_list = []
        for suc in top_suc:
            sub = df_segment[df_segment[COL_SUCURSAL] == suc]
            values = []
            for name, meta in metrics.items():
                if name not in global_risk_scores:
                    values.append(0.0)
                    continue
                g_pct = global_risk_scores[name]
                common_idx = sub.index.intersection(g_pct.index)
                values.append(float(g_pct.loc[common_idx].mean()) if len(common_idx) else 0.0)
            series_list.append({"label": suc, "values": values})

    if not series_list:
        st.info("No se pudieron calcular perfiles de riesgo comparables para el radar.")
        return

    theta = list(metrics.keys())                          # Ejes del radar
    fig = go.Figure()
    base_colors = ["#22c55e", "#0ea5e9", "#f97316", "#a855f7", "#ef4444", "#14b8a6"]
    for i, serie in enumerate(series_list):
        vals = serie["values"]
        r = vals + [vals[0]]                               # Cierra polígono
        th = theta + [theta[0]]
        fig.add_trace(go.Scatterpolar(
            r=r, theta=th, name=serie["label"],
            line=dict(color=base_colors[i % len(base_colors)], width=2),
            fill="toself", opacity=0.3
        ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1], tickformat=".0%", tickfont=dict(size=10)),
            angularaxis=dict(tickfont=dict(size=11))
        ),
        showlegend=True, title="Perfil de riesgo relativo por KPI"
    )
    apply_plotly_theme(fig, height=380)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Valores cercanos a 100% indican mayor riesgo relativo vs la red.")

def tabla_detalle(df):
    if df.empty:
        st.info("No hay datos para la tabla.")
        return

    # === Selección y renombrado ===
    df_t = df[[
        COL_SUCURSAL, COL_CLUSTER, COL_COLOCACION, COL_ICV, COL_MORA,
        COL_FPD, COL_RECUP, COL_SALDO, COL_MARGEN_NETO, "Risk_Score"
    ]].copy()

    df_t.rename(columns={
        COL_SUCURSAL: "Sucursal",
        COL_CLUSTER: "Cluster",
        COL_COLOCACION: "Colocación mensual",
        COL_ICV: "ICV",
        COL_MORA: "Mora temprana",
        COL_FPD: "%FPD",
        COL_RECUP: "Recuperación",
        COL_SALDO: "Saldo insoluto",
        COL_MARGEN_NETO: "Margen financiero neto",
        "Risk_Score": "Score riesgo"
    }, inplace=True)

    # === FORMATEO VISUAL PRO (TRUNCADO + COMAS + $ + %) ===
    df_fmt = df_t.copy()

    for col in df_fmt.columns:
        col_lower = col.lower()

        # DINERO
        if any(k in col_lower for k in ["colocación", "margen", "saldo"]):
            df_fmt[col] = df_fmt[col].apply(lambda x: f"${x:,.0f}")

        # PORCENTAJES (mora, recuperación, fpd)
        elif any(k in col_lower for k in ["mora", "recuperación", "fpd"]):
            df_fmt[col] = df_fmt[col].apply(lambda x: f"{x:.1%}")

        # SCORE
        elif "score" in col_lower:
            df_fmt[col] = df_fmt[col].apply(lambda x: f"{x:.1f}")

        # NÚMEROS NORMALES
        elif pd.api.types.is_numeric_dtype(df_fmt[col]):
            df_fmt[col] = df_fmt[col].apply(lambda x: f"{x:,.2f}")

    # === Mostrar ===
    st.dataframe(df_fmt, use_container_width=True)

    # Estilo por color según cluster
    def style_cluster(col):
        return [f"background-color: {get_cluster_color(v)}; color: #111827;" for v in col]

    styled = df_t.style.apply(style_cluster, subset=["Cluster"])     # Aplica estilo
 # Muestra DataFrame
    st.caption(f"Total de sucursales mostradas: {len(df_t)}")

def quick_actions(df_filtered):
        """Acciones rápidas tipo DIMEX."""
        st.markdown("""
        <h3  style='
            font-size:30px;
            font-weight:800;
            color:#0f172a;
            letter-spacing:-0.5px;
            margin-bottom:10px;
            text-align:center;
        '>
        Acciones rápidas
        </h3>
        """, unsafe_allow_html=True)

        # --- SOLO 2 BOTONES, CENTRADOS ---
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            crit_clicked = st.button("🔍 Ver sucursales críticas", use_container_width=True)

        with col2:
            csv = df_filtered.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Exportar reporte",
                data=csv,
                file_name=f"reporte_dimex_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        # Col3 queda vacío para que col1 y col2 queden centrados visualmente
        with col3:
            st.write("")

        # --- lógica existente
        if crit_clicked:
            crit_df = df_filtered[df_filtered["Risk_Score"] >= 80].copy()
            if crit_df.empty:
                st.info("No hay sucursales con Score de riesgo ≥ 80 en los filtros actuales.")
            else:
                st.markdown("### 🔥 Sucursales críticas (Score ≥ 80)")
                df_c = crit_df[[
                    COL_SUCURSAL, COL_CLUSTER, "Risk_Score", COL_MORA, COL_FPD, COL_RECUP
                ]].copy()

                df_c.rename(columns={
                    COL_SUCURSAL: "Sucursal",
                    COL_CLUSTER: "Cluster",
                    "Risk_Score": "Score",
                    COL_MORA: "Mora temprana",
                    COL_FPD: "%FPD",
                    COL_RECUP: "Recuperación",
                }, inplace=True)

                df_fmt = df_c.copy()
                df_fmt["Score"] = df_fmt["Score"].apply(lambda x: f"{x:.1f}")
                df_fmt["Mora temprana"] = df_fmt["Mora temprana"].apply(lambda x: f"{x:.1%}")
                df_fmt["%FPD"] = df_fmt["%FPD"].apply(lambda x: f"{x:.1f}%")
                df_fmt["Recuperación"] = df_fmt["Recuperación"].apply(lambda x: f"{x:.1%}")

                def style_cluster(col):
                    return [f"background-color: {get_cluster_color(v)}; color:#111;" for v in col]

                styled = df_fmt.style.apply(style_cluster, subset=["Cluster"])
                st.dataframe(styled, use_container_width=True, hide_index=True)



def render_alertas(df, mora_hi, recup_low):
    """Alertas ejecutivas, con diseño más bonito tipo card."""

    alerts = []

    # --- Construcción de mensajes como antes ---
    high_mora = df[df[COL_MORA] > mora_hi]
    n_high_mora = high_mora.shape[0]
    if n_high_mora > 0:
        top_names = ", ".join(high_mora[COL_SUCURSAL].head(3).tolist())
        alerts.append(
            f"{n_high_mora} sucursales con mora temprana por encima del percentil 75 "
            f"({fmt_percent(mora_hi)}). Ejemplos: {top_names}."
        )

    low_recup = df[df[COL_RECUP] < recup_low]
    n_low_recup = low_recup.shape[0]
    if n_low_recup > 0:
        top_names = ", ".join(low_recup[COL_SUCURSAL].head(3).tolist())
        alerts.append(
            f"{n_low_recup} sucursales con recuperación por debajo del percentil 25 "
            f"({fmt_percent(recup_low)}). Ejemplos: {top_names}."
        )

    if not df.empty:
        top_fpd = df.sort_values(COL_FPD, ascending=False).iloc[0]
        alerts.append(
            f"Sucursal con FPD más alto: {top_fpd[COL_SUCURSAL]} "
            f"(FPD {fmt_percent(top_fpd[COL_FPD])})."
        )

    # --- Render bonito ---
    st.markdown(
        """
        <div style="display:flex; justify-content:center; margin-bottom:14px;">
            <span class="hoverable" style="
                display:inline-block;
                background:linear-gradient(180deg,#fef2f2,#fff7f7);
                padding:6px 16px;
                border-radius:12px;
                font-size:22px;
                font-weight:700;
                color:#991b1b;
                border:1px solid #fecaca;
                box-shadow:0 4px 12px rgba(248,113,113,0.10);
                letter-spacing:-0.3px;
            ">
            Alertas clave
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )


    if not alerts:
        st.info("No se detectaron alertas críticas con los umbrales basados en históricos.")
        return

    # Card contenedor
    st.markdown(
        f"""
        <div class="hoverable" style="
            border-radius: 16px;
            padding: 12px 14px 10px 14px;
            background: linear-gradient(180deg,#fef2f2,#fff7f7);
            border: 1px solid #fecaca;
            box-shadow: 0 6px 18px rgba(248,113,113,0.18);
        ">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
                <div style="display:flex;align-items:center;gap:8px;">
                    <div style="
                        width:26px;height:26px;border-radius:999px;
                        background:radial-gradient(circle at 30% 0%, #fed7d7, #ef4444);
                        display:flex;align-items:center;justify-content:center;
                        color:white;font-weight:800;font-size:16px;
                    ">!</div>
                    <div>
                        <div style="font-size:18px;font-weight:600;color:#991b1b;">
                            Riesgos a vigilar en el segmento filtrado
                        </div>
                        <div style="font-size:16px;color:#b91c1c;">
                            {len(alerts)} alerta(s) activa(s) con base en percentiles históricos
                        </div>
                    </div>
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    # Cada alerta como “pill” con iconito
    for a in alerts:
        st.markdown(
            f"""
            <div style="
                margin-top:6px;
                display:flex;
                align-items:flex-start;
                gap:8px;
                padding:7px 9px;
                border-radius:12px;
                background:rgba(254,242,242,0.95);
                border:1px solid rgba(254,202,202,0.9);
                font-size:18px;
                color:#7f1d1d;
            ">
                <div style="
                    width:18px;height:18px;border-radius:999px;
                    background:#fee2e2;
                    display:flex;align-items:center;justify-content:center;
                    font-size:11px;font-weight:700;color:#b91c1c;
                    flex-shrink:0;
                ">!</div>
                <div style="line-height:1.35;">{a}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Cierre de la card contenedora
    st.markdown("</div>", unsafe_allow_html=True)



def render_arbol_reglas(icv_hi, mora_hi, recup_low):
    import streamlit as st

    st.markdown("""
        <style>
        .dashboard-card {
            border-radius: 16px;
            padding: 20px;
            background: #f9fdfb;
            border: 1px solid #e0f2f1;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        }
        .risk-label {
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 12px;
        }
        .low-risk {
            background-color: #d1fae5;
            color: #065f46;
        }
        .mod-risk {
            background-color: #fef9c3;
            color: #92400e;
        }
        .high-risk {
            background-color: #fee2e2;
            color: #991b1b;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("### ⚖️ Árbol predictor (reglas de negocio)")
    st.caption("Secuencia sugerida para leer el riesgo del segmento filtrado.")

    with st.container():
        

        # Calidad de venta
        st.markdown("#### 📊 Calidad de la venta (ICV)")
        col1, col2 = st.columns([1, 3])
        col1.markdown("ICV ≤")
        col2.markdown(f"`{icv_hi:.2f}` → <span class='risk-label low-risk'>riesgo bajo</span>", unsafe_allow_html=True)
        col1.markdown("ICV >")
        col2.markdown(f"`{icv_hi:.2f}` → revisar **Mora**")

        st.markdown("---")

        # Mora temprana
        st.markdown("#### ⏱️ Mora temprana")
        col1, col2 = st.columns([1, 3])
        col1.markdown("Mora ≤")
        col2.markdown(f"`{fmt_percent(mora_hi)}` → <span class='risk-label mod-risk'>riesgo moderado</span>", unsafe_allow_html=True)
        col1.markdown("Mora >")
        col2.markdown(f"`{fmt_percent(mora_hi)}` → <span class='risk-label high-risk'>riesgo alto</span>", unsafe_allow_html=True)

        st.markdown("---")

        # Recuperación
        st.markdown("#### 💸 Recuperación")
        col1, col2 = st.columns([1, 3])
        col1.markdown("Recup <")
        col2.markdown(f"`{fmt_percent(recup_low)}` → <span class='risk-label high-risk'>alerta crítica</span> con prioridad máxima", unsafe_allow_html=True)






def render_recomendaciones(df):
    st.markdown("### Recomendaciones operativas")

    # Sucursales con mayor riesgo
    top_risk = df.sort_values("Risk_Score", ascending=False).head(2)[COL_SUCURSAL].tolist()
    suc1 = top_risk[0] if len(top_risk) > 0 else "Sucursal de mayor riesgo"
    suc2 = top_risk[1] if len(top_risk) > 1 else "Siguiente sucursal en riesgo"

    # Recomendaciones visuales
    st.markdown("""
    <div style='line-height: 1.7; font-size: 19px;'>
        <ul style="list-style-type: '✅ '; padding-left: 1.2em;">
            <li>Priorizar auditoría integral en <b>{suc1}</b> y <b>{suc2}</b>, revisando <code>FPD</code>, <code>Mora temprana</code> y <code>Recuperación</code>.</li>
            <li>Plan intensivo de <b>cobranza</b> en sucursales con <span style="color:#b91c1c;"><b>Mora alta</b></span> y <span style="color:#b91c1c;"><b>Recuperación baja</b></span>.</li>
            <li>⚙️ Ajustar <b>reglas de originación</b> donde <code>FPD</code> supere el promedio de la red.</li>
            <li>📘 Documentar y replicar prácticas de <b>sucursales con buen ICV</b> y <b>baja Mora</b>.</li>
        </ul>
    </div>
    """.format(suc1=suc1, suc2=suc2), unsafe_allow_html=True)


def resumen_ejecutivo_story(total_coloc, avg_icv, avg_mora, avg_recup, avg_risk, num_suc):
    nivel, texto = get_risk_level(avg_risk)

    st.markdown(
        f"""
        <div style="
            border-radius: 999px;
            padding: 10px 18px;
            background: linear-gradient(90deg,#ecfdf5,#fefce8);
            border: 1px solid rgba(16,185,129,0.25);
            display:flex;
            align-items:center;
            gap:14px;
            font-size:16px;
            color:#374151;
        ">
            <div style="
                width:26px;height:26px;border-radius:999px;
                background:radial-gradient(circle at 30% 0%, #bbf7d0, #22c55e);
                display:flex;align-items:center;justify-content:center;
                color:white;font-weight:800;font-size:15px;
            ">
                i
            </div>
            <div style="flex:1;">
                <span style="font-weight:600;color:#022c22;">
                    {num_suc} sucursales · riesgo {nivel} · colocación {fmt_currency(total_coloc)}
                </span>
                <br>
                <span style="color:#4b5563;">{texto}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# -------------------------------------------------------------------
# HEADER (sticky) con animaciones suaves y barra de salud
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# HEADER (sticky) minimalista con barra de salud
# -------------------------------------------------------------------

def render_header(avg_health: float):
    with st.container():
        st.markdown("<div class='dimex-header'>", unsafe_allow_html=True)

        # 3 columnas: logo | título | chip de salud
        col_logo, col_title, col_health = st.columns([1, 5, 3])
        with col_health:
            st.markdown(f"""
            <div class="health-chip">

            </div>
        """, unsafe_allow_html=True)

        # Columna 1: Logo DIMEX o fallback
        with col_logo:
            logo_path = Path("dimex_logo.png")
            if logo_path.exists():
                st.image(str(logo_path), use_container_width=True)
            else:
                st.markdown(
                    """
                    <div style="
                        width:20px;height:100px;border-radius:10px;
                        background:#05966910;
                        display:flex;align-items:center;justify-content:center;
                        border:1px solid rgba(5,150,105,0.25);
                    ">
                        <span style="color:#059669;font-weight:700;font-size:20px;">D</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # Columna 2: Título + subtítulo (sin tanta decoración)
        with col_title:
            st.markdown(
                """
                <div style="padding:4px 0;">
                    <div style="display:flex;align-items:center;gap:8px;">
                        <h1 style="
                            margin:0;
                            font-size:40px;
                            font-weight:800;
                            letter-spacing:-0.03em;
                            color:#020617;
                        ">
                            Salud y Riesgo de Sucursales
                        </h1>
                    </div>
                    <p style="
                        margin:2px 0 0 0;
                        font-size:16px;
                        color:#6B7280;
                    ">
                        Dirección de Cobranza · Cartera de jubilados y pensionados
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Columna 3: Chip de índice de salud (flat, pill)
        with col_health:
            st.markdown(
                f"""
                <div  style="
                    margin-top:6px;
                    display:flex;
                    justify-content:flex-end;
                ">
                    <div style="
                        display:flex;align-items:center;gap:10px;
                        padding:8px 14px;
                        border-radius:999px;
                        border:1px solid rgba(22,163,74,0.18);
                        background:rgba(240,253,244,0.9);
                        --health-width:{avg_health:.1f}%;
                    ">
                        <span style="font-size:14px;color:#047857;font-weight:600;">
                            Índice de salud
                        </span>
                        <div class="health-bar" style="width:140px;">
                            <span></span>
                        </div>
                        <span style="
                            font-size:22px;
                            font-weight:700;
                            color:#059669;
                            min-width:64px;
                            text-align:right;
                        ">
                            {avg_health:.1f}
                            <span style="font-size:20px;color:#9CA3AF;">/ 100</span>
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div class='top-spacer'></div>", unsafe_allow_html=True)

    # (Opcional: sin lottie para que sea todavía más limpio)
    # Si quieres dejar el pulso, quita este comentario:
    # if LOTTI_AVAILABLE:
    #     st_lottie(...)
# -------------------------------------------------------------------
# LAYOUT PRINCIPAL (controles, KPIs, gráficos, tabs, FABs)
# -------------------------------------------------------------------
def main():
    # Estado inicial de filtros si no existen aún en la sesión
    if "filters" not in st.session_state:
        st.session_state["filters"] = {"cluster": "Todos", "sucursal": "Todas"}
    if "quick" not in st.session_state:
        st.session_state["quick"] = {"alto_riesgo": False, "mora_alta": False, "recup_baja": False, "umbral_riesgo": 70}

    # Atajos locales a los dicts de estado
    filters = st.session_state["filters"]
    quick   = st.session_state["quick"]

    # Umbrales automáticos a partir del histórico completo (p75/p25)
    icv_hi    = df_full[COL_ICV].quantile(0.75)
    mora_hi   = df_full[COL_MORA].quantile(0.75)
    recup_low = df_full[COL_RECUP].quantile(0.25)

    # HEADER sticky con barra de salud promedio
    avg_health = df_full["Health_Index"].mean()
    render_header(avg_health)

    # ---- FILTROS SUPERIORES -------------------------------------------------
    col_f1, col_f2, col_f3, col_f4 = st.columns([2.2, 2.2, 2.2, 3.4])
    with col_f1:
        filters["cluster"] = st.selectbox("Cluster", ["Todos"] + sorted(df_full[COL_CLUSTER].unique().tolist()))
    with col_f2:
        filters["sucursal"] = st.selectbox("Sucursal", ["Todas"] + sorted(df_full[COL_SUCURSAL].unique().tolist()))
    with col_f3:
        quick["alto_riesgo"] = st.checkbox("Filtrar alto riesgo", value=quick["alto_riesgo"])
        quick["umbral_riesgo"] = st.slider("Umbral score riesgo", 0, 100, quick["umbral_riesgo"], step=5, label_visibility="collapsed")
    with col_f4:
        c_q1, c_q2 = st.columns(2)
        with c_q1:
            quick["mora_alta"] = st.checkbox("Mora alta", value=quick["mora_alta"])
        with c_q2:
            quick["recup_baja"] = st.checkbox("Recuperación baja", value=quick["recup_baja"])

    # Aplica filtros a la base completa
    df_filtered = apply_filters(df_full, filters, quick)
    if df_filtered.empty:
        st.warning("No hay datos para los filtros seleccionados.")   # Aviso si no hay datos
        return

    # Separador visual
    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

    total_coloc = df_filtered[COL_COLOCACION].sum()
    avg_icv     = df_filtered[COL_ICV].mean()
    avg_mora    = df_filtered[COL_MORA].mean()
    avg_fpd     = df_filtered[COL_FPD].mean()
    avg_recup   = df_filtered[COL_RECUP].mean()
    avg_risk    = df_filtered["Risk_Score"].mean()
    num_suc     = len(df_filtered)
    margen_neto = df_filtered[COL_MARGEN_NETO].sum()


        # ---- STORYTELLING EJECUTIVO --------------------------------------------

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    # ---- KPIs PRINCIPALES ---------------------------------------------------
    row1 = st.columns([1,1,1,1,1], gap="large")

    with row1[0]:
        kpi_card(
            "Sucursales activas",
            f"{num_suc}",
            "Sucursales filtradas",
            color="var(--dimex-green-dark)"
        )

    with row1[1]:
        kpi_card(
            "Colocación total",
            fmt_currency(total_coloc),
            "Promedio mensual",
            color="var(--dimex-green)"
        )

    with row1[2]:
        kpi_card(
            "Margen financiero neto total",
            fmt_currency(margen_neto),
            "Contribución cartera filtrada",
            color="var(--dimex-teal)"
        )

    with row1[3]:
        kpi_card(
            "%FPD promedio",
            fmt_percent(avg_fpd),
            "Incumplimiento primer pago",
            color="var(--warn)"
        )

    with row1[4]:
        kpi_card(
            "%FPD promedio",
            fmt_percent(avg_fpd),
            "Incumplimiento primer pago",
            color="var(--warn)"
        )
    st.markdown("<div style='height:26px;'></div>", unsafe_allow_html=True)
    st.markdown("<div style='height:26px;'></div>", unsafe_allow_html=True)



# ===============================================================
# 🟩 TABS PRINCIPALES (DESPUÉS DE LOS KPIs)
# ===============================================================

    tabs = st.tabs([
        "📊 Overview ejecutivo",
        "📍 Concentración de riesgo",
        "🧠 Drivers del riesgo",
        "💹 Riesgo & rentabilidad",
        "✔ Acciones prioritarias",
        "📋 Detalle por sucursal"
    ])
     
    with tabs[0]:
        st.markdown("### 📋 Detalle por sucursal")
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        # --- SELECTBOX correcto (usa df_full, no df)
        sucursal = st.selectbox(
            "Selecciona una sucursal",
            sorted(df_full[COL_SUCURSAL].unique()),
            key="tab3_suc"
        )

        # Extrae los registros de esa sucursal
        df_suc = df_full[df_full[COL_SUCURSAL] == sucursal]

        if df_suc.empty:
            st.warning("No hay datos para esta sucursal.")
        else:
            # CARD contenedor
            card_container(True)

            st.markdown(
                f"""
                <h4 style='margin-bottom:4px;color:#064e3b;font-weight:700;'>{sucursal}</h4>
                <p style='color:#64748b;font-size:13px;margin-top:-6px;'>
                    Información completa de métricas, riesgo, colocación y desempeño operativo.
                </p>
                """,
                unsafe_allow_html=True,
            )

            # === KPIs individuales por sucursal ===
            sc1, sc2, sc3, sc4 = st.columns(4)
            row = df_suc.iloc[0]

            with sc1:
                kpi_card("Score de riesgo", f"{row['Risk_Score']:.1f}", "0–100", COLOR_CLUSTER_1)
            with sc2:
                kpi_card("Mora temprana", fmt_percent(row[COL_MORA]), "Último corte", COLOR_CLUSTER_2)
            with sc3:
                kpi_card("Recuperación", fmt_percent(row[COL_RECUP]), "Efectividad", COLOR_CLUSTER_3)
            with sc4:
                kpi_card("Colocación mensual", fmt_currency(row[COL_COLOCACION]), "Promedio", COLOR_CLUSTER_1)

            st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

            # === TABLA COMPLETA DETALLADA ===        
            st.markdown("#### Tabla detallada de KPIs")
            tabla_detalle(df_suc)

            card_container(False)

    with tabs[1]:

        # ===== TÍTULO BONITO =====
        st.markdown(
            """
            <div style="display:flex; justify-content:center; margin-top:40px; margin-bottom:24px;">
                <div style="
                    padding: 14px 28px;
                    background: #FFFFFF;
                    border-radius: 14px;
                    border: 2px solid rgba(5,150,105,0.3);
                    box-shadow: 0 4px 14px rgba(5,150,105,0.12);
                    font-size: 24px;
                    font-weight: 700;
                    color: #064E3B;
                    display:flex;
                    align-items:center;
                    gap:12px;
                ">
                    <span style="font-size:26px;">📊</span>
                    <span>Overview Ejecutivo</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)


        # ===================================================
        # STORYTELLING EJECUTIVO
        # ===================================================
        resumen_ejecutivo_story(
            total_coloc, avg_icv, avg_mora, avg_recup, avg_risk, num_suc
        )

        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)


        # ===================================================
        # FILA 1 — DISTRIBUCIÓN DEL RIESGO + RIESGO/RENTABILIDAD
        # ===================================================
        col1, col2 = st.columns(2, gap="large")

        with col1:
            card_container(True)
            st.markdown("<h3>Distribución del Riesgo</h3>", unsafe_allow_html=True)
            distribucion_riesgo(df_filtered)
            card_container(False)

        with col2:
            card_container(True)
            st.markdown("<h3>Riesgo vs Rentabilidad</h3>", unsafe_allow_html=True)
            mapa_riesgo_rentabilidad(df_filtered)
            card_container(False)


        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)


        # ===================================================
        # FILA 2 — CLUSTER + GAUGE DE RIESGO
        # ===================================================
        col3, col4 = st.columns(2, gap="large")

        with col3:
            card_container(True)
            st.markdown("<h3>Riesgo promedio por cluster</h3>", unsafe_allow_html=True)
            concentracion_clusters(df_filtered)
            card_container(False)

        with col4:
            card_container(True)
            st.markdown("<h3>Score de riesgo de la cartera</h3>", unsafe_allow_html=True)
            fig = gauge_riesgo(avg_risk)
            st.plotly_chart(fig, use_container_width=True)
            card_container(False)


        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)


        # ===================================================
        # ALERTAS CLAVE
        # ===================================================
        render_alertas(df_filtered, mora_hi, recup_low)

        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)



        # ===================================================
        # ACCIONES RÁPIDAS
        # ===================================================
        quick_actions(df_filtered)


    with tabs[2]:  
        st.markdown(
            """
            <div style="display:flex; justify-content:center; margin-bottom:14px;">
                <span style="
                    display:inline-block;
                    background:rgba(16,185,129,0.1);
                    padding:6px 14px;
                    border-radius:8px;
                    font-size:24px;
                    font-weight:600;
                    color:#047857;
                    border:1px solid rgba(16,185,129,0.15);
                ">
                    Concentración de Riesgo
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Primera fila: Cluster + Deciles
        c1, c2 = st.columns([1.1, 1])
        with c1:
            concent_riesgo_cluster(df_filtered)
        with c2:
            concent_por_decil(df_filtered)

        # Segunda fila: Mapa + Heatmap
        c3, c4 = st.columns([1.2, 1])
        with c3:
            mapa_riesgo_volumen(df_filtered)
        with c4:
            heatmap_concentracion(df_filtered)

        # ======================================================
        # FILA 1 — DISTRIBUCIÓN + RIESGO/RENTABILIDAD
        # ======================================================
        col1, col2 = st.columns(2, gap="large")

     

        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)

        # ======================================================
        # FILA 2 — CLUSTER + GAUGE   (🔥 AHORA SÍ DENTRO DEL TAB)
        # ======================================================
        col3, col4 = st.columns(2, gap="large")

    with tabs[3]:
        st.markdown("<h3 class='section-title'>Drivers de Riesgo</h3>", unsafe_allow_html=True)



        drivers_correlacion_heatmap(df_filtered)

        drivers_por_cluster(df_filtered)



    with tabs[4]:
        st.markdown("<h3 class='section-title'>Riesgo & Rentabilidad</h3>", unsafe_allow_html=True)

        st.markdown("""
            <div style="display:flex; justify-content:center; margin-bottom:16px;">
                <span style="
                    display:inline-block;
                    background:rgba(16,185,129,0.10);
                    padding:6px 16px;
                    border-radius:10px;
                    font-size:26px;
                    font-weight:700;
                    color:#047857;
                    border:1px solid rgba(16,185,129,0.20);
                ">
                    Riesgo & Rentabilidad
                </span>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("### 📈 Mapa de Riesgo vs Rentabilidad (Score vs Margen)")
        mapa_riesgo_rentabilidad(df_filtered)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 💰 Rentabilidad por Score de Riesgo")
            rentabilidad_vs_riesgo(df_filtered)

        with col2:
            st.markdown("### 🧮 Curva Margen / Volumen por Cluster")
            margen_vs_volumen_cluster(df_filtered)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        st.markdown("### 🧊 Relación Mora – Rentabilidad")
        mora_vs_margen(df_filtered)

    with tabs[5]:
        render_tab_acciones_prioritarias(df_filtered)

 
   
        



    # ================================================================
    # DIMI · Chatbot de riesgo (siempre al final del dashboard)
    # ================================================================

    if st.session_state.get("auth", False):

            st.markdown("<hr style='margin-top:40px; margin-bottom:30px;'>", unsafe_allow_html=True)

            st.markdown(
                f"""
                <div style='display:flex; align-items:center; gap:16px; margin-bottom:10px;'>
                    <img src="data:image/png;base64,{avatar}" width="110"
                        style="border-radius:100%; border:3px solid #e2e8f0;" />
                    <h2 style='margin:0; font-weight:800; color:#0f172a;'>
                        DIMI · Analista virtual de riesgo
                    </h2>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.caption(
                "Hazme preguntas sobre la cartera filtrada: sucursales críticas, escenarios, regresiones, explicaciones para comité o diagnósticos por cluster."
            )

            # Historial
            for msg in st.session_state["dimi_history"]:
                role = "user" if msg["role"] == "user" else "assistant"
                with st.chat_message(role):
                    st.markdown(msg["content"])

            # Input del usuario
            user_msg = st.chat_input("Pregúntale algo a DIMI:")
            if user_msg:
                with st.spinner("DIMI está analizando el segmento filtrado..."):
                    _ = dimi_answer(user_msg, df_filtered)
                st.rerun()

        # Botón de reset real (usa widget nativo para poder hacer rerun)
    reset_col = st.columns([10,1,1])[1]    
                               # Columna pequeña hacia la derecha
                                         # Recarga la app

# Punto de entrada del script
if __name__ == "__main__":
    main()
