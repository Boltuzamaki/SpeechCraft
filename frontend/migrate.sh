#!/bin/bash

# ==============================================================================
# Database Migration Script (UV Version)
#
# This script automates creating and applying Flask-Migrate migrations.
# It works with UV package manager and doesn't require manual venv activation.
#
# Usage:
#   ./migrate.sh
#
# Requirements:
#   - UV package manager installed
#   - pyproject.toml with Flask and Flask-Migrate dependencies
#
# ==============================================================================

# --- Style Definitions ---
COLOR_BLUE='\033[0;34m'
COLOR_GREEN='\033[0;32m'
COLOR_RED='\033[0;31m'
COLOR_YELLOW='\033[1;33m'
COLOR_NC='\033[0m' # No Color

# --- Environment Check ---
# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo -e "${COLOR_RED}Error: UV package manager is not installed or not in PATH.${COLOR_NC}"
    echo -e "Please install UV first: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# Check if pyproject.toml exists
if [ ! -f "pyproject.toml" ]; then
    echo -e "${COLOR_RED}Error: pyproject.toml not found in current directory.${COLOR_NC}"
    echo -e "Please run this script from your project root directory."
    exit 1
fi

echo -e "${COLOR_GREEN}UV package manager detected.${COLOR_NC}"
echo -e "${COLOR_YELLOW}Working directory: $(pwd)${COLOR_NC}"

# --- Main Script ---

# 1. Prompt for a migration message
echo -e "\n${COLOR_BLUE}Please enter a description for the database migration:${COLOR_NC}"
read -p "> " MIGRATION_MESSAGE

# 2. Validate the input
if [ -z "$MIGRATION_MESSAGE" ]; then
    echo -e "\n${COLOR_RED}Error: Migration message cannot be empty. Aborting.${COLOR_NC}"
    exit 1
fi

echo -e "\n${COLOR_BLUE}Step 1: Generating migration file...${COLOR_NC}"

# 3. First, sync dependencies to ensure everything is installed
echo -e "${COLOR_YELLOW}Syncing dependencies...${COLOR_NC}"
uv sync

# 4. Check if migrations folder exists, if not initialize it
if [ ! -d "migrations" ]; then
    echo -e "\n${COLOR_YELLOW}Migrations folder not found. Initializing Flask-Migrate...${COLOR_NC}"
    uv run python -m flask db init
    
    if [ $? -ne 0 ]; then
        echo -e "\n${COLOR_RED}Error: Failed to initialize Flask-Migrate. Please check your Flask app setup.${COLOR_NC}"
        exit 1
    fi
    echo -e "${COLOR_GREEN}✅ Flask-Migrate initialized successfully!${COLOR_NC}"
fi

# 5. Generate the migration file using UV
echo -e "\n${COLOR_BLUE}Generating migration file...${COLOR_NC}"
uv run python -m flask db migrate -m "$MIGRATION_MESSAGE"

# Check if the migration command was successful
if [ $? -ne 0 ]; then
    echo -e "\n${COLOR_RED}Error: 'flask db migrate' failed. Please check the output above. Aborting upgrade.${COLOR_NC}"
    echo -e "\n${COLOR_YELLOW}Troubleshooting tips:${COLOR_NC}"
    echo -e "1. Ensure all dependencies are installed: ${COLOR_GREEN}uv sync${COLOR_NC}"
    echo -e "2. Check that Flask-Migrate is properly configured in your app.py"
    echo -e "3. Verify your database models are properly defined"
    echo -e "4. Make sure your Flask app is importable"
    exit 1
fi

echo -e "\n${COLOR_BLUE}Step 2: Applying migration to the database...${COLOR_NC}"

# 6. Apply the migration to the database using UV
uv run python -m flask db upgrade

# Check if the upgrade command was successful
if [ $? -ne 0 ]; then
    echo -e "\n${COLOR_RED}Error: 'flask db upgrade' failed. The database may be in an inconsistent state. Please review the errors.${COLOR_NC}"
    exit 1
fi

echo -e "\n${COLOR_GREEN}✅ Database migration successful!${COLOR_NC}"
exit 0