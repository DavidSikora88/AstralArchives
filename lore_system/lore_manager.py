#!/usr/bin/env python3
"""
Astral Archives Lore Management System
Main interface for managing lore entries, relationships, and consistency.
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
import jsonschema

from search_engine import LoreSearchEngine
from consistency_checker import ConsistencyChecker

console = Console()

class LoreManager:
    def __init__(self, config_path: str = "lore_system/config.json"):
        """Initialize the Lore Manager with configuration."""
        self.config = self._load_config(config_path)
        self.database_path = self.config["database_path"]
        self.schema = self._load_schema()
        self.search_engine = LoreSearchEngine(self.config)
        self.consistency_checker = ConsistencyChecker(self.config)
        
        # Ensure directories exist
        os.makedirs(self.database_path, exist_ok=True)
        os.makedirs(self.config["templates_path"], exist_ok=True)
        os.makedirs(self.config["export_path"], exist_ok=True)
        os.makedirs(self.config["backup_path"], exist_ok=True)
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            console.print(f"[red]Configuration file not found: {config_path}[/red]")
            raise
    
    def _load_schema(self) -> Dict:
        """Load the JSON schema for validation."""
        schema_path = os.path.join(self.database_path, "schema.json")
        try:
            with open(schema_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            console.print(f"[red]Schema file not found: {schema_path}[/red]")
            raise
    
    def _get_category_file(self, category: str) -> str:
        """Get the file path for a specific category."""
        return os.path.join(self.database_path, f"{category}.json")
    
    def _load_category_data(self, category: str) -> Dict:
        """Load data for a specific category."""
        file_path = self._get_category_file(category)
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return {"entries": {}, "metadata": {"last_updated": datetime.now().isoformat()}}
    
    def _save_category_data(self, category: str, data: Dict):
        """Save data for a specific category."""
        file_path = self._get_category_file(category)
        data["metadata"]["last_updated"] = datetime.now().isoformat()
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def validate_entry(self, entry: Dict) -> bool:
        """Validate a lore entry against the schema."""
        try:
            jsonschema.validate(entry, self.schema)
            return True
        except jsonschema.ValidationError as e:
            console.print(f"[red]Validation error: {e.message}[/red]")
            return False
    
    def create_entry(self, category: str, entry_data: Dict) -> str:
        """Create a new lore entry."""
        if category not in self.config["categories"]:
            raise ValueError(f"Invalid category: {category}")
        
        # Generate unique ID
        entry_id = str(uuid.uuid4())
        
        # Prepare entry with metadata
        entry = {
            "id": entry_id,
            "category": category,
            "metadata": {
                "created_date": datetime.now().isoformat(),
                "modified_date": datetime.now().isoformat(),
                "author": "system",
                "version": 1,
                "status": "draft"
            },
            **entry_data
        }
        
        # Validate entry
        if not self.validate_entry(entry):
            raise ValueError("Entry validation failed")
        
        # Load category data and add entry
        data = self._load_category_data(category)
        data["entries"][entry_id] = entry
        self._save_category_data(category, data)
        
        # Refresh search index
        self.search_engine.refresh_index()
        
        console.print(f"[green]Created {category} entry: {entry.get('name', entry_id)}[/green]")
        return entry_id
    
    def update_entry(self, entry_id: str, updates: Dict) -> bool:
        """Update an existing lore entry."""
        # Find the entry across all categories
        for category in self.config["categories"]:
            data = self._load_category_data(category)
            if entry_id in data["entries"]:
                entry = data["entries"][entry_id]
                
                # Update fields
                for key, value in updates.items():
                    if key != "id":  # Prevent ID changes
                        entry[key] = value
                
                # Update metadata
                entry["metadata"]["modified_date"] = datetime.now().isoformat()
                entry["metadata"]["version"] = entry["metadata"].get("version", 1) + 1
                
                # Validate updated entry
                if not self.validate_entry(entry):
                    return False
                
                # Save changes
                data["entries"][entry_id] = entry
                self._save_category_data(category, data)
                
                # Refresh search index
                self.search_engine.refresh_index()
                
                console.print(f"[green]Updated entry: {entry.get('name', entry_id)}[/green]")
                return True
        
        console.print(f"[red]Entry not found: {entry_id}[/red]")
        return False
    
    def delete_entry(self, entry_id: str) -> bool:
        """Delete a lore entry."""
        for category in self.config["categories"]:
            data = self._load_category_data(category)
            if entry_id in data["entries"]:
                entry_name = data["entries"][entry_id].get("name", entry_id)
                del data["entries"][entry_id]
                self._save_category_data(category, data)
                
                # Refresh search index
                self.search_engine.refresh_index()
                
                console.print(f"[yellow]Deleted entry: {entry_name}[/yellow]")
                return True
        
        console.print(f"[red]Entry not found: {entry_id}[/red]")
        return False
    
    def get_entry(self, entry_id: str) -> Optional[Dict]:
        """Retrieve a specific lore entry."""
        for category in self.config["categories"]:
            data = self._load_category_data(category)
            if entry_id in data["entries"]:
                return data["entries"][entry_id]
        return None
    
    def list_entries(self, category: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """List lore entries, optionally filtered by category."""
        entries = []
        categories = [category] if category else self.config["categories"]
        
        for cat in categories:
            data = self._load_category_data(cat)
            for entry in data["entries"].values():
                entries.append(entry)
                if len(entries) >= limit:
                    break
        
        return entries[:limit]
    
    def add_relationship(self, source_id: str, target_id: str, 
                        relationship_type: str, description: str = "", 
                        strength: float = 5.0) -> bool:
        """Add a relationship between two lore entries."""
        source_entry = self.get_entry(source_id)
        target_entry = self.get_entry(target_id)
        
        if not source_entry or not target_entry:
            console.print("[red]One or both entries not found[/red]")
            return False
        
        if relationship_type not in self.config["relationship_types"]:
            console.print(f"[red]Invalid relationship type: {relationship_type}[/red]")
            return False
        
        # Add relationship to source entry
        if "relationships" not in source_entry:
            source_entry["relationships"] = []
        
        relationship = {
            "target_id": target_id,
            "relationship_type": relationship_type,
            "description": description,
            "strength": strength
        }
        
        source_entry["relationships"].append(relationship)
        
        # Update the entry
        return self.update_entry(source_id, {"relationships": source_entry["relationships"]})
    
    def backup_database(self) -> str:
        """Create a backup of the entire database."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(self.config["backup_path"], f"backup_{timestamp}")
        os.makedirs(backup_dir, exist_ok=True)
        
        # Copy all category files
        for category in self.config["categories"]:
            source_file = self._get_category_file(category)
            if os.path.exists(source_file):
                import shutil
                shutil.copy2(source_file, backup_dir)
        
        console.print(f"[green]Database backed up to: {backup_dir}[/green]")
        return backup_dir
    
    def export_to_markdown(self, output_dir: str = None) -> str:
        """Export all lore entries to markdown files."""
        if not output_dir:
            output_dir = os.path.join(self.config["export_path"], "markdown_export")
        
        os.makedirs(output_dir, exist_ok=True)
        
        for category in self.config["categories"]:
            data = self._load_category_data(category)
            if data["entries"]:
                category_dir = os.path.join(output_dir, category)
                os.makedirs(category_dir, exist_ok=True)
                
                for entry in data["entries"].values():
                    filename = f"{entry.get('name', entry['id']).replace(' ', '_')}.md"
                    filepath = os.path.join(category_dir, filename)
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(self._entry_to_markdown(entry))
        
        console.print(f"[green]Exported to markdown: {output_dir}[/green]")
        return output_dir
    
    def _entry_to_markdown(self, entry: Dict) -> str:
        """Convert a lore entry to markdown format."""
        md = f"# {entry.get('name', 'Unnamed')}\n\n"
        md += f"**Category:** {entry.get('category', 'Unknown')}\n\n"
        
        if entry.get('subcategory'):
            md += f"**Subcategory:** {entry.get('subcategory')}\n\n"
        
        md += f"## Description\n\n{entry.get('description', 'No description available.')}\n\n"
        
        if entry.get('tags'):
            md += f"**Tags:** {', '.join(entry.get('tags'))}\n\n"
        
        if entry.get('relationships'):
            md += "## Relationships\n\n"
            for rel in entry.get('relationships'):
                target_entry = self.get_entry(rel.get('target_id'))
                target_name = target_entry.get('name') if target_entry else rel.get('target_id')
                md += f"- **{rel.get('relationship_type')}**: {target_name}"
                if rel.get('description'):
                    md += f" - {rel.get('description')}"
                md += "\n"
            md += "\n"
        
        if entry.get('custom_fields'):
            md += "## Additional Information\n\n"
            for key, value in entry.get('custom_fields').items():
                md += f"**{key.replace('_', ' ').title()}:** {value}\n\n"
        
        # Metadata
        metadata = entry.get('metadata', {})
        md += "---\n\n"
        md += f"*Created: {metadata.get('created_date', 'Unknown')}*\n\n"
        md += f"*Last Modified: {metadata.get('modified_date', 'Unknown')}*\n\n"
        md += f"*Status: {metadata.get('status', 'Unknown')}*\n\n"
        
        return md

