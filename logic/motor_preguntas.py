"""Carga el JSON de preguntas y da utilidades."""
import json, os, sys
from collections import defaultdict


def ruta_recurso(rel):
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, rel)


def cargar_json(rel):
    with open(ruta_recurso(rel), "r", encoding="utf-8") as f:
        return json.load(f)


class BancoPreguntas:
    def __init__(self):
        self.preguntas = cargar_json("data/preguntas.json")
        self.por_id = {p["id"]: p for p in self.preguntas}
        self.mapa_bloques = {p["id"]: p["b"] for p in self.preguntas}
        self.bloques = defaultdict(list)
        for p in self.preguntas:
            self.bloques[p["b"]].append(p["id"])

    def obtener(self, pid): return self.por_id[pid]
    def total(self): return len(self.preguntas)
    def todas_ids(self): return [p["id"] for p in self.preguntas]
    def ids_por_bloque(self, b): return self.bloques.get(b, [])
    def bloques_ordenados(self): return sorted(self.bloques.keys())
