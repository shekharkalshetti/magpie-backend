#!/bin/bash

# ============================================
# Magpie AI - EC2 Setup Script
# ============================================
# Run this on a fresh AWS EC2 G5 instance (Ubuntu 22.04)

set -e

echo "🚀 Setting up Magpie AI on EC2..."

# Install Docker
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# Install NVIDIA Container Toolkit for GPU support
if ! command -v nvidia-container-cli &> /dev/null; then
    echo "🎮 Installing NVIDIA Container Toolkit..."
    distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
    curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
    curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
        sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    
    sudo apt-get update
    sudo apt-get install -y nvidia-container-toolkit
    sudo systemctl restart docker
fi

# Generate secrets if .env doesn't exist
if [ ! -f .env ]; then
    echo "🔐 Generating .env file..."
    cp .env.example .env
    
    # Generate secure random values
    SECRET_KEY=$(openssl rand -hex 32)
    JWT_SECRET=$(openssl rand -hex 32)
    POSTGRES_PASS=$(openssl rand -hex 16)
    ADMIN_PASS=$(openssl rand -base64 16)
    
    # Update .env file
    sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$POSTGRES_PASS/" .env
    sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
    sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET/" .env
    sed -i "s/ADMIN_PASSWORD=.*/ADMIN_PASSWORD=$ADMIN_PASS/" .env
    
    echo "✅ .env file created with secure credentials"
    echo "📝 Admin credentials saved to .env file"
fi

# Build and start containers
echo "🏗️  Building Docker images..."
docker compose build

echo "🚀 Starting services..."
docker compose up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 30

# Check health
echo ""
echo "🏥 Health Check:"
docker compose ps

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📍 Services:"
echo "   - API: http://localhost (via nginx)"
echo "   - API Docs: http://localhost/docs"
echo "   - Health: http://localhost/health"
echo ""
echo "🔑 Admin credentials are in your .env file"
echo ""
echo "📊 View logs:"
echo "   docker compose logs -f api"
echo "   docker compose logs -f llm"
echo "   docker compose logs -f worker"
echo ""
echo "🛑 Stop services:"
echo "   docker compose down"
echo ""
