"""
Sentinel 2.0 - Système de Surveillance Intelligent

Fonctionnalités :
- Monitoring automatique de tous les services
- Détection et diagnostic des problèmes
- Tentatives de réparation automatique
- Alertes et recommandations si échec
- Historique des incidents
- Métriques en temps réel
"""

import os
import time
import sqlite3
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import threading
from collections import defaultdict

# Import E2E tester (optionnel - nécessite playwright)
try:
    from e2e_tester import E2ETester
    E2E_AVAILABLE = True
except ImportError:
    E2E_AVAILABLE = False
    print("[Sentinel] E2E testing not available (install: pip install playwright && playwright install)")

load_dotenv()

PORT = int(os.getenv("PORT", "5059"))
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:5055")
CURATOR_URL = os.getenv("CURATOR_URL", "http://localhost:5061")
NARRATOR_URL = os.getenv("NARRATOR_URL", "http://localhost:5056")
PUBLISHER_URL = os.getenv("PUBLISHER_URL", "http://localhost:5058")
MONETIZER_URL = os.getenv("MONETIZER_URL", "http://localhost:5060")
PUBLIC_URL = os.getenv("PUBLIC_URL", "http://localhost:5062")
WEB_URL = os.getenv("WEB_URL", "http://localhost:5000")

# Configuration alertes
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "")
ALERT_TELEGRAM = os.getenv("ALERT_TELEGRAM_CHAT_ID", "")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL_SEC", "30"))
ALERT_THRESHOLD = int(os.getenv("ALERT_THRESHOLD_SEC", "120"))

DB_PATH = os.getenv("DB_PATH", "./sentinel.db")
os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else ".", exist_ok=True)

app = FastAPI(title="Sentinel 2.0", version="2.0")
templates = Jinja2Templates(directory="templates")

# Services à surveiller
SERVICES = {
    "gateway": {"url": GATEWAY_URL, "critical": True, "endpoints": ["/", "/jobs"]},
    "curator": {"url": CURATOR_URL, "critical": True, "endpoints": ["/", "/videos"]},
    "narrator": {"url": NARRATOR_URL, "critical": True, "endpoints": ["/"]},
    "publisher": {"url": PUBLISHER_URL, "critical": False, "endpoints": ["/"]},
    "monetizer": {"url": MONETIZER_URL, "critical": True, "endpoints": ["/", "/tokens"]},
    "public": {"url": PUBLIC_URL, "critical": True, "endpoints": ["/", "/watch/121"]},
    "web": {"url": WEB_URL, "critical": True, "endpoints": ["/"]}
}

# État du système
system_status = {
    "services": {},
    "alerts": [],
    "metrics": {
        "uptime_start": datetime.now().isoformat(),
        "total_checks": 0,
        "total_incidents": 0,
        "auto_fixes": 0
    }
}

# ============ Base de données ============

