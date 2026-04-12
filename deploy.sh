#!/bin/bash
#
# Meeting Intelligence Agent - Automated Deployment Script
# Usage: sudo bash deploy.sh [options]
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/opt/briefing-agent"
APP_USER="briefing-agent"
APP_GROUP="briefing-agent"
VENV_DIR="${APP_DIR}/venv"
LOG_DIR="/var/log/briefing-agent"
DATA_DIR="${APP_DIR}/data"

# Functions
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then 
        log_error "This script must be run as root (use: sudo bash deploy.sh)"
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check Git
    if ! command -v git &> /dev/null; then
        log_warn "Git is not installed. Skipping git operations."
    fi
    
    log_info "Prerequisites check passed ✓"
}

create_user() {
    log_info "Creating application user (if not exists)..."
    
    if ! id "$APP_USER" &>/dev/null; then
        useradd -m -s /bin/bash "$APP_USER" || log_warn "User $APP_USER already exists"
    fi
    
    log_info "User setup complete ✓"
}

setup_directories() {
    log_info "Setting up directories..."
    
    mkdir -p "$APP_DIR" "$LOG_DIR" "$DATA_DIR"
    mkdir -p "${APP_DIR}/output"
    
    chown -R "${APP_USER}:${APP_GROUP}" "$APP_DIR" "$LOG_DIR" "$DATA_DIR"
    chmod -R 755 "$APP_DIR" "$LOG_DIR" "$DATA_DIR"
    
    log_info "Directories setup complete ✓"
}

clone_repository() {
    log_info "Cloning repository..."
    
    if [ -d "$APP_DIR/.git" ]; then
        log_warn "Repository already exists, pulling latest..."
        cd "$APP_DIR"
        sudo -u "$APP_USER" git pull origin main || log_warn "Git pull failed"
    else
        if [ -z "$REPO_URL" ]; then
            REPO_URL="https://github.com/CoderKavyaG/cli-brief.git"
        fi
        
        # Clone to temp directory first
        TEMP_DIR=$(mktemp -d)
        git clone "$REPO_URL" "$TEMP_DIR"
        
        # Move files
        cp -r "$TEMP_DIR"/* "$APP_DIR/"/
        rm -rf "$TEMP_DIR"
        
        chown -R "${APP_USER}:${APP_GROUP}" "$APP_DIR"
    fi
    
    log_info "Repository ready ✓"
}

setup_python_env() {
    log_info "Setting up Python environment..."
    
    # Create virtual environment
    python3 -m venv "$VENV_DIR"
    chown -R "${APP_USER}:${APP_GROUP}" "$VENV_ENV_DIR"
    
    # Activate and upgrade pip
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip setuptools wheel
    
    # Install dependencies
    if [ -f "$APP_DIR/requirements.txt" ]; then
        pip install -r "$APP_DIR/requirements.txt"
        pip install gunicorn  # Production WSGI server
    fi
    
    log_info "Python environment setup complete ✓"
}

configure_environment() {
    log_info "Configuring environment..."
    
    if [ ! -f "$APP_DIR/.env" ]; then
        if [ -f "$APP_DIR/.env.example" ]; then
            cp "$APP_DIR/.env.example" "$APP_DIR/.env"
            log_warn ".env file created from template - PLEASE EDIT AND ADD API KEYS!"
            log_warn "Edit: $APP_DIR/.env"
        else
            log_error ".env.example not found"
            exit 1
        fi
    fi
    
    chown "${APP_USER}:${APP_GROUP}" "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"  # Restrict permissions for security
    
    log_info "Environment configuration complete ✓"
}

setup_systemd() {
    log_info "Setting up systemd service..."
    
    # Copy service file
    if [ -f "$APP_DIR/briefing-agent.service" ]; then
        cp "$APP_DIR/briefing-agent.service" /etc/systemd/system/
        
        # Reload systemd
        systemctl daemon-reload
        
        log_info "Systemd service installed ✓"
        log_info "Enable service with: sudo systemctl enable briefing-agent"
        log_info "Start service with: sudo systemctl start briefing-agent"
    else
        log_warn "Service file not found at $APP_DIR/briefing-agent.service"
    fi
}

setup_nginx() {
    log_info "Setting up Nginx (optional)..."
    
    if command -v nginx &> /dev/null; then
        if [ -f "$APP_DIR/nginx.conf.template" ]; then
            # Update server name and copy
            sed "s/YOUR_DOMAIN/localhost/g" "$APP_DIR/nginx.conf.template" > /etc/nginx/sites-available/briefing-agent
            
            # Enable site
            if [ ! -L /etc/nginx/sites-enabled/briefing-agent ]; then
                ln -s /etc/nginx/sites-available/briefing-agent /etc/nginx/sites-enabled/
            fi
            
            # Test and reload
            nginx -t && systemctl reload nginx
            
            log_info "Nginx configured ✓"
        fi
    else
        log_warn "Nginx not installed, skipping Nginx setup"
    fi
}

test_installation() {
    log_info "Testing installation..."
    
    cd "$APP_DIR"
    source "$VENV_DIR/bin/activate"
    
    # Test imports
    python3 -c "from phase1_agent.main import IntelAgent; print('✓ Imports successful')" || {
        log_error "Import test failed"
        exit 1
    }
    
    log_info "Installation test passed ✓"
}

show_next_steps() {
    log_info "✅ Deployment complete!"
    echo ""
    echo "Next steps:"
    echo "1. Edit configuration file:"
    echo "   nano $APP_DIR/.env"
    echo ""
    echo "2. Add your API keys:"
    echo "   - GROQ_API_KEY"
    echo "   - TAVILY_SEARCH_API_KEY"
    echo "   - FIRECRAWL_API_KEY (optional)"
    echo ""
    echo "3. Start the service:"
    echo "   sudo systemctl start briefing-agent"
    echo ""
    echo "4. Check status:"
    echo "   sudo systemctl status briefing-agent"
    echo ""
    echo "5. View logs:"
    echo "   sudo journalctl -u briefing-agent -f"
    echo ""
    echo "6. Access the web UI:"
    echo "   http://localhost:5000"
    echo ""
}

# Main deployment flow
main() {
    log_info "Starting Meeting Intelligence Agent deployment..."
    echo ""
    
    check_prerequisites
    create_user
    setup_directories
    clone_repository
    setup_python_env
    configure_environment
    setup_systemd
    setup_nginx
    test_installation
    show_next_steps
    
    log_info "Deployment finished!"
}

# Run main
main
