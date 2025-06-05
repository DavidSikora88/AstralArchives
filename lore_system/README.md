# Astral Archives Lore Management System

A comprehensive system for tracking, organizing, and expanding the lore of the Astrallum world. This system provides structured data storage, relationship tracking, consistency validation, and powerful search capabilities.

> **Status**: ✅ Successfully migrated 67 existing lore entries from CSV and Markdown files

## Features

### 1. Structured Database
- **JSON-based storage** with schema validation
- **10 categories**: characters, locations, events, organizations, artifacts, cultures, religions, technologies, creatures, concepts
- **Flexible custom fields** for category-specific data
- **Metadata tracking** (creation date, version, author, status)

### 2. Relationship System
- **12 relationship types**: related_to, part_of, created_by, destroyed_by, located_in, member_of, enemy_of, ally_of, predecessor_of, successor_of, influenced_by, influences
- **Bidirectional relationships** with strength ratings (0-10)
- **Relationship descriptions** for context
- **Graph-based visualization** support

### 3. Search & Discovery
- **Fuzzy text search** across all fields
- **Category and tag filtering**
- **Relationship-based queries**
- **Similarity suggestions** for related content
- **Full-text indexing** for fast retrieval

### 4. Consistency Validation
- **Date consistency** checking for events and character lifespans
- **Location hierarchy** validation (no circular containment)
- **Character relationship** conflict detection
- **Orphaned reference** detection
- **Duplicate name** checking within categories

### 5. Export & Integration
- **Markdown export** for documentation
- **JSON backup** system
- **Template system** for new entries
- **Migration tools** for existing lore

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize the system:
```bash
cd lore_system
python lore_manager.py --help
```

## Quick Start

### Migrate Existing Lore
```bash
python migrate_existing_lore.py
```

### Create a New Entry
```bash
python lore_manager.py create --category characters --name "Aria Stormwind" --description "A skilled mage from Zeloria" --tags "mage,zeloria,protagonist"
```

### Search Lore
```bash
python lore_manager.py search "Zeloria"
python lore_manager.py search "magic" --category technologies
```

### List Entries
```bash
python lore_manager.py list-entries --category locations --limit 10
```

### Add Relationships
```bash
python lore_manager.py add-relationship <source_id> <target_id> located_in --description "Character lives in this city"
```

### Validate Consistency
```bash
python lore_manager.py validate
```

### Create Backup
```bash
python lore_manager.py backup
```

### Export to Markdown
```bash
python lore_manager.py export-markdown --output-dir docs/lore
```

## System Architecture

### Directory Structure
```
lore_system/
├── config.json              # System configuration
├── lore_manager.py          # Main management interface
├── search_engine.py         # Search and indexing
├── consistency_checker.py   # Validation logic
├── migrate_existing_lore.py # Migration script
├── database/
│   ├── schema.json         # Entry validation schema
│   ├── characters.json     # Character entries
│   ├── locations.json      # Location entries
│   └── ...                 # Other category files
├── templates/
│   ├── character_template.json
│   ├── location_template.json
│   └── ...                 # Templates for each category
├── exports/                # Exported files
├── backups/               # Database backups
└── README.md              # This file
```

### Entry Structure
Each lore entry follows this structure:
```json
{
  "id": "unique-uuid",
  "name": "Entry Name",
  "category": "characters",
  "subcategory": "protagonist",
  "description": "Detailed description...",
  "tags": ["tag1", "tag2"],
  "relationships": [
    {
      "target_id": "other-entry-id",
      "relationship_type": "located_in",
      "description": "Context about the relationship",
      "strength": 8.5
    }
  ],
  "metadata": {
    "created_date": "2024-01-01T00:00:00",
    "modified_date": "2024-01-01T00:00:00",
    "author": "system",
    "version": 1,
    "status": "approved"
  },
  "custom_fields": {
    "age": "25",
    "occupation": "Mage",
    "abilities": ["Fire Magic", "Teleportation"]
  }
}
```

## Categories and Templates

### Characters
- **Purpose**: People, beings, and entities in your world
- **Custom Fields**: age, species, occupation, abilities, equipment, goals, relationships
- **Example**: Eternal Chronoglyph, rulers, heroes, villains

### Locations
- **Purpose**: Places, regions, buildings, and geographical features
- **Custom Fields**: type, population, climate, government, resources, defenses
- **Example**: Astrallum, states, cities, dungeons, landmarks

