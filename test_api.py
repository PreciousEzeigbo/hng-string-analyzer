from fastapi.testclient import TestClient
from app import app
from app import strings_db

import pytest


@pytest.fixture(autouse=True)
def clear_db_between_tests():
    strings_db.clear()
    yield
    strings_db.clear()

client = TestClient(app)


def test_create_string():
    """Test creating a new string"""
    response = client.post(
        "/strings",
        json={"value": "hello world"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["value"] == "hello world"
    assert data["properties"]["length"] == 11
    assert data["properties"]["word_count"] == 2
    assert data["properties"]["is_palindrome"] == False

def test_create_palindrome():
    """Test creating a palindrome string"""
    response = client.post(
        "/strings",
        json={"value": "racecar"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["properties"]["is_palindrome"] == True
    assert data["properties"]["word_count"] == 1

def test_create_duplicate_string():
    """Test creating duplicate string returns 409"""
    # Create first string
    client.post("/strings", json={"value": "test string duplicate"})
    
    # Try to create same string again
    response = client.post("/strings", json={"value": "test string duplicate"})
    assert response.status_code == 409

def test_get_string():
    """Test retrieving a specific string"""
    # Create string first
    client.post("/strings", json={"value": "retrieve me please"})
    
    # Retrieve it
    response = client.get("/strings/retrieve me please")
    assert response.status_code == 200
    data = response.json()
    assert data["value"] == "retrieve me please"

def test_get_nonexistent_string():
    """Test retrieving non-existent string returns 404"""
    response = client.get("/strings/this does not exist at all")
    assert response.status_code == 404

def test_get_all_strings():
    """Test getting all strings"""
    response = client.get("/strings")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "count" in data
    assert "filters_applied" in data

def test_filter_by_palindrome():
    """Test filtering by palindrome"""
    # Create some test strings
    client.post("/strings", json={"value": "noon"})
    client.post("/strings", json={"value": "not a palindrome here"})
    
    response = client.get("/strings?is_palindrome=true")
    assert response.status_code == 200
    data = response.json()
    # All returned strings should be palindromes
    for item in data["data"]:
        assert item["properties"]["is_palindrome"] == True

def test_filter_by_length():
    """Test filtering by length"""
    client.post("/strings", json={"value": "short"})
    client.post("/strings", json={"value": "this is a much longer string"})
    
    response = client.get("/strings?min_length=10")
    assert response.status_code == 200
    data = response.json()
    for item in data["data"]:
        assert item["properties"]["length"] >= 10

def test_filter_by_word_count():
    """Test filtering by word count"""
    client.post("/strings", json={"value": "single"})
    client.post("/strings", json={"value": "two words here"})
    
    response = client.get("/strings?word_count=1")
    assert response.status_code == 200
    data = response.json()
    for item in data["data"]:
        assert item["properties"]["word_count"] == 1

def test_filter_by_contains_character():
    """Test filtering by contains character"""
    client.post("/strings", json={"value": "zebra animal"})
    client.post("/strings", json={"value": "no special letter here"})
    
    response = client.get("/strings?contains_character=z")
    assert response.status_code == 200
    data = response.json()
    for item in data["data"]:
        assert "z" in item["value"].lower()

def test_natural_language_single_word_palindrome():
    """Test natural language query for single word palindromes"""
    client.post("/strings", json={"value": "level"})
    client.post("/strings", json={"value": "not a palindrome at all"})
    
    response = client.get("/strings/filter-by-natural-language?query=single word palindromic strings")
    assert response.status_code == 200
    data = response.json()
    assert "interpreted_query" in data
    assert data["interpreted_query"]["parsed_filters"]["word_count"] == 1
    assert data["interpreted_query"]["parsed_filters"]["is_palindrome"] == True

def test_natural_language_longer_than():
    """Test natural language query for length"""
    response = client.get("/strings/filter-by-natural-language?query=strings longer than 10 characters")
    assert response.status_code == 200
    data = response.json()
    assert "min_length" in data["interpreted_query"]["parsed_filters"]
    assert data["interpreted_query"]["parsed_filters"]["min_length"] == 11

def test_natural_language_contains_letter():
    """Test natural language query for contains letter"""
    response = client.get("/strings/filter-by-natural-language?query=strings containing the letter a")
    assert response.status_code == 200
    data = response.json()
    assert "contains_character" in data["interpreted_query"]["parsed_filters"]
    assert data["interpreted_query"]["parsed_filters"]["contains_character"] == "a"

def test_delete_string():
    """Test deleting a string"""
    # Create string
    client.post("/strings", json={"value": "delete me now"})
    
    # Delete it
    response = client.delete("/strings/delete me now")
    assert response.status_code == 204
    
    # Verify it's gone
    response = client.get("/strings/delete me now")
    assert response.status_code == 404

def test_delete_nonexistent_string():
    """Test deleting non-existent string returns 404"""
    response = client.delete("/strings/i really do not exist")
    assert response.status_code == 404

def test_character_frequency_map():
    """Test character frequency map is correct"""
    response = client.post("/strings", json={"value": "aabbcc"})
    data = response.json()
    freq_map = data["properties"]["character_frequency_map"]
    assert freq_map["a"] == 2
    assert freq_map["b"] == 2
    assert freq_map["c"] == 2

def test_unique_characters():
    """Test unique characters count"""
    response = client.post("/strings", json={"value": "aabbcc"})
    data = response.json()
    assert data["properties"]["unique_characters"] == 3

def test_invalid_value_type():
    """Test invalid value type returns 422"""
    response = client.post("/strings", json={"value": 123})
    assert response.status_code == 422

def test_missing_value_field():
    """Test missing value field returns 422"""
    response = client.post("/strings", json={"notvalue": "test"})
    assert response.status_code == 422

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])