# CLI Interface
@click.group()
def cli():
    """Astral Archives Lore Management System"""
    pass

@cli.command()
@click.option('--category', required=True, help='Category of the lore entry')
@click.option('--name', required=True, help='Name of the lore entry')
@click.option('--description', required=True, help='Description of the lore entry')
@click.option('--tags', help='Comma-separated tags')
def create(category, name, description, tags):
    """Create a new lore entry"""
    manager = LoreManager()
    entry_data = {
        "name": name,
        "description": description,
        "tags": [tag.strip() for tag in tags.split(',')] if tags else []
    }

    try:
        entry_id = manager.create_entry(category, entry_data)
        console.print(f"[green]Created entry with ID: {entry_id}[/green]")
    except Exception as e:
        console.print(f"[red]Error creating entry: {e}[/red]")

@cli.command()
@click.option('--category', help='Filter by category')
@click.option('--limit', default=20, help='Maximum number of entries to show')
def list_entries(category, limit):
    """List lore entries"""
    manager = LoreManager()
    entries = manager.list_entries(category, limit)

    table = Table(title="Lore Entries")
    table.add_column("Name", style="cyan")
    table.add_column("Category", style="magenta")
    table.add_column("Description", style="white", max_width=50)
    table.add_column("Last Modified", style="green")

    for entry in entries:
        table.add_row(
            entry.get("name", "Unknown"),
            entry.get("category", "Unknown"),
            entry.get("description", "")[:100] + "..." if len(entry.get("description", "")) > 100 else entry.get("description", ""),
            entry.get("metadata", {}).get("modified_date", "Unknown")
        )

    console.print(table)

