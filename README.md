# Real-Time Network Flow Dashboard

A comprehensive real-time network monitoring dashboard that captures, processes, and visualizes network flows using modern technologies.

## Architecture Overview

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   pmacct    │───▶│   Django    │───▶│  TimescaleDB│    │   React     │
│  (Capture)  │    │  (Backend)  │    │  (Storage)  │    │  (Frontend) │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                          │                    ▲
                          ▼                    │
                   ┌─────────────┐    ┌─────────────┐
                   │   Celery    │    │  Socket.IO  │
                   │ (Processing)│    │ (Real-time) │
                   └─────────────┘    └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │  RabbitMQ   │
                   │ (Message Q) │
                   └─────────────┘
```

## Features

- **Real-time Network Flow Capture**: Using pmacct to capture network flows from various sources
- **Data Processing**: Django + Celery for background processing and aggregation
- **Time-Series Storage**: TimescaleDB for efficient time-series data storage
- **Real-time Updates**: Socket.IO for live dashboard updates
- **Modern UI**: React-based dashboard with charts and visualizations
- **Scalable Architecture**: Message queue with RabbitMQ for reliable processing

## Project Structure

```
network-dashboard/
├── backend/                 # Django backend
│   ├── dashboard/          # Main Django app
│   ├── flow_processor/     # Celery tasks
│   ├── api/               # REST API endpoints
│   └── manage.py
├── frontend/              # React frontend
│   ├── src/
│   ├── public/
│   └── package.json
├── pmacct/                # pmacct configuration
├── docker/                # Docker configurations
├── scripts/               # Setup and utility scripts
└── requirements.txt
```

## Prerequisites

- Python 3.8+
- Node.js 16+
- Docker & Docker Compose
- TimescaleDB
- RabbitMQ
- pmacct

## Quick Start

1. **Clone and Setup**:
   ```bash
   git clone <repository>
   cd network-dashboard
   ```

2. **Backend Setup**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver
   ```

3. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm start
   ```

4. **Start Services**:
   ```bash
   docker-compose up -d
   ```

5. **Configure pmacct**:
   ```bash
   sudo cp pmacct/pmacctd.conf /etc/pmacct/pmacctd.conf
   sudo systemctl start pmacctd
   ```

## Configuration

### Environment Variables

Create `.env` files in the respective directories:

**Backend (.env)**:
```
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost:5432/network_flows
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
REDIS_URL=redis://localhost:6379/0
```

**Frontend (.env)**:
```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_SOCKET_URL=http://localhost:8000
```

## API Endpoints

- `GET /api/flows/` - Get network flows
- `GET /api/flows/stats/` - Get flow statistics
- `GET /api/flows/top-talkers/` - Get top talkers
- `GET /api/flows/protocols/` - Get protocol distribution
- `WS /ws/flows/` - WebSocket for real-time updates

## Dashboard Features

- **Real-time Flow Visualization**: Live network flow graphs
- **Top Talkers**: Most active IP addresses
- **Protocol Analysis**: Traffic breakdown by protocol
- **Bandwidth Monitoring**: Real-time bandwidth usage
- **Geographic Distribution**: IP geolocation mapping
- **Historical Analysis**: Time-series data analysis
- **Alert System**: Customizable alerts for anomalies

## Development

### Running Tests
```bash
# Backend tests
cd backend
python manage.py test

# Frontend tests
cd frontend
npm test
```

### Code Quality
```bash
# Backend
flake8 backend/
black backend/
isort backend/

# Frontend
npm run lint
npm run format
```

## Deployment

### Production Setup
1. Configure production environment variables
2. Set up reverse proxy (nginx)
3. Configure SSL certificates
4. Set up monitoring and logging
5. Configure backup strategies

### Docker Deployment
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Review the troubleshooting guide