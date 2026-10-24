"""
DTO del Player Behavior Summary de Dota 2 (archivo latest_conduct_*.txt).

No depende de Windows ni de Steam: solo convierte texto <-> objeto,
asi se puede testear en cualquier sistema.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from pathlib import Path

RATINGS = {
    "k_eBehaviorGood": "Bueno",
    "k_eBehaviorWarning": "Advertencia",
    "k_eBehaviorBad": "Malo",
}

# Pares 'clave: valor' separados por saltos de linea o por espacios: el archivo
# real de Valve viene todo en una sola linea. Los valores nunca llevan espacios.
_PAR = re.compile(r"(?<!\S)([A-Za-z_]\w*)\s*:\s*(\S+)")


class FormatoInvalidoError(ValueError):
    """El texto no tiene el formato esperado o le falta un campo obligatorio."""


@dataclass(frozen=True)
class ResumenConducta:
    seq_num: int
    raw_behavior_score: int
    fecha: datetime                      # campo 'date' (epoch) convertido a UTC
    account_id: int | None = None
    match_id: int | None = None
    old_raw_behavior_score: int | None = None
    behavior_rating: str = ""
    reasons: int = 0
    matches_in_report: int = 0
    matches_clean: int = 0
    matches_reported: int = 0
    matches_abandoned: int = 0
    reports_count: int = 0
    reports_parties: int = 0
    commend_count: int = 0
    comms_reports: int = 0
    comms_parties: int = 0
    extras: dict[str, str] = field(default_factory=dict, compare=False)  # campos nuevos que Valve agregue

    # ------------------------------------------------------------ parseo --

    @classmethod
    def desde_texto(cls, texto: str) -> "ResumenConducta":
        crudo = dict(_PAR.findall(texto))
        if not crudo:
            raise FormatoInvalidoError("El texto no tiene lineas 'clave: valor'.")

        for obligatorio in ("seq_num", "raw_behavior_score", "date"):
            if obligatorio not in crudo:
                raise FormatoInvalidoError(f"Falta el campo obligatorio '{obligatorio}'.")

        conocidos = {f.name for f in fields(cls)} - {"fecha", "extras"}
        valores: dict = {}
        for nombre in conocidos:
            if nombre in crudo:
                valores[nombre] = crudo[nombre] if nombre == "behavior_rating" else _entero(nombre, crudo[nombre])

        valores["fecha"] = datetime.fromtimestamp(_entero("date", crudo["date"]), tz=timezone.utc)
        valores["extras"] = {k: v for k, v in crudo.items() if k not in conocidos and k != "date"}
        return cls(**valores)

    @classmethod
    def desde_archivo(cls, ruta: Path | str) -> "ResumenConducta":
        return cls.desde_texto(Path(ruta).read_text(encoding="utf-8", errors="ignore"))

    # --------------------------------------------------------- derivados --

    @property
    def cambio(self) -> int | None:
        if self.old_raw_behavior_score is None:
            return None
        return self.raw_behavior_score - self.old_raw_behavior_score

    @property
    def rating_legible(self) -> str:
        return RATINGS.get(self.behavior_rating, self.behavior_rating)

    def a_fila(self, fecha_registro: datetime) -> dict[str, str]:
        """Fila para el CSV de historial."""
        datos = {f.name: getattr(self, f.name) for f in fields(self) if f.name not in ("fecha", "extras")}
        datos.update(self.extras)
        return {
            "fecha_registro": fecha_registro.isoformat(timespec="seconds"),
            "fecha_archivo": self.fecha.isoformat(timespec="seconds"),
            "behavior_score": str(self.raw_behavior_score),
            "behavior_anterior": "" if self.old_raw_behavior_score is None else str(self.old_raw_behavior_score),
            "rating": self.rating_legible,
            "origen": "archivo",
            "seq_num": str(self.seq_num),
            "datos": json.dumps(datos, ensure_ascii=False, default=str),
        }


def _entero(nombre: str, valor: str) -> int:
    try:
        return int(valor)
    except ValueError:
        raise FormatoInvalidoError(f"El campo '{nombre}' deberia ser numero y vino '{valor}'.") from None
