from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import uvicorn

# Security Configuration
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

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

class Token(BaseModel):
    access_token: str
    token_type: str

class Note(BaseModel):
    id: int
    title: str
    content: str
    created_at: str

class NoteCreate(BaseModel):
    title: str
    content: str

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
    if user.username in users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    users_db[user.username] = {
        "username": user.username,
        "hashed_password": hashed_password
    }
    notes_db[user.username] = []  # Initialize empty notes list for user
    
    return {"username": user.username}

@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login to get access token"""
    user = authenticate_user(form_data.username, form_data.password)
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
    """Alternative login endpoint for JSON requests"""
    user = authenticate_user(credentials.username, credentials.password)
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
    new_note = {
        "id": new_id, 
        "title": note.title, 
        "content": note.content,
        "created_at": datetime.now().isoformat()
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

@app.delete("/notes/{note_id}")
def delete_note(note_id: int, current_user: str = Depends(get_current_user)):
    """Delete a note by ID"""
    user_notes = notes_db.get(current_user, [])
    notes_db[current_user] = [n for n in user_notes if n["id"] != note_id]
    return {"message": "Note deleted successfully"}

@app.get("/me")
def read_users_me(current_user: str = Depends(get_current_user)):
    """Get current user info"""
    return {"username": current_user}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
