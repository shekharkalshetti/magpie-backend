#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

INSTALL_DIR="${HOME}/magpie"

echo -e "${BLUE}🚀 Starting Magpie Services${NC}"
echo ""

# Function to check if a service is running in tmux
check_tmux_session() {
    tmux has-session -t "$1" 2>/dev/null
}

# Start vLLM
if ! check_tmux_session "vllm"; then
    echo -e "${YELLOW}Starting vLLM...${NC}"
    tmux new-session -d -s vllm "vllm serve Qwen/Qwen2.5-1.5B-Instruct --port 1234 --host 0.0.0.0 --trust-remote-code --max-model-len 4096 --gpu-memory-utilization 0.5"
    echo -e "${GREEN}✅ vLLM started in tmux session 'vllm'${NC}"
else
    echo -e "${GREEN}✅ vLLM already running${NC}"
fi

sleep 5

# Start Backend
if ! check_tmux_session "backend"; then
    echo -e "${YELLOW}Starting Backend...${NC}"
    tmux new-session -d -s backend "cd ${INSTALL_DIR}/backend && source venv/bin/activate && uvicorn src.main:app --host 0.0.0.0 --port 8000"
    echo -e "${GREEN}✅ Backend started in tmux session 'backend'${NC}"
else
    echo -e "${GREEN}✅ Backend already running${NC}"
fi

# Start Celery Worker
if ! check_tmux_session "celery"; then
    echo -e "${YELLOW}Starting Celery Worker...${NC}"
    tmux new-session -d -s celery "cd ${INSTALL_DIR}/backend && source venv/bin/activate && celery -A src.tasks.celery_app worker --loglevel=info"
    echo -e "${GREEN}✅ Celery Worker started in tmux session 'celery'${NC}"
else
    echo -e "${GREEN}✅ Celery Worker already running${NC}"
fi

# Start Frontend
if ! check_tmux_session "frontend"; then
    echo -e "${YELLOW}Starting Frontend...${NC}"
    tmux new-session -d -s frontend "cd ${INSTALL_DIR}/frontend && npm run dev"
    echo -e "${GREEN}✅ Frontend started in tmux session 'frontend'${NC}"
else
    echo -e "${GREEN}✅ Frontend already running${NC}"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ All services started!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Access the services at:${NC}"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  vLLM: http://localhost:1234"
echo ""
echo -e "${YELLOW}View logs:${NC}"
echo "  tmux attach -t vllm      # vLLM logs"
echo "  tmux attach -t backend   # Backend logs"
echo "  tmux attach -t celery    # Celery logs"
echo "  tmux attach -t frontend  # Frontend logs"
echo ""
echo -e "${YELLOW}Stop services:${NC}"
echo "  tmux kill-session -t vllm"
echo "  tmux kill-session -t backend"
echo "  tmux kill-session -t celery"
echo "  tmux kill-session -t frontend"
echo ""
echo -e "${YELLOW}Admin credentials:${NC}"
echo "  cat ${INSTALL_DIR}/CREDENTIALS.txt"
echo ""
