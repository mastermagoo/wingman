#!/bin/bash

# Wingman Docker Deployment Script
# This script handles the deployment of the Wingman verification system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
ENV_EXAMPLE=".env.example"

# Functions
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

check_requirements() {
    print_status "Checking requirements..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi

    print_status "All requirements met"
}

setup_environment() {
    print_status "Setting up environment..."

    # Check if .env exists
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f "$ENV_EXAMPLE" ]; then
            print_warning ".env file not found. Creating from template..."
            cp "$ENV_EXAMPLE" "$ENV_FILE"
            print_warning "Please edit .env file with your configuration"
            print_warning "Especially set BOT_TOKEN and CHAT_ID for Telegram"
            exit 0
        else
            print_error ".env.example not found"
            exit 1
        fi
    fi

    print_status "Environment configured"
}

build_images() {
    print_status "Building Docker images..."
    docker-compose build --no-cache
    print_status "Images built successfully"
}

start_services() {
    print_status "Starting services..."
    docker-compose up -d
    print_status "Services started"
}

stop_services() {
    print_status "Stopping services..."
    docker-compose down
    print_status "Services stopped"
}

restart_services() {
    stop_services
    start_services
}

show_logs() {
    service=$1
    if [ -z "$service" ]; then
        docker-compose logs -f
    else
        docker-compose logs -f "$service"
    fi
}

check_health() {
    print_status "Checking service health..."

    # Wait for services to start
    sleep 5

    # Check each service
    services=("wingman-api" "wingman-postgres" "wingman-redis" "wingman-ollama")

    for service in "${services[@]}"; do
        if docker ps | grep -q "$service"; then
            status=$(docker inspect --format='{{.State.Health.Status}}' "$service" 2>/dev/null || echo "no healthcheck")
            if [ "$status" = "healthy" ]; then
                print_status "$service: ✅ Healthy"
            elif [ "$status" = "no healthcheck" ]; then
                print_status "$service: ⚠️  No healthcheck defined"
            else
                print_warning "$service: ⚠️  Status: $status"
            fi
        else
            print_error "$service: ❌ Not running"
        fi
    done
}

setup_ollama() {
    print_status "Setting up Ollama with Mistral 7B..."

    # Wait for Ollama to be ready
    print_status "Waiting for Ollama service..."
    sleep 10

    # Pull Mistral 7B model
    print_status "Pulling Mistral 7B model..."
    docker exec wingman-ollama ollama pull mistral:7b

    print_status "Ollama setup complete"
}

# Main menu
case "${1:-}" in
    start)
        check_requirements
        setup_environment
        build_images
        start_services
        setup_ollama
        check_health
        print_status "Wingman deployment complete!"
        print_status "API available at: http://localhost:5000"
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        check_health
        ;;
    build)
        build_images
        ;;
    logs)
        show_logs "$2"
        ;;
    health)
        check_health
        ;;
    setup-ollama)
        setup_ollama
        ;;
    clean)
        print_warning "This will remove all containers and volumes!"
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose down -v
            print_status "Cleanup complete"
        fi
        ;;
    *)
        echo "Wingman Docker Deployment"
        echo ""
        echo "Usage: $0 {start|stop|restart|build|logs|health|setup-ollama|clean}"
        echo ""
        echo "Commands:"
        echo "  start         - Build and start all services"
        echo "  stop          - Stop all services"
        echo "  restart       - Restart all services"
        echo "  build         - Build Docker images"
        echo "  logs [service]- Show logs (optionally for specific service)"
        echo "  health        - Check service health status"
        echo "  setup-ollama  - Setup Ollama with Mistral 7B"
        echo "  clean         - Remove all containers and volumes"
        exit 1
        ;;
esac