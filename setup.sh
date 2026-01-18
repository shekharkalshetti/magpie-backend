#!/bin/bash
# End-to-End Setup Script for Triton
# This script sets up the complete project from scratch

set -e  # Exit on error

echo "=========================================="
echo "TRITON - END-TO-END SETUP"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check prerequisites
echo -e "\n${YELLOW}Step 1: Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.11+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}"

if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}⚠ PostgreSQL client not found. You'll need a PostgreSQL database.${NC}"
else
    echo -e "${GREEN}✓ PostgreSQL client found${NC}"
fi

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker Desktop${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker is not running. Please start Docker Desktop${NC}"
    exit 1
fi

# Step 1.5: Setup PostgreSQL in Docker (clean setup)
echo -e "\n${YELLOW}Step 1.5: Setting up PostgreSQL database...${NC}"

# Remove existing container for clean setup
if docker ps -a | grep -q triton-postgres; then
    echo "Removing existing triton-postgres container for clean setup..."
    docker rm -f triton-postgres > /dev/null 2>&1
    echo -e "${GREEN}✓ Old container removed${NC}"
fi

echo "Creating fresh PostgreSQL container..."
docker run -d \
    --name triton-postgres \
    -e POSTGRES_USER=triton \
    -e POSTGRES_PASSWORD=tritonpass \
    -e POSTGRES_DB=triton \
    -p 5432:5432 \
    postgres:15

echo "Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if docker exec triton-postgres pg_isready -U triton > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PostgreSQL is ready${NC}"
        break
    fi
    echo -n "."
    sleep 1
done
echo -e "${GREEN}✓ PostgreSQL container created and running${NC}"

# Step 2: Install backend dependencies
echo -e "\n${YELLOW}Step 2: Installing backend dependencies...${NC}"
cd backend
python3 -m pip install -r requirements.txt
echo -e "${GREEN}✓ Backend dependencies installed${NC}"

# Step 3: Install SDK
echo -e "\n${YELLOW}Step 3: Installing SDK...${NC}"
cd ../sdk
python3 -m pip install -e .
echo -e "${GREEN}✓ SDK installed in development mode${NC}"

# Step 4: Setup environment variables
echo -e "\n${YELLOW}Step 4: Setting up environment...${NC}"
cd ../backend

if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    
    # Generate a random secret key
    SECRET_KEY=$(openssl rand -hex 32)
    
    # Create .env with PostgreSQL connection string
    cat > .env << EOF
DATABASE_URL=postgresql://triton:tritonpass@localhost:5432/triton
SECRET_KEY=$SECRET_KEY
EOF
    
    echo -e "${GREEN}✓ .env file created with database connection${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Load DATABASE_URL from .env
export DATABASE_URL=$(grep "^DATABASE_URL=" .env | cut -d'=' -f2-)

# Step 5: Initialize database & create test project
echo -e "\n${YELLOW}Step 5: Initializing database & creating test project...${NC}"

# Already in backend directory from Step 4

# Test database connection
if ! python3 -c "import logging; logging.basicConfig(level=logging.ERROR); from src.database import engine; engine.connect()" 2>/dev/null; then
    echo -e "${RED}❌ Could not connect to database${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Database connection successful${NC}"

# Create all database tables
echo "Creating database tables..."
python3 -c "from src.database import create_tables; create_tables()"
echo -e "${GREEN}✓ Database tables created${NC}"

# Create test project
echo "Creating test project..."
PROJECT_ID=$(python3 -m scripts.create_project \
    --name "Triton Test Project" \
    --description "Default test project" 2>&1 | grep -E '^[a-f0-9-]{36}$' | head -1)

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Failed to create project. Here's the error:${NC}"
    python3 -m scripts.create_project \
        --name "Triton Test Project" \
        --description "Default test project"
    exit 1
fi

echo -e "${GREEN}✓ Database initialized${NC}"
echo -e "${GREEN}✓ Test project created: $PROJECT_ID${NC}"

# Step 6: Seed admin user
echo -e "\n${YELLOW}Step 6: Seeding admin user...${NC}"

# Still in backend directory

# Generate random admin password (max 72 chars for bcrypt compatibility)
# Using openssl rand with base64 but limited to safe length
ADMIN_PASSWORD=$(openssl rand -base64 12 | tr -d '\n' | cut -c1-20)
ADMIN_EMAIL="admin@triton.local"
ADMIN_NAME="Admin User"

echo "Creating admin user with email: $ADMIN_EMAIL"

python3 -m scripts.seed_admin_user \
    --project-id "$PROJECT_ID" \
    --admin-email "$ADMIN_EMAIL" \
    --admin-name "$ADMIN_NAME" \
    --admin-password "$ADMIN_PASSWORD"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Admin user created${NC}"
    echo -e "${GREEN}  Email:    $ADMIN_EMAIL${NC}"
    echo -e "${GREEN}  Password: $ADMIN_PASSWORD${NC}"
else
    echo -e "${RED}❌ Failed to seed admin user${NC}"
    echo -e "${RED}The error message is shown above. Please fix and try again.${NC}"
    exit 1
fi

# Step 7: Generate API key
echo -e "\n${YELLOW}Step 7: Generating API key...${NC}"

# Still in backend directory

API_KEY=$(python3 -m scripts.generate_api_key \
    --project-id "$PROJECT_ID" \
    --name "Smoke Test Key" 2>&1 | grep -E '^tr_[A-Za-z0-9]{32}$' | head -1)

if [ -z "$API_KEY" ]; then
    echo -e "${RED}❌ Failed to generate API key${NC}"
    exit 1
fi

echo -e "${GREEN}✓ API key generated${NC}"

# Go back to project root for .env.test file
cd ..

# Step 8: Create environment file for examples
echo -e "\n${YELLOW}Step 8: Creating environment file for examples...${NC}"
cat > .env.test << EOF
# Triton Configuration for Smoke Test

# Backend & Project
TRITON_BACKEND_URL=http://localhost:8000
TRITON_PROJECT_ID=$PROJECT_ID

# SDK Authentication (API Key)
TRITON_API_KEY=$API_KEY

# Portal Authentication (User Login)
ADMIN_EMAIL=$ADMIN_EMAIL
ADMIN_PASSWORD=$ADMIN_PASSWORD
EOF

echo -e "${GREEN}✓ Environment file created: .env.test${NC}"

# Step 9: Show summary
echo -e "\n=========================================="
echo -e "${GREEN}SETUP COMPLETE!${NC}"
echo "=========================================="
echo ""
echo "Your Triton project is ready. Here's what was created:"
echo ""
echo "Project ID:       $PROJECT_ID"
echo "API Key:          $API_KEY"
echo ""
echo "Admin Credentials:"
echo "  Email:          $ADMIN_EMAIL"
echo "  Password:       $ADMIN_PASSWORD"
echo ""
echo "=========================================="
echo "NEXT STEPS:"
echo "=========================================="
echo ""
echo "1. Start the backend server:"
echo "   cd backend"
echo "   uvicorn src.main:app --reload"
echo ""
echo "2. In a new terminal, start the frontend:"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "3. Open the dashboard:"
echo "   http://localhost:3000"
echo ""
echo "4. Login to portal with admin credentials:"
echo "   Email:    $ADMIN_EMAIL"
echo "   Password: $ADMIN_PASSWORD"
echo ""
echo "5. Use the SDK with automatic observability:"
echo ""
echo "   from triton import monitor"
echo ""
echo "   @monitor("
echo "       project_id='$PROJECT_ID',"
echo "       model='gpt-4',  # or use input_token_price/output_token_price"
echo "       pii=True,               # Enable PII redaction"
echo "       content_moderation=True,# Enable policy-based moderation"
echo "       custom={'user_id': '123', 'session': 'abc'}  # Custom metadata"
echo "   )"
echo "   def my_llm_function(prompt: str) -> str:"
echo "       # Your LLM code here"
echo "       ..."
echo ""
echo "6. Verify logs were created:"
echo "   curl -H \"Authorization: Bearer $API_KEY\" \\"
echo "        http://localhost:8000/api/v1/logs?project_id=$PROJECT_ID"
echo ""
echo "Credentials saved to: .env.test"
echo ""
