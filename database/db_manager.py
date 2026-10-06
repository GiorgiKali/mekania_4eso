"""Gestor SQLite multi-usuario con autenticación segura."""
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

from logic.auth import generar_salt, hash_password, verificar_password


SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    fecha_registro TEXT,
    avatar TEXT DEFAULT 'A1',
    xp INTEGER DEFAULT 0,
    monedas INTEGER DEFAULT 0,
    nivel INTEGER DEFAULT 1,
    rango TEXT DEFAULT 'Aprendiz',
    tema TEXT DEFAULT 'oscuro',
    sonido INTEGER DEFAULT 1,
    tamano_fuente INTEGER DEFAULT 15
);

CREATE TABLE IF NOT EXISTS sesion_actual (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    usuario_id INTEGER
);

CREATE TABLE IF NOT EXISTS progreso (
    usuario_id INTEGER NOT NULL,
    id_pregunta INTEGER NOT NULL,
    caja_leitner INTEGER DEFAULT 1,
    veces_fallada INTEGER DEFAULT 0,
    veces_acertada INTEGER DEFAULT 0,
    aciertos_consecutivos INTEGER DEFAULT 0,
    dominada INTEGER DEFAULT 0,
    ultima_vez TEXT,
    proximo_repaso TEXT,
    PRIMARY KEY (usuario_id, id_pregunta)
);

CREATE TABLE IF NOT EXISTS logros (
    usuario_id INTEGER NOT NULL,
    id TEXT NOT NULL,
    desbloqueado INTEGER DEFAULT 0,
    fecha TEXT,
    PRIMARY KEY (usuario_id, id)
);

CREATE TABLE IF NOT EXISTS sesiones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    fecha TEXT,
    modo TEXT,
    aciertos INTEGER,
    fallos INTEGER,
    xp_ganado INTEGER,
    monedas_ganadas INTEGER
);

CREATE TABLE IF NOT EXISTS compras (
    usuario_id INTEGER NOT NULL,
    item_id TEXT NOT NULL,
    fecha TEXT,
    PRIMARY KEY (usuario_id, item_id)
);

CREATE TABLE IF NOT EXISTS ranking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    nombre TEXT,
    puntuacion INTEGER,
    fecha TEXT
);

