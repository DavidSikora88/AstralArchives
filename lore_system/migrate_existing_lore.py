#!/usr/bin/env python3
"""
Migration script to convert existing Astral Archives lore into the new lore management system.
"""

import json
import csv
import os
import re
from datetime import datetime
from typing import Dict, List, Any
import uuid

from lore_manager import LoreManager

class LoreMigrator:
    def __init__(self):
        """Initialize the migrator."""
        self.manager = LoreManager("lore_system/config.json")
        self.created_entries = {}  # Map of original names to new IDs
        
    def migrate_all(self):
        """Migrate all existing lore files."""
        print("Starting migration of existing lore...")
        
        # Migrate states data
        self.migrate_states_data()

        # Migrate timeline
        self.migrate_timeline()

        # Migrate world overview
        self.migrate_world_overview()
        
        # Create relationships between migrated entries
        self.create_relationships()
        
        print(f"Migration complete! Created {len(self.created_entries)} entries.")
        
        # Generate summary report
        self.generate_migration_report()
    
    def migrate_states_data(self):
        """Migrate states data from CSV file."""
        csv_path = "Data/states_data.csv"
        if not os.path.exists(csv_path):
            print(f"States data file not found: {csv_path}")
            return
        
        print("Migrating states data...")
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                if row['State'] == 'Neutrals':  # Skip neutrals entry
                    continue
                
                # Create location entry for the state
                state_entry = {
                    "name": row['Full Name'],
                    "description": f"A {row['Form'].lower()} in the world of Astrallum. "
                                 f"Capital: {row['Capital']}. Culture: {row['Culture']}. "
                                 f"Population: {row['Total Population']}.",
                    "tags": ["state", "political-entity", row['Culture'].lower(), row['Type'].lower()],
                    "custom_fields": {
                        "type": "state",
                        "government_form": row['Form'],
                        "capital": row['Capital'],
                        "culture": row['Culture'],
                        "total_population": int(row['Total Population']) if row['Total Population'].isdigit() else 0,
                        "rural_population": int(row['Rural Population']) if row['Rural Population'].isdigit() else 0,
                        "urban_population": int(row['Urban Population']) if row['Urban Population'].isdigit() else 0,
                        "area_sq_miles": int(float(row['Area mi2'])) if row['Area mi2'].replace('.', '').isdigit() else 0,
                        "expansionism": float(row['Expansionism']) if row['Expansionism'].replace('.', '').isdigit() else 0,
                        "color": row['Color']
                    }
                }
                
                try:
                    state_id = self.manager.create_entry("locations", state_entry)
                    self.created_entries[row['Full Name']] = state_id
                    self.created_entries[row['State']] = state_id  # Also map short name
                    
                    # Create capital city entry
                    capital_entry = {
                        "name": row['Capital'],
                        "description": f"Capital city of {row['Full Name']}.",
                        "tags": ["city", "capital", row['Culture'].lower()],
                        "custom_fields": {
                            "type": "city",
                            "is_capital": True,
                            "parent_state": row['Full Name']
                        }
                    }
                    
                    capital_id = self.manager.create_entry("locations", capital_entry)
                    self.created_entries[row['Capital']] = capital_id
                    
                    # Create relationship between capital and state
                    self.manager.add_relationship(
                        capital_id, state_id, "located_in",
                        f"{row['Capital']} is the capital of {row['Full Name']}", 10.0
                    )
                    
                except Exception as e:
                    print(f"Error migrating state {row['Full Name']}: {e}")
        
        print(f"Migrated {len([k for k in self.created_entries.keys() if 'Republic' in k or 'Kingdom' in k or 'Union' in k])} states")
    
    def migrate_timeline(self):
        """Migrate timeline events."""
        timeline_path = "Timeline.md"
        if not os.path.exists(timeline_path):
            print(f"Timeline file not found: {timeline_path}")
            return
        
        print("Migrating timeline...")
        
        with open(timeline_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create The Lost Epoch concept
        lost_epoch_entry = {
            "name": "The Lost Epoch",
            "description": "A time of advanced technology and prosperity, now shrouded in mystery. "
                         "This era represents the height of technological achievement before The Collapse.",
            "tags": ["era", "history", "technology", "mystery"],
            "custom_fields": {
                "type": "historical_era",
                "status": "ended",
                "significance": "Represents the peak of technological civilization"
            }
        }
        
        try:
            lost_epoch_id = self.manager.create_entry("concepts", lost_epoch_entry)
            self.created_entries["The Lost Epoch"] = lost_epoch_id
        except Exception as e:
            print(f"Error creating Lost Epoch: {e}")
        
        # Create The Collapse event
        collapse_entry = {
            "name": "The Collapse",
            "description": "A cataclysmic event that led to the technological collapse, plunging the world into chaos. "
                         "This event marks the end of The Lost Epoch and the beginning of the Eclipse Era.",
            "tags": ["event", "catastrophe", "history", "turning-point"],
            "custom_fields": {
                "type": "cataclysmic_event",
                "date": "Year 0",
                "era": "Eclipse Era",
                "impact": "Global technological collapse"
            }
        }
        
        try:
            collapse_id = self.manager.create_entry("events", collapse_entry)
            self.created_entries["The Collapse"] = collapse_id
            
            # Create relationship between Lost Epoch and The Collapse
            if "The Lost Epoch" in self.created_entries:
                self.manager.add_relationship(
                    collapse_id, self.created_entries["The Lost Epoch"], "successor_of",
                    "The Collapse ended The Lost Epoch", 10.0
                )
        except Exception as e:
            print(f"Error creating The Collapse: {e}")
        
        # Create Eclipse Era concept
        eclipse_era_entry = {
            "name": "Eclipse Era",
            "description": "The current era, where advanced technology is perceived as magic. "
                         "The truth behind the technology remains hidden from the general public. "
                         "This era began with The Collapse and continues to Year 1800.",
            "tags": ["era", "current", "magic", "technology", "mystery"],
            "custom_fields": {
                "type": "historical_era",
                "start_date": "Year 0",
                "current_date": "Year 1800",
                "status": "current",
                "characteristics": "Technology perceived as magic"
            }
        }
        
        try:
            eclipse_era_id = self.manager.create_entry("concepts", eclipse_era_entry)
            self.created_entries["Eclipse Era"] = eclipse_era_id
            
            # Create relationship with The Collapse
            if "The Collapse" in self.created_entries:
                self.manager.add_relationship(
                    eclipse_era_id, self.created_entries["The Collapse"], "created_by",
                    "The Eclipse Era began with The Collapse", 10.0
                )
        except Exception as e:
            print(f"Error creating Eclipse Era: {e}")
    
    def migrate_world_overview(self):
        """Migrate world overview concepts."""
        overview_path = "World Overview.md"
        if not os.path.exists(overview_path):
            print(f"World overview file not found: {overview_path}")
            return
        
        print("Migrating world overview...")
        
        # Create Astrallum world entry
        astrallum_entry = {
            "name": "Astrallum",
            "description": "The enigmatic world where advanced technology masquerades as magic, "
                         "and ancient mysteries are hidden behind a mystical facade. "
                         "A reality where the boundaries between magic and machinery blur, "
                         "creating an intricate tapestry of wonder and intrigue.",
            "tags": ["world", "setting", "technology", "magic", "mystery"],
            "custom_fields": {
                "type": "world",
                "genre": "Futuristic Fantasy",
                "themes": ["sci-fi", "solarpunk", "fantasy"],
                "magic_system": "Technology disguised as magic",
                "current_era": "Eclipse Era",
                "total_states": 21
            }
        }
        
        try:
            astrallum_id = self.manager.create_entry("locations", astrallum_entry)
            self.created_entries["Astrallum"] = astrallum_id
        except Exception as e:
            print(f"Error creating Astrallum: {e}")
        
        # Create Eternal Chronoglyph character
        chronoglyph_entry = {
            "name": "Eternal Chronoglyph",
            "description": "An astral archivist who serves as the vessel of information and "
                         "keeper of knowledge about Astrallum. Acts as a guide through the "
                         "mysteries and secrets of this world.",
            "tags": ["character", "archivist", "guide", "keeper", "astral"],
            "custom_fields": {
                "type": "astral_being",
                "role": "Archivist and Guide",
                "nature": "Eternal",
                "purpose": "Keeper of knowledge and secrets"
            }
        }
        
        try:
            chronoglyph_id = self.manager.create_entry("characters", chronoglyph_entry)
            self.created_entries["Eternal Chronoglyph"] = chronoglyph_id
            
            # Create relationship with Astrallum
            if "Astrallum" in self.created_entries:
                self.manager.add_relationship(
                    chronoglyph_id, self.created_entries["Astrallum"], "related_to",
                    "Eternal Chronoglyph is the keeper of Astrallum's knowledge", 10.0
                )
        except Exception as e:
            print(f"Error creating Eternal Chronoglyph: {e}")
        
        # Create Ancient Relics concept
        relics_entry = {
            "name": "Ancient Relics",
            "description": "Highly sought after artifacts of advanced technology from The Lost Epoch. "
                         "These relics are perceived as magical items but are actually remnants "
                         "of the advanced civilization that existed before The Collapse.",
            "tags": ["artifacts", "technology", "ancient", "magic", "sought-after"],
            "custom_fields": {
                "type": "artifact_category",
                "origin": "The Lost Epoch",
                "nature": "Advanced technology",
                "perception": "Magical artifacts",
                "status": "Highly sought after"
            }
        }
        
        try:
            relics_id = self.manager.create_entry("concepts", relics_entry)
            self.created_entries["Ancient Relics"] = relics_id
            
            # Create relationships
            if "The Lost Epoch" in self.created_entries:
                self.manager.add_relationship(
                    relics_id, self.created_entries["The Lost Epoch"], "created_by",
                    "Ancient Relics are remnants from The Lost Epoch", 9.0
                )
        except Exception as e:
            print(f"Error creating Ancient Relics: {e}")
    
    def create_relationships(self):
        """Create additional relationships between migrated entries."""
        print("Creating additional relationships...")
        
        # Link all states to Astrallum
        if "Astrallum" in self.created_entries:
            astrallum_id = self.created_entries["Astrallum"]
            
            for name, entry_id in self.created_entries.items():
                if any(keyword in name for keyword in ["Republic", "Kingdom", "Union", "Oligarchy", "Dominion", "Council", "Confederation", "Divine Kingdom", "Commune", "Provinces", "Collective", "Federation", "Commonwealth", "Territory", "Tribes", "City"]):
                    try:
                        self.manager.add_relationship(
                            entry_id, astrallum_id, "located_in",
                            f"{name} is located in Astrallum", 8.0
                        )
                    except Exception as e:
                        print(f"Error linking {name} to Astrallum: {e}")
        
        # Link Eclipse Era to Astrallum
        if "Eclipse Era" in self.created_entries and "Astrallum" in self.created_entries:
            try:
                self.manager.add_relationship(
                    self.created_entries["Eclipse Era"], self.created_entries["Astrallum"], "related_to",
                    "Eclipse Era is the current era of Astrallum", 10.0
                )
            except Exception as e:
                print(f"Error linking Eclipse Era to Astrallum: {e}")
    
    def generate_migration_report(self):
        """Generate a report of the migration process."""
        report_path = "lore_system/migration_report.json"
        
        report = {
            "migration_date": datetime.now().isoformat(),
            "total_entries_created": len(self.created_entries),
            "entries_by_category": {},
            "created_entries": self.created_entries,
            "source_files": [
                "Data/states_data.csv",
                "Timeline.md",
                "World Overview.md"
            ]
        }
        
        # Count entries by category
        for entry_id in self.created_entries.values():
            entry = self.manager.get_entry(entry_id)
            if entry:
                category = entry.get("category", "unknown")
                report["entries_by_category"][category] = report["entries_by_category"].get(category, 0) + 1
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Migration report saved to: {report_path}")
        print("\nMigration Summary:")
        print(f"Total entries created: {report['total_entries_created']}")
        for category, count in report["entries_by_category"].items():
            print(f"  {category}: {count}")

if __name__ == "__main__":
    migrator = LoreMigrator()
    migrator.migrate_all()
