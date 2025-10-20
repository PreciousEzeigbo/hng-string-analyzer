# String Analysis API

A RESTful API service built with FastAPI that analyzes strings and stores their computed properties including length, palindrome detection, character frequency, and more.

## Features

- **String Analysis**: Automatically computes multiple properties for each string
- **Palindrome Detection**: Case-insensitive palindrome checking
- **Character Frequency Mapping**: Detailed breakdown of character occurrences
- **Advanced Filtering**: Query strings by multiple criteria
- **Natural Language Queries**: Filter strings using plain English queries
- **SHA-256 Hashing**: Unique identification for each string

## Requirements

- Python 3.8+
- FastAPI
- Uvicorn
- Pydantic

## Local Setup Instructions

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd string-analysis-api
```

### 2. Create a Virtual Environment

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
# Development mode
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Or using Python directly
python app.py
```

The API will be available at `http://localhost:8000`

### 5. Access API Documentation

Once running, visit:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## AWS EC2 Deployment Instructions

### 1. Launch EC2 Instance

- Choose Ubuntu Server 22.04 LTS
- Instance type: t2.micro (or larger)
- Configure security group to allow:
  - SSH (port 22) from your IP
  - HTTP (port 80) from anywhere
  - Custom TCP (port 8000) from anywhere

### 2. Connect to EC2 Instance

```bash
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

### 3. Install Dependencies on EC2

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3-pip python3-venv -y

# Clone your repository
git clone <your-repo-url>
cd string-analysis-api

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 4. Run with Uvicorn (Production)

```bash
# Run in background
nohup uvicorn app:app --host 0.0.0.0 --port 8000 &
```

### 5. Optional: Setup with Nginx and Systemd

Create systemd service file:

```bash
sudo nano /etc/systemd/system/stringapi.service
```

Add content:

```ini
[Unit]
Description=String Analysis API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/string-analysis-api
Environment="PATH=/home/ubuntu/string-analysis-api/venv/bin"
ExecStart=/home/ubuntu/string-analysis-api/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
```

Enable and start service:

```bash
sudo systemctl enable stringapi
sudo systemctl start stringapi
sudo systemctl status stringapi
```

## API Endpoints

### 1. Create/Analyze String

**POST** `/strings`

```json
{
  "value": "hello world"
}
```

**Response (201):**

```json
{
  "id": "sha256_hash",
  "value": "hello world",
  "properties": {
    "length": 11,
    "is_palindrome": false,
    "unique_characters": 8,
    "word_count": 2,
    "sha256_hash": "abc123...",
    "character_frequency_map": {
      "h": 1,
      "e": 1,
      "l": 3,
      "o": 2,
      " ": 1,
      "w": 1,
      "r": 1,
      "d": 1
    }
  },
  "created_at": "2025-08-27T10:00:00Z"
}
```

### 2. Get Specific String

**GET** `/strings/{string_value}`

### 3. Get All Strings with Filtering

**GET** `/strings?is_palindrome=true&min_length=5&max_length=20&word_count=2&contains_character=a`

**Query Parameters:**

- `is_palindrome`: boolean (true/false)
- `min_length`: integer (minimum string length)
- `max_length`: integer (maximum string length)
- `word_count`: integer (exact word count)
- `contains_character`: string (single character)

### 4. Natural Language Filtering

**GET** `/strings/filter-by-natural-language?query=all%20single%20word%20palindromic%20strings`

**Example Queries:**

- "all single word palindromic strings"
- "strings longer than 10 characters"
- "palindromic strings that contain the first vowel"
- "strings containing the letter z"

### 5. Delete String

**DELETE** `/strings/{string_value}`

**Response:** 204 No Content

## Error Responses

- **400 Bad Request**: Invalid request body or query parameters
- **404 Not Found**: String does not exist
- **409 Conflict**: String already exists
- **422 Unprocessable Entity**: Invalid data type

## Environment Variables

No environment variables are required for basic operation. The application uses in-memory storage by default.

For production, consider:

- `DATABASE_URL`: Connection string for persistent database
- `API_KEY`: Optional API key authentication
- `PORT`: Custom port (default: 8000)

## Testing

### Manual Testing with cURL

```bash
# Create a string
curl -X POST http://localhost:8000/strings \
  -H "Content-Type: application/json" \
  -d '{"value": "racecar"}'

# Get a string
curl http://localhost:8000/strings/racecar

# Get all palindromes
curl "http://localhost:8000/strings?is_palindrome=true"

# Natural language query
curl "http://localhost:8000/strings/filter-by-natural-language?query=single%20word%20palindromic%20strings"

# Delete a string
curl -X DELETE http://localhost:8000/strings/racecar
```

### Testing with Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Create string
response = requests.post(f"{BASE_URL}/strings", json={"value": "racecar"})
print(response.json())

# Get string
response = requests.get(f"{BASE_URL}/strings/racecar")
print(response.json())

# Filter strings
response = requests.get(f"{BASE_URL}/strings", params={"is_palindrome": True})
print(response.json())
```

### Run Test Suite

```
pytest test_app.py -v
```

## Tech Stack

- **Framework**: FastAPI
- **Server**: Uvicorn (ASGI)
- **Validation**: Pydantic
- **Language**: Python 3.8+

The current implementation uses in-memory storage.

## Project Structure

```
string-analysis-api/
├── app.py                 # Main FastAPI application
├── test_app.py           # Test suite
├── requirements.txt       # Python dependencies
├── README.md             # This file
```

## Notes

- SHA-256 is used as the unique identifier for strings
- Palindrome checking is case-insensitive
- Character frequency includes all characters (spaces, punctuation, etc.)
- Natural language parsing supports common patterns but may not cover all cases

## Support

For issues or questions, please open an issue in the GitHub repository.
