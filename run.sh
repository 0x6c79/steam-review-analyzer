#!/bin/bash
# Steam Review Analyzer - Startup Script

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment if exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo -e "${RED}Error: Python not found${NC}"
    exit 1
fi

# Function to show menu
show_menu() {
    clear
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Steam Review Analyzer${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "1. 🚀 Launch Dashboard (Streamlit)"
    echo "2. 📊 Run Analysis"
    echo "3. 🕷️ Scrape Reviews"
    echo "4. 📥 Import CSV to Database"
    echo "5. 📤 Export Data"
    echo "6. 📈 View Statistics"
    echo "7. 🧪 Run Tests"
    echo "8. ❌ Exit"
    echo ""
}

# Function to launch dashboard
launch_dashboard() {
    echo -e "${YELLOW}Launching Dashboard...${NC}"
    python -m src.steam_review.cli.cli dashboard
}

# Function to run analysis
run_analysis() {
    echo -e "${YELLOW}Running analysis...${NC}"
    python -m src.steam_review.cli.cli analyze
}

# Function to scrape reviews
scrape_reviews() {
    echo -n "Enter Steam App ID: "
    read app_id
    echo -n "Enter review limit (default: 1000): "
    read limit
    limit=${limit:-1000}
    
    echo -e "${YELLOW}Scraping reviews for App ID: $app_id${NC}"
    python -m src.steam_review.cli.cli scrape --app_id "$app_id" --limit "$limit"
}

# Function to import CSV
import_csv() {
    echo ""
    echo -e "${YELLOW}CSV Import Options${NC}"
    echo "1. Import all CSV files from data/ directory"
    echo "2. Import specific CSV file"
    echo ""
    echo -n "Select option (1-2): "
    read import_option
    
    case $import_option in
        1)
            echo -e "${YELLOW}Importing all CSV files to database...${NC}"
            python -m src.steam_review.storage.auto_import
            ;;
        2)
            echo -n "Enter path to CSV file: "
            read csv_path
            if [ -f "$csv_path" ]; then
                echo -e "${YELLOW}Importing CSV: $csv_path${NC}"
                python -m src.steam_review.cli.cli import --csv "$csv_path"
            else
                echo -e "${RED}Error: File not found - $csv_path${NC}"
            fi
            ;;
        *)
            echo -e "${RED}Invalid option${NC}"
            ;;
    esac
}

# Function to export data
export_data() {
    echo -e "${YELLOW}Exporting data...${NC}"
    python -m src.steam_review.cli.cli export --help
}

# Function to view stats
view_stats() {
    echo -e "${YELLOW}Viewing statistics...${NC}"
    python -m src.steam_review.cli.cli stats
}

# Function to run tests
run_tests() {
    echo -e "${YELLOW}Running tests...${NC}"
    pytest src/tests/ -v
}

# Main loop
while true; do
    show_menu
    echo -n "Select option: "
    read choice
    
    case $choice in
        1) launch_dashboard ;;
        2) run_analysis ;;
        3) scrape_reviews ;;
        4) import_csv ;;
        5) export_data ;;
        6) view_stats ;;
        7) run_tests ;;
        8) 
            echo -e "${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        *) 
            echo -e "${RED}Invalid option${NC}"
            sleep 1
            ;;
    esac
    
    echo ""
    echo -n "Press Enter to continue..."
    read
done
