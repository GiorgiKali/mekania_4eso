"""Duelo online por LAN usando sockets TCP. Sin servidores externos."""
import socket
import json
import threading
import time
import random


PUERTO_DEFECTO = 55555


# ═══════════════════════════════════════════
# SERVIDOR (el que HOSTEA la partida)
# ═══════════════════════════════════════════
class ServidorDuelo:
    def __init__(self, callback_evento):
        """
        callback_evento: función que recibe dicts con eventos:
          {"tipo": "cliente_conectado", "nombre": "..."}
          {"tipo": "respuesta_cliente", "idx": 0, "acierto": True}
          {"tipo": "desconectado"}
        """
        self.callback = callback_evento
        self.socket_servidor = None
        self.socket_cliente = None
        self.activo = False
        self.nombre_jugador = "Host"
        self.hilo = None

    def iniciar(self, puerto=PUERTO_DEFECTO):
        try:
            self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket_servidor.bind(("0.0.0.0", puerto))
            self.socket_servidor.listen(1)
            self.activo = True
            self.hilo = threading.Thread(target=self._aceptar, daemon=True)
            self.hilo.start()
            return True, f"Servidor activo en puerto {puerto}"
        except Exception as e:
            return False, f"Error al abrir servidor: {e}"

    def _aceptar(self):
        try:
            self.socket_cliente, addr = self.socket_servidor.accept()
            self._recibir_loop()
        except Exception as e:
            if self.activo:
                self.callback({"tipo": "error", "msg": str(e)})

    def _recibir_loop(self):
        buffer = ""
        while self.activo:
            try:
                datos = self.socket_cliente.recv(4096).decode("utf-8")
                if not datos:
                    break
                buffer += datos
                while "\n" in buffer:
                    linea, buffer = buffer.split("\n", 1)
                    if not linea.strip():
                        continue
                    msg = json.loads(linea)
                    self._procesar(msg)
            except Exception:
                break
        self.callback({"tipo": "desconectado"})
        self.cerrar()

    def _procesar(self, msg):
        t = msg.get("tipo")
        if t == "unirse":
            self.callback({"tipo": "cliente_conectado", "nombre": msg.get("nombre", "Cliente")})
        elif t == "respuesta":
            self.callback({
                "tipo": "respuesta_cliente",
                "idx": msg.get("idx"),
                "acierto": msg.get("acierto"),
            })
        elif t == "chat":
            self.callback({"tipo": "chat", "texto": msg.get("texto", "")})

    def enviar(self, diccionario):
        if not self.socket_cliente:
            return False
        try:
            data = json.dumps(diccionario) + "\n"
            self.socket_cliente.sendall(data.encode("utf-8"))
            return True
        except Exception:
            return False

    def cerrar(self):
        self.activo = False
        for s in (self.socket_cliente, self.socket_servidor):
            try:
                if s:
                    s.close()
            except Exception:
                pass
        self.socket_cliente = None
        self.socket_servidor = None


# ═══════════════════════════════════════════
# CLIENTE (el que SE CONECTA al host)
# ═══════════════════════════════════════════
class ClienteDuelo:
    def __init__(self, callback_evento):
        self.callback = callback_evento
        self.socket = None
        self.activo = False
        self.hilo = None

    def conectar(self, ip, puerto=PUERTO_DEFECTO, nombre="Cliente"):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((ip, puerto))
            self.socket.settimeout(None)
            self.activo = True
            self.enviar({"tipo": "unirse", "nombre": nombre})
            self.hilo = threading.Thread(target=self._recibir_loop, daemon=True)
            self.hilo.start()
            return True, f"Conectado a {ip}:{puerto}"
        except Exception as e:
            return False, f"No se pudo conectar: {e}"

    def _recibir_loop(self):
        buffer = ""
        while self.activo:
            try:
                datos = self.socket.recv(4096).decode("utf-8")
                if not datos:
                    break
                buffer += datos
                while "\n" in buffer:
                    linea, buffer = buffer.split("\n", 1)
                    if not linea.strip():
                        continue
                    msg = json.loads(linea)
                    self.callback(msg)
            except Exception:
                break
        self.callback({"tipo": "desconectado"})
        self.cerrar()

    def enviar(self, diccionario):
        if not self.socket:
            return False
        try:
            data = json.dumps(diccionario) + "\n"
            self.socket.sendall(data.encode("utf-8"))
            return True
        except Exception:
            return False

    def cerrar(self):
        self.activo = False
        try:
            if self.socket:
                self.socket.close()
        except Exception:
            pass
        self.socket = None


def obtener_ip_local():
    """Devuelve la IP local del equipo para mostrarla al host."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"
