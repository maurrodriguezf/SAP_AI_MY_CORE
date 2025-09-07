import requests
from requests.auth import HTTPBasicAuth
import json

# ======== CONFIG ========
BASE_URL   = "https://<tu-host>/sap/opu/odata/sap/API_MAINTNOTIFICATION_SRV"
SAP_CLIENT = "100"  # o None si no aplica
USER       = "<usuario>"
PASSWORD   = "<password>"

# Si usas OAuth2, reemplaza auth por headers Authorization: Bearer <token>
auth = HTTPBasicAuth(USER, PASSWORD)

# ======== HELPERS ODATA V2 ========
def _with_client(url: str) -> str:
    if SAP_CLIENT:
        sep = "&" if "?" in url else "?"
        return f"{url}{sep}sap-client={SAP_CLIENT}"
    return url

def fetch_csrf(session: requests.Session) -> str:
    """
    Hace un GET para obtener X-CSRF-Token y setear cookies de sesión.
    """
    url = _with_client(f"{BASE_URL}/$metadata")
    headers = {"Accept": "application/json", "X-CSRF-Token": "Fetch"}
    r = session.get(url, headers=headers, auth=auth)
    r.raise_for_status()
    token = r.headers.get("X-CSRF-Token")
    if not token:
        raise RuntimeError("No se recibió X-CSRF-Token. Revisa autenticación/CSRF en el gateway.")
    return token

def odata_post(session: requests.Session, entity_set: str, payload: dict) -> dict:
    """
    Crea entidad en el entity set indicado (por ej. 'A_MaintenanceNotification').
    """
    token = fetch_csrf(session)
    url = _with_client(f"{BASE_URL}/{entity_set}")
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-CSRF-Token": token
    }
    r = session.post(url, headers=headers, auth=auth, data=json.dumps(payload))
    if r.status_code >= 400:
        raise RuntimeError(f"Error POST {r.status_code}: {r.text}")
    return r.json().get("d", r.json())  # OData V2 envuelve en 'd'

def odata_get(session: requests.Session, entity_path: str, select: str = None, expand: str = None) -> dict:
    """
    Lee una entidad. entity_path puede ser, por ejemplo:
    "A_MaintenanceNotification('000012345678')"
    """
    url = f"{BASE_URL}/{entity_path}"
    params = {}
    if select: params["$se]()
