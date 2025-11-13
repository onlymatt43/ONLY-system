"""
Sentinel AI - Intelligence Layer for ONLY System
Tier 2: Metrics + Alerts + Chat
Architecture ready for Tier 3-4: Predictions + Auto-healing + Render API
"""

import os
import time
import sqlite3
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import requests


# ==================== DATA MODELS ====================

@dataclass
class ServiceMetric:
    """Single metric point for a service"""
    service: str
    timestamp: float
    status_code: int
    latency_ms: float
    is_healthy: bool
    error_message: Optional[str] = None


@dataclass
class SystemHealth:
    """Overall system health snapshot"""
    timestamp: float
    health_score: int  # 0-100
    services_up: int
    services_down: int
    total_requests: int
    avg_latency_ms: float
    error_rate: float
    alerts: List[str]


@dataclass
class Alert:
    """System alert/notification"""
    level: str  # INFO, WARNING, CRITICAL
    service: str
    message: str
    timestamp: float
    resolved: bool = False


# ==================== METRICS COLLECTOR ====================

class MetricsCollector:
    """Collect and store metrics with 30-day history"""
    
    def __init__(self, db_path: str = "./sentinel_metrics.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize metrics database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    status_code INTEGER NOT NULL,
                    latency_ms REAL NOT NULL,
                    is_healthy BOOLEAN NOT NULL,
                    error_message TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_service_time 
                ON metrics(service, timestamp DESC)
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    service TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    resolved BOOLEAN DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_resolved 
                ON alerts(resolved, timestamp DESC)
            """)
    
    def record_metric(self, metric: ServiceMetric):
        """Store a service metric"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO metrics 
                (service, timestamp, status_code, latency_ms, is_healthy, error_message, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                metric.service,
                metric.timestamp,
                metric.status_code,
                metric.latency_ms,
                metric.is_healthy,
                metric.error_message,
                datetime.utcnow().isoformat()
            ))
    
    def get_metrics(self, service: str, hours: int = 24) -> List[ServiceMetric]:
        """Get metrics for service in last N hours"""
        since = time.time() - (hours * 3600)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM metrics 
                WHERE service = ? AND timestamp > ?
                ORDER BY timestamp DESC
            """, (service, since)).fetchall()
            
            return [
                ServiceMetric(
                    service=r['service'],
                    timestamp=r['timestamp'],
                    status_code=r['status_code'],
                    latency_ms=r['latency_ms'],
                    is_healthy=bool(r['is_healthy']),
                    error_message=r['error_message']
                )
                for r in rows
            ]
    
    def get_stats(self, service: str, hours: int = 1) -> Dict[str, Any]:
        """Calculate statistics for service"""
        metrics = self.get_metrics(service, hours)
        
        if not metrics:
            return {
                "service": service,
                "period_hours": hours,
                "count": 0,
                "uptime": 0.0,
                "avg_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "p99_latency_ms": 0.0,
                "error_rate": 0.0
            }
        
        latencies = [m.latency_ms for m in metrics]
        healthy_count = sum(1 for m in metrics if m.is_healthy)
        
        latencies_sorted = sorted(latencies)
        p95_idx = int(len(latencies_sorted) * 0.95)
        p99_idx = int(len(latencies_sorted) * 0.99)
        
        return {
            "service": service,
            "period_hours": hours,
            "count": len(metrics),
            "uptime": (healthy_count / len(metrics)) * 100,
            "avg_latency_ms": statistics.mean(latencies),
            "p95_latency_ms": latencies_sorted[p95_idx] if p95_idx < len(latencies_sorted) else 0,
            "p99_latency_ms": latencies_sorted[p99_idx] if p99_idx < len(latencies_sorted) else 0,
            "error_rate": ((len(metrics) - healthy_count) / len(metrics)) * 100
        }
    
    def cleanup_old_metrics(self, days: int = 30):
        """Delete metrics older than N days"""
        cutoff = time.time() - (days * 86400)
        with sqlite3.connect(self.db_path) as conn:
            deleted = conn.execute(
                "DELETE FROM metrics WHERE timestamp < ?",
                (cutoff,)
            ).rowcount
            print(f"[MetricsCollector] Cleaned up {deleted} old metrics")
    
    def record_alert(self, alert: Alert):
        """Store an alert"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO alerts 
                (level, service, message, timestamp, resolved, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                alert.level,
                alert.service,
                alert.message,
                alert.timestamp,
                alert.resolved,
                datetime.utcnow().isoformat()
            ))
    
    def get_unresolved_alerts(self) -> List[Alert]:
        """Get all unresolved alerts"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM alerts 
                WHERE resolved = 0
                ORDER BY timestamp DESC
            """).fetchall()
            
            return [
                Alert(
                    level=r['level'],
                    service=r['service'],
                    message=r['message'],
                    timestamp=r['timestamp'],
                    resolved=bool(r['resolved'])
                )
                for r in rows
            ]


