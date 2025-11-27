#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║        🚀 SaaS BI Agent - Automated Setup Script 🚀           ║"
echo "║                                                               ║"
echo "║    Mannshaft Intelligence - SaaS BI Agent                     ║"
echo "║    Multi-Agent Intelligence Platform Setup                    ║"
echo "║    Google Gemini 2.0 Flash - Kaggle Competition               ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Check if Python 3.11+ is installed
echo -e "${BLUE}Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.11 or higher.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then 
    echo -e "${RED}❌ Python version $PYTHON_VERSION found. Requires Python 3.11 or higher.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python $PYTHON_VERSION found${NC}"
echo ""

# Check if Node.js is installed
echo -e "${BLUE}Checking Node.js version...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed. Please install Node.js 18 or higher.${NC}"
    exit 1
fi

NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo -e "${RED}❌ Node.js version $NODE_VERSION found. Requires Node.js 18 or higher.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Node.js $(node --version) found${NC}"
echo ""

# ============================================================================
# STEP 1: Collect User Inputs
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  STEP 1: Configuration"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Gemini API Key
echo -e "${YELLOW}📝 Please enter your Gemini API Key:${NC}"
echo "   (Get one from: https://aistudio.google.com/app/apikey)"
read -p "   API Key: " GEMINI_API_KEY

if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${RED}❌ Gemini API Key is required!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Gemini API Key saved${NC}"
echo ""

# Google Service Account Credentials
echo -e "${YELLOW}📝 Please provide your Google Service Account credentials:${NC}"
echo "   You can either:"
echo "   1. Paste the JSON content directly"
echo "   2. Provide a path to the JSON file"
echo ""
read -p "   Choose option (1 or 2): " CRED_OPTION

if [ "$CRED_OPTION" == "1" ]; then
    echo "   Paste your JSON credentials (press Ctrl+D when done):"
    GOOGLE_CREDS=$(cat)
    CREDS_PATH="backend/config/google-credentials.json"
    mkdir -p backend/config
    echo "$GOOGLE_CREDS" > "$CREDS_PATH"
elif [ "$CRED_OPTION" == "2" ]; then
    read -p "   Path to credentials JSON: " CREDS_INPUT_PATH
    if [ ! -f "$CREDS_INPUT_PATH" ]; then
        echo -e "${RED}❌ Credentials file not found at: $CREDS_INPUT_PATH${NC}"
        exit 1
    fi
    CREDS_PATH="backend/config/google-credentials.json"
    mkdir -p backend/config
    cp "$CREDS_INPUT_PATH" "$CREDS_PATH"
else
    echo -e "${RED}❌ Invalid option. Please choose 1 or 2.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Google credentials saved${NC}"
echo ""

# User ID (optional, for demo)
echo -e "${YELLOW}📝 Enter a user ID for demo purposes (default: demo_user):${NC}"
read -p "   User ID: " USER_ID
USER_ID=${USER_ID:-demo_user}

echo ""

# ============================================================================
# STEP 2: Backend Setup
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  STEP 2: Setting Up Backend"
echo "═══════════════════════════════════════════════════════════════"
echo ""

cd backend

# Create virtual environment
echo -e "${BLUE}📦 Creating Python virtual environment...${NC}"
python3 -m venv venv

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

echo -e "${GREEN}✅ Virtual environment created${NC}"

# Install dependencies
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Python dependencies installed${NC}"
else
    echo -e "${RED}❌ Failed to install Python dependencies${NC}"
    exit 1
fi

echo ""

# ============================================================================
# STEP 3: Create and Populate Google Sheets
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  STEP 3: Creating Google Sheets with Synthetic Data"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo -e "${BLUE}🔧 Running Google Sheets setup script...${NC}"
echo "   This will:"
echo "   • Create 3 Google Sheets (Revenue, Product, Support)"
echo "   • Populate with 12 weeks of synthetic SaaS data"
echo "   • Share with your service account"
echo "   • Return sheet IDs for configuration"
echo ""

