# Migration Guide: V1 to V2

This guide helps existing users migrate from V1 (voter-list-specific) to V2 (generic schema-driven) of the Agentic Document Extractor.

## Overview of Changes

V2 transforms the system from a voter-list-specific tool into a **generic, schema-driven document extraction platform**. The core functionality remains excellent — we've simply removed domain-specific code to make the system work with any document type.

## Key Changes

### What Changed

1. **Removed Built-in Schemas** — `voter_list` and `agent_details` schemas are no longer built-in
2. **Removed Domain-Specific Methods** — `extract_voter_list()` and `extract_agent_details()` methods removed
3. **Removed CLI Command** — `extract-voters` command removed
4. **Generalized CSV Export** — Now works with any array data, not just voters
5. **Updated Imports** — Removed voter/agent schema exports

### What Stayed the Same

✅ **All core functionality** — OCR, layout detection, VLM analysis
✅ **Generic extraction** — The `extract()` method (always accepted any schema)
✅ **CLI schema loading** — Can still load schemas from files
✅ **Generic schemas** — `generic_form` and `table` schemas still available
✅ **Python API** — `DocumentProcessor` class interface unchanged

## Breaking Changes

### 1. Built-in Schema Names

**V1:**
```python
# Built-in schemas: voter_list, agent_details, generic_form
data = processor.extract_schema(result, "voter_list")
data = processor.extract_schema(result, "agent_details")
```

**V2:**
```python
# Built-in schemas: generic_form, table
data = processor.extract_schema(result, "generic_form")
data = processor.extract_schema(result, "table")

# For voter/agent extraction, load schema from file
import json
with open("examples/schemas/voter_list_schema.json") as f:
    schema = json.load(f)
data = processor.extract_schema(result, schema)
```

### 2. Dedicated Methods Removed

**V1:**
```python
# Dedicated extraction methods
voter_data = processor.extract_voter_list(result)
agent_data = processor.extract_agent_details(result)
```

**V2:**
```python
# Use generic extract_schema() with custom schema
import json

# Load voter schema
with open("examples/schemas/voter_list_schema.json") as f:
    voter_schema = json.load(f)
voter_data = processor.extract_schema(result, voter_schema)

# Load agent schema
with open("examples/schemas/agent_details_schema.json") as f:
    agent_schema = json.load(f)
agent_data = processor.extract_schema(result, agent_schema)
```

### 3. CLI Command Removed

**V1:**
```bash
# Dedicated voter extraction command
docextract extract-voters voter_list.pdf --output voters.csv
```

**V2:**
```bash
# Use generic extract command with schema file
docextract extract voter_list.pdf \
  --schema examples/schemas/voter_list_schema.json \
  --output voters.json

# CSV export happens automatically for array data
```

### 4. Import Changes

**V1:**
```python
from agentic_document_extractor import (
    VOTER_LIST_SCHEMA,
    AGENT_DETAILS_SCHEMA,
    GENERIC_FORM_SCHEMA
)
```

**V2:**
```python
from agentic_document_extractor import (
    GENERIC_FORM_SCHEMA,
    TABLE_SCHEMA,
    get_schema
)

# Or load from files
import json
with open("examples/schemas/voter_list_schema.json") as f:
    VOTER_LIST_SCHEMA = json.load(f)
```

## Migration Steps

### Step 1: Update Dependencies

```bash
# Pull latest code
git pull origin main

# Reinstall package
pip install -e .
```

### Step 2: Update Code

#### If using built-in schemas:

**Before:**
```python
from agentic_document_extractor import DocumentProcessor, VOTER_LIST_SCHEMA

processor = DocumentProcessor()
result = processor.process("document.pdf")
data = processor.extract_voter_list(result)
```

**After:**
```python
import json
from agentic_document_extractor import DocumentProcessor

processor = DocumentProcessor()
result = processor.process("document.pdf")

# Load schema from file
with open("examples/schemas/voter_list_schema.json") as f:
    schema = json.load(f)

# Use generic extract_schema method
data = processor.extract_schema(result, schema)
```

#### If using CLI:

**Before:**
```bash
docextract extract-voters voters.pdf --output data.csv
```

**After:**
```bash
docextract extract voters.pdf \
  --schema examples/schemas/voter_list_schema.json \
  --output data.json

# CSV files are auto-generated for array fields
```

### Step 3: Copy Schema Files (if needed)

If you want schemas in your project directory:

```bash
# Copy schema files to your project
cp examples/schemas/voter_list_schema.json ./schemas/
cp examples/schemas/agent_details_schema.json ./schemas/

# Use in your code
with open("schemas/voter_list_schema.json") as f:
    schema = json.load(f)
```

### Step 4: Update Tests

**Before:**
```python
def test_voter_extraction():
    processor = DocumentProcessor()
    result = processor.process("voter_list.pdf")
    data = processor.extract_voter_list(result)
    assert "voters" in data
```

**After:**
```python
import json

def test_voter_extraction():
    processor = DocumentProcessor()
    result = processor.process("voter_list.pdf")

    with open("examples/schemas/voter_list_schema.json") as f:
        schema = json.load(f)

    data = processor.extract_schema(result, schema)
    assert "voters" in data
```

## Comparison Table

