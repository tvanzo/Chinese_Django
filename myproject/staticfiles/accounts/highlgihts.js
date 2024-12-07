document.addEventListener('DOMContentLoaded', function() {
    fetchHighlights();
});

function fetchHighlights() {
    fetch('/api/user/get_highlights/')
    .then(response => response.json())
    .then(data => {
        displayHighlights(data.media_highlights);
    })
    .catch(error => console.error('Error:', error));
}

function displayHighlights(mediaHighlights) {
    const highlightsContent = document.getElementById('highlights-content');
    highlightsContent.innerHTML = ''; // Clear existing content

    for (const [media, highlights] of Object.entries(mediaHighlights)) {
        const mediaDiv = document.createElement('div');
        mediaDiv.className = 'media-block';

        const mediaTitle = document.createElement('button');
        mediaTitle.className = 'media-title';
        mediaTitle.textContent = media.title; // Assuming 'media' has a 'title' property
        mediaTitle.onclick = () => toggleHighlights(mediaDiv);

        const highlightsList = document.createElement('div');
        highlightsList.className = 'highlight-list';
        highlightsList.style.display = 'none';

        highlights.forEach(highlight => {
            const highlightDiv = document.createElement('div');
            highlightDiv.className = 'highlight';
            highlightDiv.textContent = highlight.highlighted_text; // Update with correct property
            highlightsList.appendChild(highlightDiv);
        });

        mediaDiv.appendChild(mediaTitle);
        mediaDiv.appendChild(highlightsList);
        highlightsContent.appendChild(mediaDiv);
    }
}

function toggleHighlights(mediaDiv) {
    const highlightsList = mediaDiv.querySelector('.highlight-list');
    highlightsList.style.display = highlightsList.style.display === 'none' ? 'block' : 'none';
}
