
from datetime import date, timedelta

import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(
    page_title="Control de Flotilla",
    page_icon="🚐",
    layout="wide",
)

# --------------------------------------------------
# CONEXIÓN
# --------------------------------------------------

@st.cache_resource
def conectar_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )


try:
    supabase = conectar_supabase()
except Exception as e:
    st.error(f"No se pudo conectar con Supabase: {e}")
    st.stop()


# --------------------------------------------------
# CONFIGURACIÓN DE CAMIONETAS
# --------------------------------------------------

CAMIONETAS = [
    "PEZ129C", "PCJ374B", "MES712D", "NTK697C",
    "KJ1540", "MHU436D", "KU2934A", "LND383C",
    "DUCATO SIN PLACAS", "MHU414D", "MLU978D",
    "NEL291C", "KT6231", "KX9785A", "MFX497D",
    "MLA360D", "MLH776D", "MCM900D", "MEH772",
    "MNU185D", "KU4297A", "MES705D", "MRH934D",
    "LH1978", "MUF77FC", "LH1873", "KT62084A",
    "LH1973", "CAMIONETA RANDY SIN PLACA", "MEZ971D",
    "NHA715C", "DUCATO SIN PLACAS 2", "KW3160",
]

INICIAL = {
    "PEZ129C": (500, 500, 0),
    "PCJ374B": (700, 400, 0),
    "MES712D": (500, 400, 0),
    "NTK697C": (800, 400, 0),
    "KJ1540": (0, 350, 0),
    "MHU436D": (400, 400, 0),
    "KU2934A": (0, 400, 0),
    "LND383C": (500, 500, 0),
    "DUCATO SIN PLACAS": (500, 500, 0),
    "MHU414D": (400, 0, 0),
    "MLU978D": (400, 500, 0),
    "NEL291C": (0, 300, 0),
    "KT6231": (0, 350, 0),
    "KX9785A": (0, 400, 0),
    "MFX497D": (400, 400, 0),
    "MLA360D": (450, 300, 0),
    "MLH776D": (500, 0, 0),
    "MCM900D": (500, 500, 0),
    "MEH772": (0, 400, 400),
    "MNU185D": (400, 400, 0),
    "KU4297A": (400, 400, 0),
    "MES705D": (500, 400, 0),
    "MRH934D": (300, 0, 0),
    "LH1978": (350, 0, 0),
    "MUF77FC": (500, 400, 0),
    "LH1873": (300, 350, 0),
    "KT62084A": (350, 350, 0),
    "LH1973": (500, 350, 0),
    "CAMIONETA RANDY SIN PLACA": (300, 400, 0),
    "MEZ971D": (400, 0, 0),
    "NHA715C": (0, 700, 0),
    "DUCATO SIN PLACAS 2": (500, 0, 0),
    "KW3160": (500, 0, 0),
}


# --------------------------------------------------
# BASE DE DATOS
# Requiere una restricción UNIQUE(fecha, placa).
# --------------------------------------------------

def guardar(fecha, placa, importe, observaciones=""):
    datos = {
        "fecha": str(fecha),
        "placa": placa,
        "importe": float(importe),
        "observaciones": observaciones.strip(),
    }

    return (
        supabase.table("gasolina")
        .upsert(datos, on_conflict="fecha,placa")
        .execute()
    )


def leer(desde=None, hasta=None, placa=None):
    consulta = supabase.table("gasolina").select(
        "id,fecha,placa,importe,observaciones"
    )

    if desde:
        consulta = consulta.gte("fecha", str(desde))
    if hasta:
        consulta = consulta.lte("fecha", str(hasta))
    if placa and placa != "Todas":
        consulta = consulta.eq("placa", placa)

    respuesta = (
        consulta.order("fecha", desc=True)
        .order("placa")
        .limit(10000)
        .execute()
    )

    columnas = [
        "id", "fecha", "placa", "importe", "observaciones"
    ]

    df = pd.DataFrame(respuesta.data or [], columns=columnas)

    if not df.empty:
        df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
        df["importe"] = pd.to_numeric(df["importe"], errors="coerce").fillna(0)

    return df


def rango_fechas():
    c1, c2 = st.columns(2)
    desde = c1.date_input(
        "Desde",
        value=date.today() - timedelta(days=6),
        key="desde",
    )
    hasta = c2.date_input(
        "Hasta",
        value=date.today(),
        key="hasta",
    )
    if desde > hasta:
        st.error("La fecha inicial no puede ser posterior a la final.")
        return None
    return desde, hasta


# --------------------------------------------------
# INTERFAZ
# --------------------------------------------------

st.title("🚐 Control de Flotilla")
st.caption("Versión 2.0 · Registro y análisis de gastos")

seccion = st.sidebar.radio(
    "Módulo",
    ["Dashboard", "Registrar gasolina", "Consultar", "Carga inicial"],
)

# --------------------------------------------------
# REGISTRAR GASOLINA
# --------------------------------------------------

