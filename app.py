
from datetime import date, timedelta

import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(
    page_title="Control de Flotilla",
    page_icon="🚐",
    layout="wide"
)

# ==========================================
# CONEXION CON SUPABASE
# ==========================================

@st.cache_resource
def conectar_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

try:
    supabase = conectar_supabase()
except Exception as e:
    st.error(f"No se pudo conectar con Supabase: {e}")
    st.stop()


# ==========================================
# CAMIONETAS
# ==========================================

CAMIONETAS = [
    "PEZ129C", "PCJ374B", "MES712D", "NTK697C",
    "KJ1540", "MHU436D", "KU2934A", "LND383C",
    "DUCATO SIN PLACAS", "MHU414D", "MLU978D",
    "NEL291C", "KT6231", "KX9785A", "MFX497D",
    "MLA360D", "MLH776D", "MCM900D", "MEH772",
    "MNU185D", "KU4297A", "MES705D", "MRH934D",
    "LH1978", "MUF77FC", "LH1873", "KT62084A",
    "LH1973", "CAMIONETA RANDY SIN PLACA",
    "MEZ971D", "NHA715C", "DUCATO SIN PLACAS 2",
    "KW3160"
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
    "KW3160": (500, 0, 0)
}


# ==========================================
# FUNCIONES GENERALES
# ==========================================

def consultar_tabla(tabla, columnas, placa=None,
                    desde=None, hasta=None):

    consulta = supabase.table(tabla).select("*")

    if placa and placa != "Todas":
        consulta = consulta.eq("placa", placa)

    if desde:
        consulta = consulta.gte("fecha", str(desde))

    if hasta:
        consulta = consulta.lte("fecha", str(hasta))

    respuesta = (
        consulta.order("fecha", desc=True)
        .limit(10000)
        .execute()
    )

    df = pd.DataFrame(
        respuesta.data or [],
        columns=columnas
    )

    if not df.empty:
        df["fecha"] = pd.to_datetime(
            df["fecha"]
        ).dt.date

    return df


def guardar(fecha, placa, importe, observaciones=""):

    datos = {
        "fecha": str(fecha),
        "placa": placa,
        "importe": float(importe),
        "observaciones": observaciones.strip()
    }

    return (
        supabase.table("gasolina")
        .upsert(datos, on_conflict="fecha,placa")
        .execute()
    )


def leer(desde=None, hasta=None, placa=None):

    df = consultar_tabla(
        "gasolina",
        ["id", "fecha", "placa",
         "importe", "observaciones"],
        placa, desde, hasta
    )

    if not df.empty:
        df["importe"] = pd.to_numeric(
            df["importe"], errors="coerce"
        ).fillna(0)

    return df


def guardar_kilometraje(fecha, placa, km,
                        observaciones=""):

    datos = {
        "fecha": str(fecha),
        "placa": placa,
        "kilometraje": int(km),
        "observaciones": observaciones.strip()
    }

    return (
        supabase.table("kilometraje")
        .upsert(datos, on_conflict="fecha,placa")
        .execute()
    )


def leer_kilometrajes(placa=None):

    df = consultar_tabla(
        "kilometraje",
        ["id", "fecha", "placa",
         "kilometraje", "observaciones"],
        placa
    )

    if not df.empty:
        df["kilometraje"] = pd.to_numeric(
            df["kilometraje"], errors="coerce"
        ).fillna(0)

    return df


# ==========================================
# FUNCIONES DE MANTENIMIENTO
# ==========================================

def guardar_mantenimiento(
    fecha, placa, categoria, tipo_servicio,
    kilometraje, costo, taller, observaciones
):

    datos = {
        "fecha": str(fecha),
        "placa": placa,
        "categoria": categoria,
        "tipo_servicio": tipo_servicio,
        "kilometraje": kilometraje,
        "costo": float(costo),
        "taller": taller.strip(),
        "observaciones": observaciones.strip()
    }

    return (
        supabase.table("mantenimientos")
        .insert(datos)
        .execute()
    )


