"""Salario mínimo e inflación en Colombia: ¿cuánto del aumento de 2026 pasó a los precios?

App en Shiny for Python. Lee los resultados del pipeline (DANE, GEIH, BIS → DuckDB + dbt → Python) de este repositorio.
José Nicolás Forero Urrego · https://nicolasforero.pages.dev
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from shiny import App, render, ui
from shinywidgets import output_widget, render_plotly

AQUI = Path(__file__).parent
R = {f.stem: json.load(open(f, encoding="utf-8")) for f in (AQUI / "resultados").glob("*.json")}
CM = pd.read_csv(AQUI / "publicado" / "ciudades_mensual.csv")
CX, CI, PR, SI, TX = R["contexto"], R["ciudades"], R["productos"], R["sintetico"], R["texto"]
AZUL, ROSA, MENTA, AMBAR, LAVANDA, TINTA, GRIS = "#4F6BD8", "#EBA3B0", "#8CCFB8", "#F5B482", "#B9A7E8", "#1F2430", "#C9CED6"
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def num(x, d=1):
    if x is None or x != x:
        return "–"
    s = f"{x:,.{d}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def pct(x, d=0):
    return "–" if x is None or x != x else num(100 * x, d) + " %"


def figura(fig, alto=380):
    fig.update_layout(height=alto, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Inter, system-ui", color=TINTA, size=12), legend=dict(orientation="h", y=-0.2),
                      hoverlabel=dict(bgcolor="white"), separators=",.",
                      modebar=dict(bgcolor="rgba(0,0,0,0)", color="#9CA3AF", activecolor=TINTA))
    fig.update_xaxes(gridcolor="#ECE8E0", zeroline=False)
    fig.update_yaxes(gridcolor="#ECE8E0", zeroline=False)
    return fig


def tabla(df, cols, fmts):
    cab = "".join(f"<th class='{'n' if c in fmts else ''}'>{t}</th>" for c, t in cols)
    filas = "".join("<tr>" + "".join(f"<td class='{'n' if c in fmts else ''}'>{fmts[c](r[c]) if c in fmts else r[c]}</td>" for c, _ in cols) + "</tr>"
                    for _, r in df.iterrows())
    return ui.HTML(f"<div style='overflow-x:auto'><table class='tabla'><thead><tr>{cab}</tr></thead><tbody>{filas}</tbody></table></div>")


CSS = """
:root { --bs-body-bg: #F6F4EF; --bs-body-color: #1F2430; --bs-primary: #4F6BD8; --bs-border-color: #ECE8E0;
        --bs-body-font-family: Inter, system-ui, -apple-system, 'Segoe UI', sans-serif; }
