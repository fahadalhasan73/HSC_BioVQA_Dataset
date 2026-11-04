# Shared Resources

`taxonomy/` contains the single canonical taxonomy used by all agents. Do not create agent-specific copies.

`schemas/` contains JSON Schemas for the three primary record types.

`config/taxonomy_usage_config.json` contains cross-agent rules. Agent behavior belongs in agent-specific YAML files, not inside the taxonomy.
