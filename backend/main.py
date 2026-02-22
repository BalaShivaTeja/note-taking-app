import os
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import uvicorn

# Security Configuration
# Use environment variable for secret key in production
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(title="Note Taking API with Auth")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory databases
users_db = {}  # username: {username, hashed_password}
notes_db = {}  # username: [list of notes]

# Pydantic Models
class User(BaseModel):
    username: str

class UserCreate(BaseModel):
    username: str
    password: str

    @validator('username')
    def username_must_be_valid(cls, v):
        v = v.strip()
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if len(v) > 50:
            raise ValueError('Username must be at most 50 characters')
        return v

    @validator('password')
    def password_must_be_strong(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

class Token(BaseModel):
    access_token: str
    token_type: str

class Note(BaseModel):
    id: int
    title: str
    content: str
    created_at: str
    updated_at: Optional[str] = None

class NoteCreate(BaseModel):
    title: str
    content: str

    @validator('title')
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()

    @validator('content')
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Content cannot be empty')
        return v.strip()

class NoteUpdate(BaseModel):
    title: str
    content: str

    @validator('title')
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()

    @validator('content')
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Content cannot be empty')
        return v.strip()

# Helper Functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(username: str):
    if username in users_db:
        return users_db[username]
    return None

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(username)
    if user is None:
        raise credentials_exception
    return username

# Authentication Endpoints
@app.post("/signup", response_model=User)
def signup(user: UserCreate):
    """Register a new user"""
    username = user.username.strip().lower()
    if username in users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    users_db[username] = {
        "username": username,
        "hashed_password": hashed_password
    }
    notes_db[username] = []  # Initialize empty notes list for user
    
    return {"username": username}

@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login to get access token (OAuth2 form format)"""
    username = form_data.username.strip().lower()
    user = authenticate_user(username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login", response_model=Token)
def login_json(credentials: UserCreate):
    """Login endpoint for JSON requests"""
    username = credentials.username.strip().lower()
    user = authenticate_user(username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Protected Note Endpoints
@app.get("/notes", response_model=List[Note])
def get_all_notes(current_user: str = Depends(get_current_user)):
    """Get all notes for the current user"""
    return notes_db.get(current_user, [])

@app.post("/notes", response_model=Note)
def create_note(
    note: NoteCreate, 
    current_user: str = Depends(get_current_user)
):
    """Create a new note for the current user"""
    user_notes = notes_db.get(current_user, [])
    
    new_id = max([n["id"] for n in user_notes], default=0) + 1
    now = datetime.now().isoformat()
    new_note = {
        "id": new_id, 
        "title": note.title, 
        "content": note.content,
        "created_at": now,
        "updated_at": now
    }
    
    user_notes.append(new_note)
    notes_db[current_user] = user_notes
    
    return new_note

@app.get("/notes/{note_id}", response_model=Note)
def get_note(note_id: int, current_user: str = Depends(get_current_user)):
    """Get a specific note by ID"""
    user_notes = notes_db.get(current_user, [])
    for note in user_notes:
        if note["id"] == note_id:
            return note
    raise HTTPException(status_code=404, detail="Note not found")

@app.put("/notes/{note_id}", response_model=Note)
def update_note(
    note_id: int,
    note_update: NoteUpdate,
    current_user: str = Depends(get_current_user)
):
    """Update a note by ID"""
    user_notes = notes_db.get(current_user, [])
    for i, note in enumerate(user_notes):
        if note["id"] == note_id:
            user_notes[i]["title"] = note_update.title
            user_notes[i]["content"] = note_update.content
            user_notes[i]["updated_at"] = datetime.now().isoformat()
            notes_db[current_user] = user_notes
            return user_notes[i]
    raise HTTPException(status_code=404, detail="Note not found")

@app.delete("/notes/{note_id}")
def delete_note(note_id: int, current_user: str = Depends(get_current_user)):
    """Delete a note by ID"""
    user_notes = notes_db.get(current_user, [])
    original_count = len(user_notes)
    notes_db[current_user] = [n for n in user_notes if n["id"] != note_id]
    if len(notes_db[current_user]) == original_count:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"message": "Note deleted successfully"}

@app.get("/me")
def read_users_me(current_user: str = Depends(get_current_user)):
    """Get current user info"""
    return {"username": current_user}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
