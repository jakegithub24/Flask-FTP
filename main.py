#!/usr/bin/env python3
"""
FTP-like Server with Ngrok Tunneling
Server-side Terminal UI with Dark Mode
"""

import os
import sys
import subprocess
import threading
import time
import signal
import atexit
from datetime import datetime
from colorama import init, Fore, Style, Back
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich import box
import pyngrok.ngrok
from pyngrok import ngrok

# Initialize colorama for cross-platform colored text
init(autoreset=True)

class ServerTUI:
    def __init__(self):
        self.console = Console()
        self.session_password = None
        self.access_privilege = None
        self.ngrok_url = None
        self.server_running = False
        self.layout = Layout()
        
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_banner(self):
        """Print the application banner"""
        self.clear_screen()
        
        banner = r"""
        ███████╗████████╗██████╗ 
        ██╔════╝╚══██╔══╝██╔══██╗
        █████╗     ██║   ██████╔╝
        ██╔══╝     ██║   ██╔═══╝ 
        ██║        ██║   ██║     
        ╚═╝        ╚═╝   ╚═╝     
        """

        self.console.print(f"[bold blue]{banner}[/bold blue]")
        self.console.print("[bold cyan]Secure FTP-like Server with Ngrok Tunneling[/bold cyan]")
        self.console.print("[dim]Press Ctrl+C to exit[/dim]\n")
    
    def get_session_password(self):
        """Get session password from user input"""
        self.console.print("[bold blue]⎯" * 50)
        self.console.print("[bold blue]🔐 SESSION SETUP[/bold blue]")
        self.console.print("[bold blue]⎯" * 50)
        
        while True:
            password = self.console.input("[bold cyan]Enter session password: [/bold cyan]")
            confirm = self.console.input("[bold cyan]Confirm session password: [/bold cyan]")
            
            if password == confirm:
                if len(password) >= 6:
                    self.session_password = password
                    self.console.print("[green]✓ Password set successfully![/green]")
                    return password
                else:
                    self.console.print("[red]✗ Password must be at least 6 characters long[/red]")
            else:
                self.console.print("[red]✗ Passwords don't match. Please try again.[/red]")
    
    def get_access_privilege(self):
        """Get access privilege configuration from user input"""
        self.console.print("\n[bold blue]⎯" * 50)
        self.console.print("[bold blue]🔐 ACCESS PRIVILEGE SETUP[/bold blue]")
        self.console.print("[bold blue]⎯" * 50)
        self.console.print("[cyan]What type of FTP server do you want to setup?[/cyan]\n")
        
        options = {
            '1': {'name': 'Upload Only', 'value': 'upload_only'},
            '2': {'name': 'Download Only', 'value': 'download_only'},
            '3': {'name': 'Upload and Download', 'value': 'upload_download'}
        }
        
        for key, option in options.items():
            self.console.print(f"[yellow]{key}.[/yellow] {option['name']}")
        
        while True:
            choice = self.console.input("\n[bold cyan]Select option (1-3): [/bold cyan]").strip()
            
            if choice in options:
                self.access_privilege = options[choice]['value']
                privilege_name = options[choice]['name']
                self.console.print(f"[green]✓ Access privilege set to: {privilege_name}[/green]")
                return self.access_privilege
            else:
                self.console.print("[red]✗ Invalid option. Please select 1, 2, or 3.[/red]")
    
    def start_flask_server(self):
        """Start the Flask server in a separate thread"""
        # Set the session password and access privilege as environment variables BEFORE importing app
        os.environ['SESSION_PASSWORD'] = self.session_password
        os.environ['ACCESS_PRIVILEGE'] = self.access_privilege
        
        from app import app
        
        def run_server():
            app.run(host='127.0.0.1', port=9870, debug=False, use_reloader=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(2)  # Give server time to start
        self.server_running = True
        return server_thread
    
    def start_ngrok_tunnel(self):
        """Start ngrok tunnel and get public URL"""
        self.console.print("\n[bold blue]🌐 STARTING NGROK TUNNEL[/bold blue]")
        self.console.print("[dim]Initializing secure tunnel...[/dim]")
        
        try:
            # Kill any existing ngrok tunnels
            ngrok.kill()
            
            # Create a new tunnel
            tunnel = ngrok.connect(9870, "http", bind_tls=True)
            self.ngrok_url = tunnel.public_url
            
            self.console.print(f"[green]✓ Ngrok tunnel created successfully![/green]")
            self.console.print(f"[bold yellow]Public URL:[/bold yellow] {self.ngrok_url}")
            
            return tunnel
        except Exception as e:
            self.console.print(f"[red]✗ Failed to create ngrok tunnel: {e}[/red]")
            return None
    
    def create_dashboard(self):
        """Create and display the live dashboard"""
        self.clear_screen()
        
        with Live(auto_refresh=False, screen=True) as live:
            while True:
                # Create layout
                self.layout.split(
                    Layout(name="header", size=3),
                    Layout(name="main", ratio=2),
                    Layout(name="status", size=6)
                )
                
                self.layout["main"].split_row(
                    Layout(name="left", ratio=1),
                    Layout(name="right", ratio=1)
                )
                
                # Header
                header_text = Text("🔒 FTP-LIKE SERVER DASHBOARD", style="bold blue on black")
                self.layout["header"].update(
                    Panel(header_text, box=box.DOUBLE)
                )
                
                # Left Panel - Connection Info
                connection_table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
                connection_table.add_column("Property", style="dim")
                connection_table.add_column("Value", style="bold green")
                
                connection_table.add_row("Server Status", "🟢 ONLINE")
                connection_table.add_row("Local URL", "http://127.0.0.1:9870")
                connection_table.add_row("Public URL", self.ngrok_url or "Not Available")
                connection_table.add_row("Session Active", "🟢 YES")
                connection_table.add_row("Connected Clients", "0")
                
                left_panel = Panel(
                    connection_table,
                    title="🌐 Connection Information",
                    border_style="blue",
                    padding=(1, 2)
                )
                
                # Right Panel - Quick Actions
                actions_text = Text()
                actions_text.append("Quick Actions:\n\n", style="bold cyan")
                actions_text.append("1. ", style="yellow")
                actions_text.append("Open Public URL\n", style="white")
                actions_text.append("2. ", style="yellow")
                actions_text.append("Monitor Connections\n", style="white")
                actions_text.append("3. ", style="yellow")
                actions_text.append("View Logs\n", style="white")
                actions_text.append("4. ", style="yellow")
                actions_text.append("Manage Files\n\n", style="white")
                actions_text.append("Press ", style="dim")
                actions_text.append("Ctrl+C", style="bold red")
                actions_text.append(" to shutdown server", style="dim")
                
                right_panel = Panel(
                    actions_text,
                    title="⚡ Quick Actions",
                    border_style="blue",
                    padding=(1, 2)
                )
                
                self.layout["left"].update(left_panel)
                self.layout["right"].update(right_panel)
                
                # Status Panel - Logs
                current_time = datetime.now().strftime("%H:%M:%S")
                logs = Text()
                logs.append(f"[{current_time}] ", style="dim")
                logs.append("Server started on port 9870\n", style="green")
                logs.append(f"[{current_time}] ", style="dim")
                logs.append(f"Ngrok tunnel established: {self.ngrok_url}\n", style="green")
                logs.append(f"[{current_time}] ", style="dim")
                logs.append("Waiting for connections...\n", style="cyan")
                logs.append(f"[{current_time}] ", style="dim")
                logs.append("Session password: ", style="yellow")
                logs.append("*" * len(self.session_password) + "\n", style="dim")
                
                status_panel = Panel(
                    logs,
                    title="📊 Server Logs",
                    border_style="blue",
                    padding=(1, 2)
                )
                
                self.layout["status"].update(status_panel)
                
                # Update the live display
                live.update(self.layout, refresh=True)
                
                # Check for exit condition
                try:
                    time.sleep(1)
                except KeyboardInterrupt:
                    self.console.print("\n[bold red]Shutting down server...[/bold red]")
                    ngrok.kill()
                    break
    
    def run(self):
        """Main run method"""
        try:
            self.print_banner()
            self.get_session_password()
            self.get_access_privilege()
            
            # Start Flask server
            self.console.print("\n[bold blue]🚀 STARTING SERVER[/bold blue]")
            self.console.print("[dim]Initializing Flask server on port 9870...[/dim]")
            
            server_thread = self.start_flask_server()
            
            if self.server_running:
                self.console.print("[green]✓ Flask server started successfully![/green]")
                
                # Start ngrok tunnel
                tunnel = self.start_ngrok_tunnel()
                
                if tunnel:
                    # Copy URL to clipboard (optional)
                    try:
                        import pyperclip
                        pyperclip.copy(self.ngrok_url)
                        self.console.print("[dim]✓ URL copied to clipboard[/dim]")
                    except:
                        pass
                    
                    self.console.print("\n[bold blue]📋 IMPORTANT INFORMATION[/bold blue]")
                    self.console.print("[bold cyan]Public Access URL:[/bold cyan]", style="bold white")
                    self.console.print(f"[bold green]{self.ngrok_url}[/bold green]")
                    self.console.print("\n[bold cyan]Session Password:[/bold cyan]", style="bold white")
                    self.console.print(f"[bold yellow]{self.session_password}[/bold yellow]")
                    
                    # Convert privilege setting to readable format
                    privilege_map = {
                        'upload_only': 'Upload Only',
                        'download_only': 'Download Only',
                        'upload_download': 'Upload & Download'
                    }
                    privilege_name = privilege_map.get(self.access_privilege, self.access_privilege)
                    self.console.print("\n[bold cyan]Access Privilege:[/bold cyan]", style="bold white")
                    self.console.print(f"[bold cyan]{privilege_name}[/bold cyan]")
                    
                    self.console.print("\n[dim]Press Enter to continue to dashboard...[/dim]")
                    input()
                    
                    # Show dashboard
                    self.create_dashboard()
            
        except KeyboardInterrupt:
            self.console.print("\n[bold red]Shutdown requested by user[/bold red]")
        except Exception as e:
            self.console.print(f"[bold red]Error: {e}[/bold red]")
        finally:
            # Cleanup
            self.console.print("[dim]Cleaning up resources...[/dim]")
            ngrok.kill()
            self.console.print("[green]✓ Server shutdown complete[/green]")

def main():
    """Main entry point"""
    tui = ServerTUI()
    tui.run()

if __name__ == "__main__":
    main()
