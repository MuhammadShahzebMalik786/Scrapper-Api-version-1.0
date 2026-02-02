#!/bin/bash

# Mobile.de Scraper - Complete Deployment Script
# Production Ready v2.0

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Setup environment
setup_env() {
    if [ ! -f .env ]; then
        log_info "Creating .env file..."
        cat > .env << EOF
# Mobile.de Scraper Environment Configuration

# API Security
API_TOKEN=mobile-scraper-2026-secure-token

# Database Configuration
DB_URL=postgresql://scraper:scraper123@db:5432/mobile_scraper
DB_PASSWORD=scraper123

# Application Settings
SCRAPER_DELAY=2
MAX_PAGES=5
HEADLESS_MODE=true

# Logging
LOG_LEVEL=INFO
LOG_DIR=./logs

# Chrome Configuration (optional)
# CHROME_BINARY_PATH=/usr/bin/google-chrome
# CHROMEDRIVER_PATH=/usr/bin/chromedriver
EOF
        log_info "✓ .env file created with default values"
        log_warn "Please edit .env file with your secure tokens before production use"
    else
        log_info "✓ .env file already exists"
    fi
}

# Kill processes using ports
kill_port_processes() {
    local port=$1
    local pids=$(sudo lsof -ti:$port 2>/dev/null || true)
    if [ ! -z "$pids" ]; then
        log_warn "Killing processes using port $port..."
        echo $pids | xargs sudo kill -9 2>/dev/null || true
        sleep 2
    fi
}

# Complete deployment
deploy() {
    log_info "Starting complete deployment..."
    
    # Check prerequisites
    check_docker
    
    # Setup environment
    setup_env
    
    # Clean up any existing processes
    log_info "Cleaning up existing processes..."
    kill_port_processes 8000
    kill_port_processes 5432
    
    # Stop and remove existing containers
    log_info "Stopping existing containers..."
    sudo docker-compose down --remove-orphans 2>/dev/null || true
    
    # Build and start services
    log_info "Building and starting services..."
    sudo docker-compose build --no-cache
    sudo docker-compose up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to start..."
    sleep 15
    
    # Health check
    log_info "Performing health checks..."
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        log_info "✓ API is healthy"
    else
        log_error "API health check failed"
        return 1
    fi
    
    # Check database
    if sudo docker-compose exec -T db pg_isready -U scraper >/dev/null 2>&1; then
        log_info "✓ Database is ready"
    else
        log_error "Database health check failed"
        return 1
    fi
    
    log_info "🎉 Deployment completed successfully!"
    log_info ""
    log_info "Services available at:"
    log_info "  • API: http://localhost:8000"
    log_info "  • Health: http://localhost:8000/health"
    log_info "  • Database: localhost:5432"
    log_info ""
    log_info "Next steps:"
    log_info "  1. Test API: ./deploy.sh test-api"
    log_info "  2. Start scraping: ./deploy.sh populate"
    log_info "  3. View logs: ./deploy.sh logs"
}

# Start services
start() {
    log_info "Starting services..."
    check_docker
    kill_port_processes 8000
    kill_port_processes 5432
    sudo docker-compose up -d
    sleep 10
    
    # Health check
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        log_info "✓ API is responding"
        show_status
    else
        log_error "Failed to start services"
        return 1
    fi
}

# Stop services
stop() {
    log_info "Stopping services..."
    sudo docker-compose down
    kill_port_processes 8000
    kill_port_processes 5432
    log_info "✓ Services stopped"
}

# Restart services
restart() {
    log_info "Restarting services..."
    stop
    sleep 3
    start
}

# Show status
show_status() {
    log_info "Service Status:"
    sudo docker-compose ps
    echo ""
    
    # API Health check
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        log_info "✓ API is responding"
    else
        log_error "✗ API is not responding"
    fi
}

