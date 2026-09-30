from consumer import procesar, render_resumen, resumenes_existentes, trace_id_from_key


class FakeBucket:
    def __init__(self, objetos):
        self.objetos = dict(objetos)

    def list_keys(self, prefix):
        return [k for k in self.objetos if k.startswith(prefix)]

    def get_json(self, key):
        return self.objetos[key]

    def put_text(self, key, text, content_type):
        self.objetos[key] = text


MENSAJE = {
    "status": "completed",
    "pasos": [
        {"api": "medical-api", "cloud": "gcp", "entidad": {"id": 1, "nombre": "imagen1"}},
        {"api": "adoption-api", "cloud": "aws", "entidad": {"data": {"id": 3, "nombre": "Gatubela", "especie": "Gato"}}},
        {"api": "api_a", "cloud": "oci", "entidades": {"vuelo": {"id": 1, "numero_vuelo": "AV76865", "origen": "BOG"}}},
    ],
}


def test_trace_id_from_key():
    assert trace_id_from_key("flujo/abc-1.json") == "abc-1"
    assert trace_id_from_key("adjuntos/abc-1/resumen.md") is None


def test_resumen_lista_los_pasos_de_las_tres_nubes():
    texto = render_resumen("abc-1", MENSAJE)
    assert "# Resumen del mensaje abc-1" in texto
    assert "| 1 | medical-api | gcp | id=1, nombre=imagen1 |" in texto
    assert "Gatubela" in texto
    assert "numero_vuelo=AV76865" in texto


def test_procesar_genera_un_resumen_por_mensaje_nuevo():
    bucket = FakeBucket({"flujo/t1.json": MENSAJE, "flujo/t2.json": MENSAJE})
    hechos = resumenes_existentes(bucket)
    assert sorted(procesar(bucket, hechos)) == ["t1", "t2"]
    assert "adjuntos/t1/resumen.md" in bucket.objetos
    assert procesar(bucket, hechos) == []
    assert resumenes_existentes(bucket) == {"t1", "t2"}
