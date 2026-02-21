from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uvicorn

app = FastAPI(title="Note Taking API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for notes
notes_db = [
    {"id": 1, "title": "Welcome", "content": "This is your first note!"},
    {"id": 2, "title": "Shopping List", "content": "Milk, Eggs, Bread"},
]


class Note(BaseModel):
    id: int
    title: str
    content: str


class NoteCreate(BaseModel):
    title: str
    content: str


@app.get("/notes", response_model=List[Note])
def get_all_notes():
    """Get all notes"""
    return notes_db


@app.post("/notes", response_model=Note)
def create_note(note: NoteCreate):
    """Create a new note"""
    new_id = max([n["id"] for n in notes_db], default=0) + 1
    new_note = {"id": new_id, "title": note.title, "content": note.content}
    notes_db.append(new_note)
    return new_note


@app.get("/notes/{note_id}", response_model=Note)
def get_note(note_id: int):
    """Get a specific note by ID"""
    for note in notes_db:
        if note["id"] == note_id:
            return note
    raise HTTPException(status_code=404, detail="Note not found")


@app.delete("/notes/{note_id}")
def delete_note(note_id: int):
    """Delete a note by ID"""
    global notes_db
    notes_db = [n for n in notes_db if n["id"] != note_id]
    return {"message": "Note deleted successfully"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