# Test API endpoints
test_api() {
    log_info "Testing API endpoints..."
    
    # Health check
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        log_info "✓ Health endpoint working"
    else
        log_error "✗ Health endpoint failed"
    fi
    
    # Status check
    if curl -s http://localhost:8000/ >/dev/null 2>&1; then
        log_info "✓ Status endpoint working"
    else
        log_error "✗ Status endpoint failed"
    fi
    
    # Cars endpoint (with auth)
    local token=$(grep API_TOKEN .env | cut -d'=' -f2)
    if curl -s -H "Authorization: Bearer $token" "http://localhost:8000/cars?limit=1" >/dev/null 2>&1; then
        log_info "✓ Cars endpoint working"
    else
        log_warn "⚠ Cars endpoint returned no data (may be empty database)"
    fi
}

# Populate database
populate() {
    log_info "Starting scraper to populate database..."
    local token=$(grep API_TOKEN .env | cut -d'=' -f2)
    
    if curl -s -H "Authorization: Bearer $token" -X POST http://localhost:8000/populate | grep -q "started"; then
        log_info "✓ Scraper started successfully"
        log_info "Monitor progress with: ./deploy.sh logs app"
    else
        log_error "Failed to start scraper"
        return 1
    fi
}

# View logs
logs() {
    local service=${1:-app}
    log_info "Showing logs for $service..."
    sudo docker-compose logs -f $service
}

# Database shell
db_shell() {
    log_info "Opening database shell..."
    sudo docker-compose exec db psql -U scraper -d mobile_scraper
}

# Container shell
shell() {
    log_info "Opening container shell..."
    sudo docker-compose exec app bash
}

# Backup database
backup() {
    local backup_file="backup_$(date +%Y%m%d_%H%M%S).sql"
    log_info "Creating database backup: $backup_file"
    sudo docker-compose exec -T db pg_dump -U scraper mobile_scraper > $backup_file
    log_info "✓ Backup created: $backup_file"
}

# Restore database
restore() {
    local backup_file=$1
    if [ -z "$backup_file" ]; then
        log_error "Usage: ./deploy.sh restore <backup_file.sql>"
        return 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        return 1
    fi
    
    log_info "Restoring database from: $backup_file"
    sudo docker-compose exec -T db psql -U scraper -d mobile_scraper < $backup_file
    log_info "✓ Database restored"
}

# Clean up
clean() {
    log_info "Cleaning up logs and temporary files..."
    sudo rm -rf logs/ *.log 2>/dev/null || true
    sudo docker-compose down --volumes --remove-orphans 2>/dev/null || true
    sudo docker system prune -f
    log_info "✓ Cleanup completed"
}

# Rebuild containers
rebuild() {
    log_info "Rebuilding containers..."
    sudo docker-compose down
    sudo docker-compose build --no-cache
    sudo docker-compose up -d
    sleep 10
    show_status
}

# Show help
show_help() {
    echo "Mobile.de Scraper - Deployment Script v2.0"
    echo ""
    echo "Usage: ./deploy.sh <command>"
    echo ""
    echo "Deployment Commands:"
    echo "  deploy          Complete deployment (recommended for first time)"
    echo "  start           Start all services"
    echo "  stop            Stop all services"
    echo "  restart         Restart all services"
    echo "  rebuild         Rebuild and restart containers"
    echo ""
    echo "Testing Commands:"
    echo "  test-api        Test API endpoints"
    echo "  populate        Start scraper to populate database"
    echo "  status          Show service status"
    echo ""
    echo "Maintenance Commands:"
    echo "  logs [service]  View logs (default: app)"
    echo "  shell           Open container shell"
    echo "  db-shell        Open database shell"
    echo "  backup          Backup database"
    echo "  restore <file>  Restore database from backup"
    echo "  clean           Clean up logs and containers"
    echo ""
    echo "Examples:"
    echo "  ./deploy.sh deploy          # Complete deployment"
    echo "  ./deploy.sh populate        # Start scraping"
    echo "  ./deploy.sh logs app        # View app logs"
    echo "  ./deploy.sh backup          # Backup database"
}

# Main script logic
case "${1:-help}" in
    deploy)
        deploy
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        show_status
        ;;
    test-api)
        test_api
        ;;
    populate)
        populate
        ;;
    logs)
        logs $2
        ;;
    shell)
        shell
        ;;
    db-shell)
        db_shell
        ;;
    backup)
        backup
        ;;
    restore)
        restore $2
        ;;
    clean)
        clean
        ;;
    rebuild)
        rebuild
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
