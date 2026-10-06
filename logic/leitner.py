"""Sistema Leitner de 5 cajas con repetición espaciada."""
import random
from datetime import datetime


class Leitner:
    def __init__(self, db):
        self.db = db

    def registrar_respuesta(self, id_pregunta, acertada, confianza="media"):
        p = self.db.obtener_progreso(id_pregunta)
        caja = p["caja_leitner"]
        fallos = p["veces_fallada"]
        aciertos = p["veces_acertada"]
        consec = p["aciertos_consecutivos"]
        dominada = p["dominada"]

        if acertada:
            aciertos += 1
            consec += 1
            if caja < 5:
                caja += 1
        else:
            fallos += 1
            consec = 0
            caja = 1
            dominada = 0

        if caja == 5 and consec >= 2:
            dominada = 1

        self.db.guardar_progreso(id_pregunta, caja, fallos, aciertos, consec, dominada)
        return {"caja": caja, "dominada": bool(dominada), "consec": consec}

    def preguntas_para_repaso_hoy(self):
        ahora = datetime.now()
        pendientes = []
        for pid, p in self.db.todas_las_preguntas_progreso().items():
            if p["dominada"]:
                continue
            prox = p.get("proximo_repaso")
            if not prox:
                pendientes.append(pid)
                continue
            try:
                if datetime.fromisoformat(prox) <= ahora:
                    pendientes.append(pid)
            except ValueError:
                pendientes.append(pid)
        return pendientes

    def seleccionar_sesion(self, ids_disponibles, n=10, solo_falladas=False):
        prog = self.db.todas_las_preguntas_progreso()
        cands = []
        for pid in ids_disponibles:
            p = prog.get(pid)
            if solo_falladas and p and p["dominada"]:
                continue
            caja = p["caja_leitner"] if p else 1
            cands.append((caja, pid))
        random.shuffle(cands)
        cands.sort(key=lambda x: x[0])
        return [pid for _, pid in cands[:n]]