def leer_mantenimientos(
    placa=None, desde=None, hasta=None
):

    columnas = [
        "id", "fecha", "placa", "categoria",
        "tipo_servicio", "kilometraje",
        "costo", "taller", "observaciones"
    ]

    df = consultar_tabla(
        "mantenimientos",
        columnas, placa, desde, hasta
    )

    if not df.empty:
        df["costo"] = pd.to_numeric(
            df["costo"], errors="coerce"
        ).fillna(0)

    return df


def rango_fechas(clave="general"):

    c1, c2 = st.columns(2)

    desde = c1.date_input(
        "Desde",
        value=date.today() - timedelta(days=6),
        key=f"desde_{clave}"
    )

    hasta = c2.date_input(
        "Hasta",
        value=date.today(),
        key=f"hasta_{clave}"
    )

    if desde > hasta:
        st.error(
            "La fecha inicial no puede ser posterior "
            "a la fecha final."
        )
        return None

    return desde, hasta


# ==========================================
# MENU PRINCIPAL
# ==========================================

st.title("🚐 Control de Flotilla")
st.caption(
    "Versión 2.2 · Gasolina, kilometraje y mantenimiento"
)

seccion = st.sidebar.radio(
    "Módulo",
    [
        "Dashboard",
        "Registrar gasolina",
        "Consultar",
        "Kilometraje",
        "Mantenimiento",
        "Carga inicial"
    ]
)


# ==========================================
# DASHBOARD
# ==========================================

if seccion == "Dashboard":

    st.subheader("📊 Resumen operativo")

    fechas = rango_fechas("dashboard")

    if fechas:
        try:
            df = leer(fechas[0], fechas[1])

            if df.empty:
                st.info(
                    "No hay gastos registrados "
                    "en este periodo."
                )

            else:
                total = df["importe"].sum()

                dias = max(
                    (fechas[1] - fechas[0]).days + 1,
                    1
                )

                m1, m2, m3 = st.columns(3)

                m1.metric(
                    "Gasto total",
                    f"${total:,.2f}"
                )

                m2.metric(
                    "Camionetas con gasto",
                    df["placa"].nunique()
                )

                m3.metric(
                    "Promedio diario",
                    f"${total / dias:,.2f}"
                )

                por_dia = (
                    df.groupby("fecha")["importe"]
                    .sum()
                    .sort_index()
                )

                por_placa = (
                    df.groupby("placa")["importe"]
                    .sum()
                    .sort_values(ascending=False)
                )

                st.write("### Gasto por día")
                st.bar_chart(por_dia)

                st.write("### Gasto por camioneta")
                st.bar_chart(por_placa)

                st.write("### Registros recientes")

                st.dataframe(
                    df.head(10),
                    use_container_width=True,
                    hide_index=True
                )

        except Exception as e:
            st.error(f"Error al cargar dashboard: {e}")


# ==========================================
# REGISTRAR GASOLINA
# ==========================================

elif seccion == "Registrar gasolina":

    st.subheader("⛽ Registrar gasto de gasolina")

    with st.form("form_gasolina"):

        c1, c2 = st.columns(2)

        fecha = c1.date_input(
            "Fecha",
            value=date.today()
        )

        placa = c2.selectbox(
            "Camioneta",
            CAMIONETAS
        )

        importe = st.number_input(
            "Importe ($)",
            min_value=0.0,
            max_value=100000.0,
            value=0.0,
            step=50.0,
            format="%.2f"
        )

        observaciones = st.text_input(
            "Observaciones",
            placeholder="Estación, ticket o comentario"
        )

        confirmar = st.checkbox(
            "Confirmo que los datos son correctos."
        )

        enviar = st.form_submit_button(
            "Guardar gasto",
            type="primary"
        )

    if enviar:

        if importe <= 0:
            st.error("El importe debe ser mayor que cero.")

        elif not confirmar:
            st.warning("Confirma los datos.")

        else:
            try:
                guardar(
                    fecha, placa,
                    importe, observaciones
                )

                st.success(
                    f"Gasto guardado: {placa} · "
                    f"${importe:,.2f}"
                )

                st.info(
                    "Si ya había un gasto de esa "
                    "camioneta en esa fecha, "
                    "se actualizó el registro."
                )

            except Exception as e:
                st.error(f"Error al guardar: {e}")