### Events
- **Purpose**: Historical events, battles, ceremonies, disasters
- **Custom Fields**: date, duration, participants, causes, consequences, impact
- **Example**: The Collapse, wars, festivals, discoveries

### Organizations
- **Purpose**: Groups, factions, guilds, governments, religions
- **Custom Fields**: type, leadership, goals, resources, territory, membership
- **Example**: Governments, guilds, secret societies, military orders

### Artifacts
- **Purpose**: Important items, relics, weapons, tools
- **Custom Fields**: origin, creator, function, power_level, current_owner
- **Example**: Ancient Relics, magical items, technological devices

### Cultures
- **Purpose**: Societies, ethnic groups, ways of life
- **Custom Fields**: traits, values, customs, language, territory, history
- **Example**: Sabernes, Vylhe, Cawan, Orodno cultures

### Religions
- **Purpose**: Belief systems, deities, spiritual practices
- **Custom Fields**: beliefs, practices, clergy, holy_sites, influence
- **Example**: Various faiths mentioned in world overview

### Technologies
- **Purpose**: Technological systems, both ancient and current
- **Custom Fields**: function, complexity, availability, true_nature
- **Example**: "Magic" systems that are actually technology

### Creatures
- **Purpose**: Animals, monsters, magical beings
- **Custom Fields**: habitat, behavior, abilities, threat_level, rarity
- **Example**: Fantastical creatures in Astrallum

### Concepts
- **Purpose**: Abstract ideas, philosophies, phenomena
- **Custom Fields**: significance, manifestations, related_theories
- **Example**: Eclipse Era, The Lost Epoch, magic vs technology

## Workflow for Expanding Lore

### 1. Planning New Content
1. **Identify gaps** using the search system
2. **Check consistency** with existing lore
3. **Use templates** for structured creation
4. **Plan relationships** with existing entries

### 2. Creating Entries
1. **Start with template** for your category
2. **Fill required fields** (name, category, description)
3. **Add relevant tags** for discoverability
4. **Include custom fields** specific to the category
5. **Validate entry** before saving

### 3. Building Relationships
1. **Identify connections** to existing entries
2. **Choose appropriate relationship types**
3. **Add descriptions** for context
4. **Set strength ratings** (1-10 scale)
5. **Verify bidirectional consistency**

### 4. Maintaining Consistency
1. **Run validation** regularly
2. **Review consistency reports**
3. **Resolve conflicts** and contradictions
4. **Update related entries** when making changes
5. **Document major changes**

### 5. Documentation and Export
1. **Export to markdown** for readable documentation
2. **Create backups** before major changes
3. **Generate reports** for overview
4. **Share with collaborators**

## Best Practices

### Naming Conventions
- Use **descriptive, unique names**
- Include **titles or epithets** for clarity
- Avoid **abbreviations** in main names
- Use **consistent spelling** across entries

### Descriptions
- Write **clear, concise descriptions**
- Include **key identifying information**
- Mention **important relationships**
- Avoid **contradicting existing lore**

### Tags
- Use **lowercase tags**
- Include **category-specific tags**
- Add **thematic tags** (magic, technology, politics)
- Use **location tags** for geographical context

### Relationships
- **Be specific** about relationship types
- **Add context** in descriptions
- **Use appropriate strength** ratings
- **Maintain logical consistency**

### Custom Fields
- **Use consistent field names** across similar entries
- **Include measurement units** where applicable
- **Use arrays** for multiple values
- **Keep data types consistent**

## Troubleshooting

### Common Issues
1. **Validation errors**: Check required fields and data types
2. **Search not finding entries**: Refresh the search index
3. **Relationship errors**: Verify both entries exist
4. **Consistency warnings**: Review and resolve conflicts

### Performance Tips
- **Regular backups** prevent data loss
- **Periodic validation** catches issues early
- **Index refresh** after bulk changes
- **Template usage** ensures consistency

## Contributing

When adding new lore:
1. **Follow the established patterns**
2. **Use the validation system**
3. **Document your changes**
4. **Test relationships**
5. **Export updated documentation**

## Support

For issues or questions:
1. Check the **consistency validation** output
2. Review **migration reports** for reference
3. Examine **existing entries** for patterns
4. Use **templates** as starting points
