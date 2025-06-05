#!/usr/bin/env python3
"""
Search Engine for Astral Archives Lore Management System
Provides fuzzy search, filtering, and relationship-based queries.
"""

import json
import os
import re
from typing import Dict, List, Optional, Any
from fuzzywuzzy import fuzz, process
import networkx as nx

class LoreSearchEngine:
    def __init__(self, config: Dict):
        """Initialize the search engine with configuration."""
        self.config = config
        self.database_path = config["database_path"]
        self.search_settings = config["search_settings"]
        self._index = {}
        self._relationship_graph = nx.DiGraph()
        self._build_index()
    
    def _build_index(self):
        """Build search index from all lore entries."""
        self._index = {}
        self._relationship_graph.clear()
        
        for category in self.config["categories"]:
            category_file = os.path.join(self.database_path, f"{category}.json")
            if os.path.exists(category_file):
                with open(category_file, 'r') as f:
                    data = json.load(f)
                    
                for entry_id, entry in data.get("entries", {}).items():
                    # Add to search index
                    self._index[entry_id] = {
                        "id": entry_id,
                        "name": entry.get("name", ""),
                        "category": entry.get("category", ""),
                        "description": entry.get("description", ""),
                        "tags": entry.get("tags", []),
                        "searchable_text": self._create_searchable_text(entry)
                    }
                    
                    # Add to relationship graph
                    self._relationship_graph.add_node(entry_id, **entry)
                    
                    # Add relationships to graph
                    for rel in entry.get("relationships", []):
                        target_id = rel.get("target_id")
                        rel_type = rel.get("relationship_type")
                        strength = rel.get("strength", 5.0)
                        
                        self._relationship_graph.add_edge(
                            entry_id, target_id,
                            relationship_type=rel_type,
                            strength=strength,
                            description=rel.get("description", "")
                        )
    
    def _create_searchable_text(self, entry: Dict) -> str:
        """Create a searchable text string from an entry."""
        text_parts = [
            entry.get("name", ""),
            entry.get("description", ""),
            " ".join(entry.get("tags", [])),
            entry.get("subcategory", "")
        ]
        
        # Add custom fields
        custom_fields = entry.get("custom_fields", {})
        for value in custom_fields.values():
            if isinstance(value, str):
                text_parts.append(value)
            elif isinstance(value, list):
                text_parts.extend([str(v) for v in value])
        
        return " ".join(filter(None, text_parts)).lower()
    
    def search(self, query: str, category: Optional[str] = None, 
               tags: Optional[List[str]] = None, limit: int = None) -> List[Dict]:
        """
        Search lore entries with fuzzy matching.
        
        Args:
            query: Search query string
            category: Filter by specific category
            tags: Filter by tags
            limit: Maximum number of results
        
        Returns:
            List of matching entries with scores
        """
        if not query.strip():
            return []
        
        query = query.lower()
        results = []
        
        for entry_id, indexed_entry in self._index.items():
            # Category filter
            if category and indexed_entry["category"] != category:
                continue
            
            # Tag filter
            if tags:
                entry_tags = set(indexed_entry["tags"])
                if not any(tag in entry_tags for tag in tags):
                    continue
            
            # Calculate relevance score
            score = self._calculate_relevance_score(query, indexed_entry)
            
            if score >= self.search_settings["fuzzy_threshold"] * 100:
                result = indexed_entry.copy()
                result["score"] = score
                results.append(result)
        
        # Sort by score (descending)
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # Apply limit
        limit = limit or self.search_settings["max_results"]
        return results[:limit]
    
    def _calculate_relevance_score(self, query: str, entry: Dict) -> float:
        """Calculate relevance score for an entry."""
        scores = []
        
        # Name matching (highest weight)
        name_score = fuzz.partial_ratio(query, entry["name"].lower())
        scores.append(name_score * 2.0)
        
        # Description matching
        desc_score = fuzz.partial_ratio(query, entry["description"].lower())
        scores.append(desc_score * 1.5)
        
        # Tag matching
        for tag in entry["tags"]:
            tag_score = fuzz.ratio(query, tag.lower())
            scores.append(tag_score * 1.2)
        
        # Full text matching
        text_score = fuzz.partial_ratio(query, entry["searchable_text"])
        scores.append(text_score)
        
        # Return weighted average
        if scores:
            return sum(scores) / len(scores)
        return 0.0
    
    def search_by_relationship(self, entry_id: str, relationship_type: Optional[str] = None,
                             max_depth: int = 2) -> List[Dict]:
        """
        Find entries related to a specific entry through relationships.
        
        Args:
            entry_id: ID of the source entry
            relationship_type: Filter by relationship type
            max_depth: Maximum relationship depth to explore
        
        Returns:
            List of related entries with relationship information
        """
        if entry_id not in self._relationship_graph:
            return []
        
        related_entries = []
        
        # Get direct relationships
        for target_id in self._relationship_graph.successors(entry_id):
            edge_data = self._relationship_graph.edges[entry_id, target_id]
            
            if relationship_type and edge_data.get("relationship_type") != relationship_type:
                continue
            
            if target_id in self._index:
                result = self._index[target_id].copy()
                result["relationship"] = edge_data
                result["depth"] = 1
                related_entries.append(result)
        
        # Get indirect relationships (if max_depth > 1)
        if max_depth > 1:
            for depth in range(2, max_depth + 1):
                current_level = [e for e in related_entries if e["depth"] == depth - 1]
                
                for entry in current_level:
                    for target_id in self._relationship_graph.successors(entry["id"]):
                        if target_id not in [e["id"] for e in related_entries]:
                            edge_data = self._relationship_graph.edges[entry["id"], target_id]
                            
                            if relationship_type and edge_data.get("relationship_type") != relationship_type:
                                continue
                            
                            if target_id in self._index:
                                result = self._index[target_id].copy()
                                result["relationship"] = edge_data
                                result["depth"] = depth
                                related_entries.append(result)
        
        return related_entries
    
    def get_relationship_graph(self, entry_ids: Optional[List[str]] = None) -> nx.DiGraph:
        """
        Get a subgraph of relationships for visualization.
        
        Args:
            entry_ids: List of entry IDs to include (None for all)
        
        Returns:
            NetworkX directed graph
        """
        if entry_ids:
            return self._relationship_graph.subgraph(entry_ids)
        return self._relationship_graph.copy()
    
    def suggest_related_entries(self, entry_id: str, limit: int = 5) -> List[Dict]:
        """
        Suggest entries that might be related based on content similarity.
        
        Args:
            entry_id: ID of the source entry
            limit: Maximum number of suggestions
        
        Returns:
            List of suggested entries with similarity scores
        """
        if entry_id not in self._index:
            return []
        
        source_entry = self._index[entry_id]
        suggestions = []
        
        for other_id, other_entry in self._index.items():
            if other_id == entry_id:
                continue
            
            # Calculate similarity based on tags and content
            similarity_score = self._calculate_similarity(source_entry, other_entry)
            
            if similarity_score > 0.3:  # Threshold for suggestions
                suggestion = other_entry.copy()
                suggestion["similarity_score"] = similarity_score
                suggestions.append(suggestion)
        
        # Sort by similarity score
        suggestions.sort(key=lambda x: x["similarity_score"], reverse=True)
        return suggestions[:limit]
    
    def _calculate_similarity(self, entry1: Dict, entry2: Dict) -> float:
        """Calculate similarity between two entries."""
        scores = []
        
        # Tag similarity
        tags1 = set(entry1["tags"])
        tags2 = set(entry2["tags"])
        if tags1 or tags2:
            tag_similarity = len(tags1.intersection(tags2)) / len(tags1.union(tags2))
            scores.append(tag_similarity * 2.0)
        
        # Category similarity
        if entry1["category"] == entry2["category"]:
            scores.append(1.0)
        
        # Text similarity
        text_similarity = fuzz.ratio(entry1["searchable_text"], entry2["searchable_text"]) / 100.0
        scores.append(text_similarity)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def refresh_index(self):
        """Refresh the search index with current data."""
        self._build_index()
    
    def get_statistics(self) -> Dict:
        """Get search index statistics."""
        stats = {
            "total_entries": len(self._index),
            "categories": {},
            "total_relationships": self._relationship_graph.number_of_edges(),
            "orphaned_entries": []
        }
        
        # Count entries by category
        for entry in self._index.values():
            category = entry["category"]
            stats["categories"][category] = stats["categories"].get(category, 0) + 1
        
        # Find orphaned entries (no relationships)
        for entry_id in self._index:
            if (self._relationship_graph.in_degree(entry_id) == 0 and 
                self._relationship_graph.out_degree(entry_id) == 0):
                stats["orphaned_entries"].append(entry_id)
        
        return stats