| Feature | V1 | V2 |
|---------|----|----|
| Built-in voter schema | ✅ Yes | ❌ No (use file) |
| Built-in agent schema | ✅ Yes | ❌ No (use file) |
| Generic form schema | ✅ Yes | ✅ Yes |
| Table schema | ❌ No | ✅ Yes |
| Custom schemas | ✅ Yes | ✅ Yes |
| `extract_voter_list()` | ✅ Yes | ❌ Removed |
| `extract_agent_details()` | ✅ Yes | ❌ Removed |
| `extract_schema()` | ✅ Yes | ✅ Yes |
| CLI `extract-voters` | ✅ Yes | ❌ Removed |
| CLI `extract --schema file` | ✅ Yes | ✅ Yes |
| Auto CSV export | ❌ Voters only | ✅ Any array |
| Schema file loading | ✅ Yes | ✅ Yes |

## Benefits of V2

### 1. Work with Any Document Type

**Before (V1):** Limited to voter lists and agent forms

**After (V2):** Extract from invoices, receipts, forms, tables, or any document type

```python
# Invoice extraction
with open("examples/schemas/invoice_schema.json") as f:
    schema = json.load(f)
data = processor.extract_schema(result, schema)

# Receipt extraction
with open("examples/schemas/receipt_schema.json") as f:
    schema = json.load(f)
data = processor.extract_schema(result, schema)

# Custom schema
custom_schema = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "date": {"type": "string"}
    }
}
data = processor.extract_schema(result, custom_schema)
```

### 2. No Code Changes for New Document Types

**Before (V1):** Had to modify source code to add new document types

**After (V2):** Just create a new schema JSON file

```bash
# Create new schema
cat > my_schema.json << 'EOF'
{
  "type": "object",
  "properties": {
    "field1": {"type": "string"},
    "field2": {"type": "number"}
  }
}
EOF

# Use immediately
docextract extract document.pdf --schema my_schema.json --output data.json
```

### 3. Better CSV Export

**Before (V1):** Only exported voter arrays to CSV

**After (V2):** Auto-exports any top-level array field

```python
# Schema with multiple arrays
schema = {
    "type": "object",
    "properties": {
        "customers": {"type": "array", "items": {...}},
        "products": {"type": "array", "items": {...}},
        "transactions": {"type": "array", "items": {...}}
    }
}

# All three arrays exported to separate CSV files:
# - customers_page_1.csv
# - products_page_1.csv
# - transactions_page_1.csv
```

### 4. Follows Industry Standards

V2 aligns with landing.ai and other professional document AI platforms:
- Schema-driven architecture
- No domain-specific code
- Flexible and extensible
- Best-practice patterns

## Example: Complete Migration

### V1 Code

```python
# old_code.py
from agentic_document_extractor import (
    DocumentProcessor,
    VOTER_LIST_SCHEMA,
    AGENT_DETAILS_SCHEMA
)

def extract_voters(pdf_path):
    processor = DocumentProcessor()
    result = processor.process(pdf_path)
    return processor.extract_voter_list(result)

def extract_agents(pdf_path):
    processor = DocumentProcessor()
    result = processor.process(pdf_path)
    return processor.extract_agent_details(result)

# Usage
voters = extract_voters("voters.pdf")
agents = extract_agents("agents.pdf")
```

### V2 Code

```python
# new_code.py
import json
from agentic_document_extractor import DocumentProcessor

def extract_with_schema(pdf_path, schema_path):
    """Generic extraction function for any document type."""
    processor = DocumentProcessor()
    result = processor.process(pdf_path)

    with open(schema_path) as f:
        schema = json.load(f)

    return processor.extract_schema(result, schema)

# Usage
voters = extract_with_schema(
    "voters.pdf",
    "examples/schemas/voter_list_schema.json"
)

agents = extract_with_schema(
    "agents.pdf",
    "examples/schemas/agent_details_schema.json"
)

# Now also works with any other document type!
invoices = extract_with_schema(
    "invoice.pdf",
    "examples/schemas/invoice_schema.json"
)
```

## FAQs

### Q: Can I still extract voter lists?

**A:** Yes! The voter list schema is now in `examples/schemas/voter_list_schema.json`. Load it as a file and use `extract_schema()`.

### Q: Why remove built-in schemas?

**A:** To make the system truly generic. Built-in schemas made the code domain-specific and harder to maintain. Loading schemas from files is just as easy and much more flexible.

### Q: Will my old code break?

**A:** Yes, if you used `extract_voter_list()`, `extract_agent_details()`, or imported `VOTER_LIST_SCHEMA`/`AGENT_DETAILS_SCHEMA`. Follow the migration steps above to update.

### Q: Is there a performance difference?

**A:** No. Loading a schema from a JSON file has negligible overhead. Extraction performance is identical.

### Q: Can I keep schemas in my codebase?

**A:** Yes! You can:
1. Copy schema files to your project
2. Load them as constants: `VOTER_SCHEMA = json.load(...)`
3. Version control them with your code

### Q: What if I need the old behavior?

**A:** Create wrapper functions (see "Example: Complete Migration" above). You can replicate the V1 API in your own code by wrapping `extract_schema()` with schema file loading.

## Need Help?

If you encounter issues during migration:
1. Check this migration guide
2. Review the [Schema Guide](SCHEMA_GUIDE.md)
3. Look at example schemas in `examples/schemas/`
4. Open an issue on GitHub with:
   - Your V1 code
   - What you've tried
   - Error messages (if any)

## Summary

V2 doesn't remove functionality — it makes the system **more powerful and flexible** by removing domain-specific constraints. The migration requires minimal code changes (mainly loading schemas from files instead of importing constants), but unlocks the ability to extract from **any document type** without touching the source code.

Welcome to the generic, schema-driven future of document extraction!
