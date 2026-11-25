"""Tests de desplegar.py contra una API de Dokploy simulada (http.server local). Sin red externa.

    python3 -B -m unittest discover -s tests      (desde la carpeta de la skill)
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import desplegar  # noqa: E402

TOKEN = "tok-SECRETO-de-prueba-123456"
SHA = "a" * 40
SHA_VIEJO = "b" * 40


class Falsa:
    """Estado de la API simulada: proyectos, apps, despliegues y salud."""

    def __init__(self):
        self.peticiones: list[tuple[str, str, dict]] = []
        self.deploys: dict[str, list[dict]] = {
            "appTest": [{"deploymentId": "d0", "status": "done", "createdAt": "2026-11-20T10:00:00Z",
                         "startedAt": "2026-11-20T10:00:00Z", "description": f"Commit: {SHA_VIEJO}",
                         "title": "viejo"}],
            "appProd": [],
        }
        self.resultado = "done"          # estado final del despliegue lanzado
        self.sondeos_hasta_fin = 2       # cuántas lecturas sigue "running"
        self.registrar_despliegue = True
        self.salud = 200
        self.version = SHA
        self.log = "linea 1\nDB_PASSWORD=hunter2\nlinea 3\n✅ Docker build completed."
        self._lecturas = 0

    def proyectos(self, puerto: int):
        app = lambda i, n: {"applicationId": i, "name": n, "appName": f"{n}-x"}  # noqa: E731
        return [{"name": "MRH", "projectId": "p1", "environments": [
            {"name": "development", "environmentId": "e1", "applications": [app("appTest", "landing")]},
            {"name": "production", "environmentId": "e2", "applications": [app("appProd", "front")]},
        ]}]

    def aplicacion(self, app_id: str):
        return {"applicationId": app_id, "name": "x", "applicationStatus": "done",
                "customGitUrl": "git@github.com:Deneros/mrh-landing.git", "customGitBranch": "main",
                "autoDeploy": app_id == "appTest", "env": "SECRET_KEY=no-debe-salir",
                "domains": [{"host": "localhost", "https": False, "path": "/"}],
                "deployments": list(self.deploys.get(app_id, []))}


def servidor(falsa: Falsa) -> ThreadingHTTPServer:
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _json(self, codigo: int, datos):
            cuerpo = json.dumps(datos).encode()
            self.send_response(codigo)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)

        def _ruta(self, metodo: str):
            u = urllib.parse.urlsplit(self.path)
            q = dict(urllib.parse.parse_qsl(u.query))
            cuerpo = {}
            if metodo == "POST":
                cuerpo = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            if u.path == "/salud":
                return self._json(falsa.salud, {"status": "ok"})
            if u.path == "/version":
                return self._json(200, {"commit": falsa.version})
            if self.headers.get("x-api-key") != TOKEN:
                return self._json(401, {"message": "Unauthorized"})
            falsa.peticiones.append((metodo, u.path, cuerpo or q))
            ep = u.path.removeprefix("/api/")
            if ep == "project.all":
                return self._json(200, falsa.proyectos(self.server.server_port))
            if ep == "application.one":
                return self._json(200, falsa.aplicacion(q["applicationId"]))
            if ep == "deployment.all":
                deps = falsa.deploys.get(q["applicationId"], [])
                for d in deps:
                    if d["status"] == "running":
                        falsa._lecturas += 1
                        if falsa._lecturas >= falsa.sondeos_hasta_fin:
                            d.update(status=falsa.resultado, finishedAt="2026-11-25T12:03:00Z")
                return self._json(200, list(reversed(sorted(deps, key=lambda d: d["createdAt"]))))
            if ep in ("application.deploy", "application.redeploy"):
                if falsa.registrar_despliegue:
                    falsa.deploys[cuerpo["applicationId"]].append(
                        {"deploymentId": "dNuevo", "status": "running", "createdAt": "2026-11-25T12:00:00Z",
                         "startedAt": "2026-11-25T12:00:00Z", "description": cuerpo.get("description", ""),
                         "errorMessage": "fallo de build" if falsa.resultado == "error" else None})
                return self._json(200, True)
            if ep == "deployment.readLogs":
                return self._json(200, falsa.log)
            return self._json(404, {"message": "no"})

        def do_GET(self):
            self._ruta("GET")

        def do_POST(self):
            self._ruta("POST")

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


class Base(unittest.TestCase):
    def setUp(self):
        self.falsa = Falsa()
        self.srv = servidor(self.falsa)
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)
        puerto = self.srv.server_port
        self.tmp = tempfile.mkdtemp()
        self.token = os.path.join(self.tmp, "token")
        with open(self.token, "w") as f:
            f.write(TOKEN + "\n")
        os.chmod(self.token, 0o600)
        self.salud = os.path.join(self.tmp, "app-health.json")
        with open(self.salud, "w") as f:
            json.dump({"urls": [{"nombre": "Landing (test)", "url": f"http://localhost:{puerto}/salud"}]}, f)
        self.config = os.path.join(self.tmp, "config.json")
        with open(self.config, "w") as f:
            json.dump({"version_urls": {}}, f)
        self.base = ["--api", f"http://127.0.0.1:{puerto}", "--token-file", self.token,
                     "--app-health", self.salud, "--config", self.config]
        parche = mock.patch.object(desplegar, "cabeza_rama", return_value=(SHA, "2026-11-24T00:00:00Z"))
        self.cabeza = parche.start()
        self.addCleanup(parche.stop)

    def correr(self, *args: str) -> tuple[int, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            codigo = desplegar.main(self.base + list(args))
        texto = out.getvalue() + err.getvalue()
        self.assertNotIn(TOKEN, texto, "el token nunca se imprime")
        self.assertNotIn("no-debe-salir", texto, "el env de la app nunca se imprime")
        return codigo, texto

    def lanzados(self) -> list:
        return [p for p in self.falsa.peticiones if p[1].endswith(("application.deploy", "application.redeploy"))]


class TestListarYResolver(Base):
    def test_listar_muestra_entornos_y_marca_produccion(self):
        codigo, texto = self.correr("listar")
        self.assertEqual(codigo, 0)
        self.assertIn("MRH / production — PRODUCCIÓN", texto)
        self.assertIn("landing", texto)
        self.assertIn("appTest", texto)
        self.assertEqual(self.lanzados(), [])

    def test_resolver_por_alias_de_entorno_e_id(self):
        apps = [{"proyecto": "MRH", "entorno": "development", "nombre": "landing", "id": "appTest", "appName": "l"},
                {"proyecto": "MRH", "entorno": "production", "nombre": "front", "id": "appProd", "appName": "f"}]
        self.assertEqual(desplegar.resolver(apps, "mrh/test/landing")["id"], "appTest")
        self.assertEqual(desplegar.resolver(apps, "MRH/prod/front")["id"], "appProd")
        self.assertEqual(desplegar.resolver(apps, "appProd")["id"], "appProd")
        with self.assertRaises(desplegar.Rechazo):
            desplegar.resolver(apps, "mrh/test/back")

    def test_token_incorrecto_da_fallo_sin_imprimir_token(self):
        with open(self.token, "w") as f:
            f.write("otro")
        codigo, texto = self.correr("listar")
        self.assertEqual(codigo, 1)
        self.assertIn("HTTP 401", texto)

    def test_sin_token_rechaza(self):
        os.remove(self.token)
        codigo, texto = self.correr("listar")
        self.assertEqual(codigo, 2)
        self.assertIn("token", texto)


class TestDesplegar(Base):
    def test_dry_run_no_despliega(self):
        codigo, texto = self.correr("desplegar", "mrh/test/landing", "--dry-run")
        self.assertEqual(codigo, 0)
        self.assertIn("--dry-run: no se desplegó nada", texto)
        self.assertIn(SHA[:7], texto)
        self.assertEqual(self.lanzados(), [])

    def test_produccion_sin_confirmacion_rechaza_y_no_lanza(self):
        codigo, texto = self.correr("desplegar", "mrh/prod/front")
        self.assertEqual(codigo, 2)
        self.assertIn("PRODUCCIÓN", texto)
        self.assertEqual(self.lanzados(), [])

    def test_produccion_dry_run_no_lanza_y_avisa(self):
        codigo, texto = self.correr("desplegar", "mrh/prod/front", "--dry-run")
        self.assertEqual(codigo, 0)
        self.assertIn("exige la confirmación", texto)
        codigo, _ = self.correr("desplegar", "mrh/prod/front", "--dry-run", "--si-produccion")
        self.assertEqual(codigo, 0)
        self.assertEqual(self.lanzados(), [])

    def test_despliegue_correcto_espera_muestra_log_redactado_y_verifica(self):
        codigo, texto = self.correr("desplegar", "mrh/test/landing", "--intervalo", "0.01", "--espera-salud", "0")
        self.assertEqual(codigo, 0, texto)
        lanzado = self.lanzados()
        self.assertEqual(len(lanzado), 1)
        self.assertEqual(lanzado[0][2]["applicationId"], "appTest")
        self.assertIn(SHA, lanzado[0][2]["description"])
        self.assertIn("Despliegue dNuevo: done", texto)
        self.assertIn("Docker build completed", texto)
        self.assertNotIn("hunter2", texto)
        self.assertIn("DB_PASSWORD=<REDACTADO>", texto)
        self.assertIn("Salud OK", texto)
        self.assertIn("no expone versión", texto)

    def test_despliegue_fallido_devuelve_1_con_log(self):
        self.falsa.resultado = "error"
        codigo, texto = self.correr("desplegar", "mrh/test/landing", "--intervalo", "0.01")
        self.assertEqual(codigo, 1)
        self.assertIn("FALLÓ el despliegue", texto)
        self.assertIn("fallo de build", texto)
        self.assertIn("linea 3", texto)

    def test_salud_caida_tras_desplegar_devuelve_1(self):
        self.falsa.salud = 503
        codigo, texto = self.correr("desplegar", "mrh/test/landing", "--intervalo", "0.01", "--espera-salud", "0.05")
        self.assertEqual(codigo, 1)
        self.assertIn("Salud FALLO", texto)
        self.assertIn("HTTP 503", texto)

    def test_tiempo_agotado(self):
        self.falsa.sondeos_hasta_fin = 10 ** 6
        codigo, texto = self.correr("desplegar", "mrh/test/landing", "--intervalo", "0.01", "--timeout", "0.2")
        self.assertEqual(codigo, 1)
        self.assertIn("tiempo agotado", texto)

    def test_dokploy_no_registra_el_despliegue(self):
        self.falsa.registrar_despliegue = False
        codigo, texto = self.correr("desplegar", "mrh/test/landing", "--intervalo", "0.01", "--timeout", "0.1")
        self.assertEqual(codigo, 1)
        self.assertIn("no registró", texto)

    def test_despliegue_en_curso_rechaza(self):
        self.falsa.deploys["appTest"].append({"deploymentId": "dx", "status": "running",
                                              "createdAt": "2026-11-25T11:00:00Z", "description": ""})
        self.falsa.sondeos_hasta_fin = 10 ** 6
        codigo, texto = self.correr("desplegar", "mrh/test/landing")
        self.assertEqual(codigo, 2)
        self.assertIn("en curso", texto)
        self.assertEqual(self.lanzados(), [])

    def test_version_url_que_no_coincide_falla(self):
        self.falsa.version = "c" * 40
        url = f"http://127.0.0.1:{self.srv.server_port}/version"
        codigo, texto = self.correr("desplegar", "mrh/test/landing", "--intervalo", "0.01", "--espera-salud", "0",
                                    "--version-url", url)
        self.assertEqual(codigo, 1)
        self.assertIn("NO informa el commit esperado", texto)

    def test_version_url_que_coincide(self):
        url = f"http://127.0.0.1:{self.srv.server_port}/version"
        codigo, texto = self.correr("verificar", "mrh/test/landing", "--espera-salud", "0", "--version-url", url)
        self.assertEqual(codigo, 0, texto)
        self.assertIn("informa el commit", texto)

    def test_rebuild_usa_redeploy(self):
        self.correr("desplegar", "mrh/test/landing", "--rebuild", "--intervalo", "0.01", "--espera-salud", "0")
        self.assertTrue(self.lanzados()[0][1].endswith("application.redeploy"))


class TestEstado(Base):
    def test_detecta_no_desplegado(self):
        codigo, texto = self.correr("estado", "mrh/test/landing")
        self.assertEqual(codigo, 0)
        self.assertIn("NO DESPLEGADO", texto)
        self.assertIn(SHA_VIEJO[:7], texto)

    def test_al_dia(self):
        self.cabeza.return_value = (SHA_VIEJO, "2026-11-19T00:00:00Z")
        _, texto = self.correr("estado", "mrh/test/landing")
        self.assertIn("AL DÍA", texto)

    def test_veredicto_manual_sin_commit(self):
        d = {"rama": "main", "auto": False}
        deps = [{"status": "done", "createdAt": "2026-11-25T10:00:00Z", "description": ""}]
        self.assertIn("PROBABLEMENTE AL DÍA", desplegar.veredicto(d, deps, (SHA, "2026-11-24T00:00:00Z")))
        v = desplegar.veredicto(d, deps, (SHA, "2026-11-26T00:00:00Z"))
        self.assertIn("NO DESPLEGADO", v)
        self.assertIn("autoDeploy apagado", v)


class TestUtilidades(unittest.TestCase):
    def test_urls_salud_usa_app_health_por_host(self):
        cfg = {"urls": [{"nombre": "API", "url": "https://testapi.x.net/api/core/health/"},
                        {"nombre": "Otra", "url": "https://otra.net/"}]}
        urls = desplegar.urls_salud([{"host": "testapi.x.net", "https": True, "path": "/"}], cfg)
        self.assertEqual([u["url"] for u in urls], ["https://testapi.x.net/api/core/health/"])

    def test_urls_salud_cae_a_la_raiz_y_prefiere_dominio_propio(self):
        doms = [{"host": "a.1.2.3.4.sslip.io", "https": True, "path": "/"},
                {"host": "app.x.com", "https": True, "path": "/"}]
        self.assertEqual(desplegar.urls_salud(doms, {})[0]["url"], "https://app.x.com/")
        self.assertEqual(desplegar.urls_salud([], {}), [])

    def test_redactar(self):
        t = desplegar.redactar("API_KEY=abc secret: x1 ok=1 https://u:pw@h/ tokXYZ", "tokXYZ")
        for s in ("abc", "x1", "pw@", "tokXYZ"):
            self.assertNotIn(s, t)
        self.assertIn("ok=1", t)

    def test_repo_github(self):
        self.assertEqual(desplegar.repo_github("git@github.com:Deneros/MRH.git"), "Deneros/MRH")
        self.assertEqual(desplegar.repo_github("https://github.com/Deneros/auditglow-download.git"),
                         "Deneros/auditglow-download")
        self.assertIsNone(desplegar.repo_github("ghcr.io/x"))


if __name__ == "__main__":
    unittest.main()