# ==================== HEALTH CHECKER ====================

class HealthChecker:
    """Intelligent health monitoring with anomaly detection"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.thresholds = {
            "latency_warning_ms": 2000,
            "latency_critical_ms": 5000,
            "error_rate_warning": 10,  # %
            "error_rate_critical": 25,  # %
            "uptime_warning": 95,  # %
            "uptime_critical": 80  # %
        }
    
    def check_service(self, name: str, url: str) -> ServiceMetric:
        """Check single service and return metric"""
        start = time.time()
        
        try:
            r = requests.get(url, timeout=5)
            latency_ms = (time.time() - start) * 1000
            
            metric = ServiceMetric(
                service=name,
                timestamp=time.time(),
                status_code=r.status_code,
                latency_ms=latency_ms,
                is_healthy=(200 <= r.status_code < 300)
            )
            
        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            metric = ServiceMetric(
                service=name,
                timestamp=time.time(),
                status_code=0,
                latency_ms=latency_ms,
                is_healthy=False,
                error_message=str(e)
            )
        
        # Record metric
        self.metrics.record_metric(metric)
        
        # Check for alerts
        self._check_alerts(name, metric)
        
        return metric
    
    def _check_alerts(self, service: str, metric: ServiceMetric):
        """Detect anomalies and create alerts"""
        
        # Service down
        if not metric.is_healthy:
            if metric.status_code in [502, 503, 504]:
                alert = Alert(
                    level="WARNING",
                    service=service,
                    message=f"Service returning {metric.status_code} (likely sleeping on Render Free tier)",
                    timestamp=time.time()
                )
            elif metric.status_code == 0:
                alert = Alert(
                    level="CRITICAL",
                    service=service,
                    message=f"Service unreachable: {metric.error_message}",
                    timestamp=time.time()
                )
            else:
                alert = Alert(
                    level="WARNING",
                    service=service,
                    message=f"Service unhealthy: HTTP {metric.status_code}",
                    timestamp=time.time()
                )
            
            self.metrics.record_alert(alert)
            print(f"[Alert {alert.level}] {alert.service}: {alert.message}")
        
        # High latency
        elif metric.latency_ms > self.thresholds["latency_critical_ms"]:
            alert = Alert(
                level="CRITICAL",
                service=service,
                message=f"Latency critical: {metric.latency_ms:.0f}ms (threshold: {self.thresholds['latency_critical_ms']}ms)",
                timestamp=time.time()
            )
            self.metrics.record_alert(alert)
            print(f"[Alert {alert.level}] {alert.service}: {alert.message}")
        
        elif metric.latency_ms > self.thresholds["latency_warning_ms"]:
            alert = Alert(
                level="WARNING",
                service=service,
                message=f"Latency high: {metric.latency_ms:.0f}ms",
                timestamp=time.time()
            )
            self.metrics.record_alert(alert)
            print(f"[Alert {alert.level}] {alert.service}: {alert.message}")
    
    def calculate_health_score(self, services: List[str]) -> int:
        """Calculate overall system health score (0-100)"""
        scores = []
        
        for service in services:
            stats = self.metrics.get_stats(service, hours=1)
            
            if stats["count"] == 0:
                scores.append(0)
                continue
            
            # Uptime weight: 50%
            uptime_score = stats["uptime"]
            
            # Latency weight: 30%
            avg_latency = stats["avg_latency_ms"]
            if avg_latency < 500:
                latency_score = 100
            elif avg_latency < 1000:
                latency_score = 80
            elif avg_latency < 2000:
                latency_score = 60
            else:
                latency_score = 40
            
            # Error rate weight: 20%
            error_rate = stats["error_rate"]
            if error_rate < 1:
                error_score = 100
            elif error_rate < 5:
                error_score = 80
            elif error_rate < 10:
                error_score = 60
            else:
                error_score = 40
            
            service_score = (uptime_score * 0.5) + (latency_score * 0.3) + (error_score * 0.2)
            scores.append(service_score)
        
        return int(statistics.mean(scores)) if scores else 0


# ==================== AUTO HEALER ====================

class AutoHealer:
    """Automatic problem resolution (Tier 2: wake-up, Tier 3+: Render API)"""
    
    def __init__(self, health_checker: HealthChecker):
        self.health = health_checker
        self.retry_attempts = defaultdict(int)
        self.max_retries = 3
    
    def attempt_wake_up(self, service: str, url: str) -> bool:
        """Try to wake up sleeping service (Render Free tier)"""
        print(f"[AutoHealer] Attempting to wake up {service}...")
        
        for attempt in range(self.max_retries):
            time.sleep(2)  # Wait between attempts
            
            try:
                r = requests.get(url, timeout=10)
                if 200 <= r.status_code < 300:
                    print(f"[AutoHealer] ✅ {service} is awake!")
                    self.retry_attempts[service] = 0
                    return True
            except:
                pass
        
        self.retry_attempts[service] += 1
        print(f"[AutoHealer] ❌ Failed to wake {service} (attempt {self.retry_attempts[service]})")
        
        if self.retry_attempts[service] >= self.max_retries:
            print(f"[AutoHealer] 🚨 {service} requires manual intervention!")
        
        return False
    
    def heal_service(self, service: str, url: str, metric: ServiceMetric):
        """Attempt to heal unhealthy service"""
        
        # Service down - try wake-up
        if not metric.is_healthy and metric.status_code in [502, 503, 504, 0]:
            self.attempt_wake_up(service, url)
        
        # TODO Tier 3: Render API restart
        # TODO Tier 4: Predictive scaling, rollback deploys


# ==================== CHAT INTERFACE ====================

class ChatInterface:
    """Natural language interface with Sentinel AI"""
    
    def __init__(self, health_checker: HealthChecker, metrics_collector: MetricsCollector, auto_healer: AutoHealer):
        self.health = health_checker
        self.metrics = metrics_collector
        self.healer = auto_healer
        
        # Command patterns (simple NLP for Tier 2)
        self.commands = {
            "status": ["status", "état", "health", "santé"],
            "metrics": ["metrics", "métriques", "stats", "statistiques"],
            "alerts": ["alerts", "alertes", "problems", "problèmes"],
            "restart": ["restart", "redémarrer", "wake", "réveiller"],
            "help": ["help", "aide", "?", "commandes"]
        }
    
    def parse_intent(self, message: str) -> tuple[str, Optional[str]]:
        """Parse user intent from message"""
        msg_lower = message.lower()
        
        # Detect service name
        service_names = ["gateway", "narrator", "builder", "publisher", "curator", "monetizer", "public"]
        detected_service = None
        for svc in service_names:
            if svc in msg_lower:
                detected_service = svc
                break
        
        # Detect command
        for cmd, patterns in self.commands.items():
            if any(p in msg_lower for p in patterns):
                return cmd, detected_service
        
        return "unknown", detected_service
    
    def handle_message(self, message: str, services_config: Dict[str, str]) -> Dict[str, Any]:
        """Process chat message and return response"""
        
        intent, service = self.parse_intent(message)
        
        if intent == "status":
            if service:
                stats = self.metrics.get_stats(service.capitalize(), hours=1)
                return {
                    "intent": "status",
                    "service": service,
                    "response": f"**{service.capitalize()} Status**\n"
                               f"Uptime: {stats['uptime']:.1f}%\n"
                               f"Avg Latency: {stats['avg_latency_ms']:.0f}ms\n"
                               f"Error Rate: {stats['error_rate']:.1f}%\n"
                               f"Checks: {stats['count']} in last hour",
                    "data": stats
                }
            else:
                # Overall system status
                services = list(services_config.keys())
                health_score = self.health.calculate_health_score(services)
                alerts = self.metrics.get_unresolved_alerts()
                
                return {
                    "intent": "status",
                    "service": "system",
                    "response": f"**System Health: {health_score}/100**\n"
                               f"Services: {len(services)}\n"
                               f"Active Alerts: {len(alerts)}",
                    "data": {
                        "health_score": health_score,
                        "services_count": len(services),
                        "alerts_count": len(alerts)
                    }
                }
        
        elif intent == "metrics":
            if service and service.capitalize() in services_config:
                stats_1h = self.metrics.get_stats(service.capitalize(), hours=1)
                stats_24h = self.metrics.get_stats(service.capitalize(), hours=24)
                
                return {
                    "intent": "metrics",
                    "service": service,
                    "response": f"**{service.capitalize()} Metrics**\n\n"
                               f"**Last Hour:**\n"
                               f"P95 Latency: {stats_1h['p95_latency_ms']:.0f}ms\n"
                               f"P99 Latency: {stats_1h['p99_latency_ms']:.0f}ms\n\n"
                               f"**Last 24 Hours:**\n"
                               f"Uptime: {stats_24h['uptime']:.1f}%\n"
                               f"Avg Latency: {stats_24h['avg_latency_ms']:.0f}ms\n"
                               f"Total Checks: {stats_24h['count']}",
                    "data": {
                        "1h": stats_1h,
                        "24h": stats_24h
                    }
                }
            else:
                return {
                    "intent": "metrics",
                    "response": "Please specify a service: gateway, narrator, builder, publisher, curator, monetizer, public"
                }
        
        elif intent == "alerts":
            alerts = self.metrics.get_unresolved_alerts()
            
            if not alerts:
                return {
                    "intent": "alerts",
                    "response": "✅ No active alerts - system is healthy!"
                }
            
            response = f"**{len(alerts)} Active Alerts:**\n\n"
            for alert in alerts[:10]:  # Limit to 10 most recent
                emoji = "🔥" if alert.level == "CRITICAL" else "⚠️"
                response += f"{emoji} [{alert.level}] {alert.service}: {alert.message}\n"
            
            return {
                "intent": "alerts",
                "response": response,
                "data": [asdict(a) for a in alerts]
            }
        
        elif intent == "restart":
            if service and service.capitalize() in services_config:
                url = services_config[service.capitalize()]
                success = self.healer.attempt_wake_up(service.capitalize(), url)
                
                return {
                    "intent": "restart",
                    "service": service,
                    "response": f"{'✅ Successfully woke up' if success else '❌ Failed to wake up'} {service.capitalize()}",
                    "success": success
                }
            else:
                return {
                    "intent": "restart",
                    "response": "Please specify a service to restart"
                }
        
        elif intent == "help":
            return {
                "intent": "help",
                "response": """**Sentinel AI Commands:**

