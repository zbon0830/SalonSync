import React, { useState, useEffect } from 'react';

const DEFAULT_BRANDS = [
  'Redken',
  'Wella',
  'Schwarzkopf',
  "L'Oreal",
  'Goldwell',
  'Matrix',
  'Pulp Riot',
  'Joico',
  'Kenra',
  'Other'
];

const DEFAULT_DEVELOPERS = [
  '5 vol',
  '10 vol',
  '20 vol',
  '30 vol',
  '40 vol'
];

export default function App() {
  const [activeTab, setActiveTab] = useState('login');

  // Auth fields
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  // Auth session
  const [token, setToken] = useState(() => localStorage.getItem('salonsync_token') || '');
  const [currentUser, setCurrentUser] = useState(null);

  // Status feedback
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Notes state
  const [notes, setNotes] = useState([]);
  const [showNoteForm, setShowNoteForm] = useState(false);
  const [editingNoteId, setEditingNoteId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [brandFilter, setBrandFilter] = useState('All');

  // New Note Form fields
  const [noteTitle, setNoteTitle] = useState('');
  const [noteBrand, setNoteBrand] = useState('Redken');
  const [noteShades, setNoteShades] = useState('');
  const [noteDeveloper, setNoteDeveloper] = useState('20 vol');
  const [noteProcessingTime, setNoteProcessingTime] = useState('35');
  const [noteInstructions, setNoteInstructions] = useState('');
  const [noteIsPublic, setNoteIsPublic] = useState(false);

  // Field validation errors
  const [fieldErrors, setFieldErrors] = useState({});

  useEffect(() => {
    if (token) {
      fetchUser(token);
      fetchNotes(token);
    }
  }, [token]);

  const fetchUser = async (authToken) => {
    try {
      const res = await fetch('/api/auth/me', {
        headers: { 'Authorization': `Bearer ${authToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setCurrentUser(data.user);
      } else {
        handleLogout();
      }
    } catch (err) {
      handleLogout();
    }
  };

  const fetchNotes = async (authToken, search = '', brand = '') => {
    try {
      const params = new URLSearchParams();
      if (search) params.append('q', search);
      if (brand && brand !== 'All') params.append('brand', brand);

      const res = await fetch(`/api/notes?${params.toString()}`, {
        headers: { 'Authorization': `Bearer ${authToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setNotes(data.notes || []);
      }
    } catch (err) {
      // Ignore initial notes fetch failure
    }
  };

  const handleSignupSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    setSuccessMessage('');

    const trimmedUsername = username.trim();
    const trimmedEmail = email.trim();

    if (!trimmedUsername || !trimmedEmail || !password) {
      setErrorMessage('All fields are required.');
      return;
    }

    if (trimmedUsername.length < 3 || trimmedUsername.length > 50) {
      setErrorMessage('Username must be between 3 and 50 characters.');
      return;
    }

    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(trimmedEmail)) {
      setErrorMessage('Please enter a valid email address.');
      return;
    }

    if (password.length < 8) {
      setErrorMessage('Password must be at least 8 characters long.');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('/api/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: trimmedUsername,
          email: trimmedEmail,
          password: password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setErrorMessage(data.error || 'Registration failed.');
      } else {
        setSuccessMessage('Account created successfully!');
        if (data.token) {
          localStorage.setItem('salonsync_token', data.token);
          setToken(data.token);
          setCurrentUser(data.user);
          fetchNotes(data.token);
        }
        setUsername('');
        setEmail('');
        setPassword('');
      }
    } catch (err) {
      setErrorMessage('Network error: unable to connect to the server.');
    } finally {
      setLoading(false);
    }
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    setSuccessMessage('');

    const identifier = (email || username).trim();

    if (!identifier || !password) {
      setErrorMessage('Email or username and password are required.');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: identifier,
          password: password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setErrorMessage(data.error || 'Login failed. Please check credentials.');
      } else {
        setSuccessMessage('Login successful!');
        localStorage.setItem('salonsync_token', data.token);
        setToken(data.token);
        setCurrentUser(data.user);
        fetchNotes(data.token);
        setEmail('');
        setUsername('');
        setPassword('');
      }
    } catch (err) {
      setErrorMessage('Network error: unable to connect to the server.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await fetch('/api/auth/logout', { method: 'POST' });
    } catch (err) {
      // Ignore network errors
    } finally {
      localStorage.removeItem('salonsync_token');
      setToken('');
      setCurrentUser(null);
      setNotes([]);
      setShowNoteForm(false);
      setSuccessMessage('Logged out successfully.');
      setErrorMessage('');
    }
  };

    const handleSaveNoteSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    setSuccessMessage('');
    setFieldErrors({});

    const errors = {};
    const trimmedTitle = noteTitle.trim();
    const trimmedBrand = noteBrand.trim();
    const trimmedShades = noteShades.trim();
    const trimmedDeveloper = noteDeveloper.trim();

    if (!trimmedTitle) errors.title = 'Title is required.';
    if (!trimmedBrand) errors.brand = 'Brand is required.';
    if (!trimmedShades) errors.shades = 'Shades are required.';
    if (!trimmedDeveloper) errors.developer = 'Developer is required.';

    const procTimeNum = parseInt(noteProcessingTime, 10);
    if (isNaN(procTimeNum) || procTimeNum < 1) {
      errors.processing_time = 'Must be at least 1 minute.';
    }

    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      setErrorMessage('Please fix the validation errors below.');
      return;
    }

    setLoading(true);

    const url = editingNoteId ? `/api/notes/${editingNoteId}` : '/api/notes';
    const method = editingNoteId ? 'PUT' : 'POST';

    try {
      const response = await fetch(url, {
        method: method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          title: trimmedTitle,
          brand: trimmedBrand,
          shades: trimmedShades,
          developer: trimmedDeveloper,
          processing_time: procTimeNum,
          notes: noteInstructions.trim(),
          is_public: noteIsPublic,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setErrorMessage(data.error || 'Failed to save note.');
      } else {
        setSuccessMessage(editingNoteId ? 'Formula note updated successfully!' : 'Formula note created successfully!');
        if (editingNoteId) {
          setNotes(notes.map((n) => (n.id === editingNoteId ? data.note : n)));
        } else {
          setNotes([data.note, ...notes]);
        }
        setShowNoteForm(false);
        setEditingNoteId(null);
        setNoteTitle('');
        setNoteShades('');
        setNoteInstructions('');
        setNoteProcessingTime('35');
        setNoteIsPublic(false);
      }
    } catch (err) {
      setErrorMessage('Network error: unable to save note.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteNote = async (noteId) => {
    if (!window.confirm('Are you sure you want to delete this note? This cannot be undone.')) {
      return;
    }

    setErrorMessage('');
    setSuccessMessage('');

    try {
      const response = await fetch(`/api/notes/${noteId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        setErrorMessage(data.error || 'Failed to delete note.');
      } else {
        setSuccessMessage('Formula note deleted successfully!');
        setNotes(notes.filter((n) => n.id !== noteId));
      }
    } catch (err) {
      setErrorMessage('Network error: unable to delete note.');
    }
  };

  const handleEditClick = (note) => {
    setEditingNoteId(note.id);
    setNoteTitle(note.title);
    setNoteBrand(note.brand);
    setNoteShades(note.shades);
    setNoteDeveloper(note.developer);
    setNoteProcessingTime(String(note.processing_time));
    setNoteInstructions(note.notes || '');
    setNoteIsPublic(note.is_public);
    setShowNoteForm(true);
    setErrorMessage('');
    setSuccessMessage('');
    setFieldErrors({});
  };
  return (
    <div className="container">
      <div className="brand-header">
        <h1>SalonSync</h1>
        <p>Stylist Formula Notetaking and Sharing</p>
      </div>

      {currentUser ? (
        <div>
          {/* Stylist Session Bar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', paddingBottom: '12px', borderBottom: '1px solid #e2e8f0' }}>
            <div>
              <div style={{ fontSize: '14px', fontWeight: '700' }}>{currentUser.username}</div>
              <div style={{ fontSize: '12px', color: '#718096' }}>{currentUser.email}</div>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => {
                  if (showNoteForm && editingNoteId === null) {
                    setShowNoteForm(false);
                  } else {
                    setEditingNoteId(null);
                    setNoteTitle('');
                    setNoteBrand('Redken');
                    setNoteShades('');
                    setNoteDeveloper('20 vol');
                    setNoteProcessingTime('35');
                    setNoteInstructions('');
                    setNoteIsPublic(false);
                    setShowNoteForm(true);
                  }
                  setErrorMessage('');
                  setSuccessMessage('');
                  setFieldErrors({});
                }}
              >
                {showNoteForm ? 'Close Form' : 'New note'}
              </button>
              <button
                type="button"
                className="btn-secondary"
                onClick={handleLogout}
                style={{ color: '#c53030' }}
              >
                Log Out
              </button>
            </div>
          </div>

          {errorMessage && (
            <div className="banner banner-error" role="alert">
              {errorMessage}
            </div>
          )}

          {successMessage && (
            <div className="banner banner-success" role="status">
              {successMessage}
            </div>
          )}

          {/* New Formula Note Form (US-4) */}
          {showNoteForm && (
            <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '8px', border: '1px solid #cbd5e0', marginBottom: '20px' }}>
              <h2 style={{ fontSize: '16px', marginBottom: '14px', color: '#2b6cb0' }}>{editingNoteId ? 'Edit Formula Note' : 'Create Formula Note'}</h2>
              <form onSubmit={handleSaveNoteSubmit} noValidate>
                <div className="form-group">
                  <label htmlFor="note-title">Client / Title *</label>
                  <input
                    id="note-title"
                    type="text"
                    value={noteTitle}
                    onChange={(e) => setNoteTitle(e.target.value)}
                    placeholder="e.g. Maria R. - root touch-up"
                    disabled={loading}
                  />
                  {fieldErrors.title && <div className="field-error">{fieldErrors.title}</div>}
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="note-brand">Brand *</label>
                    <select
                      id="note-brand"
                      value={noteBrand}
                      onChange={(e) => setNoteBrand(e.target.value)}
                      disabled={loading}
                    >
                      {DEFAULT_BRANDS.map((b) => (
                        <option key={b} value={b}>{b}</option>
                      ))}
                    </select>
                    {fieldErrors.brand && <div className="field-error">{fieldErrors.brand}</div>}
                  </div>

                  <div className="form-group">
                    <label htmlFor="note-developer">Developer *</label>
                    <select
                      id="note-developer"
                      value={noteDeveloper}
                      onChange={(e) => setNoteDeveloper(e.target.value)}
                      disabled={loading}
                    >
                      {DEFAULT_DEVELOPERS.map((d) => (
                        <option key={d} value={d}>{d}</option>
                      ))}
                    </select>
                    {fieldErrors.developer && <div className="field-error">{fieldErrors.developer}</div>}
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="note-shades">Shades *</label>
                    <input
                      id="note-shades"
                      type="text"
                      value={noteShades}
                      onChange={(e) => setNoteShades(e.target.value)}
                      placeholder="e.g. 6NB + 7N"
                      disabled={loading}
                    />
                    {fieldErrors.shades && <div className="field-error">{fieldErrors.shades}</div>}
                  </div>

                  <div className="form-group">
                    <label htmlFor="note-processing-time">Processing time (min) *</label>
                    <input
                      id="note-processing-time"
                      type="number"
                      value={noteProcessingTime}
                      onChange={(e) => setNoteProcessingTime(e.target.value)}
                      placeholder="e.g. 35"
                      min="1"
                      disabled={loading}
                    />
                    {fieldErrors.processing_time && <div className="field-error">{fieldErrors.processing_time}</div>}
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="note-instructions">Formula Notes and Instructions</label>
                  <textarea
                    id="note-instructions"
                    rows="3"
                    value={noteInstructions}
                    onChange={(e) => setNoteInstructions(e.target.value)}
                    placeholder="e.g. Apply roots first, pull through last 10 min"
                    disabled={loading}
                  />
                </div>

                <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <input
                    id="note-is-public"
                    type="checkbox"
                    checked={noteIsPublic}
                    onChange={(e) => setNoteIsPublic(e.target.checked)}
                    style={{ width: 'auto' }}
                    disabled={loading}
                  />
                  <label htmlFor="note-is-public" style={{ margin: 0, fontWeight: 'normal', cursor: 'pointer' }}>
                    Share publicly to salon community feed
                  </label>
                </div>

                <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                  <button type="submit" className="btn-primary" disabled={loading}>
                    {loading ? 'Saving...' : 'Save'}
                  </button>
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => setShowNoteForm(false)}
                    disabled={loading}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Notes List View */}
          <div style={{ marginTop: '16px' }}>
            <h2 style={{ fontSize: '15px', color: '#2d3748', marginBottom: '8px' }}>
              Formula Notes ({notes.length})
            </h2>

            <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
              <input
                type="text"
                placeholder="Search by client/title or shades..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  fetchNotes(token, e.target.value, brandFilter);
                }}
                style={{ flex: 1, padding: '8px', fontSize: '13px' }}
              />
              <select
                value={brandFilter}
                onChange={(e) => {
                  setBrandFilter(e.target.value);
                  fetchNotes(token, searchQuery, e.target.value);
                }}
                style={{ padding: '8px', fontSize: '13px' }}
              >
                <option value="All">All Brands</option>
                {DEFAULT_BRANDS.map((b) => (
                  <option key={b} value={b}>{b}</option>
                ))}
              </select>
            </div>

            {notes.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '30px 10px', color: '#718096', fontSize: '13.5px', background: '#f8fafc', borderRadius: '6px', border: '1px dashed #cbd5e0' }}>
                No notes yet. Click <strong>"New note"</strong> to create your first color formula.
              </div>
            ) : (
              <div className="notes-list">
                {notes.map((n) => (
                  <div key={n.id} className="note-card">
                    <div className="note-header">
                      <span className="note-title">{n.title}</span>
                      <span className={`badge ${n.is_public ? 'badge-public' : 'badge-private'}`}>
                        {n.is_public ? 'Public' : 'Private'}
                      </span>
                    </div>
                    <div className="note-formula">
                      <strong>Brand:</strong> {n.brand} &nbsp;|&nbsp; <strong>Shades:</strong> {n.shades} &nbsp;|&nbsp; <strong>Developer:</strong> {n.developer} &nbsp;|&nbsp; <strong>Time:</strong> {n.processing_time} min
                    </div>
                    {n.notes && (
                      <div style={{ fontSize: '12px', color: '#4a5568', marginTop: '4px' }}>
                        {n.notes}
                      </div>
                    )}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '8px' }}>
                    <div className="note-details">
                      Created by {n.author_username}
                    </div>
                    <button
                      type="button"
                      className="btn-secondary"
                      style={{ padding: '2px 8px', fontSize: '12px' }}
                      onClick={() => handleEditClick(n)}
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      className="btn-secondary"
                      style={{ padding: '2px 8px', fontSize: '12px', color: '#c53030' }}
                      onClick={() => handleDeleteNote(n.id)}
                    >
                      Delete
                    </button>
                  </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      ) : (
        <>
          <div style={{ display: 'flex', borderBottom: '1px solid #e2e8f0', marginBottom: '20px' }}>
            <button
              type="button"
              onClick={() => { setActiveTab('login'); setErrorMessage(''); setSuccessMessage(''); }}
              style={{
                flex: 1,
                padding: '10px',
                border: 'none',
                background: 'none',
                fontWeight: activeTab === 'login' ? '700' : '500',
                color: activeTab === 'login' ? '#2b6cb0' : '#718096',
                borderBottom: activeTab === 'login' ? '2px solid #2b6cb0' : 'none',
                cursor: 'pointer',
              }}
            >
              Stylist Login
            </button>
            <button
              type="button"
              onClick={() => { setActiveTab('signup'); setErrorMessage(''); setSuccessMessage(''); }}
              style={{
                flex: 1,
                padding: '10px',
                border: 'none',
                background: 'none',
                fontWeight: activeTab === 'signup' ? '700' : '500',
                color: activeTab === 'signup' ? '#2b6cb0' : '#718096',
                borderBottom: activeTab === 'signup' ? '2px solid #2b6cb0' : 'none',
                cursor: 'pointer',
              }}
            >
              New Registration
            </button>
          </div>

          {errorMessage && (
            <div className="banner banner-error" role="alert">
              {errorMessage}
            </div>
          )}

          {successMessage && (
            <div className="banner banner-success" role="status">
              {successMessage}
            </div>
          )}

          {activeTab === 'login' ? (
            <form onSubmit={handleLoginSubmit} noValidate>
              <div className="form-group">
                <label htmlFor="login-identifier">Email or Username</label>
                <input
                  id="login-identifier"
                  type="text"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="e.g. jsmith@example.com"
                  required
                  disabled={loading}
                />
              </div>

              <div className="form-group">
                <label htmlFor="login-password">Password</label>
                <input
                  id="login-password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  required
                  disabled={loading}
                />
              </div>

              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? 'Authenticating...' : 'Log In'}
              </button>
            </form>
          ) : (
            <form onSubmit={handleSignupSubmit} noValidate>
              <div className="form-group">
                <label htmlFor="signup-username">Username</label>
                <input
                  id="signup-username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. jsmith_color"
                  required
                  disabled={loading}
                />
                <div className="hint-text">3 to 50 characters, letters, numbers, underscores.</div>
              </div>

              <div className="form-group">
                <label htmlFor="signup-email">Email Address</label>
                <input
                  id="signup-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="e.g. jsmith@example.com"
                  required
                  disabled={loading}
                />
              </div>

              <div className="form-group">
                <label htmlFor="signup-password">Password</label>
                <input
                  id="signup-password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Minimum 8 characters"
                  required
                  disabled={loading}
                />
                <div className="hint-text">Must be at least 8 characters long.</div>
              </div>

              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? 'Creating Account...' : 'Create Account'}
              </button>
            </form>
          )}
        </>
      )}
    </div>
  );
}
