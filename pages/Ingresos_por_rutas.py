
from datetime import date, timedelta

import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(
    page_title="Ingresos por rutas",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Ingresos por rutas")
st.caption("Control de ingresos de Mercado Libre por camioneta y día")


# CONEXIÓN A SUPABASE
@st.cache_resource
def conectar():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )


try:
    supabase = conectar()
except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.stop()


# OBTENER CAMIONETAS REGISTRADAS
@st.cache_data(ttl=60)
def obtener_camionetas():
    placas = set()

    for tabla in ["gasolina", "kilometraje", "mantenimientos"]:
        try:
            respuesta = (
                supabase.table(tabla)
                .select("placa")
                .limit(1000)
                .execute()
            )

            for fila in respuesta.data:
                placa = fila.get("placa")
                if placa:
                    placas.add(placa.strip().upper())

        except Exception:
            pass

    return sorted(placas)


# CONSULTAR INGRESOS
def consultar_ingresos():
    respuesta = (
        supabase.table("ingresos_rutas")
        .select("*")
        .order("fecha", desc=True)
        .limit(10000)
        .execute()
    )

    return pd.DataFrame(respuesta.data)


tab1, tab2 = st.tabs([
    "Registrar ingreso",
    "Consultar ingresos"
])


# REGISTRAR INGRESOS
with tab1:
    st.subheader("Registrar ruta realizada")

    placas = obtener_camionetas()

    with st.form("formulario_ingresos"):
        col1, col2 = st.columns(2)

        with col1:
            fecha = st.date_input(
                "Fecha de la ruta",
                value=date.today()
            )

            opciones = placas + ["Otra camioneta"]

            camioneta = st.selectbox(
                "Camioneta",
                opciones
            )

            placa_manual = ""

            if camioneta == "Otra camioneta":
                placa_manual = st.text_input(
                    "Escribe la placa o nombre de la unidad"
                )

            numero_ruta = st.selectbox(
                "Número de ruta",
                [1, 2]
            )

        with col2:
            chofer = st.text_input("Nombre del chofer")

            tipo_ruta = st.selectbox(
                "Tipo de ruta",
                ["Small", "Large", "Extra Large"]
            )

            importe = st.number_input(
                "Ingreso de la ruta ($)",
                min_value=0.0,
                step=50.0,
                format="%.2f"
            )

        observaciones = st.text_area(
            "Observaciones (opcional)"
        )

        confirmar = st.checkbox(
            "Confirmo que los datos son correctos"
        )

        guardar = st.form_submit_button(
            "Guardar ingreso",
            type="primary"
        )

    if guardar:
        placa = (
            placa_manual.strip().upper()
            if camioneta == "Otra camioneta"
            else camioneta
        )

        if not placa or not chofer.strip():
            st.warning("Completa la camioneta y el chofer.")

        elif importe <= 0:
            st.warning("El ingreso debe ser mayor a cero.")

        elif not confirmar:
            st.warning("Confirma los datos antes de guardar.")

        else:
            try:
                existente = (
                    supabase.table("ingresos_rutas")
                    .select("id")
                    .eq("fecha", fecha.isoformat())
                    .eq("placa", placa)
                    .eq("numero_ruta", numero_ruta)
                    .limit(1)
                    .execute()
                )

                if existente.data:
                    st.warning(
                        "Esta camioneta ya tiene registrada "
                        "esa ruta en la fecha seleccionada."
                    )

                else:
                    datos = {
                        "fecha": fecha.isoformat(),
                        "placa": placa,
                        "numero_ruta": numero_ruta,
                        "chofer": chofer.strip(),
                        "tipo_ruta": tipo_ruta,
                        "importe": float(importe),
                        "observaciones": observaciones.strip()
                    }

                    supabase.table("ingresos_rutas").insert(
                        datos
                    ).execute()

                    st.success(
                        "Ingreso registrado correctamente."
                    )

            except Exception as e:
                st.error(f"No se pudo guardar: {e}")


# CONSULTAR INGRESOS
with tab2:
    st.subheader("Historial de ingresos")

    col1, col2 = st.columns(2)

    with col1:
        desde = st.date_input(
            "Desde",
            value=date.today() - timedelta(days=6),
            key="ingresos_desde"
        )

    with col2:
        hasta = st.date_input(
            "Hasta",
            value=date.today(),
            key="ingresos_hasta"
        )

    try:
        df = consultar_ingresos()

        if df.empty:
            st.info("Todavía no hay ingresos registrados.")

        else:
            df["fecha"] = pd.to_datetime(df["fecha"])
            df["importe"] = pd.to_numeric(df["importe"])

            df = df[
                (df["fecha"].dt.date >= desde) &
                (df["fecha"].dt.date <= hasta)
            ].copy()

            placas_filtro = sorted(
                df["placa"].dropna().unique().tolist()
            )

            filtro = st.selectbox(
                "Filtrar por camioneta",
                ["Todas"] + placas_filtro
            )

            if filtro != "Todas":
                df = df[df["placa"] == filtro]

            total = df["importe"].sum()

            c1, c2 = st.columns(2)

            c1.metric(
                "Ingresos del periodo",
                f"${total:,.2f}"
            )

            c2.metric(
                "Rutas registradas",
                len(df)
            )

            if not df.empty:
                st.subheader("Ingresos por camioneta")

                resumen = (
                    df.groupby("placa")["importe"]
                    .sum()
                    .sort_values(ascending=False)
                )

                st.bar_chart(resumen)

                st.subheader("Detalle de rutas")

                columnas = [
                    "fecha",
                    "placa",
                    "numero_ruta",
                    "chofer",
                    "tipo_ruta",
                    "importe",
                    "observaciones"
                ]

                st.dataframe(
                    df[columnas],
                    use_container_width=True,
                    hide_index=True
                )

                csv = df.to_csv(index=False).encode("utf-8-sig")

                st.download_button(
                    "Descargar ingresos CSV",
                    data=csv,
                    file_name="ingresos_rutas.csv",
                    mime="text/csv"
                )

            else:
                st.info(
                    "No hay ingresos en el periodo seleccionado."
                )

    except Exception as e:
        st.error(f"Error al consultar ingresos: {e}")
