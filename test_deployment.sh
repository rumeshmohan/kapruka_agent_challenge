#!/bin/bash
# Quick deployment test script
# Run this locally before pushing to Railway

echo "=========================================="
echo "Railway Deployment Pre-Check"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check 1: Python version
echo -n "Checking Python version... "
python_version=$(python --version 2>&1 | cut -d' ' -f2)
if [[ $(echo "$python_version" | cut -d'.' -f1) -ge 3 ]] && [[ $(echo "$python_version" | cut -d'.' -f2) -ge 10 ]]; then
    echo -e "${GREEN}✓${NC} Python $python_version"
else
    echo -e "${RED}✗${NC} Python $python_version (need >= 3.10)"
    exit 1
fi

# Check 2: Required files exist
echo -n "Checking required files... "
required_files=("Dockerfile" "requirements.txt" "app.py" "main.py" "railway.json" ".dockerignore")
missing_files=()
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -eq 0 ]; then
    echo -e "${GREEN}✓${NC} All required files present"
else
    echo -e "${RED}✗${NC} Missing: ${missing_files[*]}"
    exit 1
fi

# Check 3: Environment variables
echo -n "Checking environment variables... "
if [ -f ".env" ]; then
    source .env
    if [ -n "$OPENAI_API_KEY" ] || [ -n "$GROQ_API_KEY" ] || [ -n "$OPENROUTER_API_KEY" ]; then
        echo -e "${GREEN}✓${NC} API keys found in .env"
    else
        echo -e "${YELLOW}⚠${NC} No API keys in .env (set them in Railway)"
    fi
else
    echo -e "${YELLOW}⚠${NC} No .env file (set keys in Railway Variables)"
fi

# Check 4: Docker installed
echo -n "Checking Docker... "
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker installed"

    # Optional: Build Docker image
    echo ""
    read -p "Do you want to build and test Docker image locally? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Building Docker image..."
        docker build -t kapi-test . || exit 1
        echo -e "${GREEN}✓${NC} Docker build successful"

        echo ""
        echo "To run locally:"
        echo "  docker run -p 8080:8080 -e OPENAI_API_KEY=\$OPENAI_API_KEY kapi-test"
    fi
else
    echo -e "${YELLOW}⚠${NC} Docker not found (optional for local testing)"
fi

# Check 5: Git status
echo ""
echo -n "Checking Git status... "
if git rev-parse --git-dir > /dev/null 2>&1; then
    modified=$(git status --short | wc -l)
    if [ $modified -gt 0 ]; then
        echo -e "${YELLOW}⚠${NC} $modified uncommitted changes"
        echo ""
        echo "Modified files:"
        git status --short
    else
        echo -e "${GREEN}✓${NC} Working tree clean"
    fi
else
    echo -e "${YELLOW}⚠${NC} Not a git repository"
fi

# Check 6: Railway CLI
echo ""
echo -n "Checking Railway CLI... "
if command -v railway &> /dev/null; then
    echo -e "${GREEN}✓${NC} Railway CLI installed"
    echo ""
    echo "To deploy now:"
    echo "  railway up"
else
    echo -e "${YELLOW}⚠${NC} Railway CLI not installed"
    echo ""
    echo "Install with: npm install -g @railway/cli"
fi

echo ""
echo "=========================================="
echo "Pre-Check Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Commit changes: git add . && git commit -m 'Fix Railway crashes'"
echo "2. Push to GitHub: git push origin main"
echo "3. Railway will auto-deploy (if connected to GitHub)"
echo ""
echo "Or deploy via CLI:"
echo "  railway up"
echo ""
echo "Monitor deployment:"
echo "  railway logs --tail 100"
echo ""
