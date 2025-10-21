from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.responses import Response
from pydantic import BaseModel, validator
from typing import Optional, Dict, List
from datetime import datetime
import hashlib
import re
from collections import Counter

app = FastAPI(
    title="String Analysis API",
    description="RESTful API service that analyzes strings and stores their computed properties",
    version="1.0.0"
)

# In-memory storage
strings_db: Dict[str, dict] = {}

# Request/Response Models
class StringInput(BaseModel):
    value: str
    
    @validator('value')
    def validate_value(cls, v):
        if not isinstance(v, str):
            raise ValueError('value must be a string')
        return v

class StringProperties(BaseModel):
    length: int
    is_palindrome: bool
    unique_characters: int
    word_count: int
    sha256_hash: str
    character_frequency_map: Dict[str, int]

class StringResponse(BaseModel):
    id: str
    value: str
    properties: StringProperties
    created_at: str

class StringListResponse(BaseModel):
    data: List[StringResponse]
    count: int
    filters_applied: Dict

class NaturalLanguageResponse(BaseModel):
    data: List[StringResponse]
    count: int
    interpreted_query: Dict

# Helper Functions
def compute_sha256(text: str) -> str:
    """Compute SHA-256 hash of the string"""
    return hashlib.sha256(text.encode()).hexdigest()

def is_palindrome(text: str) -> bool:
    """Check if string is a palindrome (case-insensitive)"""
    cleaned = text.lower().replace(" ", "")
    return cleaned == cleaned[::-1]

def count_unique_characters(text: str) -> int:
    """Count distinct characters in the string"""
    return len(set(text))

def count_words(text: str) -> int:
    """Count words separated by whitespace"""
    return len(text.split())

def get_character_frequency(text: str) -> Dict[str, int]:
    """Get character frequency map"""
    return dict(Counter(text))

def analyze_string(value: str) -> dict:
    """Analyze string and compute all properties"""
    sha256_hash = compute_sha256(value)
    
    properties = {
        "length": len(value),
        "is_palindrome": is_palindrome(value),
        "unique_characters": count_unique_characters(value),
        "word_count": count_words(value),
        "sha256_hash": sha256_hash,
        "character_frequency_map": get_character_frequency(value)
    }
    
    return {
        "id": sha256_hash,
        "value": value,
        "properties": properties,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }

def parse_natural_language_query(query: str) -> Dict:
    """Parse natural language query into filter parameters"""
    query_lower = query.lower()
    filters = {}
    
    # Parse palindrome
    if "palindrom" in query_lower:
        filters["is_palindrome"] = True
    
    # Parse word count
    if "single word" in query_lower or "one word" in query_lower:
        filters["word_count"] = 1
    elif "two word" in query_lower:
        filters["word_count"] = 2
    elif "three word" in query_lower:
        filters["word_count"] = 3
    
    # Parse length requirements
    length_match = re.search(r'longer than (\d+)', query_lower)
    if length_match:
        filters["min_length"] = int(length_match.group(1)) + 1
    
    length_match = re.search(r'shorter than (\d+)', query_lower)
    if length_match:
        filters["max_length"] = int(length_match.group(1)) - 1
    
    length_match = re.search(r'at least (\d+)', query_lower)
    if length_match:
        filters["min_length"] = int(length_match.group(1))
    
    # Parse character contains
    char_match = re.search(r'contain(?:ing|s)? (?:the )?letter ([a-z])', query_lower)
    if char_match:
        filters["contains_character"] = char_match.group(1)
    
    # Parse "first vowel" as 'a'
    if "first vowel" in query_lower:
        filters["contains_character"] = "a"
    
    return filters

def apply_filters(strings_list: List[dict], filters: Dict) -> List[dict]:
    """Apply filters to list of strings"""
    filtered = strings_list
    
    if "is_palindrome" in filters:
        filtered = [s for s in filtered if s["properties"]["is_palindrome"] == filters["is_palindrome"]]
    
    if "min_length" in filters:
        filtered = [s for s in filtered if s["properties"]["length"] >= filters["min_length"]]
    
    if "max_length" in filters:
        filtered = [s for s in filtered if s["properties"]["length"] <= filters["max_length"]]
    
    if "word_count" in filters:
        filtered = [s for s in filtered if s["properties"]["word_count"] == filters["word_count"]]
    
    if "contains_character" in filters:
        char = filters["contains_character"]
        filtered = [s for s in filtered if char in s["value"].lower()]
    
    return filtered

# API Endpoints 

@app.post("/strings", status_code=201, response_model=StringResponse)
async def create_string(string_input: StringInput):
    """Analyze and store a new string"""
    value = string_input.value
    
    # Check if string already exists
    sha256_hash = compute_sha256(value)
    if sha256_hash in strings_db:
        raise HTTPException(status_code=409, detail="String already exists in the system")
    
    # Analyze and store string
    result = analyze_string(value)
    strings_db[sha256_hash] = result
    
    return result

@app.get("/strings/filter-by-natural-language", response_model=NaturalLanguageResponse)
async def filter_by_natural_language(query: str = Query(..., min_length=1)):
    """Filter strings using natural language queries - MUST be before /strings/{string_value}"""
    # Parse natural language query
    filters = parse_natural_language_query(query)
    
    if not filters:
        raise HTTPException(status_code=400, detail="Unable to parse natural language query")
    
    # Apply filters
    all_strings = list(strings_db.values())
    filtered_strings = apply_filters(all_strings, filters)
    
    return {
        "data": filtered_strings,
        "count": len(filtered_strings),
        "interpreted_query": {
            "original": query,
            "parsed_filters": filters
        }
    }

@app.get("/strings", response_model=StringListResponse)
async def get_all_strings(
    is_palindrome: Optional[bool] = Query(None),
    min_length: Optional[int] = Query(None, ge=0),
    max_length: Optional[int] = Query(None, ge=0),
    word_count: Optional[int] = Query(None, ge=0),
    contains_character: Optional[str] = Query(None, min_length=1, max_length=1)
):
    """Get all strings with optional filtering"""
    # Validate parameters
    if min_length is not None and max_length is not None and min_length > max_length:
        raise HTTPException(status_code=400, detail="min_length cannot be greater than max_length")
    
    # Build filters dictionary
    filters = {}
    if is_palindrome is not None:
        filters["is_palindrome"] = is_palindrome
    if min_length is not None:
        filters["min_length"] = min_length
    if max_length is not None:
        filters["max_length"] = max_length
    if word_count is not None:
        filters["word_count"] = word_count
    if contains_character is not None:
        filters["contains_character"] = contains_character.lower()
    
    # Apply filters
    all_strings = list(strings_db.values())
    filtered_strings = apply_filters(all_strings, filters)
    
    return {
        "data": filtered_strings,
        "count": len(filtered_strings),
        "filters_applied": filters
    }

@app.get("/strings/{string_value}", response_model=StringResponse)
async def get_string(string_value: str = Path(...)):
    """Retrieve a specific string by its value"""
    sha256_hash = compute_sha256(string_value)
    
    if sha256_hash not in strings_db:
        raise HTTPException(status_code=404, detail="String does not exist in the system")
    
    return strings_db[sha256_hash]

@app.delete("/strings/{string_value}", status_code=204)
async def delete_string(string_value: str = Path(...)):
    """Delete a string from the system"""
    sha256_hash = compute_sha256(string_value)
    
    if sha256_hash not in strings_db:
        raise HTTPException(status_code=404, detail="String does not exist in the system")
    
    del strings_db[sha256_hash]
    return Response(status_code=204)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)