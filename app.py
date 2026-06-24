import re
from datetime import datetime, date
from typing import List, Dict, Any

import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# =========================
# CONFIGURACIÓN GENERAL
# =========================
st.set_page_config(
    page_title="Iron Body | Clases de Prueba",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded",
)

SHEET_NAME = "Iron Body - Clases de Prueba"
# Recomendado: define spreadsheet_id en .streamlit/secrets.toml para usar una hoja específica.
# Si no lo defines, la app intentará crear/abrir una hoja con SHEET_NAME desde la cuenta de servicio.
WORKSHEET_NAME = "Registros"
DISCIPLINAS = ["Pesas y cardio", "TRX", "Iron Reformer", "Cycling", "Jiujitsu"]
COLUMNAS = [
    "Fecha registro",
    "Fecha clase",
    "Nombre",
    "Cédula",
    "Celular",
    "Horario",
    "Disciplina",
]

# =========================
# ESTILOS
# =========================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700;800&display=swap');

    :root {
        --bg: #080808;
        --panel: #111111;
        --panel2: #1a1a1a;
        --border: #333333;
        --text: #ffffff;
        --muted: #9ca3af;
        --red: #ff4050;
        --red2: #e73343;
    }

    .stApp {
        background: radial-gradient(circle at top left, #191919 0%, #080808 35%, #050505 100%);
        color: var(--text);
        font-family: 'Inter', sans-serif;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #171717 0%, #0d0d0d 100%);
        border-right: 2px solid var(--red);
    }

    [data-testid="stSidebar"] * {
        color: #ffffff;
    }

    .brand-title {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 54px;
        line-height: .9;
        letter-spacing: 5px;
        color: white;
        margin-bottom: 0;
    }

    .brand-subtitle {
        font-size: 12px;
        letter-spacing: 7px;
        color: #ffffff;
        margin-top: 4px;
        margin-bottom: 35px;
    }

    .main-title {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 58px;
        line-height: 1;
        letter-spacing: 8px;
        color: var(--red);
        margin-bottom: 4px;
    }

    .main-subtitle {
        letter-spacing: 7px;
        color: var(--muted);
        font-size: 12px;
        text-transform: uppercase;
        margin-bottom: 28px;
    }

    .section-title {
        font-family: 'Bebas Neue', sans-serif;
        color: var(--red);
        font-size: 30px;
        letter-spacing: 4px;
        margin: 0 0 12px 0;
    }

    .metric-card {
        background: rgba(26, 26, 26, .88);
        border: 1px solid #2f2f2f;
        border-left: 5px solid var(--red);
        border-radius: 12px;
        padding: 22px 24px;
        margin-bottom: 16px;
        box-shadow: 0 10px 28px rgba(0,0,0,.25);
    }

    .metric-label {
        font-size: 11px;
        letter-spacing: 4px;
        text-transform: uppercase;
        color: #d6d6d6;
        font-weight: 800;
        margin-bottom: 4px;
    }

    .metric-number {
        font-size: 42px;
        font-weight: 900;
        line-height: 1;
        color: #ffffff;
        margin: 0;
    }

    .metric-help {
        font-size: 12px;
        color: #d1d5db;
        margin-top: 8px;
    }

    .content-card {
        background: rgba(12, 12, 12, .82);
        border: 1px solid #3a3a3a;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 16px 34px rgba(0,0,0,.35);
    }

    div[data-testid="stTextInput"] label,
    div[data-testid="stSelectbox"] label,
    div[data-testid="stDateInput"] label {
        color: #ffffff !important;
        font-weight: 800 !important;
    }

    .stTextInput input,
    .stSelectbox div[data-baseweb="select"] > div,
    .stDateInput input {
        background-color: #2a2a2a !important;
        color: #ffffff !important;
        border: 1px solid #434343 !important;
        border-radius: 8px !important;
        min-height: 44px;
    }

    .stButton > button {
        background: linear-gradient(135deg, var(--red), var(--red2));
        color: white;
        border: 0;
        border-radius: 10px;
        padding: 12px 20px;
        font-weight: 900;
        letter-spacing: 1.5px;
        width: 100%;
        min-height: 48px;
        text-transform: uppercase;
    }

    .stButton > button:hover {
        border: 0;
        color: white;
        filter: brightness(1.08);
        transform: translateY(-1px);
    }

    [data-testid="stDataFrame"] {
        border: 1px solid #333333;
        border-radius: 12px;
    }

    hr {
        border-color: #2e2e2e;
    }

    .small-note {
        color: #a3a3a3;
        font-size: 12px;
        line-height: 1.5;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# GOOGLE SHEETS
# =========================
def get_google_credentials() -> Credentials:
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    if "gcp_service_account" not in st.secrets:
        st.error(
            "No encuentro las credenciales de Google Sheets. Revisa el archivo .streamlit/secrets.toml o los Secrets de Streamlit Cloud."
        )
        st.stop()

    credentials_info = dict(st.secrets["gcp_service_account"])
    return Credentials.from_service_account_info(credentials_info, scopes=scopes)


@st.cache_resource(show_spinner=False)
def get_worksheet():
    creds = get_google_credentials()
    client = gspread.authorize(creds)

    spreadsheet_id = st.secrets.get("GOOGLE_SHEET_ID", st.secrets.get("spreadsheet_id", ""))

    try:
        if spreadsheet_id:
            spreadsheet = client.open_by_key(spreadsheet_id)
        else:
            spreadsheet = client.open(SHEET_NAME)
    except gspread.SpreadsheetNotFound:
        spreadsheet = client.create(SHEET_NAME)
    except gspread.exceptions.APIError as error:
        st.error("No pude abrir el Google Sheet. Revisa que el archivo esté compartido con el correo de la cuenta de servicio.")
        st.code(credentials_email())
        st.stop()

    try:
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=WORKSHEET_NAME, rows=1000, cols=len(COLUMNAS))

    ensure_headers(worksheet)
    return worksheet


def credentials_email() -> str:
    try:
        return st.secrets["gcp_service_account"]["client_email"]
    except Exception:
        return ""


def ensure_headers(worksheet) -> None:
    """
    Asegura que la hoja tenga todos los encabezados necesarios sin borrar datos existentes.
    Si ya tienes registros anteriores, agrega columnas faltantes al final y conserva la información.
    """
    existing = worksheet.row_values(1)

    if not existing:
        worksheet.append_row(COLUMNAS)
        return

    updated_headers = existing.copy()
    changed = False
    for col in COLUMNAS:
        if col not in updated_headers:
            updated_headers.append(col)
            changed = True

    if changed:
        worksheet.update("1:1", [updated_headers])


@st.cache_data(ttl=20, show_spinner=False)
def load_data() -> pd.DataFrame:
    worksheet = get_worksheet()
    records: List[Dict[str, Any]] = worksheet.get_all_records()
    if not records:
        return pd.DataFrame(columns=COLUMNAS)
    df = pd.DataFrame(records)
    for col in COLUMNAS:
        if col not in df.columns:
            df[col] = ""

    df["Fecha clase"] = df["Fecha clase"].astype(str).replace({"nan": "", "None": ""})
    df["Fecha registro"] = df["Fecha registro"].astype(str).replace({"nan": "", "None": ""})
    return df[COLUMNAS]


def save_record(record: Dict[str, str]) -> None:
    worksheet = get_worksheet()
    headers = worksheet.row_values(1) or COLUMNAS
    row = [record.get(col, "") for col in headers]
    worksheet.append_row(row, value_input_option="USER_ENTERED")
    load_data.clear()

# =========================
# VALIDACIONES
# =========================
def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def only_digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def validate_form(nombre: str, cedula: str, celular: str, horario: str, disciplina: str) -> List[str]:
    errors = []

    if len(nombre) < 3:
        errors.append("El nombre debe tener al menos 3 caracteres.")

    if not cedula.isdigit() or len(cedula) < 8 or len(cedula) > 13:
        errors.append("La cédula debe contener entre 8 y 13 números.")

    if not celular.isdigit() or len(celular) < 7 or len(celular) > 13:
        errors.append("El celular debe contener entre 7 y 13 números.")

    if len(horario) < 2:
        errors.append("Debes ingresar un horario. Ejemplo: 18:00, 7pm, lunes 6pm.")

    if disciplina not in DISCIPLINAS:
        errors.append("Debes seleccionar una disciplina válida.")

    return errors

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.markdown('<div class="brand-title">IRON BODY</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-subtitle">CLASES DE PRUEBA</div>', unsafe_allow_html=True)

    page = st.radio(
        "",
        ["📝 Registrar clase", "📅 Clases de hoy", "📊 Dashboard", "📋 Todos los registros"],
        label_visibility="collapsed",
    )

    df_sidebar = load_data()
    total = len(df_sidebar)
    disciplina_top = "Sin datos"
    if not df_sidebar.empty and "Disciplina" in df_sidebar.columns:
        counts = df_sidebar["Disciplina"].value_counts()
        if not counts.empty:
            disciplina_top = counts.index[0]

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Total registros</div>
            <div class="metric-number">{total}</div>
            <div class="metric-help">clases de prueba registradas</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Disciplina top</div>
            <div class="metric-number" style="font-size: 28px;">{disciplina_top}</div>
            <div class="metric-help">más solicitada</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================
# PÁGINAS
# =========================
if page == "📝 Registrar clase":
    st.markdown('<div class="main-title">REGISTRAR CLASE</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="main-subtitle">Completa los datos para guardar una nueva clase de prueba</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">DATOS DEL CLIENTE</div>', unsafe_allow_html=True)
    st.divider()

    with st.form("registro_clase", clear_on_submit=True):
        col1, col2 = st.columns([2, 1])
        with col1:
            nombre = st.text_input("Nombre *", placeholder="Ej: María García")
        with col2:
            cedula = st.text_input("Cédula *", placeholder="Ej: 1712345678")

        col3, col4, col5 = st.columns([1, 1, 1])
        with col3:
            celular = st.text_input("Celular *", placeholder="Ej: 0991234567")
        with col4:
            fecha_clase = st.date_input("Fecha de clase *", value=date.today(), format="YYYY-MM-DD")
        with col5:
            horario = st.text_input("Horario *", placeholder="Ej: 18:00")

        disciplina = st.selectbox("Disciplina *", DISCIPLINAS)

        submitted = st.form_submit_button("Guardar registro")

        if submitted:
            nombre_clean = clean_text(nombre)
            cedula_clean = only_digits(cedula)
            celular_clean = only_digits(celular)
            horario_clean = clean_text(horario)

            errors = validate_form(nombre_clean, cedula_clean, celular_clean, horario_clean, disciplina)

            df_current = load_data()
            if not df_current.empty and cedula_clean in df_current["Cédula"].astype(str).str.replace(r"\D", "", regex=True).values:
                st.warning("Esta cédula ya existe en la base. Igual puedes guardarla si es una nueva clase, pero revisa que no sea duplicado.")

            if errors:
                for error in errors:
                    st.error(error)
            else:
                record = {
                    "Fecha registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Fecha clase": fecha_clase.strftime("%Y-%m-%d"),
                    "Nombre": nombre_clean,
                    "Cédula": cedula_clean,
                    "Celular": celular_clean,
                    "Horario": horario_clean,
                    "Disciplina": disciplina,
                }
                save_record(record)
                st.success("Registro guardado correctamente en Google Sheets.")

    st.markdown("</div>", unsafe_allow_html=True)

elif page == "📅 Clases de hoy":
    st.markdown('<div class="main-title">CLASES DE HOY</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="main-subtitle">Personas que tienen clase de prueba en la fecha seleccionada</div>',
        unsafe_allow_html=True,
    )

    df = load_data()

    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    fecha_consulta = st.date_input("Selecciona el día a revisar", value=date.today(), format="YYYY-MM-DD")
    fecha_txt = fecha_consulta.strftime("%Y-%m-%d")

    if df.empty:
        st.info("Todavía no existen registros guardados.")
    else:
        clases_dia = df[df["Fecha clase"].astype(str).str[:10] == fecha_txt].copy()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Clases del día</div>
                    <div class="metric-number">{len(clases_dia)}</div>
                    <div class="metric-help">para {fecha_txt}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col2:
            disciplina_top_dia = "Sin datos"
            if not clases_dia.empty:
                disciplina_top_dia = clases_dia["Disciplina"].value_counts().index[0]
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Disciplina top</div>
                    <div class="metric-number" style="font-size: 28px;">{disciplina_top_dia}</div>
                    <div class="metric-help">en la fecha seleccionada</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col3:
            horarios = clases_dia["Horario"].replace("", pd.NA).dropna().nunique() if not clases_dia.empty else 0
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Horarios</div>
                    <div class="metric-number">{horarios}</div>
                    <div class="metric-help">horarios distintos</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown('<div class="section-title">LISTA DEL DÍA</div>', unsafe_allow_html=True)

        if clases_dia.empty:
            st.warning("No hay clases de prueba registradas para ese día.")
        else:
            columnas_vista = ["Fecha clase", "Horario", "Nombre", "Cédula", "Celular", "Disciplina"]
            clases_dia = clases_dia[columnas_vista].sort_values(by=["Horario", "Nombre"], ascending=True)
            st.dataframe(clases_dia, use_container_width=True, hide_index=True)

            csv = clases_dia.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "Descargar lista del día",
                data=csv,
                file_name=f"iron_body_clases_{fecha_txt}.csv",
                mime="text/csv",
            )

    st.markdown("</div>", unsafe_allow_html=True)

