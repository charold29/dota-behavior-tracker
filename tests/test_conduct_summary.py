import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from conduct_summary import FormatoInvalidoError, ResumenConducta

RESOURCES = Path(__file__).parent / "resources"
SAMPLE = RESOURCES / "latest_conduct_sample.txt"


@pytest.fixture
def texto_sample() -> str:
    return SAMPLE.read_text(encoding="utf-8")


@pytest.fixture
def resumen() -> ResumenConducta:
    return ResumenConducta.desde_archivo(SAMPLE)


# ------------------------------------------------------------- parseo ok ---

def test_lee_todos_los_campos_del_archivo(resumen):
    assert resumen.account_id == 123456789
    assert resumen.match_id == 1234567890
    assert resumen.seq_num == 8759
    assert resumen.reasons == 1
    assert resumen.matches_in_report == 15
    assert resumen.matches_clean == 14
    assert resumen.matches_reported == 1
    assert resumen.matches_abandoned == 0
    assert resumen.reports_count == 3
    assert resumen.reports_parties == 3
    assert resumen.commend_count == 8
    assert resumen.raw_behavior_score == 7843
    assert resumen.old_raw_behavior_score == 7738
    assert resumen.comms_reports == 0
    assert resumen.comms_parties == 0
    assert resumen.behavior_rating == "k_eBehaviorGood"
    assert resumen.extras == {}


def test_convierte_date_epoch_a_datetime_utc(resumen):
    assert resumen.fecha == datetime(2026, 5, 29, 0, 19, 23, tzinfo=timezone.utc)


def test_desde_texto_y_desde_archivo_dan_lo_mismo(texto_sample, resumen):
    assert ResumenConducta.desde_texto(texto_sample) == resumen


def test_tolera_espacios_y_saltos_de_linea_windows(texto_sample):
    texto = "\r\n".join(f"   {linea}   " for linea in texto_sample.splitlines())
    assert ResumenConducta.desde_texto(texto).raw_behavior_score == 7843


def test_lee_el_formato_real_en_una_sola_linea(texto_sample, resumen):
    # asi lo escribe Valve: todos los campos en una linea separados por espacios
    texto = " ".join(texto_sample.split("\n")).strip()
    assert ResumenConducta.desde_texto(texto) == resumen


# ---------------------------------------------------------- derivados ------

def test_cambio_es_la_diferencia_con_el_score_anterior(resumen):
    assert resumen.cambio == 105


def test_cambio_es_none_si_no_hay_score_anterior(texto_sample):
    texto = _sin_campo(texto_sample, "old_raw_behavior_score")
    assert ResumenConducta.desde_texto(texto).cambio is None


@pytest.mark.parametrize("crudo, legible", [
    ("k_eBehaviorGood", "Bueno"),
    ("k_eBehaviorWarning", "Advertencia"),
    ("k_eBehaviorBad", "Malo"),
    ("k_eBehaviorAlgoNuevo", "k_eBehaviorAlgoNuevo"),  # desconocido: se deja tal cual
])
def test_rating_legible(texto_sample, crudo, legible):
    texto = texto_sample.replace("k_eBehaviorGood", crudo)
    assert ResumenConducta.desde_texto(texto).rating_legible == legible


def test_campos_desconocidos_van_a_extras(texto_sample):
    texto = texto_sample + "campo_nuevo_de_valve: 42\n"
    r = ResumenConducta.desde_texto(texto)
    assert r.extras == {"campo_nuevo_de_valve": "42"}


# ------------------------------------------------------------ errores -----

@pytest.mark.parametrize("obligatorio", ["seq_num", "raw_behavior_score", "date"])
def test_falla_si_falta_un_campo_obligatorio(texto_sample, obligatorio):
    with pytest.raises(FormatoInvalidoError, match=obligatorio):
        ResumenConducta.desde_texto(_sin_campo(texto_sample, obligatorio))


def test_falla_si_un_numero_no_es_numero(texto_sample):
    texto = texto_sample.replace("raw_behavior_score: 7843", "raw_behavior_score: abc")
    with pytest.raises(FormatoInvalidoError, match="raw_behavior_score"):
        ResumenConducta.desde_texto(texto)


@pytest.mark.parametrize("texto", ["", "   \n\n", "esto no es el formato"])
def test_falla_con_texto_vacio_o_basura(texto):
    with pytest.raises(FormatoInvalidoError):
        ResumenConducta.desde_texto(texto)


def test_campos_opcionales_faltantes_usan_default():
    texto = "seq_num: 1\nraw_behavior_score: 10000\ndate: 0\n"
    r = ResumenConducta.desde_texto(texto)
    assert r.account_id is None
    assert r.commend_count == 0
    assert r.behavior_rating == ""


# --------------------------------------------------------- a_fila (CSV) ---

def test_a_fila_genera_la_fila_del_csv(resumen):
    registro = datetime(2026, 10, 24, 13, 0, tzinfo=timezone.utc)
    fila = resumen.a_fila(fecha_registro=registro)

    assert fila["fecha_registro"] == "2026-10-24T13:00:00+00:00"
    assert fila["fecha_archivo"] == "2026-05-29T00:19:23+00:00"
    assert fila["behavior_score"] == "7843"
    assert fila["behavior_anterior"] == "7738"
    assert fila["rating"] == "Bueno"
    assert fila["origen"] == "archivo"
    assert fila["seq_num"] == "8759"
    assert json.loads(fila["datos"])["commend_count"] == 8


# ----------------------------------------------------------- helpers ------

def _sin_campo(texto: str, campo: str) -> str:
    return "\n".join(l for l in texto.splitlines() if not l.startswith(f"{campo}:"))