# ==========================================
# CONSULTAR GASOLINA
# ==========================================

elif seccion == "Consultar":

    st.subheader("🔎 Consultar gastos")

    fechas = rango_fechas("gasolina")

    placa = st.selectbox(
        "Camioneta",
        ["Todas"] + CAMIONETAS
    )

    if fechas:
        try:
            df = leer(
                fechas[0], fechas[1], placa
            )

            if df.empty:
                st.info(
                    "No hay registros en este periodo."
                )

            else:
                st.metric(
                    "Total del periodo",
                    f"${df['importe'].sum():,.2f}"
                )

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )

                st.download_button(
                    "Descargar CSV",
                    df.to_csv(index=False).encode(
                        "utf-8-sig"
                    ),
                    "gasolina_consulta.csv",
                    "text/csv"
                )

        except Exception as e:
            st.error(f"Error al consultar: {e}")


# ==========================================
# KILOMETRAJE SEMANAL
# ==========================================

elif seccion == "Kilometraje":

    st.subheader("🚐 Kilometraje semanal")

    st.caption(
        "Solicita cada lunes por WhatsApp "
        "la foto del odómetro. "
        "El kilometraje corresponde a la camioneta, "
        "no al chofer."
    )

    tab1, tab2 = st.tabs([
        "Registrar kilometraje",
        "Consultar historial"
    ])

    with tab1:

        lunes_actual = (
            date.today()
            - timedelta(days=date.today().weekday())
        )

        with st.form("form_kilometraje"):

            c1, c2 = st.columns(2)

            fecha_km = c1.date_input(
                "Fecha de lectura",
                value=lunes_actual
            )

            placa_km = c2.selectbox(
                "Camioneta",
                CAMIONETAS
            )

            km = st.number_input(
                "Kilometraje del odómetro",
                min_value=0,
                max_value=9999999,
                value=0,
                step=1
            )

            obs_km = st.text_input(
                "Observaciones",
                placeholder="Chofer o comentario"
            )

            confirmar_km = st.checkbox(
                "Confirmo la placa, fecha y kilometraje."
            )

            enviar_km = st.form_submit_button(
                "Guardar kilometraje",
                type="primary"
            )

        if enviar_km:

            if not confirmar_km:
                st.warning("Confirma los datos.")

            elif fecha_km > date.today():
                st.error(
                    "No puedes registrar una fecha futura."
                )

            else:
                try:
                    historial = leer_kilometrajes(
                        placa_km
                    )

                    otros = historial[
                        historial["fecha"] != fecha_km
                    ]

                    anteriores = otros[
                        otros["fecha"] < fecha_km
                    ]

                    posteriores = otros[
                        otros["fecha"] > fecha_km
                    ]

                    error = None

                    if not anteriores.empty:
                        anterior = int(
                            anteriores.sort_values(
                                "fecha"
                            ).iloc[-1]["kilometraje"]
                        )

                        if km < anterior:
                            error = (
                                "El kilometraje es menor "
                                "que una lectura anterior."
                            )

                    if not posteriores.empty:
                        posterior = int(
                            posteriores.sort_values(
                                "fecha"
                            ).iloc[0]["kilometraje"]
                        )

                        if km > posterior:
                            error = (
                                "El kilometraje supera "
                                "una lectura posterior."
                            )

                    if error:
                        st.error(error)

                    else:
                        guardar_kilometraje(
                            fecha_km,
                            placa_km,
                            km,
                            obs_km
                        )

                        st.success(
                            "Kilometraje guardado correctamente."
                        )

                        st.info(
                            "Una nueva lectura con la misma "
                            "fecha y camioneta reemplazará "
                            "la lectura existente."
                        )

                except Exception as e:
                    st.error(
                        f"Error al guardar kilometraje: {e}"
                    )

    with tab2:

        placa_consulta = st.selectbox(
            "Consultar camioneta",
            ["Todas"] + CAMIONETAS,
            key="consulta_km"
        )

        try:
            df = leer_kilometrajes(
                placa_consulta
            )

            if df.empty:
                st.info(
                    "Todavía no hay lecturas "
                    "de kilometraje registradas."
                )

            else:
                st.metric(
                    "Lecturas registradas",
                    len(df)
                )

                if placa_consulta != "Todas":

                    ordenado = df.sort_values("fecha")

                    ultimo = ordenado.iloc[-1]

                    st.metric(
                        "Última lectura",
                        f"{int(ultimo['kilometraje']):,} km"
                    )

                    if len(ordenado) >= 2:

                        previo = ordenado.iloc[-2]

                        diferencia = (
                            int(ultimo["kilometraje"])
                            - int(previo["kilometraje"])
                        )

                        st.metric(
                            "Recorrido entre últimas lecturas",
                            f"{diferencia:,} km"
                        )

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )

                st.download_button(
                    "Descargar kilometrajes CSV",
                    df.to_csv(index=False).encode(
                        "utf-8-sig"
                    ),
                    "kilometrajes.csv",
                    "text/csv"
                )

        except Exception as e:
            st.error(
                f"Error al consultar kilometraje: {e}"
            )


