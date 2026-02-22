import React, { useState, useEffect } from 'react';

function Notes({ token, user, onLogout, apiUrl }) {
  const [notes, setNotes] = useState([]);
  const [newNote, setNewNote] = useState({ title: '', content: '' });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchNotes();
  }, []);

  const fetchNotes = async () => {
    try {
      const response = await fetch(`${apiUrl}/notes`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setNotes(data);
      } else if (response.status === 401) {
        onLogout();
      }
    } catch (error) {
      console.error('Error fetching notes:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddNote = async (e) => {
    e.preventDefault();
    if (!newNote.title.trim() || !newNote.content.trim()) return;

    try {
      const response = await fetch(`${apiUrl}/notes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(newNote),
      });
      
      if (response.ok) {
        setNewNote({ title: '', content: '' });
        fetchNotes();
      } else if (response.status === 401) {
        onLogout();
      }
    } catch (error) {
      console.error('Error adding note:', error);
    }
  };

  const handleDeleteNote = async (id) => {
    try {
      const response = await fetch(`${apiUrl}/notes/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        fetchNotes();
      } else if (response.status === 401) {
        onLogout();
      }
    } catch (error) {
      console.error('Error deleting note:', error);
    }
  };

  return (
    <div className="notes-container">
      <header className="notes-header">
        <div className="user-info">
          <span>👤 {user?.username}</span>
        </div>
        <button onClick={onLogout} className="logout-btn">Logout</button>
      </header>

      <h1>My Notes</h1>
      
      <form onSubmit={handleAddNote} className="note-form">
        <input
          type="text"
          placeholder="Note title..."
          value={newNote.title}
          onChange={(e) => setNewNote({ ...newNote, title: e.target.value })}
        />
        <textarea
          placeholder="Write your note here..."
          value={newNote.content}
          onChange={(e) => setNewNote({ ...newNote, content: e.target.value })}
        />
        <button type="submit">Add Note</button>
      </form>

      {loading ? (
        <div className="loading">Loading notes...</div>
      ) : (
        <div className="notes-list">
          {notes.length === 0 ? (
            <p className="empty-state">No notes yet. Create one above!</p>
          ) : (
            notes.map((note) => (
              <div key={note.id} className="note-card">
                <div className="note-header">
                  <h3>{note.title}</h3>
                  <span className="note-date">
                    {new Date(note.created_at).toLocaleDateString()}
                  </span>
                </div>
                <p>{note.content}</p>
                <button 
                  className="delete-btn"
                  onClick={() => handleDeleteNote(note.id)}
                >
                  🗑️ Delete
                </button>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

export default Notes;