**status** [service] - System or service health
**metrics** <service> - Detailed statistics
**alerts** - Show active alerts
**restart** <service> - Wake up sleeping service
**help** - Show this message

**Examples:**
- "status gateway"
- "metrics curator"
- "restart narrator"
- "show me all alerts"
"""
            }
        
        else:
            return {
                "intent": "unknown",
                "response": "I don't understand that command. Type 'help' for available commands."
            }


# ==================== MAIN SENTINEL AI ====================

class SentinelAI:
    """Central AI controller for ONLY system"""
    
    def __init__(self, services_config: Dict[str, str]):
        self.services = services_config
        self.metrics = MetricsCollector()
        self.health = HealthChecker(self.metrics)
        self.healer = AutoHealer(self.health)
        self.chat = ChatInterface(self.health, self.metrics, self.healer)
    
    def monitor_cycle(self):
        """Single monitoring cycle - check all services"""
        for name, url in self.services.items():
            metric = self.health.check_service(name, url)
            
            # Auto-healing if needed
            if not metric.is_healthy:
                self.healer.heal_service(name, url, metric)
    
    def get_system_snapshot(self) -> SystemHealth:
        """Get current system health snapshot"""
        services = list(self.services.keys())
        health_score = self.health.calculate_health_score(services)
        alerts = self.metrics.get_unresolved_alerts()
        
        # Aggregate stats
        all_stats = [self.metrics.get_stats(svc, hours=1) for svc in services]
        total_checks = sum(s['count'] for s in all_stats if s['count'] > 0)
        
        if total_checks > 0:
            avg_latency = statistics.mean([s['avg_latency_ms'] for s in all_stats if s['count'] > 0])
            avg_uptime = statistics.mean([s['uptime'] for s in all_stats if s['count'] > 0])
            error_rate = statistics.mean([s['error_rate'] for s in all_stats if s['count'] > 0])
        else:
            avg_latency = 0
            avg_uptime = 0
            error_rate = 0
        
        services_up = sum(1 for s in all_stats if s['count'] > 0 and s['uptime'] > 90)
        services_down = len(services) - services_up
        
        return SystemHealth(
            timestamp=time.time(),
            health_score=health_score,
            services_up=services_up,
            services_down=services_down,
            total_requests=total_checks,
            avg_latency_ms=avg_latency,
            error_rate=error_rate,
            alerts=[f"[{a.level}] {a.service}: {a.message}" for a in alerts[:5]]
        )