# ==========================================
# NUEVO MODULO: MANTENIMIENTO
# ==========================================

elif seccion == "Mantenimiento":

    st.subheader("🔧 Control de mantenimiento")

    st.caption(
        "Registra servicios preventivos y "
        "reparaciones correctivas por camioneta."
    )

    tab_registro, tab_historial = st.tabs([
        "Registrar mantenimiento",
        "Consultar historial"
    ])

    # --------------------------------------
    # REGISTRAR MANTENIMIENTO
    # --------------------------------------

    with tab_registro:

        with st.form("form_mantenimiento"):

            c1, c2 = st.columns(2)

            fecha_m = c1.date_input(
                "Fecha del servicio",
                value=date.today()
            )

            placa_m = c2.selectbox(
                "Camioneta",
                CAMIONETAS,
                key="placa_mantenimiento"
            )

            categoria = st.selectbox(
                "Categoría",
                ["Preventivo", "Correctivo"]
            )

            servicios_preventivos = [
                "Cambio de aceite",
                "Cambio de filtros",
                "Cambio de anticongelante",
                "Revisión de frenos",
                "Revisión de suspensión",
                "Afinación",
                "Revisión general",
                "Cambio de llantas",
                "Otro"
            ]

            servicios_correctivos = [
                "Reparación de motor",
                "Reparación de transmisión",
                "Reparación de frenos",
                "Reparación de suspensión",
                "Sistema de enfriamiento",
                "Sistema eléctrico",
                "Reparación de llantas",
                "Falla mecánica general",
                "Otro"
            ]

            if categoria == "Preventivo":
                opciones = servicios_preventivos
            else:
                opciones = servicios_correctivos

            tipo_servicio = st.selectbox(
                "Servicio realizado",
                opciones
            )

            if tipo_servicio == "Otro":
                tipo_servicio = st.text_input(
                    "Especifica el servicio"
                ).strip()

            c3, c4 = st.columns(2)

            km_m = c3.number_input(
                "Kilometraje al realizar el servicio",
                min_value=0,
                max_value=9999999,
                value=0,
                step=1
            )

            costo_m = c4.number_input(
                "Costo del mantenimiento ($)",
                min_value=0.0,
                max_value=1000000.0,
                value=0.0,
                step=100.0,
                format="%.2f"
            )

            taller = st.text_input(
                "Taller o mecánico",
                placeholder="Nombre del taller o responsable"
            )

            observaciones_m = st.text_area(
                "Observaciones",
                placeholder=(
                    "Describe el trabajo realizado, "
                    "refacciones utilizadas o falla detectada."
                )
            )

            confirmar_m = st.checkbox(
                "Confirmo que los datos del servicio son correctos."
            )

            enviar_m = st.form_submit_button(
                "Guardar mantenimiento",
                type="primary"
            )

        if enviar_m:

            if not confirmar_m:
                st.warning(
                    "Debes confirmar los datos."
                )

            elif fecha_m > date.today():
                st.error(
                    "La fecha no puede ser futura."
                )

            elif not tipo_servicio:
                st.error(
                    "Especifica el servicio realizado."
                )

            else:
                try:
                    guardar_mantenimiento(
                        fecha_m,
                        placa_m,
                        categoria,
                        tipo_servicio,
                        km_m if km_m > 0 else None,
                        costo_m,
                        taller,
                        observaciones_m
                    )

                    st.success(
                        "¡Mantenimiento registrado correctamente!"
                    )

                    st.write(
                        f"**Camioneta:** {placa_m}"
                    )

                    st.write(
                        f"**Categoría:** {categoria}"
                    )

                    st.write(
                        f"**Servicio:** {tipo_servicio}"
                    )

                    st.write(
                        f"**Costo:** ${costo_m:,.2f}"
                    )

                except Exception as e:
                    st.error(
                        f"No se pudo guardar: {e}"
                    )

    # --------------------------------------
    # CONSULTAR MANTENIMIENTOS
    # --------------------------------------

    with tab_historial:

        st.write("### Historial de servicios")

        placa_filtro = st.selectbox(
            "Camioneta",
            ["Todas"] + CAMIONETAS,
            key="filtro_mantenimiento"
        )

        categoria_filtro = st.selectbox(
            "Categoría",
            ["Todas", "Preventivo", "Correctivo"],
            key="categoria_filtro"
        )

        fechas_m = rango_fechas(
            "mantenimiento"
        )

        if fechas_m:
            try:
                df_m = leer_mantenimientos(
                    placa_filtro,
                    fechas_m[0],
                    fechas_m[1]
                )

                if categoria_filtro != "Todas":
                    df_m = df_m[
                        df_m["categoria"] == categoria_filtro
                    ]

                if df_m.empty:
                    st.info(
                        "Todavía no hay mantenimientos "
                        "registrados para estos filtros."
                    )

                else:
                    total_m = df_m["costo"].sum()

                    total_preventivo = df_m.loc[
                        df_m["categoria"] == "Preventivo",
                        "costo"
                    ].sum()

                    total_correctivo = df_m.loc[
                        df_m["categoria"] == "Correctivo",
                        "costo"
                    ].sum()

                    m1, m2, m3 = st.columns(3)

                    m1.metric(
                        "Gasto total",
                        f"${total_m:,.2f}"
                    )

                    m2.metric(
                        "Mantenimiento preventivo",
                        f"${total_preventivo:,.2f}"
                    )

                    m3.metric(
                        "Mantenimiento correctivo",
                        f"${total_correctivo:,.2f}"
                    )

                    st.write(
                        "### Gastos por categoría"
                    )

                    resumen_categoria = (
                        df_m.groupby("categoria")["costo"]
                        .sum()
                    )

                    st.bar_chart(
                        resumen_categoria
                    )

                    st.write(
                        "### Gastos por camioneta"
                    )

                    resumen_camionetas = (
                        df_m.groupby("placa")["costo"]
                        .sum()
                        .sort_values(ascending=False)
                    )

                    st.bar_chart(
                        resumen_camionetas
                    )

                    st.write(
                        "### Servicios registrados"
                    )

                    st.dataframe(
                        df_m,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "costo": st.column_config.NumberColumn(
                                "Costo ($)",
                                format="$%.2f"
                            )
                        }
                    )

                    st.download_button(
                        "Descargar historial CSV",
                        df_m.to_csv(
                            index=False
                        ).encode("utf-8-sig"),
                        "historial_mantenimiento.csv",
                        "text/csv"
                    )

            except Exception as e:
                st.error(
                    f"Error al consultar mantenimientos: {e}"
                )


