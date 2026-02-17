# Prometheus/Grafana Monitoring — Operations Guide

## Overview

Wingman TEST environment includes integrated Prometheus and Grafana monitoring for observability, metrics collection, and alerting.

**Version:** Phase 6.1+ (Added 2026-02-17)
**Status:** Operational in TEST, Ready for PRD

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Wingman TEST Stack                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    /metrics     ┌────────────────┐       │
│  │ Wingman API  │◄───────────────►│  Prometheus    │       │
│  │  :5000       │   (scrape 15s)  │  :9090 (9091)  │       │
│  └──────────────┘                 └────────┬───────┘       │
│         │                                    │               │
│         │ health checks                      │ datasource   │
│         ▼                                    ▼               │
│  ┌──────────────┐                 ┌────────────────┐       │
│  │  Postgres    │                 │    Grafana     │       │
│  │  Redis       │                 │ :3000 (3333)   │       │
│  └──────────────┘                 └────────────────┘       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

**Key Components:**

1. **Wingman API** — Exposes `/metrics` endpoint (Prometheus format)
2. **Prometheus** — Scrapes metrics, stores time-series data
3. **Grafana** — Visualizes metrics, dashboards, alerting

---

## Quick Start

### Access URLs

| Service    | URL                       | Credentials    |
|------------|---------------------------|----------------|
| Prometheus | http://localhost:9091     | (none)         |
| Grafana    | http://localhost:3333     | admin / admin  |
| Metrics    | http://localhost:8101/metrics | (none)     |

### First Login to Grafana

1. Open http://localhost:3333
2. Login: `admin` / `admin`
3. (Optional) Change password when prompted
4. Datasource "Prometheus" is pre-configured

### View Metrics in Prometheus

1. Open http://localhost:9091
2. Navigate to **Status → Targets** to see scrape health
3. Navigate to **Graph** to query metrics
4. Example queries:
   ```promql
   wingman_health_status
   wingman_verifier_available
   wingman_database_connected
   ```

---

## Metrics Reference

### Available Metrics

| Metric Name                      | Type  | Description                                    | Labels                  |
|----------------------------------|-------|------------------------------------------------|-------------------------|
| `wingman_health_status`          | gauge | Overall health (1=healthy, 0=unhealthy)        | (none)                  |
| `wingman_verifier_available`     | gauge | Verifier availability (1=available, 0=unavail) | `verifier` (simple/enhanced) |
| `wingman_validator_available`    | gauge | Validator availability (1=available, 0=unavail)| `validator` (input/output) |
| `wingman_database_connected`     | gauge | Database connection (1=connected, 0=disconn)   | (none)                  |
| `wingman_start_time_seconds`     | gauge | Process start time (Unix timestamp)            | (none)                  |

### Example Queries

**Check API health:**
```promql
wingman_health_status
```

**Verifier availability over time:**
```promql
wingman_verifier_available{verifier="simple"}
```

**Calculate uptime:**
```promql
time() - wingman_start_time_seconds
```

**Alert if database disconnected:**
```promql
wingman_database_connected == 0
```

---

## Creating Grafana Dashboards

### Option 1: Manual Dashboard Creation