@cli.command()
@click.argument('query')
@click.option('--category', help='Filter by category')
@click.option('--limit', default=10, help='Maximum number of results')
def search(query, category, limit):
    """Search lore entries"""
    manager = LoreManager()
    results = manager.search_engine.search(query, category=category, limit=limit)

    if not results:
        console.print("[yellow]No results found[/yellow]")
        return

    for result in results:
        panel = Panel(
            f"[bold]{result['name']}[/bold]\n"
            f"Category: {result['category']}\n"
            f"Score: {result.get('score', 0):.2f}\n\n"
            f"{result['description'][:200]}...",
            title=f"ID: {result['id']}"
        )
        console.print(panel)

@cli.command()
def backup():
    """Create a backup of the lore database"""
    manager = LoreManager()
    backup_path = manager.backup_database()
    console.print(f"[green]Backup created at: {backup_path}[/green]")

@cli.command()
def validate():
    """Validate all lore entries for consistency"""
    manager = LoreManager()
    issues = manager.consistency_checker.check_all()

    if not issues:
        console.print("[green]No consistency issues found![/green]")
    else:
        console.print(f"[yellow]Found {len(issues)} consistency issues:[/yellow]")
        for issue in issues:
            console.print(f"[red]• {issue}[/red]")

@cli.command()
@click.option('--output-dir', help='Output directory for markdown files')
def export_markdown(output_dir):
    """Export all lore entries to markdown files"""
    manager = LoreManager()
    export_path = manager.export_to_markdown(output_dir)
    console.print(f"[green]Exported to: {export_path}[/green]")

@cli.command()
@click.argument('source_id')
@click.argument('target_id')
@click.argument('relationship_type')
@click.option('--description', default='', help='Description of the relationship')
@click.option('--strength', default=5.0, help='Relationship strength (0-10)')
def add_relationship(source_id, target_id, relationship_type, description, strength):
    """Add a relationship between two lore entries"""
    manager = LoreManager()
    success = manager.add_relationship(source_id, target_id, relationship_type, description, strength)

    if success:
        console.print("[green]Relationship added successfully[/green]")
    else:
        console.print("[red]Failed to add relationship[/red]")

if __name__ == "__main__":
    cli()