# ==========================================
# CARGA INICIAL DE GASOLINA
# ==========================================

elif seccion == "Carga inicial":

    st.subheader("📥 Carga inicial")

    st.warning(
        "Esta función actualiza registros existentes "
        "si coinciden la fecha y la camioneta. "
        "No vuelvas a cargar datos históricos "
        "sin verificar primero las fechas."
    )

    lunes = st.date_input(
        "Fecha del lunes de la tabla original",
        value=(
            date.today()
            - timedelta(days=date.today().weekday())
        )
    )

    st.write(
        "Totales de referencia: "
        "lunes $11,850 · martes $10,750 · "
        "miércoles $400."
    )

    confirmar_carga = st.checkbox(
        "Confirmo que las fechas corresponden "
        "a la tabla original."
    )

    if st.button(
        "Cargar datos iniciales",
        type="primary"
    ):

        if not confirmar_carga:
            st.warning(
                "Confirma las fechas antes de cargar."
            )

        else:
            try:
                cantidad = 0

                for placa, importes in INICIAL.items():

                    for offset, importe in enumerate(importes):

                        if importe > 0:

                            guardar(
                                lunes + timedelta(
                                    days=offset
                                ),
                                placa,
                                importe,
                                "Carga inicial desde tabla"
                            )

                            cantidad += 1

                st.success(
                    f"Proceso terminado. "
                    f"Se procesaron {cantidad} registros."
                )

            except Exception as e:
                st.error(
                    f"Falló la carga inicial: {e}"
                )