CREATE INDEX IF NOT EXISTS idx_progreso_usuario ON progreso(usuario_id);
CREATE INDEX IF NOT EXISTS idx_sesiones_usuario ON sesiones(usuario_id);
CREATE INDEX IF NOT EXISTS idx_ranking_usuario ON ranking(usuario_id);
"""


def carpeta_datos():
    base = Path(os.environ.get("APPDATA", Path.home())) if os.name == "nt" else Path.home() / ".config"
    carpeta = base / "Mecania"
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


class Database:
    def __init__(self):
        self.ruta = carpeta_datos() / "mecania.db"
        self.con = sqlite3.connect(str(self.ruta))
        self.con.row_factory = sqlite3.Row
        self.con.executescript(SCHEMA)
        self.con.commit()
        self.usuario_id = None

    # ==================== AUTENTICACIÓN ====================
    def registrar(self, nombre: str, password: str):
        """Crea un usuario nuevo. Devuelve (ok, mensaje)."""
        nombre = nombre.strip()
        try:
            salt = generar_salt()
            pwd_hash = hash_password(password, salt)
            ahora = datetime.now().isoformat(timespec="seconds")
            self.con.execute(
                "INSERT INTO usuarios (nombre, password_hash, salt, fecha_registro) "
                "VALUES (?,?,?,?)",
                (nombre, pwd_hash, salt, ahora),
            )
            self.con.commit()
            uid = self.con.execute(
                "SELECT id FROM usuarios WHERE nombre=?", (nombre,)
            ).fetchone()[0]
            self.usuario_id = uid
            self._guardar_sesion(uid)
            return True, f"¡Bienvenido/a, {nombre}!"
        except sqlite3.IntegrityError:
            return False, "Ese nombre ya está en uso."
        except Exception as e:
            return False, f"Error al registrar: {e}"

    def login(self, nombre: str, password: str):
        """Inicia sesión. Devuelve (ok, mensaje)."""
        nombre = nombre.strip()
        cur = self.con.execute(
            "SELECT id, password_hash, salt FROM usuarios WHERE nombre=?", (nombre,)
        )
        fila = cur.fetchone()
        if not fila:
            return False, "Usuario no encontrado."
        if not verificar_password(password, fila["salt"], fila["password_hash"]):
            return False, "Contraseña incorrecta."
        self.usuario_id = fila["id"]
        self._guardar_sesion(self.usuario_id)
        return True, f"¡Hola de nuevo, {nombre}!"

    def logout(self):
        self.usuario_id = None
        self._limpiar_sesion()

    def _guardar_sesion(self, uid):
        self.con.execute(
            "INSERT INTO sesion_actual (id, usuario_id) VALUES (1, ?) "
            "ON CONFLICT(id) DO UPDATE SET usuario_id=excluded.usuario_id",
            (uid,),
        )
        self.con.commit()
    def agregar_avatar_custom(self, ruta):
        """Guarda una ruta de avatar custom en la lista del usuario."""
        # Guardamos en una tabla simple; usamos compras con prefijo
        # para no romper el esquema actual
        uid = self.usuario_id
        self.con.execute(
            "INSERT OR IGNORE INTO compras (usuario_id, item_id, fecha) VALUES (?,?,?)",
            (uid, f"custom:{ruta}", datetime.now().isoformat(timespec="seconds")),
        )
        self.con.commit()

    def listar_avatares_custom(self):
        """Devuelve lista de rutas de avatares custom del usuario."""
        uid = self.usuario_id
        cur = self.con.execute(
            "SELECT item_id FROM compras WHERE usuario_id=? AND item_id LIKE 'custom:%'",
            (uid,),
        )
        return [r[0][len("custom:"):] for r in cur.fetchall()]

    def _limpiar_sesion(self):
        self.con.execute("DELETE FROM sesion_actual WHERE id=1")
        self.con.commit()

    def sesion_guardada(self):
        """Devuelve el id del último usuario logueado, o None."""
        try:
            fila = self.con.execute(
                "SELECT usuario_id FROM sesion_actual WHERE id=1"
            ).fetchone()
            return fila["usuario_id"] if fila else None
        except sqlite3.OperationalError:
            return None

    def retomar_sesion(self):
        """Reanuda la última sesión guardada (auto-login)."""
        uid = self.sesion_guardada()
        if uid is None:
            return False
        fila = self.con.execute("SELECT id FROM usuarios WHERE id=?", (uid,)).fetchone()
        if not fila:
            return False
        self.usuario_id = uid
        return True

    def listar_usuarios(self):
        cur = self.con.execute(
            "SELECT id, nombre, fecha_registro, xp, nivel, rango FROM usuarios ORDER BY xp DESC"
        )
        return [dict(r) for r in cur.fetchall()]

    # ==================== JUGADOR ACTUAL ====================
    def jugador(self):
        if not self.usuario_id:
            return None
        cur = self.con.execute("SELECT * FROM usuarios WHERE id=?", (self.usuario_id,))
        fila = cur.fetchone()
        return dict(fila) if fila else None

    def actualizar_jugador(self, **campos):
        if not self.usuario_id or not campos:
            return
        cols = ", ".join(f"{k}=?" for k in campos)
        vals = list(campos.values()) + [self.usuario_id]
        self.con.execute(f"UPDATE usuarios SET {cols} WHERE id=?", vals)
        self.con.commit()

    def cambiar_password(self, password_actual, password_nueva):
        u = self.jugador()
        if not u:
            return False, "No hay sesión."
        if not verificar_password(password_actual, u["salt"], u["password_hash"]):
            return False, "Contraseña actual incorrecta."
        salt = generar_salt()
        nuevo_hash = hash_password(password_nueva, salt)
        self.con.execute(
            "UPDATE usuarios SET password_hash=?, salt=? WHERE id=?",
            (nuevo_hash, salt, self.usuario_id),
        )
        self.con.commit()
        return True, "Contraseña actualizada."

    # ==================== PROGRESO ====================
    def obtener_progreso(self, id_pregunta):
        uid = self.usuario_id
        cur = self.con.execute(
            "SELECT * FROM progreso WHERE usuario_id=? AND id_pregunta=?",
            (uid, id_pregunta),
        )
        fila = cur.fetchone()
        if fila is None:
            self.con.execute(
                "INSERT INTO progreso (usuario_id, id_pregunta) VALUES (?,?)",
                (uid, id_pregunta),
            )
            self.con.commit()
            return self.obtener_progreso(id_pregunta)
        return dict(fila)

    def guardar_progreso(self, id_pregunta, caja, fallos, aciertos, consec, dominada):
        ahora = datetime.now().isoformat(timespec="seconds")
        dias = {1: 0, 2: 1, 3: 3, 4: 7, 5: 30}.get(caja, 0)
        proximo = (datetime.now() + timedelta(days=dias)).isoformat(timespec="seconds")
        self.con.execute(
            """INSERT INTO progreso (usuario_id, id_pregunta, caja_leitner,
                veces_fallada, veces_acertada, aciertos_consecutivos, dominada,
                ultima_vez, proximo_repaso)
               VALUES (?,?,?,?,?,?,?,?,?)
               ON CONFLICT(usuario_id, id_pregunta) DO UPDATE SET
                caja_leitner=excluded.caja_leitner,
                veces_fallada=excluded.veces_fallada,
                veces_acertada=excluded.veces_acertada,
                aciertos_consecutivos=excluded.aciertos_consecutivos,
                dominada=excluded.dominada,
                ultima_vez=excluded.ultima_vez,
                proximo_repaso=excluded.proximo_repaso""",
            (self.usuario_id, id_pregunta, caja, fallos, aciertos, consec,
             dominada, ahora, proximo),
        )
        self.con.commit()

    def listar_falladas(self):
        cur = self.con.execute(
            "SELECT id_pregunta FROM progreso WHERE usuario_id=? AND dominada=0",
            (self.usuario_id,),
        )
        return [r[0] for r in cur.fetchall()]

    def contar_dominadas(self):
        cur = self.con.execute(
            "SELECT COUNT(*) FROM progreso WHERE usuario_id=? AND dominada=1",
            (self.usuario_id,),
        )
        return cur.fetchone()[0]

    def todas_las_preguntas_progreso(self):
        cur = self.con.execute(
            "SELECT * FROM progreso WHERE usuario_id=?", (self.usuario_id,)
        )
        return {r["id_pregunta"]: dict(r) for r in cur.fetchall()}

    # ==================== LOGROS ====================
    def logro_desbloqueado(self, lid):
        r = self.con.execute(
            "SELECT desbloqueado FROM logros WHERE usuario_id=? AND id=?",
            (self.usuario_id, lid),
        ).fetchone()
        return bool(r and r[0])

    def desbloquear_logro(self, lid):
        ahora = datetime.now().isoformat(timespec="seconds")
        self.con.execute(
            """INSERT INTO logros (usuario_id, id, desbloqueado, fecha)
               VALUES (?,?,1,?)
               ON CONFLICT(usuario_id, id) DO UPDATE SET
                desbloqueado=1, fecha=excluded.fecha""",
            (self.usuario_id, lid, ahora),
        )
        self.con.commit()

    def listar_logros(self):
        cur = self.con.execute(
            "SELECT id, desbloqueado, fecha FROM logros WHERE usuario_id=?",
            (self.usuario_id,),
        )
        return {r["id"]: dict(r) for r in cur.fetchall()}

    # ==================== SESIONES / ESTADÍSTICAS ====================
    def registrar_sesion(self, modo, aciertos, fallos, xp, monedas):
        self.con.execute(
            "INSERT INTO sesiones (usuario_id, fecha, modo, aciertos, fallos, "
            "xp_ganado, monedas_ganadas) VALUES (?,?,?,?,?,?,?)",
            (self.usuario_id, datetime.now().isoformat(timespec="seconds"),
             modo, aciertos, fallos, xp, monedas),
        )
        self.con.commit()

    def estadisticas_por_bloque(self, mapa_bloques):
        cur = self.con.execute(
            "SELECT id_pregunta, veces_acertada, veces_fallada FROM progreso "
            "WHERE usuario_id=?", (self.usuario_id,)
        )
        res = {}
        for r in cur.fetchall():
            b = mapa_bloques.get(r["id_pregunta"], "?")
            a, f = r["veces_acertada"], r["veces_fallada"]
            ac, tot = res.get(b, (0, 0))
            res[b] = (ac + a, tot + a + f)
        return res

    # ==================== COMPRAS ====================
    def tiene_compra(self, item_id):
        return self.con.execute(
            "SELECT 1 FROM compras WHERE usuario_id=? AND item_id=?",
            (self.usuario_id, item_id),
        ).fetchone() is not None

    def registrar_compra(self, item_id):
        self.con.execute(
            "INSERT OR IGNORE INTO compras (usuario_id, item_id, fecha) VALUES (?,?,?)",
            (self.usuario_id, item_id, datetime.now().isoformat(timespec="seconds")),
        )
        self.con.commit()

    # ==================== RANKING ====================
    def agregar_ranking(self, puntuacion):
        u = self.jugador()
        if not u:
            return
        self.con.execute(
            "INSERT INTO ranking (usuario_id, nombre, puntuacion, fecha) VALUES (?,?,?,?)",
            (self.usuario_id, u["nombre"], puntuacion,
             datetime.now().isoformat(timespec="seconds")),
        )
        self.con.commit()

    def top_ranking(self, n=10):
        cur = self.con.execute(
            "SELECT nombre, puntuacion, fecha FROM ranking ORDER BY puntuacion DESC LIMIT ?",
            (n,),
        )
        return [dict(r) for r in cur.fetchall()]

    # ==================== RESET ====================
    def resetear_progreso(self):
        uid = self.usuario_id
        for tabla in ("progreso", "logros", "sesiones", "compras"):
            self.con.execute(f"DELETE FROM {tabla} WHERE usuario_id=?", (uid,))
        self.con.execute(
            "UPDATE usuarios SET xp=0, monedas=0, nivel=1, rango='Aprendiz' WHERE id=?",
            (uid,),
        )
        self.con.commit()

    def eliminar_usuario(self):
        uid = self.usuario_id
        for tabla in ("progreso", "logros", "sesiones", "compras"):
            self.con.execute(f"DELETE FROM {tabla} WHERE usuario_id=?", (uid,))
        self.con.execute("DELETE FROM usuarios WHERE id=?", (uid,))
        self._limpiar_sesion()
        self.con.commit()
    # ==================== RANKING GLOBAL ====================
    def ranking_por_xp(self, limite=20):
        cur = self.con.execute(
            "SELECT nombre, xp, nivel, rango, avatar FROM usuarios "
            "ORDER BY xp DESC LIMIT ?", (limite,)
        )
        return [dict(r) for r in cur.fetchall()]

    def ranking_por_dominadas(self, limite=20):
        cur = self.con.execute("""
            SELECT u.nombre, u.avatar,
                   COUNT(CASE WHEN p.dominada=1 THEN 1 END) AS dominadas,
                   u.xp
            FROM usuarios u
            LEFT JOIN progreso p ON p.usuario_id = u.id
            GROUP BY u.id
            ORDER BY dominadas DESC, u.xp DESC
            LIMIT ?
        """, (limite,))
        return [dict(r) for r in cur.fetchall()]

    def ranking_por_examen(self, limite=20):
        cur = self.con.execute("""
            SELECT u.nombre, u.avatar, MAX(s.aciertos) AS mejor
            FROM usuarios u
            LEFT JOIN sesiones s ON s.usuario_id = u.id AND s.modo='examen'
            GROUP BY u.id
            HAVING mejor IS NOT NULL
            ORDER BY mejor DESC
            LIMIT ?
        """, (limite,))
        return [dict(r) for r in cur.fetchall()]

    def lista_usuarios_para_duelo(self):
        cur = self.con.execute(
            "SELECT id, nombre, avatar, xp, nivel FROM usuarios ORDER BY xp DESC"
        )
        return [dict(r) for r in cur.fetchall()]

    def obtener_por_id(self, uid):
        cur = self.con.execute("SELECT * FROM usuarios WHERE id=?", (uid,))
        r = cur.fetchone()
        return dict(r) if r else None
    def agregar_ranking_para(self, usuario_id, puntuacion):
        u = self.obtener_por_id(usuario_id)
        if not u:
            return
        self.con.execute(
            "INSERT INTO ranking (usuario_id, nombre, puntuacion, fecha) VALUES (?,?,?,?)",
            (usuario_id, u["nombre"], puntuacion,
             datetime.now().isoformat(timespec="seconds")),
        )
        self.con.commit()
