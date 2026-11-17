from pathlib import Path

from chaos.security.resguardo import CopiaAislada


def test_la_copia_no_se_sobrescribe_ni_se_borra(tmp_path: Path):
    copia = CopiaAislada(tmp_path)
    copia.guardar("flujo/resumen.json", b"original")
    try:
        copia.guardar("flujo/resumen.json", b"otro")
    except PermissionError:
        pass
    else:
        raise AssertionError("dejo sobrescribir")
    try:
        copia.borrar("flujo/resumen.json")
    except PermissionError:
        pass
    else:
        raise AssertionError("dejo borrar")
    assert copia.leer("flujo/resumen.json") == b"original"