def init_db():
    """Initialise la base de données Sentinel"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table des checks de santé
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT NOT NULL,
            status TEXT NOT NULL,
            response_time_ms INTEGER,
            checked_at TEXT NOT NULL,
            error_message TEXT
        )
    """)
    
    # Table des incidents
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT NOT NULL,
            severity TEXT NOT NULL,
            issue TEXT NOT NULL,
            detected_at TEXT NOT NULL,
            resolved_at TEXT,
            auto_fixed BOOLEAN DEFAULT 0,
            resolution TEXT,
            recommendation TEXT
        )
    """)
    
    # Table des alertes envoyées
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id INTEGER,
            channel TEXT NOT NULL,
            sent_at TEXT NOT NULL,
            message TEXT,
            FOREIGN KEY (incident_id) REFERENCES incidents(id)
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"[Sentinel] Database initialized: {DB_PATH}")

def log_health_check(service: str, status: str, response_time: Optional[int], error: Optional[str] = None):
    """Enregistre un check de santé"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO health_checks (service, status, response_time_ms, checked_at, error_message)
        VALUES (?, ?, ?, ?, ?)
    """, (service, status, response_time, datetime.now().isoformat(), error))
    conn.commit()
    conn.close()

def log_incident(service: str, severity: str, issue: str, recommendation: str) -> int:
    """Enregistre un incident et retourne son ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO incidents (service, severity, issue, detected_at, recommendation)
        VALUES (?, ?, ?, ?, ?)
    """, (service, severity, issue, datetime.now().isoformat(), recommendation))
    incident_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return incident_id

def resolve_incident(incident_id: int, auto_fixed: bool, resolution: str):
    """Marque un incident comme résolu"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE incidents
        SET resolved_at = ?, auto_fixed = ?, resolution = ?
        WHERE id = ?
    """, (datetime.now().isoformat(), auto_fixed, resolution, incident_id))
    conn.commit()
    conn.close()

def get_open_incidents() -> List[Dict]:
    """Récupère les incidents non résolus"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT * FROM incidents
        WHERE resolved_at IS NULL
        ORDER BY detected_at DESC
    """).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_service_uptime(service: str, hours: int = 24) -> float:
    """Calcule l'uptime d'un service sur X heures"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    since = (datetime.now() - timedelta(hours=hours)).isoformat()
    
    total = cursor.execute("""
        SELECT COUNT(*) FROM health_checks
        WHERE service = ? AND checked_at > ?
    """, (service, since)).fetchone()[0]
    
    if total == 0:
        return 100.0
    
    success = cursor.execute("""
        SELECT COUNT(*) FROM health_checks
        WHERE service = ? AND checked_at > ? AND status = 'healthy'
    """, (service, since)).fetchone()[0]
    
    conn.close()
    return (success / total) * 100

# ============ Monitoring & Auto-Repair ============

