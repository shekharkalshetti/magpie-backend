#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Magpie Full Stack Native Deployment${NC}"
echo "========================================"
echo ""

# Installation directory
INSTALL_DIR="${HOME}/magpie"
echo -e "📁 Installation directory: ${INSTALL_DIR}"
echo ""

# Create installation directory
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 1: Installing System Dependencies${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Install PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "Installing PostgreSQL..."
    sudo apt-get update
    sudo apt-get install -y postgresql postgresql-contrib
    echo -e "${GREEN}✅ PostgreSQL installed${NC}"
else
    echo -e "${GREEN}✅ PostgreSQL already installed${NC}"
fi

# Install Redis
if ! command -v redis-server &> /dev/null; then
    echo "Installing Redis..."
    sudo apt-get install -y redis-server
    echo -e "${GREEN}✅ Redis installed${NC}"
else
    echo -e "${GREEN}✅ Redis already installed${NC}"
fi

# Install Node.js (for frontend)
if ! command -v node &> /dev/null; then
    echo "Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
    echo -e "${GREEN}✅ Node.js installed${NC}"
else
    echo -e "${GREEN}✅ Node.js already installed${NC}"
fi

# Install Python dependencies
if ! command -v python3 &> /dev/null; then
    echo "Installing Python..."
    sudo apt-get install -y python3 python3-pip python3-venv
    echo -e "${GREEN}✅ Python installed${NC}"
else
    echo -e "${GREEN}✅ Python already installed${NC}"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 2: Cloning Repositories${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Clone backend
if [ ! -d "backend" ]; then
    echo "Cloning backend..."
    git clone https://github.com/shekharkalshetti/magpie-backend.git backend
    echo -e "${GREEN}✅ Backend cloned${NC}"
else
    echo -e "${GREEN}✅ Backend already exists${NC}"
fi

# Clone frontend
if [ ! -d "frontend" ]; then
    echo "Cloning frontend..."
    git clone https://github.com/shekharkalshetti/magpie-frontend.git frontend
    echo -e "${GREEN}✅ Frontend cloned${NC}"
else
    echo -e "${GREEN}✅ Frontend already exists${NC}"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 3: Setting Up PostgreSQL${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Start PostgreSQL
sudo service postgresql start || sudo systemctl start postgresql || true
sleep 3

# Create database and user
DB_NAME="magpie"
DB_USER="magpie"
DB_PASSWORD=$(openssl rand -hex 16)

echo "Creating database and user..."
sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME};" 2>/dev/null || echo "Database already exists"
sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';" 2>/dev/null || echo "User already exists"
sudo -u postgres psql -c "ALTER USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};" 2>/dev/null || true
sudo -u postgres psql -d ${DB_NAME} -c "GRANT ALL ON SCHEMA public TO ${DB_USER};" 2>/dev/null || true

echo -e "${GREEN}✅ PostgreSQL configured${NC}"
echo -e "${YELLOW}Database: ${DB_NAME}${NC}"
echo -e "${YELLOW}User: ${DB_USER}${NC}"
echo -e "${YELLOW}Password: ${DB_PASSWORD}${NC}"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 4: Setting Up Redis${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Start Redis
sudo service redis-server start || sudo systemctl start redis || redis-server --daemonize yes || true
sleep 2

if redis-cli ping &> /dev/null; then
    echo -e "${GREEN}✅ Redis is running${NC}"
else
    echo -e "${YELLOW}⚠️  Redis may not be running, but continuing...${NC}"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 5: Configuring Backend${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

cd "$INSTALL_DIR/backend"

# Create Python virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Generate secrets
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)

# Create .env file
cat > .env << EOF
# Database
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=${SECRET_KEY}
JWT_SECRET_KEY=${JWT_SECRET}
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=production
DEBUG=False

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Admin user (change after first login)
ADMIN_EMAIL=admin@magpie.local
ADMIN_PASSWORD=$(openssl rand -base64 12)

# vLLM
VLLM_URL=http://localhost:1234
EOF

echo -e "${GREEN}✅ Backend .env created${NC}"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Create admin user
echo "Creating admin user..."
python scripts/seed_admin_user.py

echo -e "${GREEN}✅ Backend configured${NC}"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 6: Configuring Frontend${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

cd "$INSTALL_DIR/frontend"

# Install npm dependencies
echo "Installing npm dependencies..."
npm install

# Create .env.local
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF

echo -e "${GREEN}✅ Frontend configured${NC}"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 7: Checking vLLM Service${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if curl -s http://localhost:1234/v1/models > /dev/null 2>&1; then
    echo -e "${GREEN}✅ vLLM is running on port 1234${NC}"
else
    echo -e "${YELLOW}⚠️  vLLM is not running on port 1234${NC}"
    echo -e "${YELLOW}Start vLLM with:${NC}"
    echo "  tmux new -s vllm"
    echo "  vllm serve Qwen/Qwen2.5-1.5B-Instruct --port 1234 --host 0.0.0.0 --trust-remote-code --max-model-len 4096 --gpu-memory-utilization 0.5"
    echo ""
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🎉 Deployment Complete!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Save admin credentials
ADMIN_EMAIL=$(grep ADMIN_EMAIL "$INSTALL_DIR/backend/.env" | cut -d'=' -f2)
ADMIN_PASSWORD=$(grep ADMIN_PASSWORD "$INSTALL_DIR/backend/.env" | cut -d'=' -f2)

cat > "$INSTALL_DIR/CREDENTIALS.txt" << EOF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Magpie Deployment Credentials
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Admin Login:
  Email: ${ADMIN_EMAIL}
  Password: ${ADMIN_PASSWORD}

Database:
  Database: ${DB_NAME}
  User: ${DB_USER}
  Password: ${DB_PASSWORD}
  URL: postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}

Services:
  Backend: http://localhost:8000
  Frontend: http://localhost:3000
  vLLM: http://localhost:1234

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF

echo -e "${GREEN}📋 Credentials saved to: ${INSTALL_DIR}/CREDENTIALS.txt${NC}"
echo ""
echo -e "${YELLOW}To start the services, run:${NC}"
echo ""
echo -e "${BLUE}1. Start vLLM (if not already running):${NC}"
echo "   tmux new -s vllm"
echo "   vllm serve Qwen/Qwen2.5-1.5B-Instruct --port 1234 --host 0.0.0.0 --trust-remote-code --max-model-len 4096 --gpu-memory-utilization 0.5"
echo "   # Press Ctrl+B then D to detach from tmux"
echo ""
echo -e "${BLUE}2. Start Backend (in new terminal):${NC}"
echo "   cd ${INSTALL_DIR}/backend"
echo "   source venv/bin/activate"
echo "   uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo -e "${BLUE}3. Start Celery Worker (in new terminal):${NC}"
echo "   cd ${INSTALL_DIR}/backend"
echo "   source venv/bin/activate"
echo "   celery -A src.tasks.celery_app worker --loglevel=info"
echo ""
echo -e "${BLUE}4. Start Frontend (in new terminal):${NC}"
echo "   cd ${INSTALL_DIR}/frontend"
echo "   npm run dev"
echo ""
echo -e "${YELLOW}Or use the start script:${NC}"
echo "   ${INSTALL_DIR}/backend/start-services.sh"
echo ""
