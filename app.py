
from datetime import date, timedelta

import pandas as pd
import streamlit as st
from supabase import create_client


# ---------------------------------------------------------
# CONFIGURACIÓN GENERAL
# ---------------------------------------------------------

st.set_page_config(
    page_title="Control de Flotilla",
    page_icon="🚐",
    layout="wide"
)


# ---------------------------------------------------------
# CONEXIÓN A SUPABASE
# ---------------------------------------------------------

@st.cache_resource
def conectar_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )


supabase = conectar_supabase()


# ---------------------------------------------------------
# CAMIONETAS
# ---------------------------------------------------------

CAMIONETAS = [
    "PEZ129C",
    "PCJ374B",
    "MES712D",
    "NTK697C",
    "KJ1540",
    "MHU436D",
    "KU2934A",
    "LND383C",
    "DUCATO SIN PLACAS",
    "MHU414D",
    "MLU978D",
    "NEL291C",
    "KT6231",
    "KX9785A",
    "MFX497D",
    "MLA360D",
    "MLH776D",
    "MCM900D",
    "MEH772",
    "MNU185D",
    "KU4297A",
    "MES705D",
    "MRH934D",
    "LH1978",
    "MUF77FC",
    "LH1873",
    "KT62084A",
    "LH1973",
    "CAMIONETA RANDY SIN PLACA",
    "MEZ971D",
    "NHA715C",
    "DUCATO SIN PLACAS 2",
    "KW3160"
]


# ---------------------------------------------------------
# DATOS INICIALES
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# FUNCIONES DE BASE DE DATOS
# ---------------------------------------------------------

def guardar(fecha, placa, importe, obs=""):
    """
    Guarda un registro en Supabase.

    Si ya existe un registro para la misma fecha y placa,
    actualiza el importe y las observaciones.
    """

    fecha_texto = str(fecha)

    existente = (
        supabase
        .table("gasolina")
        .select("id")
        .eq("fecha", fecha_texto)
        .eq("placa", placa)
        .execute()
    )

    datos = {
        "fecha": fecha_texto,
        "placa": placa,
        "importe": float(importe),
        "observaciones": obs
    }

    if existente.data:
        registro_id = existente.data[0]["id"]

        (
            supabase
            .table("gasolina")
            .update(datos)
            .eq("id", registro_id)
            .execute()
        )

    else:
        (
            supabase
            .table("gasolina")
            .insert(datos)
            .execute()
        )


def leer(desde=None, hasta=None, placa=None):
    """
    Lee los registros directamente desde Supabase.
    """

    consulta = (
        supabase
        .table("gasolina")
        .select("fecha,placa,importe,observaciones")
    )

    if desde:
        consulta = consulta.gte("fecha", str(desde))

    if hasta:
        consulta = consulta.lte("fecha", str(hasta))

    if placa and placa != "Todas":
        consulta = consulta.eq("placa", placa)

    respuesta = (
        consulta
        .order("fecha")
        .order("placa")
        .execute()
    )

    if not respuesta.data:
        return pd.DataFrame(
            columns=[
                "fecha",
                "placa",
                "importe",
                "observaciones"
            ]
        )

    df = pd.DataFrame(respuesta.data)

    df["fecha"] = pd.to_datetime(df["fecha"])
    df["importe"] = pd.to_numeric(
        df["importe"],
        errors="coerce"
    ).fillna(0)

    return df


# ---------------------------------------------------------
# INTERFAZ
# ---------------------------------------------------------

st.title("🚐 Control de Flotilla")
st.caption("Primera versión: control de gasolina por camioneta")


seccion = st.sidebar.radio(
    "Módulo",
    [
        "Dashboard",
        "Registrar gasolina",
        "Consultar",
        "Carga inicial"
    ]
)


# ---------------------------------------------------------
# REGISTRAR GASOLINA
# ---------------------------------------------------------

if seccion == "Registrar gasolina":

    st.subheader("Registrar gasolina")

    c1, c2, c3 = st.columns(3)

    fecha = c1.date_input(
        "Fecha",
        value=date.today()
    )

    placa = c2.selectbox(
        "Camioneta",
        CAMIONETAS
    )

    importe = c3.number_input(
        "Importe ($)",
        min_value=0.0,
        step=50.0,
        format="%.2f"
    )

    obs = st.text_input(
        "Observaciones",
        placeholder="Opcional"
    )

    if st.button(
        "Guardar gasto",
        type="primary"
    ):

        try:

            guardar(
                fecha,
                placa,
                importe,
                obs
            )

            st.success(
                f"Guardado en Supabase: "
                f"{placa} — "
                f"${importe:,.2f} — "
                f"{fecha}"
            )

        except Exception as e:

            st.error(
                f"No se pudo guardar el registro: {e}"
            )