if seccion == "Registrar gasolina":
    st.subheader("⛽ Registrar gasto")

    with st.form("form_gasolina"):
        c1, c2 = st.columns(2)
        fecha = c1.date_input("Fecha", value=date.today())
        placa = c2.selectbox("Camioneta", CAMIONETAS)

        importe = st.number_input(
            "Importe ($)",
            min_value=0.0,
            max_value=100000.0,
            value=0.0,
            step=50.0,
            format="%.2f",
        )
        observaciones = st.text_input(
            "Observaciones",
            placeholder="Estación, ticket o comentario (opcional)",
        )

        confirmar = st.checkbox(
            "Confirmo que la fecha, camioneta e importe son correctos."
        )
        enviar = st.form_submit_button(
            "Guardar gasto",
            type="primary",
        )

    if enviar:
        if importe <= 0:
            st.error("El importe debe ser mayor que cero.")
        elif not confirmar:
            st.warning("Confirma los datos antes de guardar.")
        else:
            try:
                guardar(fecha, placa, importe, observaciones)
                st.success(
                    f"Registro guardado: {placa} · "
                    f"${importe:,.2f} · {fecha}"
                )
                st.info(
                    "Si ya había un registro de esa camioneta "
                    "en esa fecha, se actualizó en lugar de duplicarse."
                )
            except Exception as e:
                st.error(f"No se pudo guardar en Supabase: {e}")


# --------------------------------------------------
# CONSULTAR
# --------------------------------------------------

elif seccion == "Consultar":
    st.subheader("🔎 Consultar gastos")

    fechas = rango_fechas()
    placa = st.selectbox("Camioneta", ["Todas"] + CAMIONETAS)

    if fechas:
        try:
            df = leer(fechas[0], fechas[1], placa)

            if df.empty:
                st.info("No hay registros en el periodo seleccionado.")
            else:
                st.metric("Total del periodo", f"${df['importe'].sum():,.2f}")
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "importe": st.column_config.NumberColumn(
                            "Importe ($)", format="$%.2f"
                        )
                    },
                )

                st.download_button(
                    "Descargar CSV",
                    df.to_csv(index=False).encode("utf-8-sig"),
                    "gasolina_consulta.csv",
                    "text/csv",
                )
        except Exception as e:
            st.error(f"Error al consultar los registros: {e}")


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

elif seccion == "Dashboard":
    st.subheader("📊 Resumen operativo")

    fechas = rango_fechas()

    if fechas:
        try:
            df = leer(fechas[0], fechas[1])

            if df.empty:
                st.info("No hay gastos registrados en este periodo.")
            else:
                total = df["importe"].sum()
                dias = max((fechas[1] - fechas[0]).days + 1, 1)
                promedio = total / dias
                por_placa = (
                    df.groupby("placa")["importe"]
                    .sum()
                    .sort_values(ascending=False)
                )
                por_dia = (
                    df.groupby("fecha")["importe"]
                    .sum()
                    .sort_index()
                )

                m1, m2, m3 = st.columns(3)
                m1.metric("Gasto total", f"${total:,.2f}")
                m2.metric("Camionetas con gasto", df["placa"].nunique())
                m3.metric("Promedio diario", f"${promedio:,.2f}")

                st.write("### Gasto por día")
                st.bar_chart(por_dia)

                st.write("### Gasto por camioneta")
                st.bar_chart(por_placa)

                st.write("### Registros recientes")
                st.dataframe(
                    df.head(10),
                    use_container_width=True,
                    hide_index=True,
                )

        except Exception as e:
            st.error(f"No se pudo cargar el dashboard: {e}")


# --------------------------------------------------
# CARGA INICIAL IDEMPOTENTE
# --------------------------------------------------

else:
    st.subheader("📥 Carga inicial")

    st.warning(
        "Esta carga utiliza una combinación de fecha y camioneta. "
        "Si ya existe ese registro, actualiza el importe. "
        "No la uses para importar otra vez datos históricos "
        "sin verificar primero las fechas."
    )

    lunes = st.date_input(
        "Fecha del lunes de la tabla original",
        value=date.today() - timedelta(days=date.today().weekday()),
    )

    st.write("Totales de referencia: lunes $11,850 · martes $10,750 · miércoles $400.")

    confirmar_carga = st.checkbox(
        "Confirmo que las fechas corresponden a la tabla original."
    )

    if st.button("Cargar datos iniciales", type="primary"):
        if not confirmar_carga:
            st.warning("Confirma las fechas antes de cargar.")
        else:
            try:
                cantidad = 0

                for placa, importes in INICIAL.items():
                    for offset, importe in enumerate(importes):
                        if importe > 0:
                            guardar(
                                lunes + timedelta(days=offset),
                                placa,
                                importe,
                                "Carga inicial desde tabla",
                            )
                            cantidad += 1

                st.success(
                    f"Proceso terminado. Se procesaron {cantidad} "
                    "combinaciones de fecha y camioneta."
                )
                st.info(
                    "Los registros existentes se actualizaron. "
                    "Consulta el periodo para verificar los totales."
                )
            except Exception as e:
                st.error(f"Falló la carga inicial: {e}")


      
