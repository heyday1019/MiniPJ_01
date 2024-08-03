// frontend/src/App.jsx (or similar file depending on your framework)

import React, { useState, useEffect } from 'react';

function App() {
  const [story, setStory] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [choices, setChoices] = useState([]);
  const [genre, setGenre] = useState('');  // Add state for genre input
  const [history, setHistory] = useState(''); // Add state for history

  useEffect(() => {
    // ... (API call logic from previous response)
  }, []);

  const handleChoice = (choice) => {
    fetch('/api/continue', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ storyId, choice })
    })
      .then(res => res.json())
      .then(data => {
        setStory(data.storyText);
        setImageUrl(data.imageUrl);
        setChoices(extractChoices(data.storyText));
        setHistory(data.history);  // Update the history state
      });
  };

  // ... (helper functions to extract choices, etc.)

  return (
    <div>
      <input type="text" value={genre} onChange={(e) => setGenre(e.target.value)} />
      <button onClick={() => handleStartStory(genre)}>Start Story</button>
      {/* ... Rest of your UI to display story, image, and choices */}
    </div>
  );
}