# Run the setup script
python3 ../scripts/setup_google_sheets.py "$CREDS_PATH"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Google Sheets created and populated${NC}"
    
    # Read the generated sheet IDs
    if [ -f "../.sheet_ids.tmp" ]; then
        source ../.sheet_ids.tmp
        rm ../.sheet_ids.tmp
    else
        echo -e "${RED}❌ Failed to retrieve sheet IDs${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Failed to create Google Sheets${NC}"
    exit 1
fi

echo ""

# ============================================================================
# STEP 4: Create Backend .env File
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  STEP 4: Configuring Backend Environment"
echo "═══════════════════════════════════════════════════════════════"
echo ""

cat > .env << EOF
# Gemini API Configuration
GEMINI_API_KEY=$GEMINI_API_KEY
GEMINI_MODEL=gemini-2.0-flash-exp

# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_PATH=config/google-credentials.json
REVENUE_SHEET_ID=$REVENUE_SHEET_ID
PRODUCT_SHEET_ID=$PRODUCT_SHEET_ID
SUPPORT_SHEET_ID=$SUPPORT_SHEET_ID

# Database Configuration
DATABASE_URL=sqlite:///data/agent_cache.db

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True
LOG_LEVEL=INFO

# CORS Configuration (for frontend)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000

# Demo Configuration
USER_ID=$USER_ID
HITL_MODE=demo
AUTO_APPROVE_DELAY_SECONDS=2

# Cache Configuration
CACHE_TTL_PROMPTS_HOURS=168
CACHE_TTL_AGENTS_HOURS=24
CACHE_TTL_EVALUATIONS_HOURS=168

# Performance Configuration
MAX_CONCURRENT_AGENTS=3
AGENT_TIMEOUT_SECONDS=30
EOF

echo -e "${GREEN}✅ Backend .env file created${NC}"

# Create data directory
mkdir -p data
echo -e "${GREEN}✅ Data directory created${NC}"

# Initialize database
echo -e "${BLUE}🗄️  Initializing SQLite database...${NC}"
python3 ../scripts/init_database.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database initialized${NC}"
else
    echo -e "${YELLOW}⚠️  Database initialization failed (will retry on first run)${NC}"
fi

cd ..

echo ""

# ============================================================================
# STEP 5: Frontend Setup
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  STEP 5: Setting Up Frontend"
echo "═══════════════════════════════════════════════════════════════"
echo ""

cd frontend

echo -e "${BLUE}📦 Installing Node.js dependencies...${NC}"
npm install > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Node.js dependencies installed${NC}"
else
    echo -e "${RED}❌ Failed to install Node.js dependencies${NC}"
    exit 1
fi

# Create frontend .env.local
cat > .env.local << EOF
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Analytics (optional)
NEXT_PUBLIC_VERCEL_ANALYTICS_ID=

# Demo Mode
NEXT_PUBLIC_USER_ID=$USER_ID
EOF

echo -e "${GREEN}✅ Frontend .env.local file created${NC}"

cd ..

echo ""

# ============================================================================
# STEP 6: Create Helper Scripts
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  STEP 6: Creating Helper Scripts"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Create start script
cat > start.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting SaaS BI Agent System..."
echo ""

# Start backend
echo "📊 Starting Backend Server (Port 8000)..."
cd backend
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi
uvicorn api.main:app --reload --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

echo "✅ Backend started (PID: $BACKEND_PID)"

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
sleep 5

# Start frontend
echo "🎨 Starting Frontend Server (Port 3000)..."
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo "✅ Frontend started (PID: $FRONTEND_PID)"
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║  ✅ System is running!                                        ║"
echo "║                                                               ║"
echo "║  Frontend:  http://localhost:3000                            ║"
echo "║  Backend:   http://localhost:8000                            ║"
echo "║  API Docs:  http://localhost:8000/docs                       ║"
echo "║                                                               ║"
echo "║  Logs:      tail -f logs/backend.log                         ║"
echo "║             tail -f logs/frontend.log                        ║"
echo "║                                                               ║"
echo "║  To stop:   ./stop.sh                                        ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Save PIDs
echo "BACKEND_PID=$BACKEND_PID" > .pids
echo "FRONTEND_PID=$FRONTEND_PID" >> .pids
EOF

chmod +x start.sh

# Create stop script
cat > stop.sh << 'EOF'
#!/bin/bash

echo "🛑 Stopping SaaS BI Agent System..."