def check_service_health(service_name: str, config: Dict) -> Dict[str, Any]:
    """Vérifie la santé d'un service"""
    url = config["url"]
    endpoints = config.get("endpoints", ["/"])
    
    results = {
        "service": service_name,
        "status": "healthy",
        "response_times": [],
        "errors": [],
        "tested_endpoints": len(endpoints)
    }
    
    for endpoint in endpoints:
        try:
            start = time.time()
            response = requests.get(f"{url}{endpoint}", timeout=5)
            elapsed_ms = int((time.time() - start) * 1000)
            
            results["response_times"].append(elapsed_ms)
            
            if response.status_code >= 500:
                results["status"] = "degraded"
                results["errors"].append(f"{endpoint}: HTTP {response.status_code}")
            elif response.status_code >= 400:
                results["status"] = "warning"
                results["errors"].append(f"{endpoint}: HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            results["status"] = "down"
            results["errors"].append(f"{endpoint}: Timeout (>5s)")
        except requests.exceptions.ConnectionError:
            results["status"] = "down"
            results["errors"].append(f"{endpoint}: Connection refused")
        except Exception as e:
            results["status"] = "down"
            results["errors"].append(f"{endpoint}: {str(e)}")
    
    # Calcule temps de réponse moyen
    if results["response_times"]:
        results["avg_response_time"] = sum(results["response_times"]) // len(results["response_times"])
    else:
        results["avg_response_time"] = None
    
    return results

def diagnose_issue(service_name: str, health_result: Dict) -> Dict[str, str]:
    """Diagnostic intelligent du problème"""
    diagnosis = {
        "issue": "",
        "cause": "",
        "severity": "low",
        "recommendation": ""
    }
    
    status = health_result["status"]
    errors = health_result["errors"]
    
    if status == "down":
        diagnosis["issue"] = f"Service {service_name} inaccessible"
        diagnosis["severity"] = "critical" if SERVICES[service_name].get("critical") else "high"
        
        if "Connection refused" in str(errors):
            diagnosis["cause"] = "Le service ne répond pas (crash ou non démarré)"
            diagnosis["recommendation"] = (
                f"🔧 Action requise:\n"
                f"1. Va sur Render Dashboard → {service_name}\n"
                f"2. Vérifie les logs pour voir l'erreur\n"
                f"3. Clique 'Manual Deploy' → 'Deploy latest commit'\n"
                f"4. Si erreur persiste: vérifie les variables d'environnement"
            )
        elif "Timeout" in str(errors):
            diagnosis["cause"] = "Le service est trop lent ou surchargé"
            diagnosis["recommendation"] = (
                f"⚡ Action requise:\n"
                f"1. Vérifie les logs de {service_name} sur Render\n"
                f"2. Cherche des boucles infinies ou requêtes lentes\n"
                f"3. Considère upgrade plan (plus de RAM/CPU)"
            )
        else:
            diagnosis["cause"] = f"Erreur réseau: {errors[0] if errors else 'Inconnue'}"
            diagnosis["recommendation"] = (
                f"🌐 Action requise:\n"
                f"1. Vérifie que l'URL est correcte: {SERVICES[service_name]['url']}\n"
                f"2. Vérifie les variables d'environnement sur Render\n"
                f"3. Teste manuellement: curl {SERVICES[service_name]['url']}"
            )
    
    elif status == "degraded":
        diagnosis["issue"] = f"Service {service_name} en erreur"
        diagnosis["severity"] = "high"
        diagnosis["cause"] = f"Erreurs HTTP 500: {', '.join(errors)}"
        diagnosis["recommendation"] = (
            f"🐛 Action requise:\n"
            f"1. Va sur Render → {service_name} → Logs\n"
            f"2. Cherche les Traceback Python (erreurs en rouge)\n"
            f"3. Corrige le bug dans le code\n"
            f"4. git add/commit/push pour auto-deploy"
        )
    
    elif status == "warning":
        diagnosis["issue"] = f"Service {service_name} avec avertissements"
        diagnosis["severity"] = "medium"
        diagnosis["cause"] = f"Erreurs HTTP 4xx: {', '.join(errors)}"
        diagnosis["recommendation"] = (
            f"⚠️ À vérifier:\n"
            f"1. Endpoints retournent 404 ou 405\n"
            f"2. Vérifie que les routes existent dans le code\n"
            f"3. Non critique si c'est juste /health ou /favicon.ico"
        )
    
    return diagnosis

def attempt_auto_repair(service_name: str, diagnosis: Dict) -> bool:
    """Tente de réparer automatiquement (limité sur Render Free)"""
    # Sur Render, on ne peut pas restart automatiquement via API
    # Mais on peut tenter des workarounds
    
    severity = diagnosis["severity"]
    
    # Tentative de wake-up pour cold start
    if "Timeout" in diagnosis["cause"] or "Connection refused" in diagnosis["cause"]:
        print(f"[Sentinel] Tentative wake-up de {service_name}...")
        try:
            # Ping simple pour réveiller le service
            requests.get(f"{SERVICES[service_name]['url']}/", timeout=30)
            time.sleep(3)
            # Re-check
            result = check_service_health(service_name, SERVICES[service_name])
            if result["status"] == "healthy":
                print(f"[Sentinel] ✅ {service_name} réveillé avec succès!")
                return True
        except:
            pass
    
    return False

def check_video_security() -> Dict[str, Any]:
    """Vérifie que les vidéos sont sécurisées avec Token Auth"""
    print("[Sentinel] 🔒 Vérification sécurité vidéo...")
    
    results = {
        "secure": True,
        "checks": [],
        "vulnerabilities": []
    }
    
    try:
        # Test 1: Vérifier que Token Auth est actif (token + expires dans URL)
        print("  → Test 1: Token Auth actif?")
        response = requests.get(f"{PUBLIC_URL}/watch/121", allow_redirects=False, timeout=10)
        
        if response.status_code in [301, 302, 303, 307, 308]:
            # Redirige vers login = bon signe!
            results["checks"].append({
                "name": "Page redirect sans auth",
                "status": "PASS",
                "message": "Page /watch redirige vers login (sécurisé)"
            })
            print("  ✅ Page redirige vers login")
        elif response.status_code == 200:
            # Vérifie si iframe visible avec token
            html = response.text
            
            # Cherche l'iframe Bunny
            import re
            iframe_match = re.search(r'src="([^"]*iframe\.mediadelivery\.net[^"]*)"', html)
            
            if iframe_match:
                iframe_url = iframe_match.group(1)
                # Decode HTML entities
                iframe_url = iframe_url.replace("&amp;", "&")
                
                if "token=" in iframe_url and "expires=" in iframe_url:
                    results["checks"].append({
                        "name": "Token Auth présent",
                        "status": "PASS",
                        "message": "URL vidéo contient token et expiration"
                    })
                    print("  ✅ Token Auth actif dans iframe URL")
                else:
                    # CRITIQUE: iframe sans token!
                    results["secure"] = False
                    results["vulnerabilities"].append({
                        "severity": "CRITICAL",
                        "issue": "Iframe vidéo sans Token Auth",
                        "impact": "Vidéos copiables et embeddables n'importe où",
                        "fix": "Ajouter BUNNY_SECURITY_KEY=453f0507-2f2c-4155-95bd-31a2fdd3610c dans Render env vars"
                    })
                    results["checks"].append({
                        "name": "Token Auth présent",
                        "status": "FAIL",
                        "message": f"iframe visible SANS token - VULNÉRABILITÉ!\nURL: {iframe_url[:100]}"
                    })
                    print("  ❌ CRITIQUE: iframe sans token détecté!")
            else:
                results["checks"].append({
                    "name": "Token Auth présent",
                    "status": "WARNING",
                    "message": "Impossible de vérifier (pas d'iframe trouvé)"
                })
                print("  ⚠️  Pas d'iframe trouvé dans HTML")
        
        # Test 2: Vérifier que HLS URLs sont bloquées (403)
        print("  → Test 2: HLS URLs bloquées?")
        test_hls = "https://vz-a3ab0733-842.b-cdn.net/85e41419-5b46-4db9-ba15-32c86aa08032/playlist.m3u8"
        hls_response = requests.get(test_hls, timeout=5)
        
        if hls_response.status_code == 403:
            results["checks"].append({
                "name": "HLS direct access blocked",
                "status": "PASS",
                "message": "URLs HLS bloquées (403 Forbidden)"
            })
            print("  ✅ HLS URLs bloquées")
        else:
            results["secure"] = False
            results["vulnerabilities"].append({
                "severity": "CRITICAL",
                "issue": "URLs HLS accessibles directement",
                "impact": "Vidéos téléchargeables en masse",
                "fix": "Activer 'CDN Token Auth' dans Bunny Dashboard"
            })
            results["checks"].append({
                "name": "HLS direct access blocked",
                "status": "FAIL",
                "message": f"HLS accessible! Status: {hls_response.status_code}"
            })
            print(f"  ❌ HLS accessible (status {hls_response.status_code})")
        
        # Test 3: Vérifier que API ne leak pas metadata VIP
        print("  → Test 3: API metadata sécurisée?")
        api_response = requests.get(f"{PUBLIC_URL}/api/videos", timeout=5)
        if api_response.status_code == 200:
            videos = api_response.json()
            vip_videos = [v for v in videos if v.get("access_level") == "vip"]
            
            if vip_videos:
                results["vulnerabilities"].append({
                    "severity": "MEDIUM",
                    "issue": f"{len(vip_videos)} vidéos VIP dans API publique",
                    "impact": "Metadata exposée (titres, thumbnails)",
                    "fix": "Filtrer access_level='vip' dans /api/videos"
                })
                results["checks"].append({
                    "name": "API metadata protection",
                    "status": "FAIL",
                    "message": f"{len(vip_videos)} vidéos VIP exposées"
                })
                print(f"  ⚠️  {len(vip_videos)} vidéos VIP dans API publique")
            else:
                results["checks"].append({
                    "name": "API metadata protection",
                    "status": "PASS",
                    "message": "Seulement vidéos publiques dans API"
                })
                print("  ✅ API ne contient que vidéos publiques")
        
    except Exception as e:
        results["checks"].append({
            "name": "Security audit",
            "status": "ERROR",
            "message": f"Erreur audit: {str(e)}"
        })
        print(f"  ❌ Erreur audit: {e}")
    
    # Score de sécurité
    passed = sum(1 for c in results["checks"] if c["status"] == "PASS")
    total = len(results["checks"])
    results["security_score"] = (passed / total * 100) if total > 0 else 0
    
    print(f"  📊 Score sécurité: {results['security_score']:.0f}% ({passed}/{total})")
    
    return results

def monitoring_loop():
    """Boucle de monitoring principale"""
    print(f"[Sentinel] Monitoring démarré (interval: {CHECK_INTERVAL}s)")
    
    consecutive_failures = defaultdict(int)
    security_check_counter = 0
    SECURITY_CHECK_EVERY = 10  # Check sécurité tous les 10 cycles (5 minutes si interval=30s)
    
    while True:
        try:
            # Check sécurité périodique
            security_check_counter += 1
            if security_check_counter >= SECURITY_CHECK_EVERY:
                security_check_counter = 0
                security_results = check_video_security()
                system_status["security"] = security_results
                
                # Créer incident si vulnérabilité critique
                if not security_results["secure"]:
                    critical_vulns = [v for v in security_results["vulnerabilities"] if v["severity"] == "CRITICAL"]
                    if critical_vulns:
                        for vuln in critical_vulns:
                            # Vérifier si incident déjà ouvert
                            open_incidents = get_open_incidents()
                            existing = any(i["issue"] == vuln["issue"] and not i["resolved_at"] for i in open_incidents)
                            
                            if not existing:
                                incident_id = log_incident(
                                    "security",
                                    vuln["severity"],
                                    vuln["issue"],
                                    vuln["fix"]
                                )
                                print(f"[Sentinel] 🚨 SÉCURITÉ: {vuln['issue']}")
                                
                                # Ajouter à alertes
                                system_status["alerts"].append({
                                    "id": incident_id,
                                    "service": "security",
                                    "severity": vuln["severity"],
                                    "issue": vuln["issue"],
                                    "recommendation": vuln["fix"],
                                    "timestamp": datetime.now().isoformat()
                                })
            
            for service_name, config in SERVICES.items():
                # Check santé
                health_result = check_service_health(service_name, config)
                status = health_result["status"]
                avg_time = health_result["avg_response_time"]
                
                # Log dans DB
                log_health_check(
                    service_name,
                    status,
                    avg_time,
                    "; ".join(health_result["errors"]) if health_result["errors"] else None
                )
                
                # Update system status
                system_status["services"][service_name] = {
                    "status": status,
                    "last_check": datetime.now().isoformat(),
                    "response_time_ms": avg_time,
                    "uptime_24h": get_service_uptime(service_name, 24)
                }
                system_status["metrics"]["total_checks"] += 1
                
                # Si problème détecté
                if status in ["down", "degraded"]:
                    consecutive_failures[service_name] += 1
                    
                    # Après X échecs consécutifs, créer incident
                    if consecutive_failures[service_name] >= 2:
                        diagnosis = diagnose_issue(service_name, health_result)
                        
                        # Vérifier si incident déjà ouvert
                        open_incidents = get_open_incidents()
                        existing = any(i["service"] == service_name and not i["resolved_at"] for i in open_incidents)
                        
                        if not existing:
                            # Créer nouvel incident
                            incident_id = log_incident(
                                service_name,
                                diagnosis["severity"],
                                diagnosis["issue"],
                                diagnosis["recommendation"]
                            )
                            
                            system_status["metrics"]["total_incidents"] += 1
                            
                            # Ajouter à la liste d'alertes
                            alert = {
                                "id": incident_id,
                                "service": service_name,
                                "severity": diagnosis["severity"],
                                "issue": diagnosis["issue"],
                                "recommendation": diagnosis["recommendation"],
                                "timestamp": datetime.now().isoformat()
                            }
                            system_status["alerts"].append(alert)
                            
                            # Tentative auto-repair
                            if attempt_auto_repair(service_name, diagnosis):
                                resolve_incident(incident_id, True, "Auto-réparé par wake-up")
                                system_status["metrics"]["auto_fixes"] += 1
                                # Retirer de la liste d'alertes
                                system_status["alerts"] = [a for a in system_status["alerts"] if a["id"] != incident_id]
                            
                            print(f"[Sentinel] 🚨 Incident créé: {diagnosis['issue']}")
                else:
                    # Service OK, reset compteur
                    if consecutive_failures[service_name] > 0:
                        # Résoudre incidents ouverts pour ce service
                        open_incidents = get_open_incidents()
                        for incident in open_incidents:
                            if incident["service"] == service_name:
                                resolve_incident(incident["id"], False, "Service restored")
                                # Retirer de la liste d'alertes
                                system_status["alerts"] = [a for a in system_status["alerts"] if a["id"] != incident["id"]]
                        
                    consecutive_failures[service_name] = 0
            
            time.sleep(CHECK_INTERVAL)
            
        except Exception as e:
            print(f"[Sentinel] Erreur monitoring loop: {e}")
            time.sleep(CHECK_INTERVAL)

# ============ API Endpoints ============

@app.on_event("startup")
def startup():
    init_db()
    # Démarrer monitoring en background
    threading.Thread(target=monitoring_loop, daemon=True).start()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard page with real-time monitoring"""
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    return templates.TemplateResponse(
        "sentinel2.html",
        {
            "request": request,
            "check_interval": CHECK_INTERVAL
        }
    )

@app.get("/api/status")
def get_system_status():
    """Retourne l'état complet du système"""
    return JSONResponse(system_status)

@app.get("/api/e2e/test")
def run_e2e_tests():
    """Lance les tests E2E sur Public Interface"""
    if not E2E_AVAILABLE:
        return JSONResponse({
            "error": "E2E testing not available",
            "install": "pip install playwright && playwright install chromium"
        }, status_code=503)
    
    try:
        tester = E2ETester(
            public_url=PUBLIC_URL,
            curator_url=CURATOR_URL
        )
        results = tester.run_all_tests()
        
        # Convertit en dict sérialisable
        results_dict = {
            name: {
                "test_name": r.test_name,
                "passed": r.passed,
                "error_message": r.error_message,
                "screenshot_path": r.screenshot_path,
                "duration_ms": r.duration_ms,
                "timestamp": r.timestamp
            }
            for name, r in results.items()
        }
        
        passed_count = sum(1 for r in results.values() if r.passed)
        total_count = len(results)
        
        return JSONResponse({
            "summary": {
                "passed": passed_count,
                "failed": total_count - passed_count,
                "total": total_count,
                "success_rate": (passed_count / total_count * 100) if total_count > 0 else 0
            },
            "results": results_dict
        })
        
    except Exception as e:
        return JSONResponse({
            "error": str(e)
        }, status_code=500)

@app.get("/api/incidents")
def get_incidents(open_only: bool = True):
    """Liste des incidents"""
    if open_only:
        incidents = get_open_incidents()
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        rows = cursor.execute("""
            SELECT * FROM incidents
            ORDER BY detected_at DESC
            LIMIT 100
        """).fetchall()
        conn.close()
        incidents = [dict(row) for row in rows]
    
    return JSONResponse({"incidents": incidents})

@app.get("/api/metrics")
def get_metrics():
    """Métriques détaillées"""
    metrics = {}
    
    for service_name in SERVICES.keys():
        metrics[service_name] = {
            "uptime_1h": get_service_uptime(service_name, 1),
            "uptime_24h": get_service_uptime(service_name, 24),
            "uptime_7d": get_service_uptime(service_name, 24 * 7)
        }
    
    return JSONResponse(metrics)

@app.get("/api/security/check")
def run_security_check():
    """Lance un check de sécurité vidéo manuel"""
    results = check_video_security()
    return JSONResponse(results)

@app.get("/api/security/status")
def get_security_status():
    """Retourne le dernier état de sécurité"""
    security = system_status.get("security", {"message": "Aucun check effectué encore"})
    return JSONResponse(security)

@app.get("/health")
def health():
    return {"status": "healthy", "service": "sentinel"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
