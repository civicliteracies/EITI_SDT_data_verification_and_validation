# merge_schemas.py
import json
from pathlib import Path

def rewrite_refs(node):
    """
    Recursively finds all '$ref' keys and rewrites their URN-based values
    to simple, local JSON Pointer references.
    """
    if isinstance(node, dict):
        if "$ref" in node and isinstance(node["$ref"], str):
            ref_value = node["$ref"]
            if ref_value == "urn:entity":
                node["$ref"] = "#/$defs/Entity Record Details"
            elif ref_value == "urn:relationship":
                node["$ref"] = "#/$defs/Relationship Record Details"
            elif ref_value.startswith("urn:components#"):
                # Rewrites 'urn:components#/$defs/Address' to '#/$defs/Address'
                node["$ref"] = f"#{ref_value.split('#', 1)[1]}"
        
        for key, value in node.items():
            rewrite_refs(value)
            
    elif isinstance(node, list):
        for item in node:
            rewrite_refs(item)

def main():
    """
    Loads all schema files, merges them into a single schema, rewrites
    the references, and saves the result.
    """
    schema_dir = Path(".")
    
    # 1. Load the main schema file as the base.
    with open(schema_dir / "statement.json", "r") as f:
        unified_schema = json.load(f)

    # 2. Define the other schemas to merge.
    files_to_merge = {
        "components.json": None,
        "entity-record.json": "Entity Record Details",
        "relationship-record.json": "Relationship Record Details",
    }

    print("Merging schema files...")
    for filename, defs_key in files_to_merge.items():
        with open(schema_dir / filename, "r") as f:
            schema = json.load(f)
            # Merge the '$defs' from the other files.
            if "$defs" in schema:
                unified_schema["$defs"].update(schema["$defs"])
            # If a top-level schema needs to be referenced, add it to '$defs'.
            if defs_key:
                top_level_def = {k: v for k, v in schema.items() if not k.startswith("$")}
                unified_schema["$defs"][defs_key] = top_level_def
                
    # 3. Recursively rewrite all URN-based references.
    print("Rewriting URN references...")
    rewrite_refs(unified_schema)

    # 4. Save the final, self-contained schema.
    output_file = "unified_schema.json"
    print(f"Writing unified schema to: {output_file}")
    with open(output_file, "w") as f:
        json.dump(unified_schema, f, indent=2)

    print("Done. 'unified_schema.json' is ready for datamodel-code-generator.")

if __name__ == "__main__":
    main()
