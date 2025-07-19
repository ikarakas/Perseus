#!/bin/bash
# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0

# Real-Time Git Repository Monitor (Bash Version)
# ==============================================
# Simple shell script to monitor Git repository changes in real-time

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
INTERVAL=${1:-1}  # Default 1 second interval
REPO_PATH=${2:-.} # Default current directory

# Check if we're in a git repository
if ! git -C "$REPO_PATH" rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Not a Git repository: $REPO_PATH${NC}"
    exit 1
fi

echo -e "${GREEN}🔍 Monitoring Git repository: $(realpath "$REPO_PATH")${NC}"
echo -e "${BLUE}📊 Refresh interval: ${INTERVAL}s${NC}"
echo -e "${CYAN}Press Ctrl+C to stop monitoring${NC}"
echo ""

# Initialize state
last_status=""
last_branch=""
last_commit=""

# Function to get current branch
get_current_branch() {
    git -C "$REPO_PATH" branch --show-current 2>/dev/null || echo "detached HEAD"
}

# Function to get current commit
get_current_commit() {
    git -C "$REPO_PATH" rev-parse --short HEAD 2>/dev/null || echo "unknown"
}

# Function to get git status
get_git_status() {
    git -C "$REPO_PATH" status --porcelain 2>/dev/null
}

# Function to display status
display_status() {
    local status="$1"
    local branch="$2"
    local commit="$3"
    local timestamp=$(date "+%H:%M:%S")
    
    # Clear screen
    clear
    
    # Header
    echo -e "${BOLD}${BLUE}============================================================${NC}"
    echo -e "${BOLD}${BLUE}Git Repository Monitor - $timestamp${NC}"
    echo -e "${BOLD}${BLUE}============================================================${NC}"
    echo -e "${CYAN}Repository: $(realpath "$REPO_PATH")${NC}"
    echo -e "${CYAN}Branch: $branch ($commit)${NC}"
    echo ""
    
    # Check for branch changes
    if [ -n "$last_branch" ] && [ "$last_branch" != "$branch" ]; then
        echo -e "${MAGENTA}🔄 Branch changed: $last_branch → $branch${NC}"
        echo ""
    fi
    
    # Check for new commits
    if [ -n "$last_commit" ] && [ "$last_commit" != "$commit" ]; then
        echo -e "${MAGENTA}📝 New commit: $last_commit → $commit${NC}"
        echo ""
    fi
    
    if [ -z "$status" ]; then
        echo -e "${GREEN}✅ Repository is clean - no changes detected${NC}"
    else
        # Parse and display status
        local modified_files=""
        local added_files=""
        local deleted_files=""
        local untracked_files=""
        local staged_files=""
        
        while IFS= read -r line; do
            if [ -z "$line" ]; then continue; fi
            
            local index_status="${line:0:1}"
            local work_status="${line:1:1}"
            local filepath="${line:3}"
            
            case "$work_status" in
                "M") modified_files="${modified_files}  ${YELLOW}• $filepath${NC}\n";;
                "D") deleted_files="${deleted_files}  ${RED}• $filepath${NC}\n";;
                "?") untracked_files="${untracked_files}  ${MAGENTA}• $filepath${NC}\n";;
            esac
            
            case "$index_status" in
                "A") added_files="${added_files}  ${GREEN}• $filepath${NC}\n";;
                "M"|"R"|"C") staged_files="${staged_files}  ${BLUE}• $index_status $filepath${NC}\n";;
            esac
        done <<< "$status"
        
        # Display sections
        if [ -n "$modified_files" ]; then
            echo -e "${YELLOW}${BOLD}📝 Modified files:${NC}"
            echo -e "$modified_files"
        fi
        
        if [ -n "$added_files" ]; then
            echo -e "${GREEN}${BOLD}➕ Added files:${NC}"
            echo -e "$added_files"
        fi
        
        if [ -n "$deleted_files" ]; then
            echo -e "${RED}${BOLD}🗑️  Deleted files:${NC}"
            echo -e "$deleted_files"
        fi
        
        if [ -n "$staged_files" ]; then
            echo -e "${BLUE}${BOLD}📦 Staged changes:${NC}"
            echo -e "$staged_files"
        fi
        
        if [ -n "$untracked_files" ]; then
            echo -e "${MAGENTA}${BOLD}❓ Untracked files:${NC}"
            echo -e "$untracked_files"
        fi
        
        # Show recent diff for first modified file
        local first_modified=$(echo "$status" | grep "^.M" | head -1 | cut -c4-)
        if [ -n "$first_modified" ]; then
            echo -e "${BOLD}${YELLOW}📋 Recent changes in $first_modified:${NC}"
            git -C "$REPO_PATH" diff --color=always "$first_modified" 2>/dev/null | head -20
            echo ""
        fi
        
        # Summary
        local total_changes=$(echo "$status" | wc -l | tr -d ' ')
        echo -e "${YELLOW}📊 Total changes: $total_changes files${NC}"
    fi
    
    echo ""
    echo -e "${CYAN}Last updated: $timestamp | Press Ctrl+C to stop${NC}"
}

# Function to detect changes
detect_changes() {
    local current_status="$1"
    local current_branch="$2"
    local current_commit="$3"
    
    local changes=""
    
    # Check if status changed
    if [ "$last_status" != "$current_status" ]; then
        changes="${changes}Status changed\n"
    fi
    
    # Check if branch changed
    if [ -n "$last_branch" ] && [ "$last_branch" != "$current_branch" ]; then
        changes="${changes}Branch changed: $last_branch → $current_branch\n"
    fi
    
    # Check if commit changed
    if [ -n "$last_commit" ] && [ "$last_commit" != "$current_commit" ]; then
        changes="${changes}New commit: $last_commit → $current_commit\n"
    fi
    
    if [ -n "$changes" ]; then
        echo -e "\n${BOLD}${GREEN}🔔 Changes detected:${NC}"
        echo -e "$changes"
    fi
}

# Trap Ctrl+C
trap 'echo -e "\n${YELLOW}👋 Monitoring stopped by user${NC}"; exit 0' INT

# Initial state
last_branch=$(get_current_branch)
last_commit=$(get_current_commit)
last_status=$(get_git_status)

# Main monitoring loop
while true; do
    current_status=$(get_git_status)
    current_branch=$(get_current_branch)
    current_commit=$(get_current_commit)
    
    # Always display current status
    display_status "$current_status" "$current_branch" "$current_commit"
    
    # Detect and show changes
    detect_changes "$current_status" "$current_branch" "$current_commit"
    
    # Update state
    last_status="$current_status"
    last_branch="$current_branch"
    last_commit="$current_commit"
    
    sleep "$INTERVAL"
done