# ---------------------------------------------------------
# CARGA INICIAL
# ---------------------------------------------------------

elif seccion == "Carga inicial":

    st.subheader(
        "Cargar datos de la tabla que ya tienes"
    )

    st.write(
        "Elige la fecha que corresponde al **lunes** "
        "de esa tabla. La app colocará automáticamente "
        "lunes, martes y miércoles."
    )

    lunes = st.date_input(
        "Fecha del lunes",
        value=date.today()
        - timedelta(days=date.today().weekday())
    )

    st.info(
        "Totales de la tabla: "
        "lunes $11,850 · "
        "martes $10,750 · "
        "miércoles $400."
    )

    if st.button(
        "Cargar datos iniciales",
        type="primary"
    ):

        try:

            for placa, (lun, mar, mie) in INICIAL.items():

                importes = [
                    lun,
                    mar,
                    mie
                ]

                for offset, importe in enumerate(importes):

                    if importe > 0:

                        guardar(
                            lunes + timedelta(days=offset),
                            placa,
                            importe,
                            "Carga inicial desde tabla"
                        )

            st.success(
                "Datos iniciales cargados correctamente "
                "en Supabase. Si vuelves a pulsar, "
                "los registros existentes se actualizan."
            )

        except Exception as e:

            st.error(
                f"No se pudieron cargar los datos: {e}"
            )


# ---------------------------------------------------------
# CONSULTAR
# ---------------------------------------------------------

elif seccion == "Consultar":

    st.subheader(
        "Consulta por camioneta"
    )

    c1, c2, c3 = st.columns(3)

    placa = c1.selectbox(
        "Camioneta",
        ["Todas"] + CAMIONETAS
    )

    desde = c2.date_input(
        "Desde",
        value=date.today() - timedelta(days=6)
    )

    hasta = c3.date_input(
        "Hasta",
        value=date.today()
    )

    try:

        df = leer(
            desde,
            hasta,
            placa
        )

        if df.empty:

            st.warning(
                "No hay registros en ese periodo."
            )

        else:

            total = df["importe"].sum()

            st.metric(
                "Total de gasolina",
                f"${total:,.2f}"
            )

            mostrar = df.copy()

            mostrar["fecha"] = (
                mostrar["fecha"].dt.date
            )

            mostrar["importe"] = (
                mostrar["importe"]
                .map(lambda x: f"${x:,.2f}")
            )

            st.dataframe(
                mostrar,
                use_container_width=True,
                hide_index=True
            )

            csv = (
                df
                .to_csv(index=False)
                .encode("utf-8-sig")
            )

            st.download_button(
                "Descargar CSV",
                csv,
                "gasolina_consulta.csv",
                "text/csv"
            )

    except Exception as e:

        st.error(
            f"No se pudieron consultar los datos: {e}"
        )


# ---------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------

else:

    st.subheader("Dashboard")

    c1, c2 = st.columns(2)

    desde = c1.date_input(
        "Desde",
        value=date.today() - timedelta(days=6),
        key="d1"
    )

    hasta = c2.date_input(
        "Hasta",
        value=date.today(),
        key="d2"
    )

    try:

        df = leer(
            desde,
            hasta
        )

        if df.empty:

            st.info(
                "Aún no hay datos en este periodo. "
                "Ve a 'Carga inicial' o registra un gasto."
            )

        else:

            total = df["importe"].sum()

            por_placa = (
                df
                .groupby(
                    "placa",
                    as_index=False
                )["importe"]
                .sum()
                .sort_values(
                    "importe",
                    ascending=False
                )
            )

            por_dia = (
                df
                .groupby(
                    "fecha",
                    as_index=False
                )["importe"]
                .sum()
            )

            m1, m2, m3 = st.columns(3)

            m1.metric(
                "Gasolina total",
                f"${total:,.2f}"
            )

            m2.metric(
                "Camionetas con gasto",
                f"{df['placa'].nunique()}"
            )

            top = por_placa.iloc[0]

            m3.metric(
                "Mayor gasto",
                f"{top['placa']}",
                f"${top['importe']:,.2f}"
            )

            st.write("### Gasto por día")

            st.bar_chart(
                por_dia
                .set_index("fecha")["importe"]
            )

            st.write(
                "### Total por camioneta"
            )

            tabla = por_placa.copy()

            tabla["importe"] = (
                tabla["importe"]
                .map(lambda x: f"${x:,.2f}")
            )

            st.dataframe(
                tabla,
                use_container_width=True,
                hide_index=True
            )

    except Exception as e:

        st.error(
            f"No se pudieron cargar los datos: {e}"
        )

      
