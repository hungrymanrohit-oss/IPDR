# Network Flow Dashboard - Deployment Guide

This guide provides detailed instructions for deploying the Network Flow Dashboard in production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Production Setup](#production-setup)
4. [Configuration](#configuration)
5. [Security Considerations](#security-considerations)
6. [Monitoring and Logging](#monitoring-and-logging)
7. [Backup and Recovery](#backup-and-recovery)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ recommended)
- **CPU**: 4+ cores
- **RAM**: 8GB+ (16GB recommended for high-traffic environments)
- **Storage**: 100GB+ SSD (depends on retention requirements)
- **Network**: Gigabit Ethernet or faster

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- Git
- Nginx (for reverse proxy)
- SSL certificates (Let's Encrypt recommended)

### Network Requirements

- Access to network interfaces for flow capture
- Outbound internet access for updates and GeoIP lookups
- Firewall rules configured appropriately

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │───▶│   Nginx Proxy   │───▶│   React App     │
│   (Optional)    │    │                 │    │   (Frontend)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Django API    │
                       │   (Backend)     │
                       └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   pmacct        │───▶│   Celery        │───▶│  TimescaleDB    │
│   (Flow Capture)│    │   (Processing)  │    │  (Storage)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   RabbitMQ      │
                       │   (Message Q)   │
                       └─────────────────┘
```

## Production Setup

### 1. Clone and Prepare Repository

```bash
# Clone the repository
git clone <repository-url>
cd network-dashboard

# Create production environment
cp docker-compose.yml docker-compose.prod.yml
```

### 2. Configure Environment Variables

Create production environment files:

**Backend (.env.prod)**:
```bash
DEBUG=False
SECRET_KEY=your-super-secret-production-key
DB_NAME=network_flows_prod
DB_USER=network_user
DB_PASSWORD=secure-db-password
DB_HOST=postgres
DB_PORT=5432
REDIS_URL=redis://redis:6379/0
RABBITMQ_URL=amqp://network_user:secure-mq-password@rabbitmq:5672/
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CORS_ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com
FLOW_RETENTION_DAYS=90
MAX_FLOWS_PER_BATCH=5000
FLOW_PROCESSING_INTERVAL=30
ENABLE_GEOIP=True
GEOIP_DATABASE_PATH=/usr/share/GeoIP/GeoLite2-City.mmdb
```

**Frontend (.env.prod)**:
```bash
REACT_APP_API_URL=https://api.your-domain.com
REACT_APP_SOCKET_URL=wss://api.your-domain.com
```

### 3. Configure Nginx

Create Nginx configuration:

```nginx
# /etc/nginx/sites-available/network-dashboard
upstream backend {
    server 127.0.0.1:8000;
}

upstream frontend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /var/www/network-dashboard/backend/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /var/www/network-dashboard/backend/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 4. SSL Certificate Setup

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Set up auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 5. Configure pmacct

Install and configure pmacct for flow capture:

```bash
# Install pmacct
sudo apt install pmacct

# Copy configuration
sudo cp pmacct/pmacctd.conf /etc/pmacct/pmacctd.conf

# Edit configuration for your environment
sudo nano /etc/pmacct/pmacctd.conf

# Start pmacct service
sudo systemctl enable pmacctd
sudo systemctl start pmacctd
```

### 6. Deploy with Docker Compose

```bash
# Build and start production services
docker-compose -f docker-compose.prod.yml up -d --build

# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

## Configuration

### Database Configuration

For production, consider using external PostgreSQL/TimescaleDB:

```yaml
# docker-compose.prod.yml
services:
  postgres:
    image: timescale/timescaledb:latest-pg14
    environment:
      POSTGRES_DB: network_flows_prod
      POSTGRES_USER: network_user
      POSTGRES_PASSWORD: secure-db-password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-timescale.sql:/docker-entrypoint-initdb.d/init-timescale.sql
    ports:
      - "127.0.0.1:5432:5432"  # Only local access
```

### Redis Configuration

For high availability, consider Redis Cluster:

```yaml
services:
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass secure-redis-password
    volumes:
      - redis_data:/data
    ports:
      - "127.0.0.1:6379:6379"
```

### Celery Configuration

Optimize Celery for production:

```python
# backend/flow_processor/celery.py
app.conf.update(
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
)
```

## Security Considerations

### 1. Network Security

- Use firewall rules to restrict access
- Implement network segmentation
- Use VPN for remote access
- Monitor network traffic

### 2. Application Security

- Keep all software updated
- Use strong passwords
- Implement rate limiting
- Enable audit logging
- Regular security scans

### 3. Data Security

- Encrypt data at rest
- Use TLS for data in transit
- Implement access controls
- Regular backups
- Data retention policies

### 4. Container Security

```bash
# Run containers as non-root
# In Dockerfile
USER nobody

# Use security scanning
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image your-image:tag
```

## Monitoring and Logging

### 1. Application Monitoring

```yaml
# Add to docker-compose.prod.yml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=secure-grafana-password
    ports:
      - "3001:3000"
```

### 2. Log Aggregation

```yaml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"

  kibana:
    image: docker.elastic.co/kibana/kibana:8.8.0
    ports:
      - "5601:5601"

  filebeat:
    image: docker.elastic.co/beats/filebeat:8.8.0
    volumes:
      - ./logs:/var/log/network-dashboard
      - ./monitoring/filebeat.yml:/usr/share/filebeat/filebeat.yml
```

### 3. Health Checks

```yaml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Backup and Recovery

### 1. Database Backups

```bash
#!/bin/bash
# scripts/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Database backup
docker-compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U network_user network_flows_prod > \
  $BACKUP_DIR/db_backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/db_backup_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete
```

### 2. Configuration Backups

```bash
# Backup configuration files
tar -czf config_backup_$DATE.tar.gz \
  docker-compose.prod.yml \
  backend/.env.prod \
  frontend/.env.prod \
  pmacct/pmacctd.conf \
  /etc/nginx/sites-available/network-dashboard
```

### 3. Recovery Procedures

```bash
# Database recovery
gunzip -c db_backup_20231201_120000.sql.gz | \
  docker-compose -f docker-compose.prod.yml exec -T postgres \
  psql -U network_user network_flows_prod

# Service recovery
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   ```bash
   # Check memory usage
   docker stats
   
   # Optimize Celery workers
   docker-compose -f docker-compose.prod.yml scale celery_worker=2
   ```

2. **Database Performance**
   ```sql
   -- Check slow queries
   SELECT query, calls, total_time, mean_time
   FROM pg_stat_statements
   ORDER BY mean_time DESC
   LIMIT 10;
   ```

3. **Network Flow Capture Issues**
   ```bash
   # Check pmacct status
   sudo systemctl status pmacctd
   
   # Check pmacct logs
   sudo journalctl -u pmacctd -f
   ```

### Performance Tuning

1. **Database Optimization**
   ```sql
   -- Analyze table statistics
   ANALYZE network_flows;
   
   -- Check index usage
   SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
   FROM pg_stat_user_indexes;
   ```

2. **Application Optimization**
   ```python
   # Increase worker processes
   CELERY_WORKER_CONCURRENCY = 4
   
   # Optimize database connections
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'CONN_MAX_AGE': 600,
           'OPTIONS': {
               'MAX_CONNS': 20,
           }
       }
   }
   ```

### Support and Maintenance

- Regular security updates
- Performance monitoring
- Capacity planning
- Documentation updates
- Training for operators

For additional support, refer to the project documentation or create an issue in the repository.