if [ -f .pids ]; then
    source .pids
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "✅ Backend stopped"
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "✅ Frontend stopped"
    fi
    
    rm .pids
else
    echo "⚠️  No running processes found"
    # Fallback: kill by port
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    lsof -ti:3000 | xargs kill -9 2>/dev/null
fi

echo "✅ System stopped"
EOF

chmod +x stop.sh

# Create logs directory
mkdir -p logs

echo -e "${GREEN}✅ Helper scripts created${NC}"
echo ""

# ============================================================================
# STEP 7: Test Configuration
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  STEP 7: Testing Configuration"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo -e "${BLUE}🧪 Running configuration tests...${NC}"

cd backend
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate

python3 << PYEOF
import sys
import os
from pathlib import Path

# Test Gemini API Key
api_key = os.getenv('GEMINI_API_KEY', '$GEMINI_API_KEY')
if api_key and len(api_key) > 20:
    print("✅ Gemini API Key: Valid format")
else:
    print("❌ Gemini API Key: Invalid")
    sys.exit(1)

# Test Google Credentials
creds_path = Path("config/google-credentials.json")
if creds_path.exists():
    print("✅ Google Credentials: File exists")
    try:
        import json
        with open(creds_path) as f:
            creds = json.load(f)
        if 'client_email' in creds and 'private_key' in creds:
            print(f"✅ Service Account Email: {creds['client_email']}")
        else:
            print("❌ Google Credentials: Invalid format")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Google Credentials: {e}")
        sys.exit(1)
else:
    print("❌ Google Credentials: File not found")
    sys.exit(1)

# Test Database
db_path = Path("data/agent_cache.db")
if db_path.exists():
    print("✅ Database: Initialized")
else:
    print("⚠️  Database: Will be created on first run")

print("\n✅ All configuration tests passed!")
PYEOF

cd ..

echo ""

# ============================================================================
# COMPLETION SUMMARY
# ============================================================================

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║              ✅ SETUP COMPLETED SUCCESSFULLY! ✅              ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "📋 SETUP SUMMARY"
echo "─────────────────────────────────────────────────────────────────"
echo ""
echo "✅ Backend configured with:"
echo "   • Gemini API Key: ****${GEMINI_API_KEY: -8}"
echo "   • Database: SQLite (data/agent_cache.db)"
echo "   • Google Sheets: 3 sheets created with synthetic data"
echo ""
echo "✅ Frontend configured with:"
echo "   • Next.js with TypeScript"
echo "   • Connected to backend at http://localhost:8000"
echo ""
echo "✅ Google Sheets Created:"
echo "   • Revenue Data: https://docs.google.com/spreadsheets/d/$REVENUE_SHEET_ID"
echo "   • Product Data: https://docs.google.com/spreadsheets/d/$PRODUCT_SHEET_ID"
echo "   • Support Data: https://docs.google.com/spreadsheets/d/$SUPPORT_SHEET_ID"
echo ""
echo "─────────────────────────────────────────────────────────────────"
echo ""
echo "🚀 QUICK START"
echo ""
echo "1. Start the system:"
echo "   ./start.sh"
echo ""
echo "2. Open your browser:"
echo "   http://localhost:3000"
echo ""
echo "3. Stop the system:"
echo "   ./stop.sh"
echo ""
echo "─────────────────────────────────────────────────────────────────"
echo ""
echo "📚 NEXT STEPS"
echo ""
echo "1. Review the architecture:"
echo "   • docs/ARCHITECTURE_MERMAID.md"
echo "   • docs/CACHE_README.md"
echo ""
echo "2. Explore the API:"
echo "   • http://localhost:8000/docs (Swagger UI)"
echo ""
echo "3. Test the system:"
echo "   • Trigger Week 8 Analysis from the dashboard"
echo "   • Monitor agent performance and cache efficiency"
echo ""
echo "─────────────────────────────────────────────────────────────────"
echo ""
echo "💡 TIPS"
echo ""
echo "• All logs are in the logs/ directory"
echo "• Cache database is in backend/data/agent_cache.db"
echo "• Configuration files: backend/.env and frontend/.env.local"
echo ""
echo "🎉 Happy analyzing! Your SaaS BI Agent is ready to use."
echo ""