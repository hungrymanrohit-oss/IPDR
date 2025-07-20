#!/bin/bash

# Network Flow Dashboard Setup Script
# This script sets up the entire project environment

set -e

echo "🚀 Setting up Network Flow Dashboard..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Check if Node.js is installed
check_nodejs() {
    if ! command -v node &> /dev/null; then
        print_warning "Node.js is not installed. Frontend development will not work."
    else
        print_success "Node.js is installed (version: $(node --version))"
    fi
}

# Check if Python is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_warning "Python 3 is not installed. Backend development will not work."
    else
        print_success "Python 3 is installed (version: $(python3 --version))"
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p logs
    mkdir -p backend/static
    mkdir -p backend/media
    mkdir -p frontend/build
    
    print_success "Directories created"
}

# Create environment files
create_env_files() {
    print_status "Creating environment files..."
    
    # Backend .env
    if [ ! -f backend/.env ]; then
        cat > backend/.env << EOF
DEBUG=True
SECRET_KEY=your-secret-key-change-me-in-production
DB_NAME=network_flows
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/0
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
FLOW_RETENTION_DAYS=30
MAX_FLOWS_PER_BATCH=1000
FLOW_PROCESSING_INTERVAL=60
ENABLE_GEOIP=True
GEOIP_DATABASE_PATH=/usr/share/GeoIP/GeoLite2-City.mmdb
EOF
        print_success "Backend .env file created"
    else
        print_warning "Backend .env file already exists"
    fi
    
    # Frontend .env
    if [ ! -f frontend/.env ]; then
        cat > frontend/.env << EOF
REACT_APP_API_URL=http://localhost:8000
REACT_APP_SOCKET_URL=ws://localhost:8000
EOF
        print_success "Frontend .env file created"
    else
        print_warning "Frontend .env file already exists"
    fi
}

# Setup backend (if Python is available)
setup_backend() {
    if command -v python3 &> /dev/null; then
        print_status "Setting up backend..."
        
        cd backend
        
        # Create virtual environment
        if [ ! -d "venv" ]; then
            print_status "Creating Python virtual environment..."
            python3 -m venv venv
        fi
        
        # Activate virtual environment and install dependencies
        print_status "Installing Python dependencies..."
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
        
        # Run migrations
        print_status "Running database migrations..."
        python manage.py makemigrations
        python manage.py migrate
        
        # Create superuser
        print_status "Creating superuser..."
        echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'admin') if not User.objects.filter(username='admin').exists() else None" | python manage.py shell
        
        cd ..
        print_success "Backend setup completed"
    else
        print_warning "Skipping backend setup (Python not available)"
    fi
}

# Setup frontend (if Node.js is available)
setup_frontend() {
    if command -v node &> /dev/null; then
        print_status "Setting up frontend..."
        
        cd frontend
        
        # Install dependencies
        print_status "Installing Node.js dependencies..."
        npm install
        
        cd ..
        print_success "Frontend setup completed"
    else
        print_warning "Skipping frontend setup (Node.js not available)"
    fi
}

# Start services with Docker
start_services() {
    print_status "Starting services with Docker Compose..."
    
    # Build and start services
    docker-compose up -d --build
    
    print_success "Services started successfully"
    print_status "Waiting for services to be ready..."
    sleep 30
    
    # Check service status
    print_status "Checking service status..."
    docker-compose ps
}

# Display access information
show_access_info() {
    echo ""
    echo "🎉 Network Flow Dashboard Setup Complete!"
    echo ""
    echo "📊 Access Information:"
    echo "  • Frontend Dashboard: http://localhost:3000"
    echo "  • Backend API: http://localhost:8000"
    echo "  • API Documentation: http://localhost:8000/swagger/"
    echo "  • Django Admin: http://localhost:8000/admin/"
    echo "  • RabbitMQ Management: http://localhost:15672/"
    echo ""
    echo "🔐 Default Credentials:"
    echo "  • Django Admin: admin / admin"
    echo "  • RabbitMQ: guest / guest"
    echo ""
    echo "📁 Project Structure:"
    echo "  • Backend: ./backend/"
    echo "  • Frontend: ./frontend/"
    echo "  • Logs: ./logs/"
    echo "  • Docker: ./docker-compose.yml"
    echo ""
    echo "🛠️  Useful Commands:"
    echo "  • View logs: docker-compose logs -f"
    echo "  • Stop services: docker-compose down"
    echo "  • Restart services: docker-compose restart"
    echo "  • Backend shell: docker-compose exec backend python manage.py shell"
    echo ""
    echo "📚 Next Steps:"
    echo "  1. Configure pmacct to capture network flows"
    echo "  2. Set up GeoIP database for location data"
    echo "  3. Configure alert thresholds"
    echo "  4. Set up monitoring and logging"
    echo ""
}

# Main setup function
main() {
    print_status "Starting Network Flow Dashboard setup..."
    
    # Check prerequisites
    check_docker
    check_nodejs
    check_python
    
    # Create directories and files
    create_directories
    create_env_files
    
    # Setup development environment
    setup_backend
    setup_frontend
    
    # Start services
    start_services
    
    # Show access information
    show_access_info
}

# Run main function
main "$@"