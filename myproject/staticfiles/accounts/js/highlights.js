document.addEventListener('DOMContentLoaded', function() {
    fetchAllHighlights();
});
 function getCookie(name) {
      var cookieArr = document.cookie.split(";");

      for(let i = 0; i < cookieArr.length; i++) {
        var cookiePair = cookieArr[i].split("=");

        if(name == cookiePair[0].trim()) {
          return decodeURIComponent(cookiePair[1]);
        }
      }

      // Return null if the cookie by that name does not exist
      return null;
    }

var csrftoken2;
 document.addEventListener('DOMContentLoaded', (event) => {
        csrftoken2=getCookie('csrftoken');

});

function fetchAllHighlights() {
    console.log("Fetching all highlights");  // Log 1
    fetch('/api/user/get_highlights/', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken2
        },
    })
    .then(response => {
        console.log("Received response", response);  // Log 2
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json(); // This already parses the JSON response
    })
    .then(parsedData => {
        console.log("Parsed data:", parsedData);  // Log the parsed data
        displayHighlights(parsedData); // Pass the parsed data directly
    })
    .catch(error => {
        console.log('Error during fetch:', error);
    });
}


function displayHighlights(highlights) {
    const highlightsContent = document.getElementById('highlights-content');
    highlightsContent.innerHTML = '';  // Clear existing content

    // Parse the JSON string and then group highlights by media
    const parsedHighlights = JSON.parse(highlights);
    const highlightsByMedia = groupHighlightsByMedia(parsedHighlights);

    Object.keys(highlightsByMedia).forEach(mediaId => {
        const mediaDiv = document.createElement('div');
        mediaDiv.className = 'media';
        mediaDiv.textContent = `Media ID: ${mediaId}`;  // Use Media ID for now

        const highlightsDiv = document.createElement('div');
        highlightsDiv.className = 'highlights';
        highlightsDiv.style.display = 'none';  // Initially hide the highlights

        highlightsByMedia[mediaId].forEach(highlight => {
            const highlightDiv = document.createElement('div');
            highlightDiv.className = 'highlight';
            highlightDiv.textContent = highlight.fields.highlighted_text;
            highlightsDiv.appendChild(highlightDiv);
        });

        mediaDiv.addEventListener('click', function() {
            // Toggle display of highlights
            highlightsDiv.style.display = highlightsDiv.style.display === 'none' ? 'block' : 'none';
        });

        highlightsContent.appendChild(mediaDiv);
        highlightsContent.appendChild(highlightsDiv);
    });
}

function groupHighlightsByMedia(highlights) {
    const grouped = {};
    highlights.forEach(highlight => {
        const mediaId = highlight.fields.media;  // Using media ID from fields
        if (!grouped[mediaId]) {
            grouped[mediaId] = [];
        }
        grouped[mediaId].push(highlight);
    });
    return grouped;
}


