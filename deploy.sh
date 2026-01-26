#!/bin/bash
set -e

echo "🚀 Magpie Full Stack Deployment"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
BACKEND_REPO="https://github.com/shekharkalshetti/magpie-backend.git"
FRONTEND_REPO="https://github.com/shekharkalshetti/magpie-frontend.git"
INSTALL_DIR="$HOME/magpie"

echo -e "${BLUE}📁 Installation directory: ${INSTALL_DIR}${NC}"
echo ""

# Create installation directory
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# ============================================================
# Step 1: Install Docker
# ============================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 1: Installing Docker${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo -e "${GREEN}✅ Docker installed${NC}"
else
    echo -e "${GREEN}✅ Docker already installed${NC}"
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}Installing Docker Compose...${NC}"
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✅ Docker Compose installed${NC}"
else
    echo -e "${GREEN}✅ Docker Compose already installed${NC}"
fi

# Check if Docker daemon is running
if ! docker ps &> /dev/null; then
    echo ""
    echo -e "${YELLOW}⚠️  Docker daemon is not accessible${NC}"
    echo ""
    echo -e "${YELLOW}Starting Docker daemon...${NC}"
    
    # Start Docker daemon in background with flags for restricted environments
    # --iptables=false and --bridge=none are needed in some containerized environments
    # --storage-driver=vfs is slower but works in restricted environments
    dockerd --iptables=false --bridge=none --storage-driver=vfs > /tmp/dockerd.log 2>&1 &
    DOCKERD_PID=$!
    
    # Wait for Docker daemon to be ready (up to 30 seconds)
    echo -n "Waiting for Docker daemon"
    for i in {1..30}; do
        if docker ps &> /dev/null 2>&1; then
            echo ""
            echo -e "${GREEN}✅ Docker daemon started successfully${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done
    echo ""
    
    # Final check
    if ! docker ps &> /dev/null 2>&1; then
        echo ""
        echo -e "${RED}❌ Failed to start Docker daemon${NC}"
        echo ""
        echo -e "${YELLOW}Docker daemon logs:${NC}"
        tail -20 /tmp/dockerd.log
        echo ""
        echo -e "${YELLOW}Try running manually:${NC}"
        echo "  dockerd --iptables=false --bridge=none --storage-driver=vfs &"
        echo "  # Wait a few seconds, then:"
        echo "  ./deploy.sh"
        echo ""
        exit 1
    fi
else
    echo -e "${GREEN}✅ Docker daemon is running${NC}"
fi

USE_SUDO="${USE_SUDO:-}"

# ============================================================
# Step 2: Clone Repositories
# ============================================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 2: Cloning Repositories${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Clone backend
if [ -d "backend" ]; then
    echo -e "${YELLOW}Backend directory exists, pulling latest...${NC}"
    cd backend
    git pull
    cd ..
else
    echo -e "${YELLOW}Cloning backend...${NC}"
    git clone "$BACKEND_REPO" backend
fi
echo -e "${GREEN}✅ Backend ready${NC}"

# Clone frontend
if [ -d "frontend" ]; then
    echo -e "${YELLOW}Frontend directory exists, pulling latest...${NC}"
    cd frontend
    git pull
    cd ..
else
    echo -e "${YELLOW}Cloning frontend...${NC}"
    git clone "$FRONTEND_REPO" frontend
fi
echo -e "${GREEN}✅ Frontend ready${NC}"

# ============================================================
# Step 3: Setup Environment Files
# ============================================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 3: Configuring Environment${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Generate secrets
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -base64 32)
POSTGRES_PASS="magpie_db_$(date +%s)"

# Backend .env
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}Creating backend .env...${NC}"
    cat > backend/.env << EOF
# Database
POSTGRES_PASSWORD=${POSTGRES_PASS}
DATABASE_URL=postgresql://postgres:${POSTGRES_PASS}@postgres:5432/triton

# Redis
REDIS_URL=redis://redis:6379

# Application
SECRET_KEY=${SECRET_KEY}
BACKEND_URL=http://localhost:8000

# vLLM
VLLM_URL=http://localhost:1234
EOF
    echo -e "${GREEN}✅ Backend .env created${NC}"
else
    echo -e "${YELLOW}⚠️  Backend .env exists, skipping...${NC}"
fi

# Frontend .env.local
if [ ! -f "frontend/.env.local" ]; then
    echo -e "${YELLOW}Creating frontend .env.local...${NC}"
    cat > frontend/.env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
    echo -e "${GREEN}✅ Frontend .env.local created${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend .env.local exists, skipping...${NC}"
fi

# ============================================================
# Step 4: Check vLLM
# ============================================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 4: Checking vLLM Service${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if curl -s http://localhost:1234/health > /dev/null 2>&1 || curl -s http://localhost:1234/v1/models > /dev/null 2>&1; then
    echo -e "${GREEN}✅ vLLM is running on port 1234${NC}"
else
    echo -e "${RED}❌ vLLM not detected on port 1234${NC}"
    echo ""
    echo -e "${YELLOW}You need to start vLLM before continuing:${NC}"
    echo ""
    echo "  1. Open a new terminal (or use tmux/screen)"
    echo "  2. Run:"
    echo "     ${YELLOW}vllm serve Qwen/Qwen2.5-1.5B-Instruct --port 1234 --host 0.0.0.0${NC}"
    echo ""
    echo "Or use the provided script in backend directory:"
    echo "     ${YELLOW}cd $INSTALL_DIR/backend && ./start-vllm.sh${NC}"
    echo ""
    read -p "Press Enter once vLLM is running to continue..."
fi

# ============================================================
# Step 5: Start Services
# ============================================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 5: Starting Services${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

cd backend
echo -e "${YELLOW}Starting PostgreSQL, Redis, Backend, Celery, and Frontend...${NC}"
$USE_SUDO docker-compose up -d

echo ""
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 10

# Show service status
echo ""
echo -e "${BLUE}Service Status:${NC}"
$USE_SUDO docker-compose ps

# ============================================================
# Done!
# ============================================================
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}Services running:${NC}"
echo "  • Backend:    http://localhost:8000"
echo "  • Frontend:   http://localhost:3000"
echo "  • API Docs:   http://localhost:8000/docs"
echo "  • vLLM:       http://localhost:1234"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo "  • View logs:         ${YELLOW}cd $INSTALL_DIR/backend && docker-compose logs -f${NC}"
echo "  • Stop services:     ${YELLOW}cd $INSTALL_DIR/backend && docker-compose down${NC}"
echo "  • Restart services:  ${YELLOW}cd $INSTALL_DIR/backend && docker-compose restart${NC}"
echo "  • Reattach to vLLM:  ${YELLOW}tmux attach -t vllm${NC} (if using tmux)"
echo ""
echo -e "${YELLOW}Admin credentials:${NC}"
echo "  Check backend logs for admin user details"
echo "  ${YELLOW}${USE_SUDO} docker-compose logs backend | grep -A 5 'Admin user'${NC}"
echo ""
echo -e "${YELLOW}Note:${NC} If you needed sudo, add it to all docker-compose commands:"
echo "  ${YELLOW}${USE_SUDO} docker-compose logs -f${NC}"
echo ""
