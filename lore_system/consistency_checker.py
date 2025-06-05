#!/usr/bin/env python3
"""
Consistency Checker for Astral Archives Lore Management System
Validates lore entries for internal consistency and logical contradictions.
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import networkx as nx

class ConsistencyChecker:
    def __init__(self, config: Dict):
        """Initialize the consistency checker with configuration."""
        self.config = config
        self.database_path = config["database_path"]
        self.validation_rules = config["validation_rules"]
        self.all_entries = {}
        self._load_all_entries()
    
    def _load_all_entries(self):
        """Load all entries from all categories."""
        self.all_entries = {}
        
        for category in self.config["categories"]:
            category_file = os.path.join(self.database_path, f"{category}.json")
            if os.path.exists(category_file):
                with open(category_file, 'r') as f:
                    data = json.load(f)
                    for entry_id, entry in data.get("entries", {}).items():
                        self.all_entries[entry_id] = entry
    
    def check_all(self) -> List[str]:
        """Run all consistency checks and return list of issues."""
        issues = []
        
        if self.validation_rules.get("check_date_consistency", True):
            issues.extend(self.check_date_consistency())
        
        if self.validation_rules.get("check_location_hierarchy", True):
            issues.extend(self.check_location_hierarchy())
        
        if self.validation_rules.get("check_character_relationships", True):
            issues.extend(self.check_character_relationships())
        
        issues.extend(self.check_orphaned_references())
        issues.extend(self.check_circular_relationships())
        issues.extend(self.check_duplicate_names())
        
        return issues
    
    def check_date_consistency(self) -> List[str]:
        """Check for date inconsistencies in events and character lifespans."""
        issues = []
        events = [e for e in self.all_entries.values() if e.get("category") == "events"]
        characters = [e for e in self.all_entries.values() if e.get("category") == "characters"]
        
        # Sort events by date
        dated_events = []
        for event in events:
            date_str = event.get("custom_fields", {}).get("date") or event.get("date")
            if date_str:
                try:
                    # Parse various date formats
                    date_value = self._parse_date(date_str)
                    if date_value is not None:
                        dated_events.append((event, date_value))
                except:
                    issues.append(f"Invalid date format in event '{event.get('name')}': {date_str}")
        
        dated_events.sort(key=lambda x: x[1])
        
        # Check for logical inconsistencies
        for i in range(len(dated_events) - 1):
            current_event, current_date = dated_events[i]
            next_event, next_date = dated_events[i + 1]
            
            # Check if events that should be sequential are in wrong order
            if self._events_should_be_sequential(current_event, next_event):
                if current_date > next_date:
                    issues.append(
                        f"Date inconsistency: '{current_event.get('name')}' "
                        f"should occur before '{next_event.get('name')}'"
                    )
        
        # Check character lifespans against events
        for character in characters:
            birth_date = character.get("custom_fields", {}).get("birth_date")
            death_date = character.get("custom_fields", {}).get("death_date")
            
            if birth_date and death_date:
                try:
                    birth_val = self._parse_date(birth_date)
                    death_val = self._parse_date(death_date)
                    
                    if birth_val and death_val and birth_val > death_val:
                        issues.append(
                            f"Character '{character.get('name')}' has birth date "
                            f"after death date"
                        )
                except:
                    pass
        
        return issues
    
    def check_location_hierarchy(self) -> List[str]:
        """Check for logical inconsistencies in location relationships."""
        issues = []
        locations = [e for e in self.all_entries.values() if e.get("category") == "locations"]
        
        # Build location hierarchy graph
        location_graph = nx.DiGraph()
        
        for location in locations:
            location_id = location["id"]
            location_graph.add_node(location_id, **location)
            
            # Add parent-child relationships
            for rel in location.get("relationships", []):
                if rel.get("relationship_type") == "part_of":
                    parent_id = rel.get("target_id")
                    if parent_id in [l["id"] for l in locations]:
                        location_graph.add_edge(location_id, parent_id)
        
        # Check for cycles in location hierarchy
        try:
            cycles = list(nx.simple_cycles(location_graph))
            for cycle in cycles:
                cycle_names = [self.all_entries[loc_id].get("name", loc_id) for loc_id in cycle]
                issues.append(f"Circular location hierarchy detected: {' -> '.join(cycle_names)}")
        except:
            pass
        
        # Check for impossible containment (e.g., city containing a continent)
        for location in locations:
            location_type = location.get("custom_fields", {}).get("type", "").lower()
            
            for rel in location.get("relationships", []):
                if rel.get("relationship_type") == "part_of":
                    parent_id = rel.get("target_id")
                    parent = self.all_entries.get(parent_id)
                    
                    if parent:
                        parent_type = parent.get("custom_fields", {}).get("type", "").lower()
                        
                        if self._is_impossible_containment(location_type, parent_type):
                            issues.append(
                                f"Impossible location hierarchy: {location_type} "
                                f"'{location.get('name')}' cannot be part of {parent_type} "
                                f"'{parent.get('name')}'"
                            )
        
        return issues
    
    def check_character_relationships(self) -> List[str]:
        """Check for inconsistencies in character relationships."""
        issues = []
        characters = [e for e in self.all_entries.values() if e.get("category") == "characters"]
        
        for character in characters:
            char_id = character["id"]
            
            for rel in character.get("relationships", []):
                target_id = rel.get("target_id")
                rel_type = rel.get("relationship_type")
                target = self.all_entries.get(target_id)
                
                if not target:
                    continue
                
                # Check for mutual exclusive relationships
                if rel_type in ["enemy_of", "ally_of"]:
                    # Check if target has conflicting relationship
                    for target_rel in target.get("relationships", []):
                        if (target_rel.get("target_id") == char_id and 
                            target_rel.get("relationship_type") in ["enemy_of", "ally_of"]):
                            
                            if (rel_type == "enemy_of" and target_rel.get("relationship_type") == "ally_of") or \
                               (rel_type == "ally_of" and target_rel.get("relationship_type") == "enemy_of"):
                                issues.append(
                                    f"Conflicting relationship: '{character.get('name')}' "
                                    f"and '{target.get('name')}' have contradictory relationships"
                                )
        
        return issues
    
    def check_orphaned_references(self) -> List[str]:
        """Check for references to non-existent entries."""
        issues = []
        
        for entry in self.all_entries.values():
            for rel in entry.get("relationships", []):
                target_id = rel.get("target_id")
                
                if target_id not in self.all_entries:
                    issues.append(
                        f"Entry '{entry.get('name')}' references non-existent entry: {target_id}"
                    )
        
        return issues
    
    def check_circular_relationships(self) -> List[str]:
        """Check for circular relationships that don't make logical sense."""
        issues = []
        
        # Build relationship graph
        rel_graph = nx.DiGraph()
        
        for entry in self.all_entries.values():
            entry_id = entry["id"]
            rel_graph.add_node(entry_id)
            
            for rel in entry.get("relationships", []):
                target_id = rel.get("target_id")
                rel_type = rel.get("relationship_type")
                
                if target_id in self.all_entries:
                    rel_graph.add_edge(entry_id, target_id, type=rel_type)
        
        # Check for problematic cycles
        try:
            cycles = list(nx.simple_cycles(rel_graph))
            for cycle in cycles:
                if len(cycle) == 2:  # Direct circular relationship
                    entry1 = self.all_entries[cycle[0]]
                    entry2 = self.all_entries[cycle[1]]
                    
                    # Get relationship types
                    rel1_type = None
                    rel2_type = None
                    
                    for rel in entry1.get("relationships", []):
                        if rel.get("target_id") == cycle[1]:
                            rel1_type = rel.get("relationship_type")
                            break
                    
                    for rel in entry2.get("relationships", []):
                        if rel.get("target_id") == cycle[0]:
                            rel2_type = rel.get("relationship_type")
                            break
                    
                    if rel1_type == "part_of" and rel2_type == "part_of":
                        issues.append(
                            f"Circular 'part_of' relationship between "
                            f"'{entry1.get('name')}' and '{entry2.get('name')}'"
                        )
        except:
            pass
        
        return issues
    
    def check_duplicate_names(self) -> List[str]:
        """Check for duplicate names within the same category."""
        issues = []
        name_map = {}
        
        for entry in self.all_entries.values():
            name = entry.get("name", "").lower().strip()
            category = entry.get("category")
            
            if name:
                key = (name, category)
                if key in name_map:
                    issues.append(
                        f"Duplicate name in {category}: '{entry.get('name')}' "
                        f"(IDs: {name_map[key]} and {entry['id']})"
                    )
                else:
                    name_map[key] = entry["id"]
        
        return issues
    
    def _parse_date(self, date_str: str) -> Optional[int]:
        """Parse various date formats and return a comparable value."""
        if not date_str:
            return None
        
        # Handle Eclipse Era dates (e.g., "Year 1800", "1800 EE")
        eclipse_match = re.search(r'(?:year\s+)?(\d+)(?:\s+ee)?', date_str.lower())
        if eclipse_match:
            return int(eclipse_match.group(1))
        
        # Handle relative dates (e.g., "The Collapse", "Before the Collapse")
        if "collapse" in date_str.lower():
            if "before" in date_str.lower():
                return -1  # Before Year 0
            else:
                return 0   # Year 0
        
        # Handle numeric dates
        numeric_match = re.search(r'(\d+)', date_str)
        if numeric_match:
            return int(numeric_match.group(1))
        
        return None
    
    def _events_should_be_sequential(self, event1: Dict, event2: Dict) -> bool:
        """Check if two events should logically be sequential."""
        # This is a simplified check - you can expand this based on your lore
        name1 = event1.get("name", "").lower()
        name2 = event2.get("name", "").lower()
        
        # Check for obvious sequential patterns
        if "collapse" in name1 and any(word in name2 for word in ["aftermath", "recovery", "rebuilding"]):
            return True
        
        return False
    
    def _is_impossible_containment(self, child_type: str, parent_type: str) -> bool:
        """Check if a containment relationship is logically impossible."""
        # Define size hierarchy (smaller to larger)
        size_hierarchy = [
            "building", "district", "settlement", "city", "region", 
            "province", "state", "continent", "world", "plane"
        ]
        
        try:
            child_idx = size_hierarchy.index(child_type)
            parent_idx = size_hierarchy.index(parent_type)
            return child_idx > parent_idx
        except ValueError:
            return False  # Unknown types, assume valid
    
    def generate_consistency_report(self) -> Dict:
        """Generate a comprehensive consistency report."""
        issues = self.check_all()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_entries": len(self.all_entries),
            "total_issues": len(issues),
            "issues_by_type": {},
            "issues": issues,
            "summary": {
                "critical_issues": 0,
                "warnings": 0,
                "suggestions": 0
            }
        }
        
        # Categorize issues
        for issue in issues:
            issue_type = self._categorize_issue(issue)
            report["issues_by_type"][issue_type] = report["issues_by_type"].get(issue_type, 0) + 1
            
            # Count by severity
            if any(word in issue.lower() for word in ["circular", "impossible", "conflicting"]):
                report["summary"]["critical_issues"] += 1
            elif any(word in issue.lower() for word in ["duplicate", "orphaned", "inconsistency"]):
                report["summary"]["warnings"] += 1
            else:
                report["summary"]["suggestions"] += 1
        
        return report
    
    def _categorize_issue(self, issue: str) -> str:
        """Categorize an issue by type."""
        issue_lower = issue.lower()
        
        if "date" in issue_lower:
            return "Date Consistency"
        elif "location" in issue_lower or "hierarchy" in issue_lower:
            return "Location Hierarchy"
        elif "relationship" in issue_lower:
            return "Relationships"
        elif "duplicate" in issue_lower:
            return "Duplicates"
        elif "orphaned" in issue_lower or "non-existent" in issue_lower:
            return "References"
        elif "circular" in issue_lower:
            return "Circular References"
        else:
            return "Other"
