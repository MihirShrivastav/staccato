"""
JSON Schema for LLM API responses in Staccato.

This module defines the JSON schema that should be passed to LLM APIs
to ensure structured responses that match the expected format for
document chunking events.
"""

# JSON Schema for the LLM response format
LLM_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "events": {
            "type": "array",
            "description": "List of structural events identified in the document pages",
            "items": {
                "type": "object",
                "properties": {
                    "event": {
                        "type": "string",
                        "enum": ["STARTS", "ENDS", "CONTINUATION"],
                        "description": "The type of structural event"
                    },
                    "level": {
                        "type": "string",
                        "description": "The semantic level of the element (e.g., 'section', 'table', 'list_item', 'code_block', 'paragraph')",
                        "examples": ["section", "table", "list_item", "code_block", "paragraph"]
                    },
                    "page_number": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "The 1-indexed page number where this event occurred"
                    },
                    "title": {
                        "type": "string",
                        "description": "The title of the element, required for STARTS events, optional for others"
                    },
                    "fingerprint": {
                        "type": "string",
                        "description": "A short, unique snippet of text that anchors the event's position on the page. For STARTS events: words at the beginning of the block. For ENDS events: words at the end of the block or beginning of the next block."
                    }
                },
                "required": ["event", "level", "page_number"],
                "additionalProperties": False
            },
            "minItems": 0
        }
    },
    "required": ["events"],
    "additionalProperties": False
}

# Simplified schema for OpenAI's structured output (without unsupported features)
OPENAI_SIMPLE_SCHEMA = {
    "type": "object",
    "properties": {
        "events": {
            "type": "array",
            "description": "List of structural events identified in the document pages",
            "items": {
                "type": "object",
                "properties": {
                    "event": {
                        "type": "string",
                        "enum": ["STARTS", "ENDS", "CONTINUATION"],
                        "description": "The type of structural event"
                    },
                    "level": {
                        "type": "string",
                        "description": "The semantic level of the element"
                    },
                    "page_number": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "The 1-indexed page number where this event occurred"
                    },
                    "title": {
                        "type": "string",
                        "description": "The title of the element (required for STARTS events)"
                    },
                    "fingerprint": {
                        "type": "string",
                        "description": "A short snippet of text that anchors the event's position"
                    }
                },
                "required": ["event", "level", "page_number"],
                "additionalProperties": False
            }
        }
    },
    "required": ["events"],
    "additionalProperties": False
}

# OpenAI-compatible response format specification (simplified)
OPENAI_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "document_structure_analysis",
        "description": "Structured analysis of document pages identifying semantic blocks and their boundaries",
        "schema": OPENAI_SIMPLE_SCHEMA,
        "strict": True
    }
}

# Fallback format for basic JSON object mode
BASIC_JSON_FORMAT = {
    "type": "json_object"
}

# Alternative format for providers that use different schema specifications
GENERIC_RESPONSE_FORMAT = {
    "type": "json_object",
    "schema": LLM_RESPONSE_SCHEMA
}

def get_response_format(provider: str = "openai") -> dict:
    """
    Get the appropriate response format specification for the given provider.
    
    Args:
        provider: The LLM provider ("openai", "google", "lmstudio", etc.)
        
    Returns:
        Dictionary containing the response format specification
    """
    if provider == "openai":
        return OPENAI_RESPONSE_FORMAT
    else:
        # For Google, LM Studio, and other providers, use generic format
        return OPENAI_RESPONSE_FORMAT

def get_json_schema() -> dict:
    """
    Get the raw JSON schema for the LLM response format.
    
    Returns:
        Dictionary containing the JSON schema
    """
    return LLM_RESPONSE_SCHEMA


# Example of a valid response that matches this schema
EXAMPLE_RESPONSE = {
    "events": [
        {
            "event": "ENDS",
            "level": "section",
            "page_number": 5,
            "fingerprint": "3. New Section"
        },
        {
            "event": "STARTS",
            "level": "section",
            "title": "3. New Section",
            "page_number": 5,
            "fingerprint": "3. New Section"
        },
        {
            "event": "CONTINUATION",
            "level": "section",
            "page_number": 6
        },
        {
            "event": "STARTS",
            "level": "table",
            "title": "Performance Metrics",
            "page_number": 6,
            "fingerprint": "Table 1: Performance"
        },
        {
            "event": "ENDS",
            "level": "table",
            "page_number": 7,
            "fingerprint": "4. Conclusion"
        }
    ]
}