elif page == "📊 Dashboard":
    st.markdown('<div class="main-title">DASHBOARD</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="main-subtitle">Resumen de clases de prueba registradas</div>',
        unsafe_allow_html=True,
    )

    df = load_data()

    if df.empty:
        st.info("Todavía no existen registros. Registra la primera clase de prueba para ver el dashboard.")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Total</div>
                    <div class="metric-number">{len(df)}</div>
                    <div class="metric-help">registros generales</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col2:
            hoy = date.today().strftime("%Y-%m-%d")
            clases_hoy = df[df["Fecha clase"].astype(str).str[:10] == hoy]
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Clases hoy</div>
                    <div class="metric-number">{len(clases_hoy)}</div>
                    <div class="metric-help">agendadas para hoy</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col3:
            top = df["Disciplina"].value_counts().index[0]
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Top disciplina</div>
                    <div class="metric-number" style="font-size: 28px;">{top}</div>
                    <div class="metric-help">mayor demanda</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">REGISTROS POR DISCIPLINA</div>', unsafe_allow_html=True)
        chart_df = df["Disciplina"].value_counts().reset_index()
        chart_df.columns = ["Disciplina", "Registros"]
        st.bar_chart(chart_df, x="Disciplina", y="Registros", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">ÚLTIMOS REGISTROS</div>', unsafe_allow_html=True)
        st.dataframe(df.tail(10).sort_index(ascending=False), use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

else:
    st.markdown('<div class="main-title">TODOS LOS REGISTROS</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="main-subtitle">Consulta, filtra y descarga la base de clases de prueba</div>',
        unsafe_allow_html=True,
    )

    df = load_data()

    if df.empty:
        st.info("Todavía no existen registros guardados.")
    else:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            disciplina_filter = st.selectbox("Filtrar por disciplina", ["Todas"] + DISCIPLINAS)
        with col2:
            fecha_filter = st.date_input("Filtrar por fecha de clase", value=None, format="YYYY-MM-DD")
        with col3:
            search = st.text_input("Buscar por nombre, cédula o celular", placeholder="Escribe aquí...")

        filtered = df.copy()
        if disciplina_filter != "Todas":
            filtered = filtered[filtered["Disciplina"] == disciplina_filter]

        if fecha_filter:
            fecha_filter_txt = fecha_filter.strftime("%Y-%m-%d")
            filtered = filtered[filtered["Fecha clase"].astype(str).str[:10] == fecha_filter_txt]

        if search.strip():
            s = search.strip().lower()
            filtered = filtered[
                filtered["Nombre"].astype(str).str.lower().str.contains(s, na=False)
                | filtered["Cédula"].astype(str).str.lower().str.contains(s, na=False)
                | filtered["Celular"].astype(str).str.lower().str.contains(s, na=False)
            ]

        st.dataframe(filtered.sort_index(ascending=False), use_container_width=True, hide_index=True)

        csv = filtered.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "Descargar CSV",
            data=csv,
            file_name="iron_body_clases_prueba.csv",
            mime="text/csv",
        )
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    """
    <br>
    <div class="small-note">
        Iron Body · Sistema conectado a Google Sheets · Base de datos en la nube
    </div>
    """,
    unsafe_allow_html=True,
)