1. Login to Grafana (http://localhost:3333)
2. Click **+** → **Create Dashboard**
3. Click **Add visualization**
4. Select **Prometheus** datasource
5. Enter metric query (e.g., `wingman_health_status`)
6. Configure visualization type (Graph, Gauge, Stat, etc.)
7. Click **Apply** and **Save dashboard**

### Option 2: Import Pre-built Dashboard

Create a JSON dashboard file:

```json
{
  "dashboard": {
    "title": "Wingman Health Overview",
    "panels": [
      {
        "type": "stat",
        "title": "API Health",
        "targets": [
          {
            "expr": "wingman_health_status",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                {"value": 0, "color": "red"},
                {"value": 1, "color": "green"}
              ]
            }
          }
        }
      },
      {
        "type": "graph",
        "title": "Verifier Availability",
        "targets": [
          {
            "expr": "wingman_verifier_available",
            "legendFormat": "{{verifier}}"
          }
        ]
      }
    ]
  }
}
```

Import:
1. **Dashboards** → **Import**
2. Paste JSON or upload file
3. Click **Load** and **Import**

---

## Alerting Setup

### Prometheus Alerting Rules

Create alert rules in `monitoring/prometheus-alerts.yml`:

```yaml
groups:
  - name: wingman_alerts
    interval: 30s
    rules:
      - alert: WingmanAPIDown
        expr: wingman_health_status == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Wingman API is down"
          description: "API health status has been 0 for 2+ minutes"

      - alert: DatabaseDisconnected
        expr: wingman_database_connected == 0
        for: 5m
        labels:
          severity: high
        annotations:
          summary: "Database disconnected"
          description: "Wingman has lost database connection"

      - alert: EnhancedVerifierDown
        expr: wingman_verifier_available{verifier="enhanced"} == 0
        for: 10m
        labels:
          severity: medium
        annotations:
          summary: "Enhanced verifier unavailable"
          description: "Mistral LLM verifier has been down for 10+ minutes"
```

Update `monitoring/prometheus.yml`:

```yaml
# Add to prometheus.yml
rule_files:
  - 'prometheus-alerts.yml'

# Alertmanager configuration (if using)
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

### Grafana Alerting

1. Open dashboard panel
2. Click **Alert** tab
3. Create alert rule:
   - **Condition:** `WHEN last() OF query(A) IS BELOW 1`
   - **Evaluate:** Every 1m for 2m
4. Configure notification channel (Telegram, email, Slack, etc.)

---

## Maintenance Tasks

### Restart Prometheus

```bash
docker compose -f docker-compose.yml -p wingman-test restart prometheus
```

### Restart Grafana

```bash
docker compose -f docker-compose.yml -p wingman-test restart grafana
```

### Check Prometheus Logs

```bash
docker compose -f docker-compose.yml -p wingman-test logs prometheus --tail 50
```

### Check Grafana Logs

```bash
docker compose -f docker-compose.yml -p wingman-test logs grafana --tail 50
```

### View Prometheus Configuration

```bash
curl http://localhost:9091/api/v1/status/config | jq .
```

### Verify Scrape Targets

```bash
curl -s http://localhost:9091/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'
```

**Expected output:**
```json
{
  "job": "wingman-api",
  "health": "up"
}
{
  "job": "prometheus",
  "health": "up"
}
```

### Backup Grafana Dashboards

Dashboards are stored in Grafana database (`grafana_data` volume).

**Manual backup:**
```bash
docker compose -f docker-compose.yml -p wingman-test exec grafana \
  grafana-cli admin export-dashboard > wingman-dashboard-backup.json
```

**Volume backup:**
```bash
docker run --rm -v wingman-test_grafana_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/grafana-backup.tar.gz -C /data .
```

---

## Troubleshooting

### Prometheus Not Scraping Wingman API

**Symptom:** Target shows "down" in Prometheus UI

**Check:**
1. Verify API is healthy: `curl http://localhost:8101/health`
2. Verify metrics endpoint: `curl http://localhost:8101/metrics`
3. Check Prometheus logs: `docker logs wingman-test-prometheus-1`
4. Verify network connectivity:
   ```bash
   docker compose -f docker-compose.yml -p wingman-test exec prometheus \
     wget -O- http://wingman-api:5000/metrics
   ```

**Fix:** Restart Prometheus and Wingman API:
```bash
docker compose -f docker-compose.yml -p wingman-test restart prometheus wingman-api
```

### Grafana Cannot Connect to Prometheus

**Symptom:** Datasource test fails

**Check:**
1. Verify Prometheus is running: `curl http://localhost:9091/-/healthy`
2. Check Grafana logs for connection errors
3. Verify datasource config:
   ```bash
   cat monitoring/grafana-datasources.yml
   ```

**Fix:** Recreate Grafana container:
```bash
docker compose -f docker-compose.yml -p wingman-test up -d --force-recreate grafana
```

### Metrics Not Updating

**Symptom:** Metrics show stale data

**Check:**
1. Verify API is running: `docker compose -f docker-compose.yml -p wingman-test ps wingman-api`
2. Check `/metrics` endpoint returns current data
3. Verify Prometheus scrape interval (default: 15s)

**Fix:** Restart API server:
```bash
docker compose -f docker-compose.yml -p wingman-test restart wingman-api
```

### Grafana Login Issues

**Symptom:** Cannot login with admin/admin

**Fix:** Reset admin password:
```bash
docker compose -f docker-compose.yml -p wingman-test exec grafana \
  grafana-cli admin reset-admin-password newpassword
```

---

## Configuration Files

### `monitoring/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    environment: 'test'
    cluster: 'wingman'

scrape_configs:
  - job_name: 'wingman-api'
    static_configs:
      - targets: ['wingman-api:5000']
        labels:
          service: 'wingman-api'
          environment: 'test'

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
        labels:
          service: 'prometheus'
```

### `monitoring/grafana-datasources.yml`

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
    jsonData:
      timeInterval: '15s'
      httpMethod: 'POST'
```

---

## Production Deployment (PRD)

To deploy monitoring to PRD environment:

1. **Update PRD compose file** (`docker-compose.prd.yml`):
   ```yaml
   # Add prometheus and grafana services (same as TEST)
   # Use different ports: 9092 (Prometheus), 3334 (Grafana)
   ```

2. **Create PRD monitoring configs:**
   ```bash
   cp monitoring/prometheus.yml monitoring/prometheus-prd.yml
   cp monitoring/grafana-datasources.yml monitoring/grafana-datasources-prd.yml
   ```

3. **Update environment labels:**
   ```yaml
   # In prometheus-prd.yml
   external_labels:
     environment: 'prd'
     cluster: 'wingman'
   ```

4. **Secure Grafana credentials:**
   ```bash
   # In .env.prd
   GRAFANA_ADMIN_USER=admin
   GRAFANA_ADMIN_PASSWORD=<strong-password>
   ```

5. **Deploy:**
   ```bash
   docker compose -f docker-compose.prd.yml -p wingman-prd \
     --env-file .env.prd up -d prometheus grafana
   ```

6. **Validate:**
   ```bash
   curl http://localhost:9092/-/healthy  # Prometheus
   curl http://localhost:3334/api/health # Grafana
   ```

---

## Future Enhancements

### Planned Additions

1. **Postgres Exporter** — Database metrics (connections, queries, cache hit ratio)
2. **Redis Exporter** — Cache metrics (hit rate, memory usage, keys)
3. **Custom Metrics** — Request latency, approval queue depth, validation scores
4. **Alertmanager** — Alert routing, silencing, aggregation
5. **Telegram Alerts** — Integration with existing Wingman Telegram bot

### Custom Metrics Examples

Add to `api_server.py`:

```python
# Request counter
request_counter = Counter('wingman_requests_total', 'Total requests', ['endpoint', 'method'])

# Request duration histogram
request_duration = Histogram('wingman_request_duration_seconds', 'Request duration', ['endpoint'])

# Approval queue depth
approval_queue_depth = Gauge('wingman_approval_queue_depth', 'Pending approvals count')
```

---

## References

- **Prometheus Documentation:** https://prometheus.io/docs/
- **Grafana Documentation:** https://grafana.com/docs/
- **PromQL Query Language:** https://prometheus.io/docs/prometheus/latest/querying/basics/
- **Grafana Dashboard Gallery:** https://grafana.com/grafana/dashboards/

---

## Support

For monitoring issues or questions:
1. Check this guide first
2. Review [WINGMAN_AUTOMATION_AUDIT_2026-02-17.md](../03-operations/WINGMAN_AUTOMATION_AUDIT_2026-02-17.md)
3. Check Prometheus/Grafana logs
4. Contact: Mark (via Telegram)

---

**Last Updated:** 2026-02-17
**Phase:** 6.1
**Status:** Operational (TEST), Ready for PRD