body { background: #F6F4EF; } .navbar { background: #F6F4EF !important; border-bottom: 1px solid #ECE8E0; }
.navbar-brand { font-family: Georgia, serif; font-size: 1.3rem; }
.card { border: 1px solid #ECE8E0; box-shadow: none; border-radius: 14px; }
.card-header { background: transparent; font-weight: 600; border-bottom: 1px solid #ECE8E0; }
.bslib-value-box { border: 1px solid #ECE8E0 !important; border-radius: 14px; }
.bslib-value-box .value-box-title { color: #6B7280; font-size: .85rem; } .bslib-value-box .value-box-value { font-family: Georgia, serif; font-size: 1.8rem; }
.lead { font-size: 1.05rem; max-width: 62rem; color: #374151; } .nota { color: #6B7280; font-size: .85rem; }
table.tabla { width: 100%; font-size: .9rem; } table.tabla td, table.tabla th { padding: .38rem .5rem; border-bottom: 1px solid #ECE8E0; white-space: nowrap; }
table.tabla th { color: #6B7280; font-weight: 600; font-size: .8rem; } table.tabla td.n, table.tabla th.n { text-align: right; font-variant-numeric: tabular-nums; }
footer.pie { color: #6B7280; font-size: .8rem; margin: 1.5rem 0 1rem; }
"""
pie = ui.tags.footer({"class": "pie"}, "Datos: DANE (IPC por subclase y por ciudad, GEIH 2025), BIS (precios al consumidor), Wikipedia (salario mínimo). ",
                     "Código: ", ui.a("github.com/Forero25/salario-minimo-inflacion", href="https://github.com/Forero25/salario-minimo-inflacion"), " · ",
                     ui.a("José Nicolás Forero Urrego", href="https://nicolasforero.pages.dev"))


def tarjeta(t, *c, **kw):
    return ui.card(ui.card_header(t), *c, **kw)


a26 = [a for a in CX["aumentos"] if a["anio"] == 2026][0]
pr = CI["principal"]
app_ui = ui.page_navbar(
    ui.nav_panel("Contexto",
        ui.p({"class": "lead mt-3"}, "El salario mínimo de 2026 subió " + num(a26["aumento"]) + " %, " + num(a26["real"]) +
             " puntos por encima de la inflación de 2025. Es el aumento real más grande de la serie. ¿Cuánto de eso terminó en los precios?"),
        ui.layout_columns(
            ui.value_box("Aumento del salario mínimo 2026", num(a26["aumento"]) + " %", "nominal"),
            ui.value_box("Por encima de la inflación previa", num(a26["real"]) + " puntos", "aumento real"),
            ui.value_box("Inflación anual, " + MESES[CX["ultimo"]["mes"] - 1] + " " + str(CX["ultimo"]["anio"]), num(CX["ultimo"]["var_anual"], 2) + " %", "DANE"),
            fill=False),
        tarjeta("Aumento del salario mínimo e inflación del año anterior", output_widget("g_contexto")),
    ),
    ui.nav_panel("Ciudades",
        ui.p({"class": "lead mt-3"}, "Si el mínimo empuja los precios, debería notarse más donde más trabajadores lo ganan. Comparo cada ciudad consigo misma "
             "entre 2017 y 2026: ¿sube más su inflación de enero a marzo los años de aumento real grande, y más mientras más expuesta está?"),
        ui.layout_columns(
            ui.value_box("Efecto estimado (β)", num(pr["beta"], 3), f"IC 95 %: {num(pr['ic_bajo'], 3)} a {num(pr['ic_alto'], 3)}; p = {num(pr['p'], 3)}"),
            ui.value_box("Placebo (julio a septiembre)", num(CI["placebo_t3"]["beta"], 3), f"p = {num(CI['placebo_t3']['p'], 2)}: sin efecto, como debe ser"),
            ui.value_box("Más vs. menos expuesta, 2026", "+" + num(CI["brecha_2026"]["extra_t1"], 2) + " puntos", f"{CI['brecha_2026']['ciudad_alta']} frente a {CI['brecha_2026']['ciudad_baja']}, enero a marzo"),
            fill=False),
        ui.layout_columns(
            tarjeta("Exposición y exceso de inflación de enero a marzo de 2026", output_widget("g_ciudades")),
            tarjeta("Mes a mes: pendiente entre exposición e inflación extra", output_widget("g_meses"))),
        tarjeta("Pruebas de robustez", ui.output_ui("t_rob")),
    ),
    ui.nav_panel("Productos",
        ui.p({"class": "lead mt-3"}, "El mismo diseño con las 188 subclases del IPC, según la proporción de trabajadores en el mínimo del sector que las produce, "
             "no encuentra efecto. Los servicios intensivos en trabajo sí se movieron más en 2026."),
        ui.layout_columns(
            tarjeta("Servicios intensivos en trabajo: variación de enero a marzo", ui.output_ui("t_servicios")),
            tarjeta("Diseño por productos", ui.output_ui("t_productos"))),
    ),
    ui.nav_panel("Control sintético",
        ui.p({"class": "lead mt-3"}, "¿Se desvió la inflación de Colombia en 2026 de la de una combinación de países que la imitaba entre 2023 y 2025?"),
        ui.layout_columns(
            ui.value_box("Brecha promedio en 2026", "+" + num(SI["brecha_media_post"], 2) + " puntos", "inflación anual, Colombia menos el sintético"),
            ui.value_box("Puesto entre los placebos", f"{SI['puesto']} de {SI['paises']}", "1 = la desviación más grande"),
            ui.value_box("Ajuste antes de 2026", num(SI["rmspe_pre"], 2) + " puntos", "error cuadrático medio"),
            fill=False),
        ui.layout_columns(
            tarjeta("Colombia y su sintético", output_widget("g_sint")),
            tarjeta("Placebos: desviación después / ajuste antes", output_widget("g_plac"))),
    ),
    ui.nav_panel("Texto",
        ui.p({"class": "lead mt-3"}, "Cada mes el DANE explica la inflación en un boletín técnico y nombra las subclases que más aportaron. Extraje esos "
             "párrafos de los " + str(TX["boletines"]) + " boletines desde 2019 y medí qué parte del relato se llevan los servicios cuyo costo principal es el trabajo."),
        ui.layout_columns(
            ui.value_box("Menciones extraídas y validadas", f"{TX['validacion']['coinciden']} de {TX['validacion']['con_dato']}",
                         "la variación escrita coincide con la calculada con los índices"),
            ui.value_box("Servicios intensivos en trabajo, enero a abril", pct(TX["ene_abr"]["2026"]), f"de las subclases nombradas en 2026; {pct(TX['ene_abr']['2019_2025'])} en 2019-2025"),
            ui.value_box("Veces que el boletín menciona el salario mínimo", str(TX["menciones_salario_minimo"]), "el DANE describe, no atribuye causas"),
            fill=False),
        tarjeta("Proporción de servicios intensivos en trabajo entre las subclases que el DANE nombra como mayores aportes", output_widget("g_texto")),
    ),
    ui.nav_panel("Explorar",
        ui.layout_sidebar(
            ui.sidebar(ui.input_selectize("ciu", "Ciudades", sorted(CM.ciudad.unique()), selected=["Bogotá D.C.", "Cúcuta", "Armenia"], multiple=True),
                       ui.input_radio_buttons("anio", "Año", ["2026", "2025", "2024", "2023"], selected="2026"), width=260),
            tarjeta("Inflación mensual por ciudad", output_widget("g_explorar")))),
    ui.nav_panel("Método",
        ui.div({"class": "mt-3", "style": "max-width: 62rem"}, ui.markdown("""
**Datos.** IPC del DANE: índices mensuales de 188 subclases (2019-2026, base diciembre de 2018) e inflación mensual de 24 ciudades (2017-2026).
GEIH 2025 del DANE: proporción de asalariados que ganan entre 0,95 y 1,05 salarios mínimos, por ciudad y por sector (los microdatos no salen
del computador donde se procesan; solo agregados). Inflación anual de 26 países del BIS. Salario mínimo de cada año: Wikipedia.

**Validación.** El índice total reconstruido con las 188 subclases y sus ponderaciones reproduce el publicado por el DANE con una diferencia máxima
de 0,04 puntos de índice en 94 meses.

**Diseño por ciudades.** Inflación de enero a marzo de cada ciudad y año = efecto fijo de ciudad + efecto fijo de año + β × (aumento real del mínimo)
× (exposición de la ciudad). El aumento real es el aumento nominal menos la inflación del año anterior. Errores agrupados por ciudad e inferencia por
permutación de las exposiciones.

**Control sintético.** Pesos no negativos que suman 1 sobre la inflación anual de otros países para imitar a Colombia en 2023-2025; placebos con cada país.

**Texto.** De cada boletín técnico mensual del IPC se extrae el párrafo del mes con las subclases que más aportaron (expresiones regulares) y cada nombre se asocia con su código (TF-IDF de n-gramas de caracteres, similitud coseno). La variación escrita en el texto coincide con la calculada con los índices en 919 de 920 menciones.

**Lo que no hace.** No mide el efecto del mínimo sobre el nivel general de precios de todo el país (los efectos de año lo absorben); la identificación
descansa casi toda en 2026; la exposición es de 2025 y por ciudad, no por empresa.
"""))),
    title="Salario mínimo e inflación", header=ui.tags.style(CSS), footer=pie, fillable=False, lang="es",
)


def server(input, output, session):
    @render_plotly
    def g_contexto():
        a = pd.DataFrame(CX["aumentos"])
        fig = go.Figure()
        fig.add_bar(x=a.anio, y=a.aumento, name="Aumento del salario mínimo", marker_color=AZUL)
        fig.add_scatter(x=a.anio, y=a.inflacion_previa, name="Inflación del año anterior", mode="lines+markers", line=dict(color=ROSA, width=3))
        fig.update_yaxes(title="%")
        return figura(fig)

    @render_plotly
    def g_ciudades():
        d = pd.DataFrame(CI["ciudades_2026"])
        fig = go.Figure(go.Scatter(x=d.en_minimo, y=d.exceso, mode="markers+text", text=d.ciudad, textposition="top center",
                                   marker=dict(size=10, color=AZUL, opacity=.75), textfont=dict(size=10, color="#6B7280"),
                                   hovertemplate="%{text}<br>En el mínimo: %{x:.0%}<br>Exceso: %{y:.2f} puntos<extra></extra>"))
        fig.update_xaxes(title="Asalariados que ganan el mínimo (GEIH 2025)", tickformat=".0%")
        fig.update_yaxes(title="Inflación ene-mar 2026 − promedio 2023-2025 (puntos)")
        return figura(fig, 420)

    @render_plotly
    def g_meses():
        fig = go.Figure()
        for anio, col in [(2026, AZUL), (2025, GRIS)]:
            d = pd.DataFrame(CI[f"mes_a_mes_{anio}"])
            fig.add_scatter(x=[MESES[m - 1] for m in d.mes], y=d.pendiente, mode="lines+markers", name=str(anio), line=dict(color=col, width=3),
                            error_y=dict(type="data", symmetric=False, array=d.ic_alto - d.pendiente, arrayminus=d.pendiente - d.ic_bajo, color=col, thickness=1))
        fig.add_hline(y=0, line_color="#9CA3AF", line_dash="dot")
        fig.update_yaxes(title="Puntos de inflación extra por cada 100 % de exposición")
        return figura(fig, 420)

    @render.ui
    def t_rob():
        filas = [("Principal: enero a marzo, aumento real", CI["principal"]), ("Solo enero", CI["solo_enero"]), ("Aumento nominal", CI["nominal"]),
                 ("Placebo: julio a septiembre", CI["placebo_t3"]), ("Sin 2026", CI["sin_2026"])]
        filas += [(f"Exposición: {n}", CI["otras_exposiciones"][k]) for k, n in [("hasta_15", "entre 0,95 y 1,5 mínimos"), ("en_minimo_cotizantes", "en el mínimo y cotizando")]]
        d = pd.DataFrame([{"esp": n, "beta": r["beta"], "ic": f"{num(r['ic_bajo'], 3)} a {num(r['ic_alto'], 3)}", "p": r["p"], "n": r["n"]} for n, r in filas])
        ri = CI["inferencia_aleatoria"]; lo = CI["sin_cada_ciudad"]
        return ui.div(tabla(d, [("esp", "Especificación"), ("beta", "β"), ("ic", "IC 95 %"), ("p", "p"), ("n", "Obs.")],
                            {"beta": lambda x: num(x, 3), "ic": str, "p": lambda x: num(x, 3), "n": str}),
                      ui.p({"class": "nota mt-2"}, f"Permutando las exposiciones entre ciudades {ri['reps']} veces, p = {num(ri['p_dos_colas'], 3)}. "
                           f"Quitando una ciudad a la vez, β va de {num(lo['min'], 3)} a {num(lo['max'], 3)}."))

    @render.ui
    def t_servicios():
        d = pd.DataFrame(PR["servicios"])
        return tabla(d, [("nombre", "Servicio"), ("previo", "Promedio 2023-2025"), ("t1_2025", "2025"), ("t1_2026", "2026")],
                     {"previo": lambda x: num(x, 2) + " %", "t1_2025": lambda x: num(x, 2) + " %", "t1_2026": lambda x: num(x, 2) + " %"})

    @render.ui
    def t_productos():
        filas = [("Todas las subclases (ponderadas)", PR["todas"]), ("Sin ponderar", PR["sin_pesos"]), ("Sin alimentos ni regulados", PR["nucleo"]),
                 ("Exposición hasta 1,5 mínimos", PR["hasta_15"]), ("Placebo: julio a septiembre", PR["placebo_t3"])]
        d = pd.DataFrame([{"esp": n, "beta": r["beta"], "p": r["p"], "s": r["subclases"]} for n, r in filas])
        return tabla(d, [("esp", "Especificación"), ("beta", "β"), ("p", "p"), ("s", "Subclases")], {"beta": lambda x: num(x, 3), "p": lambda x: num(x, 3), "s": str})

    @render_plotly
    def g_sint():
        s = pd.DataFrame(SI["serie"]); x = [f"{MESES[m - 1]} {a}" for a, m in zip(s.anio, s.mes)]
        fig = go.Figure()
        fig.add_scatter(x=x, y=s.real, name="Colombia", line=dict(color=ROSA, width=3))
        fig.add_scatter(x=x, y=s.sintetico, name="Colombia sintética", line=dict(color=AZUL, width=3, dash="dash"))
        fig.add_vline(x=x[list(s.anio).index(2026)], line_color="#9CA3AF", line_dash="dot")
        fig.update_yaxes(title="Inflación anual (%)")
        return figura(fig, 420)

    @render_plotly
    def g_plac():
        p = pd.DataFrame(SI["placebos"]).iloc[::-1]
        fig = go.Figure(go.Bar(x=p.razon, y=p.nombre, orientation="h", marker_color=[ROSA if c == "CO" else GRIS for c in p.pais]))
        fig.update_xaxes(title="Desviación en 2026 / error de ajuste antes")
        return figura(fig, 560)

    @render_plotly
    def g_texto():
        a = pd.DataFrame(TX["ene_abr_por_anio"]); b = pd.DataFrame(TX["resto_del_anio"])
        fig = go.Figure()
        fig.add_bar(x=a.anio, y=a.pct_trabajo, name="Enero a abril", marker_color=AZUL)
        fig.add_bar(x=b.anio, y=b.pct_trabajo, name="Mayo a diciembre", marker_color=GRIS)
        fig.update_yaxes(tickformat=".0%"); fig.update_layout(barmode="group")
        return figura(fig)

    @render_plotly
    def g_explorar():
        d = CM[CM.ciudad.isin(input.ciu()) & (CM.anio == int(input.anio()))]
        fig = go.Figure()
        for c, col in zip(input.ciu(), [AZUL, ROSA, MENTA, AMBAR, LAVANDA, GRIS] * 5):
            x = d[d.ciudad == c]
            fig.add_scatter(x=[MESES[m - 1] for m in x.mes], y=x.var_mensual, name=c, mode="lines+markers", line=dict(color=col, width=3))
        fig.update_yaxes(title="Variación mensual (%)")
        return figura(fig, 420)


app = App(app_ui, server)
