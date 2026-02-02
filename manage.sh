#!/bin/bash

set -e

API_TOKEN="mobile-scraper-2026-secure-token"
BASE_URL="http://localhost:8080"

case "$1" in
    start)
        echo "Starting Mobile Scraper services..."
        docker-compose up -d
        echo "Services started. Check status with: $0 status"
        ;;
    stop)
        echo "Stopping Mobile Scraper services..."
        docker-compose down
        ;;
    restart)
        echo "Restarting Mobile Scraper services..."
        docker-compose down
        docker-compose up -d
        ;;
    status)
        echo "Service Status:"
        docker-compose ps
        echo -e "\nAPI Health:"
        curl -s "$BASE_URL/health" | jq . 2>/dev/null || curl -s "$BASE_URL/health"
        ;;
    logs)
        service=${2:-app}
        echo "Showing logs for $service..."
        docker-compose logs -f "$service"
        ;;
    test)
        echo "Testing API endpoints..."
        echo "Health check:"
        curl -s "$BASE_URL/health" | jq . 2>/dev/null || curl -s "$BASE_URL/health"
        echo -e "\nSystem status:"
        curl -s "$BASE_URL/" | jq . 2>/dev/null || curl -s "$BASE_URL/"
        echo -e "\nScraper status:"
        curl -s "$BASE_URL/status" | jq . 2>/dev/null || curl -s "$BASE_URL/status"
        ;;
    scrape)
        echo "Starting scraper..."
        curl -s -X POST -H "Authorization: Bearer $API_TOKEN" "$BASE_URL/populate" | jq . 2>/dev/null || curl -s -X POST -H "Authorization: Bearer $API_TOKEN" "$BASE_URL/populate"
        ;;
    build)
        echo "Building services..."
        docker-compose build
        ;;
    clean)
        echo "Cleaning up..."
        docker-compose down -v
        docker system prune -f
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|test|scrape|build|clean}"
        echo ""
        echo "Commands:"
        echo "  start    - Start all services"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  status   - Show service status"
        echo "  logs     - Show logs (optional: specify service)"
        echo "  test     - Test API endpoints"
        echo "  scrape   - Trigger scraping manually"
        echo "  build    - Build Docker images"
        echo "  clean    - Clean up containers and volumes"
        exit 1
        ;;
esac
