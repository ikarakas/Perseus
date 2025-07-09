#!/usr/bin/env python3
"""
Real-Time Git Repository Monitor
===============================

This script monitors your Git repository in real-time and displays changes
as they happen. Perfect for watching how external applications modify your codebase.

Features:
- Real-time file change detection
- Git status monitoring
- Diff display for modified files
- Branch change detection
- Colored output for better visibility
- Configurable refresh intervals
"""

import subprocess
import time
import os
import sys
from pathlib import Path
from datetime import datetime
import argparse
from typing import Dict, List, Set, Optional
import threading
import signal

class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class GitMonitor:
    """Real-time Git repository monitor"""
    
    def __init__(self, repo_path: str = ".", interval: float = 1.0, show_diffs: bool = True):
        self.repo_path = Path(repo_path).resolve()
        self.interval = interval
        self.show_diffs = show_diffs
        self.running = True
        self.last_status = {}
        self.last_branch = ""
        self.last_commit = ""
        
        # Check if we're in a Git repository
        if not self._is_git_repo():
            print(f"{Colors.RED}❌ Not a Git repository: {self.repo_path}{Colors.END}")
            sys.exit(1)
            
        print(f"{Colors.GREEN}🔍 Monitoring Git repository: {self.repo_path}{Colors.END}")
        print(f"{Colors.BLUE}📊 Refresh interval: {interval}s{Colors.END}")
        print(f"{Colors.CYAN}Press Ctrl+C to stop monitoring{Colors.END}\n")
        
    def _is_git_repo(self) -> bool:
        """Check if the current directory is a Git repository"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _run_git_command(self, cmd: List[str]) -> Optional[str]:
        """Run a Git command and return output"""
        try:
            result = subprocess.run(
                ["git"] + cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return None
    
    def _get_current_branch(self) -> str:
        """Get the current Git branch"""
        branch = self._run_git_command(["branch", "--show-current"])
        return branch or "detached HEAD"
    
    def _get_current_commit(self) -> str:
        """Get the current commit hash"""
        commit = self._run_git_command(["rev-parse", "HEAD"])
        return commit[:8] if commit else "unknown"
    
    def _get_git_status(self) -> Dict[str, List[str]]:
        """Get Git status information"""
        status_output = self._run_git_command(["status", "--porcelain=v1"])
        if not status_output:
            return {}
        
        status = {
            'modified': [],
            'added': [],
            'deleted': [],
            'renamed': [],
            'untracked': [],
            'staged': []
        }
        
        for line in status_output.split('\n'):
            if len(line) < 3:
                continue
                
            index_status = line[0]
            worktree_status = line[1]
            filepath = line[3:]
            
            # Staged changes
            if index_status != ' ':
                status['staged'].append(f"{index_status} {filepath}")
            
            # Working tree changes
            if worktree_status == 'M':
                status['modified'].append(filepath)
            elif worktree_status == 'D':
                status['deleted'].append(filepath)
            elif worktree_status == '?':
                status['untracked'].append(filepath)
            elif index_status == 'A':
                status['added'].append(filepath)
            elif index_status == 'R':
                status['renamed'].append(filepath)
        
        return status
    
    def _get_file_diff(self, filepath: str) -> str:
        """Get diff for a specific file"""
        diff_output = self._run_git_command(["diff", filepath])
        return diff_output or ""
    
    def _get_staged_diff(self, filepath: str) -> str:
        """Get staged diff for a specific file"""
        diff_output = self._run_git_command(["diff", "--cached", filepath])
        return diff_output or ""
    
    def _format_diff(self, diff: str, max_lines: int = 20) -> str:
        """Format diff output with colors and line limits"""
        if not diff:
            return ""
        
        lines = diff.split('\n')
        formatted_lines = []
        
        for i, line in enumerate(lines[:max_lines]):
            if line.startswith('+++') or line.startswith('---'):
                formatted_lines.append(f"{Colors.BOLD}{line}{Colors.END}")
            elif line.startswith('+'):
                formatted_lines.append(f"{Colors.GREEN}{line}{Colors.END}")
            elif line.startswith('-'):
                formatted_lines.append(f"{Colors.RED}{line}{Colors.END}")
            elif line.startswith('@@'):
                formatted_lines.append(f"{Colors.CYAN}{line}{Colors.END}")
            else:
                formatted_lines.append(line)
        
        if len(lines) > max_lines:
            formatted_lines.append(f"{Colors.YELLOW}... ({len(lines) - max_lines} more lines){Colors.END}")
        
        return '\n'.join(formatted_lines)
    
    def _print_status_section(self, title: str, files: List[str], color: str):
        """Print a section of the status report"""
        if files:
            print(f"{color}{Colors.BOLD}{title}:{Colors.END}")
            for file in files:
                print(f"  {color}• {file}{Colors.END}")
            print()
    
    def _display_changes(self, status: Dict[str, List[str]]):
        """Display the current repository status"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        branch = self._get_current_branch()
        commit = self._get_current_commit()
        
        # Clear screen for real-time effect
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}Git Repository Monitor - {timestamp}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.CYAN}Repository: {self.repo_path}{Colors.END}")
        print(f"{Colors.CYAN}Branch: {branch} ({commit}){Colors.END}")
        print()
        
        # Check for branch changes
        if self.last_branch and self.last_branch != branch:
            print(f"{Colors.MAGENTA}🔄 Branch changed: {self.last_branch} → {branch}{Colors.END}")
            print()
        
        # Check for new commits
        if self.last_commit and self.last_commit != commit:
            print(f"{Colors.MAGENTA}📝 New commit: {self.last_commit} → {commit}{Colors.END}")
            print()
        
        # Display status sections
        self._print_status_section("📝 Modified files", status.get('modified', []), Colors.YELLOW)
        self._print_status_section("➕ Added files", status.get('added', []), Colors.GREEN)
        self._print_status_section("🗑️  Deleted files", status.get('deleted', []), Colors.RED)
        self._print_status_section("📦 Staged changes", status.get('staged', []), Colors.BLUE)
        self._print_status_section("❓ Untracked files", status.get('untracked', []), Colors.MAGENTA)
        self._print_status_section("🔄 Renamed files", status.get('renamed', []), Colors.CYAN)
        
        # Show diffs for modified files (if enabled)
        if self.show_diffs and status.get('modified'):
            print(f"{Colors.BOLD}{Colors.YELLOW}📋 Recent Changes:{Colors.END}")
            for filepath in status['modified'][:3]:  # Show max 3 files
                print(f"\n{Colors.UNDERLINE}{filepath}:{Colors.END}")
                diff = self._get_file_diff(filepath)
                formatted_diff = self._format_diff(diff, max_lines=10)
                if formatted_diff:
                    print(formatted_diff)
                else:
                    print(f"{Colors.YELLOW}  (Binary file or no changes detected){Colors.END}")
        
        # Show summary
        total_changes = sum(len(files) for files in status.values())
        if total_changes == 0:
            print(f"{Colors.GREEN}✅ Repository is clean - no changes detected{Colors.END}")
        else:
            print(f"{Colors.YELLOW}📊 Total changes: {total_changes} files{Colors.END}")
        
        print(f"\n{Colors.CYAN}Last updated: {timestamp} | Press Ctrl+C to stop{Colors.END}")
    
    def _detect_changes(self, current_status: Dict[str, List[str]]) -> List[str]:
        """Detect what changed since last check"""
        changes = []
        
        for category, files in current_status.items():
            last_files = set(self.last_status.get(category, []))
            current_files = set(files)
            
            # New files in this category
            new_files = current_files - last_files
            if new_files:
                changes.extend([f"New {category}: {f}" for f in new_files])
            
            # Removed files from this category
            removed_files = last_files - current_files
            if removed_files:
                changes.extend([f"Resolved {category}: {f}" for f in removed_files])
        
        return changes
    
    def start_monitoring(self):
        """Start the monitoring loop"""
        try:
            # Initial state
            self.last_branch = self._get_current_branch()
            self.last_commit = self._get_current_commit()
            self.last_status = self._get_git_status()
            
            while self.running:
                current_status = self._get_git_status()
                current_branch = self._get_current_branch()
                current_commit = self._get_current_commit()
                
                # Detect and display changes
                changes = self._detect_changes(current_status)
                if changes or current_status != self.last_status or current_branch != self.last_branch or current_commit != self.last_commit:
                    self._display_changes(current_status)
                    
                    # Show change notifications
                    if changes:
                        print(f"\n{Colors.BOLD}{Colors.GREEN}🔔 Changes detected:{Colors.END}")
                        for change in changes:
                            print(f"  {Colors.GREEN}• {change}{Colors.END}")
                
                # Update state
                self.last_status = current_status
                self.last_branch = current_branch
                self.last_commit = current_commit
                
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}👋 Monitoring stopped by user{Colors.END}")
        except Exception as e:
            print(f"\n{Colors.RED}❌ Error: {e}{Colors.END}")
        finally:
            self.running = False

def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(
        description="Real-time Git repository monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python git_monitor.py                    # Monitor current directory
  python git_monitor.py --path /path/to/repo  # Monitor specific repository
  python git_monitor.py --interval 0.5    # Faster refresh rate
  python git_monitor.py --no-diffs        # Don't show file diffs
        """
    )
    
    parser.add_argument(
        "--path", "-p",
        default=".",
        help="Path to Git repository (default: current directory)"
    )
    
    parser.add_argument(
        "--interval", "-i",
        type=float,
        default=1.0,
        help="Refresh interval in seconds (default: 1.0)"
    )
    
    parser.add_argument(
        "--no-diffs",
        action="store_true",
        help="Don't show file diffs (faster performance)"
    )
    
    args = parser.parse_args()
    
    # Create and start monitor
    monitor = GitMonitor(
        repo_path=args.path,
        interval=args.interval,
        show_diffs=not args.no_diffs
    )
    
    monitor.start_monitoring()

if __name__ == "__main__":
    main()