# ============================================
# ALERTAS DE MANTENIMIENTO PREVENTIVO
# ============================================

def obtener_alertas_mantenimiento():
    try:
        config = (
            supabase.table("configuracion_mantenimiento")
            .select("intervalo_km,alerta_anticipada_km")
            .eq("tipo_servicio", "Cambio de aceite")
            .single()
            .execute()
        )

        intervalo = int(config.data["intervalo_km"])
        anticipacion = int(config.data["alerta_anticipada_km"])

        servicios = (
            supabase.table("mantenimientos")
            .select("placa,fecha,kilometraje")
            .eq("tipo_servicio", "Cambio de aceite")
            .order("fecha", desc=True)
            .order("id", desc=True)
            .execute()
        ).data or []

        lecturas = (
            supabase.table("kilometraje")
            .select("placa,fecha,kilometraje")
            .order("fecha", desc=True)
            .order("id", desc=True)
            .execute()
        ).data or []

        ultimos_servicios = {}
        for servicio in servicios:
            placa = servicio["placa"]
            if placa not in ultimos_servicios:
                ultimos_servicios[placa] = servicio

        ultimas_lecturas = {}
        for lectura in lecturas:
            placa = lectura["placa"]
            if placa not in ultimas_lecturas:
                ultimas_lecturas[placa] = lectura

        resultados = []

        for placa, servicio in ultimos_servicios.items():
            if placa not in ultimas_lecturas:
                continue

            lectura = ultimas_lecturas[placa]

            # Evitar comparar una lectura anterior al servicio.
            if lectura["fecha"] < servicio["fecha"]:
                continue

            km_actual = int(lectura["kilometraje"])
            km_servicio = int(servicio["kilometraje"])

            if km_actual < km_servicio:
                continue

            proximo = km_servicio + intervalo
            restantes = proximo - km_actual

            if restantes <= 0:
                estado = "Vencido"
            elif restantes <= anticipacion:
                estado = "Próximo"
            else:
                estado = "Al corriente"

            resultados.append({
                "Camioneta": placa,
                "Kilometraje actual": km_actual,
                "Próximo servicio": proximo,
                "Km restantes": restantes,
                "Estado": estado
            })

        return pd.DataFrame(resultados), None

    except Exception as e:
        return pd.DataFrame(), str(e)


st.divider()
st.subheader("🔧 Alertas de cambio de aceite")

alertas, error_alertas = obtener_alertas_mantenimiento()

if error_alertas:
    st.error(f"No se pudieron consultar las alertas: {error_alertas}")

elif alertas.empty:
    st.info(
        "Todavía no hay suficientes lecturas de kilometraje "
        "posteriores a los cambios de aceite registrados."
    )

else:
    orden = {"Vencido": 0, "Próximo": 1, "Al corriente": 2}

    alertas["prioridad"] = alertas["Estado"].map(orden)
    alertas = alertas.sort_values(
        ["prioridad", "Km restantes"]
    ).drop(columns=["prioridad"])

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "🔴 Vencidos",
        int((alertas["Estado"] == "Vencido").sum())
    )

    c2.metric(
        "🟡 Próximos",
        int((alertas["Estado"] == "Próximo").sum())
    )

    c3.metric(
        "🟢 Al corriente",
        int((alertas["Estado"] == "Al corriente").sum())
    )

    st.dataframe(
        alertas,
        use_container_width=True,
        hide_index=True
    )
