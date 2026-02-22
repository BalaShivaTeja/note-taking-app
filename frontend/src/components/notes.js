import React, { useState, useEffect, useCallback } from 'react';

function Notes({ token, user, onLogout, apiUrl }) {
  const [notes, setNotes] = useState([]);
  const [newNote, setNewNote] = useState({ title: '', content: '' });
  const [editingNote, setEditingNote] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [addError, setAddError] = useState('');

  const fetchNotes = useCallback(async () => {
    try {
      const response = await fetch(`${apiUrl}/notes`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setNotes(data);
        setError('');
      } else if (response.status === 401) {
        onLogout();
      } else {
        setError('Failed to load notes.');
      }
    } catch (err) {
      setError('Network error. Please try again.');
      console.error('Error fetching notes:', err);
    } finally {
      setLoading(false);
    }
  }, [apiUrl, token, onLogout]);

  useEffect(() => {
    fetchNotes();
  }, [fetchNotes]);

  const handleAddNote = async (e) => {
    e.preventDefault();
    setAddError('');
    if (!newNote.title.trim() || !newNote.content.trim()) {
      setAddError('Both title and content are required.');
      return;
    }
    try {
      const response = await fetch(`${apiUrl}/notes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ title: newNote.title.trim(), content: newNote.content.trim() }),
      });

      if (response.ok) {
        setNewNote({ title: '', content: '' });
        fetchNotes();
      } else if (response.status === 401) {
        onLogout();
      } else {
        const data = await response.json();
        setAddError(data.detail || 'Failed to add note.');
      }
    } catch (err) {
      setAddError('Network error. Please try again.');
      console.error('Error adding note:', err);
    }
  };

  const handleUpdateNote = async (e) => {
    e.preventDefault();
    if (!editingNote) return;
    if (!editingNote.title.trim() || !editingNote.content.trim()) {
      setError('Both title and content are required.');
      return;
    }
    try {
      const response = await fetch(`${apiUrl}/notes/${editingNote.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ title: editingNote.title.trim(), content: editingNote.content.trim() }),
      });

      if (response.ok) {
        setEditingNote(null);
        fetchNotes();
      } else if (response.status === 401) {
        onLogout();
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to update note.');
      }
    } catch (err) {
      setError('Network error. Please try again.');
      console.error('Error updating note:', err);
    }
  };

  const handleDeleteNote = async (id) => {
    if (!window.confirm('Are you sure you want to delete this note?')) return;
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
      } else {
        setError('Failed to delete note.');
      }
    } catch (err) {
      setError('Network error. Please try again.');
      console.error('Error deleting note:', err);
    }
  };

  return (
    <div className="notes-container">
      <header className="notes-header">
        <div className="user-info">
          <span>&#x1F464; {user?.username}</span>
        </div>
        <button onClick={onLogout} className="logout-btn">Logout</button>
      </header>

      <h1>My Notes</h1>

      {error && <div className="error-message">{error}</div>}

      {editingNote ? (
        <form onSubmit={handleUpdateNote} className="note-form">
          <h3>Edit Note</h3>
          <input
            type="text"
            placeholder="Note title..."
            value={editingNote.title}
            onChange={(e) => setEditingNote({ ...editingNote, title: e.target.value })}
          />
          <textarea
            placeholder="Write your note here..."
            value={editingNote.content}
            onChange={(e) => setEditingNote({ ...editingNote, content: e.target.value })}
          />
          <div className="edit-actions">
            <button type="submit">Save Changes</button>
            <button type="button" className="cancel-btn" onClick={() => setEditingNote(null)}>Cancel</button>
          </div>
        </form>
      ) : (
        <form onSubmit={handleAddNote} className="note-form">
          <h3>Add New Note</h3>
          {addError && <div className="error-message">{addError}</div>}
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
      )}

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
                <div className="note-actions">
                  <button
                    className="edit-btn"
                    onClick={() => setEditingNote({ ...note })}
                  >
                    &#x270F;&#xFE0F; Edit
                  </button>
                  <button
                    className="delete-btn"
                    onClick={() => handleDeleteNote(note.id)}
                  >
                    &#x1F5D1;&#xFE0F; Delete
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

export default Notes;
