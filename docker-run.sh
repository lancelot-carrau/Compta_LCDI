#!/bin/bash

# 🐳 Script de gestion Docker pour LCDI App
# Usage: ./docker-run.sh [build|start|stop|restart|logs|shell]

set -e

APP_NAME="lcdi-compta-app"
COMPOSE_FILE="docker-compose.yml"

echo "🐳 === GESTION DOCKER LCDI APP ==="

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages colorés
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

# Vérifier si Docker est installé
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker n'est pas installé. Installez Docker Desktop."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose n'est pas installé."
        exit 1
    fi
}

# Générer le fichier .env s'il n'existe pas
setup_env() {
    if [ ! -f ".env" ]; then
        print_warning "Fichier .env manquant. Création depuis .env.example..."
        cp .env.example .env
        
        # Générer une clé secrète
        SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))' 2>/dev/null || openssl rand -hex 32)
        sed -i "s/your-super-secret-key-here-change-me-in-production/$SECRET_KEY/" .env
        
        print_success "Fichier .env créé avec une clé secrète générée"
        print_warning "Vérifiez et modifiez le fichier .env selon vos besoins"
    fi
}

# Construire l'image Docker
build_image() {
    print_status "Construction de l'image Docker..."
    docker-compose build --no-cache
    print_success "Image construite avec succès"
}

# Démarrer l'application
start_app() {
    print_status "Démarrage de l'application LCDI..."
    docker-compose up -d
    print_success "Application démarrée"
    print_status "Accès: http://localhost:5000"
    
    # Attendre que l'application soit prête
    print_status "Vérification de l'état de l'application..."
    sleep 5
    
    if curl -f http://localhost:5000 >/dev/null 2>&1; then
        print_success "✅ Application accessible sur http://localhost:5000"
    else
        print_warning "⚠️ L'application met du temps à démarrer. Vérifiez les logs: ./docker-run.sh logs"
    fi
}

# Arrêter l'application
stop_app() {
    print_status "Arrêt de l'application..."
    docker-compose down
    print_success "Application arrêtée"
}

# Redémarrer l'application
restart_app() {
    print_status "Redémarrage de l'application..."
    docker-compose restart
    print_success "Application redémarrée"
}

# Afficher les logs
show_logs() {
    print_status "Affichage des logs (Ctrl+C pour quitter)..."
    docker-compose logs -f
}

# Ouvrir un shell dans le conteneur
open_shell() {
    print_status "Ouverture d'un shell dans le conteneur..."
    docker exec -it $APP_NAME /bin/bash
}

# Nettoyer les ressources Docker
cleanup() {
    print_status "Nettoyage des ressources Docker..."
    docker-compose down -v --remove-orphans
    docker system prune -f
    print_success "Nettoyage terminé"
}

# Afficher le statut
show_status() {
    print_status "Statut des conteneurs:"
    docker-compose ps
    
    print_status "\nUtilisation des ressources:"
    docker stats --no-stream $APP_NAME 2>/dev/null || print_warning "Conteneur non démarré"
}

# Menu principal
case "${1:-help}" in
    "build")
        check_docker
        setup_env
        build_image
        ;;
    "start")
        check_docker
        setup_env
        start_app
        ;;
    "stop")
        check_docker
        stop_app
        ;;
    "restart")
        check_docker
        restart_app
        ;;
    "logs")
        check_docker
        show_logs
        ;;
    "shell")
        check_docker
        open_shell
        ;;
    "status")
        check_docker
        show_status
        ;;
    "cleanup")
        check_docker
        cleanup
        ;;
    "dev")
        check_docker
        setup_env
        print_status "Démarrage en mode développement avec rechargement automatique..."
        docker-compose up --build
        ;;
    "help"|*)
        echo ""
        echo "🐳 Commandes disponibles:"
        echo "  ./docker-run.sh build     - Construire l'image Docker"
        echo "  ./docker-run.sh start     - Démarrer l'application en arrière-plan"
        echo "  ./docker-run.sh stop      - Arrêter l'application"
        echo "  ./docker-run.sh restart   - Redémarrer l'application"
        echo "  ./docker-run.sh logs      - Afficher les logs en temps réel"
        echo "  ./docker-run.sh shell     - Ouvrir un shell dans le conteneur"
        echo "  ./docker-run.sh status    - Afficher le statut et les ressources"
        echo "  ./docker-run.sh cleanup   - Nettoyer les ressources Docker"
        echo "  ./docker-run.sh dev       - Mode développement (premier plan)"
        echo "  ./docker-run.sh help      - Afficher cette aide"
        echo ""
        echo "🚀 Démarrage rapide:"
        echo "  ./docker-run.sh build && ./docker-run.sh start"
        echo ""
        ;;
esac
