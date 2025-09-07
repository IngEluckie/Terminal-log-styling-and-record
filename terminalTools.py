# terminalTools.py

"""
Tool for terminal font styling and log registration for
activity control.
"""

# Import libraries
from pathlib import Path
from typing import Any, Tuple, Optional, List, Final
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
import time

# Date helper
# Return example: [11/Aug/2025 20:41:36]
@dataclass
class FechaHora:
    registro: str = ""

    def __post_init__(self):
        self.registro = datetime.now().strftime("[%d/%b/%Y %H:%M:%S]")

class CsvManager:

    def __init__(self, filename: str, base_dir: str = "."):
        self.filename = f"{filename}.csv"
        self.filepath = Path(base_dir) / self.filename

        if not self.filepath.exists():
            print("Archivo no encontrado")
            self.filepath.touch()
            print("Archivo creado")
        else:
            print("Arvhivo encontrado e inicializado")

    def addTopRow(self, row: Tuple[Any, ...]) -> None:
        """Añade una fila al inicio del archivo CSV."""
        # Construir la línea de la nueva fila, con coma al final para marcar fin de fila
        row_line = ",".join(str(item) for item in row) + ",\n"
        # Leer el contenido existente del archivo (si existe)
        existing_content = ""
        if self.filepath.exists():
            existing_content = self.filepath.read_text()
        # Escribir la nueva fila y luego el contenido antiguo
        self.filepath.write_text(row_line + existing_content)
        print(f"addTopRow() added {row} to {self.filename}")

    def addEntry(self, row: Tuple[Any, ...]) -> None:
        """
        Añade una fila al final del archivo CSV.
        Si el archivo ya contiene datos y no termina en salto de línea,
        se agrega uno antes de la nueva fila para evitar que las líneas
        queden concatenadas.
        """
        # Construimos la línea con coma final, exactamente
        # igual que en addTopRow para mantener consistencia.
        row_line = ",".join(str(item) for item in row) + ",\n"

        # Creamos el archivo si, por alguna razón, se borró entre llamadas
        if not self.filepath.exists():
            self.filepath.touch()

        # Abrimos en modo append binario para evitar problemas de codificación
        with self.filepath.open("ab+") as f:
            f.seek(0, 2)               # Saltar al final
            last_pos = f.tell()
            if last_pos > 0:
                f.seek(-1, 2)          # Leer último byte
                last_char = f.read(1)
                # Si el archivo no termina en \n, lo agregamos
                if last_char != b"\n":
                    f.write(b"\n")
            f.write(row_line.encode())

        print(f"addEntry() added {row} to {self.filename}")

    def changePath(self, newBasePath: Path):
        pass

    def changeFileName(self):
        pass

    # Internal tooling
    def _saveError(self, error: str = "Causa no especificada") -> None:
        """
        Reporta un error al intentar guardar en el CSV.
        Muestra el aviso en color naranja (ANSI) y explica que el log no fue guardado.
        """
        ORANGE = "\033[93m"   # Amarillo intenso ≈ naranja en la mayoría de consolas
        RESET = "\033[0m"

        print(
            f"{ORANGE}CsvManager error report: {error}.\n"
            f" --Log no guardado en registro-- \n{RESET}"
        )

# ---- Colores ANSI
_RED: Final[str] = "\033[91m"
_YELLOW: Final[str] = "\033[93m"
_CYAN: Final[str] = "\033[96m"
_GREEN: Final[str] = "\033[92m"
_GRAY: Final[str] = "\033[90m"
_RESET: Final[str] = "\033[0m"

class Logger:
    """
    Logger con niveles y persistencia en CSV (vía CsvManager compatible).
    - Imprime en consola con color.
    - Intenta guardar en CSV; si falla, notifica en rojo.
    - Control de modo debug.
    - Limpieza vía dispose() o uso como context manager.
    """

    def __init__(self, doc: CsvManager, *, debug_enabled: bool = False) -> None:
        self._doc: Optional[CsvManager] = doc
        self._debug_enabled: bool = debug_enabled
        self._disposed: bool = False

    # ---------- API pública ----------
    def error(self, text: str) -> None:
        self._save("ERROR", text, _RED)

    def warning(self, text: str) -> None:
        self._save("WARNING", text, _YELLOW)

    def info(self, text: str) -> None:
        self._save("INFO", text, _CYAN)

    def success(self, text: str) -> None:
        self._save("SUCCESS", text, _GREEN)

    def debug(self, text: str) -> None:
        if not self._debug_enabled:
            return
        self._save("DEBUG", text, _GRAY)

    def set_debug(self, enabled: bool = True) -> None:
        """Activa o desactiva la salida DEBUG."""
        self._debug_enabled = enabled

    def dispose(self) -> None:
        """
        “Elimina” el objeto de forma segura:
        - Marca como disposed (ignora futuros guardados).
        - Suelta la referencia a manager para GC.
        """
        self._disposed = True
        self._doc = None

    # ---------- Context manager ----------
    def __enter__(self) -> "Logger":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        # Asegura limpieza de recursos
        self.dispose()

    # ---------- Internos ----------
    def _save(self, level: str, text: str, color: str) -> None:
        # 1) Consola
        print(f"{color}[{level}] {text}{_RESET}")

        # 2) Persistencia (si no está disposed y hay manager)
        if self._disposed or self._doc is None:
            return

        try:
            self._doc.addTopRow((f"[{level}] {text}", FechaHora().registro))
        except Exception as e:
            # Mantén tu mismo patrón de alerta en rojo
            print(f"{_RED}[ERROR] Desde {level}Log() '{e}': No se pudo guardar el registro en archivo.{_RESET}")


if __name__ == "__main__":

    def test1():
        csv = CsvManager("logRecord")
        csv.addTopRow(("fecha", "evento", "usuario"))
        print("Holis!")
        # Ok! El CSV manager sí funciona

    def test2():
        doc = CsvManager("lugTest")
        logger = Logger(doc, debug_enabled= False)

        logger.info("Servicio iniciado")
        logger.success("Usuario autenticado")
        logger.warning("Uso de API cercano al límite")
        logger.error("Archivo de configuración no encontrado")
        logger.debug("Payload crudo: {...}")   # (no imprimirá si debug_enabled=False)

        logger.set_debug(True)
        logger.debug("Índice calculado: 42")   # ahora sí imprimirá

        # Limpieza explícita
        logger.dispose()
        # Sí funciona, la cohesión también.

    pass
