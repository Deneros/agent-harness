#!/usr/bin/env python3
"""desplegar: listar, desplegar y verificar aplicaciones de Dokploy (MRH y AuditGlow) por su API.

Solo biblioteca estándar (Python 3.9+). El token se lee de ~/.dokploy-token y nunca se imprime.
Códigos de salida: 0 = bien, 1 = se intentó y falló (despliegue, salud o commit), 2 = rechazado
(uso, producción sin confirmar, despliegue en curso, app inexistente): no se cambió nada.

  desplegar.py listar [--proyecto mrh]
  desplegar.py estado mrh/test/front                 # ¿ya se desplegó? cabeza de la rama contra lo desplegado
  desplegar.py desplegar mrh/test/landing --dry-run  # qué haría, sin desplegar
  desplegar.py desplegar mrh/test/landing            # despliega, espera, muestra el log y verifica
  desplegar.py desplegar auditglow/prod/web --si-produccion   # solo tras la confirmación explícita del usuario
  desplegar.py verificar auditglow/prod/back         # salud pública y commit, sin desplegar
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DIR = os.path.dirname(os.path.abspath(__file__))
OK, FALLO, RECHAZO = 0, 1, 2

API_POR_DEFECTO = "http://100.90.12.126:3000"
TOKEN_POR_DEFECTO = "~/.dokploy-token"
APP_HEALTH_POR_DEFECTO = "~/development/operaciones/acris/app-health/config.json"

ENTORNOS = {
    "test": "development", "dev": "development", "development": "development", "desarrollo": "development",
    "pruebas": "development", "staging": "development",
    "prod": "production", "produccion": "production", "producción": "production", "production": "production",
}
EN_CURSO = {"running", "queued", "pending"}
TERMINADOS = {"done", "error", "cancelled"}
RE_COMMIT = re.compile(r"Commit(?: esperado)?:\s*([0-9a-f]{7,40})", re.I)
RE_SECRETO = re.compile(
    r"(?i)\b([A-Z0-9_]*(?:PASS(?:WORD)?|SECRET|TOKEN|API[_-]?KEY|PRIVATE[_-]?KEY|ACCESS[_-]?KEY|CREDENTIAL)[A-Z0-9_]*"
    r"\s*[=:]\s*)(\"[^\"]*\"|'[^']*'|\S+)")
RE_URL_CON_CLAVE = re.compile(r"(://[^/\s:@]+:)[^@\s/]+@")


class Rechazo(Exception):
    """Petición rechazada antes de cambiar nada (código 2)."""


class Fallo(Exception):
    """Se intentó y falló (código 1)."""


# ---------------------------------------------------------------------------- utilidades

def redactar(texto: str, token: str = "") -> str:
    """Quita del texto valores con aspecto de secreto (y el token, si aparece)."""
    if token:
        texto = texto.replace(token, "<REDACTADO>")
    texto = RE_URL_CON_CLAVE.sub(r"\1<REDACTADO>@", texto)
    return RE_SECRETO.sub(r"\1<REDACTADO>", texto)


def corto(sha: str | None) -> str:
    return sha[:7] if sha else "?"


def fecha(iso: str | None) -> str:
    return (iso or "")[:16].replace("T", " ") or "?"


def leer_json(ruta: str) -> dict:
    with open(os.path.expanduser(ruta), encoding="utf-8") as f:
        return json.load(f)


def leer_token(ruta: str) -> str:
    ruta = os.path.expanduser(ruta)
    try:
        with open(ruta, encoding="utf-8") as f:
            token = f.read().strip()
    except OSError as e:
        raise Rechazo(f"no se pudo leer el token de Dokploy ({ruta}): {e.strerror}") from None
    if not token:
        raise Rechazo(f"el archivo del token de Dokploy está vacío ({ruta})")
    if os.stat(ruta).st_mode & 0o077:
        print(f"aviso: {ruta} debería tener permisos 600", file=sys.stderr)
    return token


# ---------------------------------------------------------------------------- API de Dokploy

class Dokploy:
    def __init__(self, base: str, token: str, timeout: float = 30):
        self.base = base.rstrip("/") + "/api/"
        self._token = token
        self.timeout = timeout

    def _pedir(self, metodo: str, endpoint: str, params: dict | None = None, cuerpo: dict | None = None):
        url = self.base + endpoint
        if params:
            url += "?" + urllib.parse.urlencode(params)
        datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
        req = urllib.request.Request(url, data=datos, method=metodo)
        req.add_header("x-api-key", self._token)
        req.add_header("Accept", "application/json")
        if datos is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                bruto = r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            cuerpo_err = e.read().decode("utf-8", "replace")[:300]
            raise Fallo(f"Dokploy {endpoint}: HTTP {e.code} {redactar(cuerpo_err, self._token)}") from None
        except (urllib.error.URLError, OSError) as e:
            motivo = getattr(e, "reason", e)
            raise Fallo(f"Dokploy {endpoint}: sin conexión ({motivo}). ¿Tailscale conectado?") from None
        if not bruto.strip():
            return None
        try:
            return json.loads(bruto)
        except ValueError:
            return bruto

    def get(self, endpoint: str, **params):
        return self._pedir("GET", endpoint, params=params)

    def post(self, endpoint: str, cuerpo: dict):
        return self._pedir("POST", endpoint, cuerpo=cuerpo)


def inventario(api: Dokploy) -> list[dict]:
    apps = []
    for p in api.get("project.all") or []:
        for e in p.get("environments") or []:
            for a in e.get("applications") or []:
                apps.append({"proyecto": p.get("name", ""), "entorno": e.get("name", ""),
                             "nombre": a.get("name", ""), "id": a.get("applicationId", ""),
                             "appName": a.get("appName", "")})
    return apps


def resolver(apps: list[dict], selector: str) -> dict:
    """Acepta un applicationId, un appName o proyecto/entorno/nombre (entorno: test, prod...)."""
    exactos = [a for a in apps if selector in (a["id"], a["appName"])]
    if len(exactos) == 1:
        return exactos[0]
    partes = selector.strip("/").split("/")
    if len(partes) != 3:
        raise Rechazo(f"app '{selector}' no encontrada; usa proyecto/entorno/nombre (p. ej. mrh/test/front) "
                      "o el applicationId. `listar` muestra todas")
    proyecto, entorno, nombre = (x.lower() for x in partes)
    entorno = ENTORNOS.get(entorno, entorno)
    hallados = [a for a in apps if a["proyecto"].lower() == proyecto and a["entorno"].lower() == entorno
                and a["nombre"].lower() == nombre]
    if not hallados:
        candidatos = [f"{a['proyecto']}/{a['entorno']}/{a['nombre']}" for a in apps
                      if a["proyecto"].lower() == proyecto]
        pista = ("; en ese proyecto hay: " + ", ".join(candidatos)) if candidatos else ""
        raise Rechazo(f"app '{selector}' no encontrada{pista}")
    if len(hallados) > 1:
        raise Rechazo(f"'{selector}' es ambiguo: " + ", ".join(a["id"] for a in hallados))
    return hallados[0]


def detalle(api: Dokploy, ref: dict) -> dict:
    """Solo los campos seguros de application.one (nunca env, secretos ni contraseñas)."""
    a = api.get("application.one", applicationId=ref["id"]) or {}
    dominios = [{"host": d.get("host", ""), "https": bool(d.get("https")), "path": d.get("path") or "/"}
                for d in (a.get("domains") or []) if d.get("host")]
    return {
        **ref,
        "estado": a.get("applicationStatus", "?"),
        "repo": a.get("customGitUrl") or a.get("repository") or "",
        "rama": a.get("customGitBranch") or a.get("branch") or "",
        "auto": bool(a.get("autoDeploy")),
        "dominios": dominios,
        "despliegues": ordenar(a.get("deployments") or []),
    }


def ordenar(despliegues: list[dict]) -> list[dict]:
    return sorted(despliegues, key=lambda d: d.get("createdAt") or "", reverse=True)


def despliegues(api: Dokploy, app_id: str) -> list[dict]:
    return ordenar(api.get("deployment.all", applicationId=app_id) or [])


def commit_de(dep: dict) -> str | None:
    m = RE_COMMIT.search(dep.get("description") or "")
    return m.group(1) if m else None


def log_final(api: Dokploy, dep_id: str, lineas: int, token: str) -> str:
    try:
        texto = api.get("deployment.readLogs", deploymentId=dep_id, tail=max(lineas, 1))
    except Fallo as e:
        return f"(no se pudo leer el log: {e})"
    if not isinstance(texto, str):
        texto = json.dumps(texto, ensure_ascii=False)
    final = texto.rstrip("\n").splitlines()[-lineas:]
    return redactar("\n".join(final), token)


# ---------------------------------------------------------------------------- git

def repo_github(url: str) -> str | None:
    m = re.search(r"github\.com[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", url or "")
    return f"{m.group(1)}/{m.group(2)}" if m else None


def cabeza_rama(repo_url: str, rama: str) -> tuple[str, str] | None:
    """(sha, fecha) de la cabeza de la rama en GitHub, con el `gh` ya autenticado. None si no se puede."""
    repo = repo_github(repo_url)
    if not repo or not rama:
        return None
    try:
        r = subprocess.run(["gh", "api", f"repos/{repo}/commits/{rama}", "--jq",
                            '.sha + " " + .commit.committer.date'],
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    partes = r.stdout.split()
    if r.returncode != 0 or len(partes) != 2 or not re.fullmatch(r"[0-9a-f]{40}", partes[0]):
        return None
    return partes[0], partes[1]


# ---------------------------------------------------------------------------- salud

class SinRedireccion(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # como app-health: el código esperado es el de la URL tal cual
        return None


_ABRIR = urllib.request.build_opener(SinRedireccion)


def urls_salud(dominios: list[dict], app_health: dict) -> list[dict]:
    """URLs de salud de la app: las de app-health cuyo host es un dominio de la app; si no hay, la raíz del dominio."""
    hosts = {d["host"].lower() for d in dominios}
    elegidas = []
    for u in app_health.get("urls") or []:
        host = (urllib.parse.urlsplit(u.get("url", "")).hostname or "").lower()
        if host in hosts:
            esperado = u.get("esperado", 200)
            elegidas.append({"nombre": u.get("nombre", host), "url": u["url"],
                             "esperado": esperado if isinstance(esperado, list) else [esperado]})
    if elegidas:
        return elegidas
    propios = [d for d in dominios if "sslip.io" not in d["host"]] or dominios
    if not propios:
        return []
    d = propios[0]
    url = f"{'https' if d['https'] else 'http'}://{d['host']}{d['path'] or '/'}"
    return [{"nombre": d["host"], "url": url, "esperado": [200]}]


def comprobar_url(url: str, esperado: list[int], timeout: float = 10) -> tuple[bool, str]:
    inicio = time.monotonic()
    try:
        with _ABRIR.open(urllib.request.Request(url, headers={"User-Agent": "desplegar/1"}), timeout=timeout) as r:
            r.read(65536)
            codigo = r.status
    except urllib.error.HTTPError as e:
        codigo = e.code
    except (urllib.error.URLError, OSError) as e:
        return False, f"sin respuesta ({getattr(e, 'reason', e)})"
    ms = int((time.monotonic() - inicio) * 1000)
    return codigo in esperado, f"HTTP {codigo} en {ms} ms" + ("" if codigo in esperado else f", se esperaba {esperado}")


def verificar_salud(urls: list[dict], espera: float, intervalo: float) -> bool:
    """Reintenta hasta `espera` segundos (el contenedor nuevo tarda en arrancar). Imprime el resultado final."""
    if not urls:
        print("Salud: la app no tiene dominio público (worker o beat); revisa su log en Dokploy.")
        return True
    limite = time.monotonic() + espera
    while True:
        resultados = [(u, *comprobar_url(u["url"], u["esperado"])) for u in urls]
        if all(ok for _, ok, _ in resultados) or time.monotonic() >= limite:
            break
        time.sleep(intervalo)
    for u, ok, info in resultados:
        print(f"Salud {'OK   ' if ok else 'FALLO'} {u['nombre']}: {u['url']} → {info}")
    return all(ok for _, ok, _ in resultados)


def verificar_version(url: str, sha: str) -> tuple[bool, str]:
    try:
        with _ABRIR.open(urllib.request.Request(url, headers={"User-Agent": "desplegar/1"}), timeout=10) as r:
            cuerpo = r.read(65536).decode("utf-8", "replace")
    except (urllib.error.URLError, OSError) as e:
        return False, f"no se pudo leer la versión en {url} ({getattr(e, 'reason', e)})"
    if sha[:7] in cuerpo:
        return True, f"la app informa el commit {corto(sha)} ({url})"
    return False, f"la app NO informa el commit esperado {corto(sha)} ({url})"


# ---------------------------------------------------------------------------- comandos

def linea_app(d: dict) -> str:
    ultimo = d["despliegues"][0] if d["despliegues"] else None
    ult = (f"último {fecha(ultimo.get('createdAt'))} {ultimo.get('status')} {corto(commit_de(ultimo))}"
           if ultimo else "sin despliegues")
    hosts = ",".join(x["host"] for x in d["dominios"]) or "-"
    return (f"  {d['nombre']:<18} {d['id']:<22} rama={d['rama'] or '-':<8} "
            f"{'auto' if d['auto'] else 'manual'} estado={d['estado']:<6} {hosts}  ({ult})")


def cmd_listar(api: Dokploy, args) -> int:
    apps = inventario(api)
    if args.proyecto:
        apps = [a for a in apps if a["proyecto"].lower() == args.proyecto.lower()]
        if not apps:
            raise Rechazo(f"no hay apps en el proyecto '{args.proyecto}'")
    grupo = None
    for a in sorted(apps, key=lambda a: (a["proyecto"], a["entorno"] != "production", a["nombre"])):
        if (a["proyecto"], a["entorno"]) != grupo:
            grupo = (a["proyecto"], a["entorno"])
            nota = " — PRODUCCIÓN: pedir confirmación" if a["entorno"] == "production" else " (test)"
            print(f"{a['proyecto']} / {a['entorno']}{nota}")
        print(linea_app(detalle(api, a)))
    return OK


def veredicto(d: dict, deps: list[dict], cabeza: tuple[str, str] | None) -> str:
    if not deps:
        return "Nunca se ha desplegado."
    ultimo = deps[0]
    if ultimo.get("status") in EN_CURSO:
        return f"Hay un despliegue EN CURSO desde {fecha(ultimo.get('startedAt') or ultimo.get('createdAt'))}."
    hechos = [x for x in deps if x.get("status") == "done"]
    aviso = ""
    if ultimo.get("status") != "done":
        aviso = (f" El último intento ({fecha(ultimo.get('createdAt'))}) terminó en '{ultimo.get('status')}'"
                 f"{': ' + ultimo['errorMessage'] if ultimo.get('errorMessage') else ''}.")
    if not hechos:
        return "Ningún despliegue terminó bien." + aviso
    bueno = hechos[0]
    if not cabeza:
        return (f"Último despliegue bueno: {fecha(bueno.get('createdAt'))}, commit {corto(commit_de(bueno))}. "
                "No se pudo leer la cabeza de la rama en GitHub (¿gh autenticado?)." + aviso)
    sha, cuando = cabeza
    sha_dep = commit_de(bueno)
    manual = "" if d["auto"] else " Esta app NO se despliega sola (autoDeploy apagado): hay que lanzarla."
    if sha_dep:
        if sha.startswith(sha_dep) or sha_dep.startswith(sha):
            return f"AL DÍA: {corto(sha)} (cabeza de {d['rama']}) desplegado el {fecha(bueno.get('createdAt'))}." + aviso
        return (f"NO DESPLEGADO: la cabeza de {d['rama']} es {corto(sha)} ({fecha(cuando)}) y lo último desplegado "
                f"es {corto(sha_dep)} ({fecha(bueno.get('createdAt'))})." + manual + aviso)
    if (bueno.get("startedAt") or bueno.get("createdAt") or "") > cuando:
        return (f"PROBABLEMENTE AL DÍA: el último despliegue bueno ({fecha(bueno.get('createdAt'))}, manual, Dokploy "
                f"no anotó el commit) empezó después del commit {corto(sha)} ({fecha(cuando)}).") + aviso
    return (f"NO DESPLEGADO: la cabeza de {d['rama']} ({corto(sha)}, {fecha(cuando)}) es posterior al último "
            f"despliegue bueno ({fecha(bueno.get('createdAt'))})." + manual + aviso)


def cmd_estado(api: Dokploy, args, app_health: dict) -> int:
    d = detalle(api, resolver(inventario(api), args.app))
    deps = despliegues(api, d["id"])
    cabeza = (args.commit, "") if args.commit else cabeza_rama(d["repo"], d["rama"])
    print(f"{d['proyecto']} / {d['entorno']} / {d['nombre']} ({d['id']})  repo={repo_github(d['repo']) or d['repo']} "
          f"rama={d['rama']} {'auto' if d['auto'] else 'manual'} estado={d['estado']}")
    for x in deps[:5]:
        titulo = (x.get("title") or "").splitlines()[0][:60] if x.get("title") else ""
        print(f"  {fecha(x.get('createdAt'))}  {x.get('status'):<9} {corto(commit_de(x))}  {titulo}")
    print(veredicto(d, deps, cabeza))
    salud_ok = verificar_salud(urls_salud(d["dominios"], app_health), 0, 0)
    return OK if salud_ok else FALLO


def esperar(api: Dokploy, app_id: str, previos: set, timeout: float, intervalo: float) -> dict:
    limite = time.monotonic() + timeout
    visto = None
    while time.monotonic() < limite:
        nuevos = [x for x in despliegues(api, app_id) if x.get("deploymentId") not in previos]
        if nuevos:  # el primero creado tras lanzar es el nuestro
            visto = sorted(nuevos, key=lambda x: x.get("createdAt") or "")[0]
            if visto.get("status") in TERMINADOS:
                return visto
        time.sleep(intervalo)
    if visto is None:
        raise Fallo(f"Dokploy no registró el despliegue en {int(timeout)} s (¿cola atascada? `deployment.queueList`)")
    raise Fallo(f"tiempo agotado ({int(timeout)} s): el despliegue {visto.get('deploymentId')} sigue en "
                f"'{visto.get('status')}' en Dokploy; vuelve a mirar con `estado`")


def comprobar_commit(d: dict, sha: str | None, version_url: str | None, dep: dict | None) -> bool:
    if not sha:
        print("Commit: no hay commit esperado (no se pudo leer la rama en GitHub ni se pasó --commit).")
        return True
    if version_url:
        ok, info = verificar_version(version_url, sha)
        print(f"Commit {'OK   ' if ok else 'FALLO'} {info}")
        return ok
    registrado = commit_de(dep) if dep else None
    if registrado and dep and "esperado" not in (dep.get("description") or "").lower():
        ok = sha.startswith(registrado) or registrado.startswith(sha)
        print(f"Commit {'OK   ' if ok else 'FALLO'} Dokploy anotó {corto(registrado)}; esperado {corto(sha)}")
        return ok
    print(f"Commit: la app no expone versión; Dokploy construyó la cabeza de {d['rama']}, que al lanzar era "
          f"{corto(sha)} (no verificable en la app).")
    return True


def cmd_verificar(api: Dokploy, args, app_health: dict, config: dict) -> int:
    d = detalle(api, resolver(inventario(api), args.app))
    deps = [x for x in despliegues(api, d["id"]) if x.get("status") == "done"]
    sha = args.commit or (cabeza_rama(d["repo"], d["rama"]) or (None,))[0]
    salud = verificar_salud(urls_salud(d["dominios"], app_health), args.espera_salud, args.intervalo)
    url_version = args.version_url or (config.get("version_urls") or {}).get(d["id"])
    commit = comprobar_commit(d, sha, url_version, deps[0] if deps else None)
    return OK if salud and commit else FALLO


def cmd_desplegar(api: Dokploy, args, app_health: dict, config: dict, token: str) -> int:
    d = detalle(api, resolver(inventario(api), args.app))
    nombre = f"{d['proyecto']}/{d['entorno']}/{d['nombre']}"
    produccion = d["entorno"].lower() == "production"
    if produccion and not args.si_produccion and not args.dry_run:
        raise Rechazo(f"{nombre} es PRODUCCIÓN: no se despliega sin la confirmación explícita del usuario. "
                      "Con ella (y los gates de la skill cumplidos), repite con --si-produccion")
    deps = despliegues(api, d["id"])
    en_curso = [x for x in deps if x.get("status") in EN_CURSO]
    if en_curso or d["estado"] in EN_CURSO:
        raise Rechazo(f"{nombre} ya tiene un despliegue en curso; espera a que termine (`estado {args.app}`)")
    cabeza = None if args.commit else cabeza_rama(d["repo"], d["rama"])
    sha = args.commit or (cabeza[0] if cabeza else None)
    urls = urls_salud(d["dominios"], app_health)
    url_version = args.version_url or (config.get("version_urls") or {}).get(d["id"])
    endpoint = "application.redeploy" if args.rebuild else "application.deploy"

    print(f"App: {nombre} ({d['id']}){' — PRODUCCIÓN' if produccion else ''}")
    print(f"Fuente: {repo_github(d['repo']) or d['repo']} rama {d['rama']} · commit esperado {corto(sha)}")
    print(f"Acción: POST {endpoint} · espera máx. {int(args.timeout)} s · salud: "
          + (", ".join(u["url"] for u in urls) or "sin dominio público"))
    if deps:
        print(f"Último despliegue: {fecha(deps[0].get('createdAt'))} {deps[0].get('status')} {corto(commit_de(deps[0]))}")
    if args.dry_run:
        if produccion and not args.si_produccion:
            print("PRODUCCIÓN: el despliegue real exige la confirmación explícita del usuario y --si-produccion.")
        print("--dry-run: no se desplegó nada.")
        return OK

    previos = {x.get("deploymentId") for x in deps}
    titulo = f"desplegar: {corto(sha)}" if sha else "desplegar"
    descripcion = (f"Commit esperado: {sha} (cabeza de {d['rama']} al lanzar)" if sha else "lanzado con desplegar.py")
    api.post(endpoint, {"applicationId": d["id"], "title": titulo, "description": descripcion})
    print(f"Lanzado {time.strftime('%H:%M:%S')}; esperando a Dokploy...")
    dep = esperar(api, d["id"], previos, args.timeout, args.intervalo)
    duracion = ""
    if dep.get("startedAt") and dep.get("finishedAt"):
        duracion = f" ({fecha(dep['startedAt'])} → {fecha(dep['finishedAt'])})"
    print(f"Despliegue {dep.get('deploymentId')}: {dep.get('status')}{duracion}")
    print(f"--- final del log ({args.lineas_log} líneas) ---")
    print(log_final(api, dep["deploymentId"], args.lineas_log, token))
    print("--- fin del log ---")
    if dep.get("status") != "done":
        if dep.get("errorMessage"):
            print(f"Error de Dokploy: {redactar(dep['errorMessage'], token)}")
        print(f"FALLÓ el despliegue de {nombre}.")
        return FALLO
    salud = verificar_salud(urls, args.espera_salud, args.intervalo)
    commit = comprobar_commit(d, sha, url_version, dep)
    if cabeza and not args.commit:
        despues = cabeza_rama(d["repo"], d["rama"])
        if despues and despues[0] != sha:
            print(f"Aviso: la rama avanzó durante el despliegue ({corto(sha)} → {corto(despues[0])}).")
    print(f"{'OK' if salud and commit else 'FALLO'}: {nombre} desplegado"
          + ("" if salud and commit else " pero la verificación no pasó") + ".")
    return OK if salud and commit else FALLO


# ---------------------------------------------------------------------------- CLI

def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="desplegar.py", description="Despliegues de Dokploy (MRH y AuditGlow).")
    p.add_argument("--api", default=os.environ.get("DOKPLOY_URL", API_POR_DEFECTO))
    p.add_argument("--token-file", default=os.environ.get("DOKPLOY_TOKEN_FILE", TOKEN_POR_DEFECTO))
    p.add_argument("--app-health", default=os.environ.get("APP_HEALTH_CONFIG", APP_HEALTH_POR_DEFECTO),
                   help="config.json de acris/app-health (URLs de salud)")
    p.add_argument("--config", default=os.path.join(DIR, "config.json"))
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("listar", help="proyectos, entornos y apps con su último despliegue")
    s.add_argument("--proyecto")
    for nombre, ayuda in (("estado", "¿ya se desplegó? cabeza de la rama contra lo desplegado, y salud"),
                          ("verificar", "salud pública y commit, sin desplegar"),
                          ("desplegar", "lanza un despliegue, espera, muestra el log y verifica")):
        s = sub.add_parser(nombre, help=ayuda)
        s.add_argument("app", help="proyecto/entorno/nombre (mrh/test/front, auditglow/prod/web) o applicationId")
        s.add_argument("--commit", help="commit esperado (por defecto, la cabeza de la rama en GitHub)")
        s.add_argument("--version-url", help="URL donde la app informa su commit, si lo expone")
        s.add_argument("--espera-salud", type=float, default=180, help="segundos de reintento de la salud")
        s.add_argument("--intervalo", type=float, default=10, help="segundos entre sondeos")
        if nombre == "desplegar":
            s.add_argument("--dry-run", action="store_true", help="muestra qué haría, sin desplegar")
            s.add_argument("--si-produccion", action="store_true",
                           help="solo tras la confirmación explícita del usuario")
            s.add_argument("--rebuild", action="store_true", help="application.redeploy en vez de deploy")
            s.add_argument("--timeout", type=float, default=1200, help="espera máxima del despliegue (s)")
            s.add_argument("--lineas-log", type=int, default=40)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    token = ""
    try:
        token = leer_token(args.token_file)
        api = Dokploy(args.api, token)
        config = leer_json(args.config) if os.path.exists(args.config) else {}
        try:
            app_health = leer_json(args.app_health)
        except (OSError, ValueError):
            print(f"aviso: no se pudo leer {args.app_health}; la salud usará la raíz de cada dominio", file=sys.stderr)
            app_health = {}
        if args.cmd == "listar":
            return cmd_listar(api, args)
        if args.cmd == "estado":
            return cmd_estado(api, args, app_health)
        if args.cmd == "verificar":
            return cmd_verificar(api, args, app_health, config)
        return cmd_desplegar(api, args, app_health, config, token)
    except Rechazo as e:
        print(f"RECHAZADO: {redactar(str(e), token)}", file=sys.stderr)
        return RECHAZO
    except Fallo as e:
        print(f"FALLO: {redactar(str(e), token)}", file=sys.stderr)
        return FALLO


if __name__ == "__main__":
    sys.exit(main())
