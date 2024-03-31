var mediaHasBeenPlayed = false;

function getCookie(name) {
    var cookieArr = document.cookie.split(";");

    for (let i = 0; i < cookieArr.length; i++) {
        var cookiePair = cookieArr[i].split("=");

        if (name == cookiePair[0].trim()) {
            return decodeURIComponent(cookiePair[1]);
        }
    }
    return null; // Return null if the cookie by that name does not exist
}

var csrftoken2;
document.addEventListener('DOMContentLoaded', (event) => {
    csrftoken2 = getCookie('csrftoken');
});

// Assuming 'player' is the YouTube Player object
function onPlayerReady(event) {
    // You can call createSubtitles here if needed, or in response to another event
    playerReady = true;
    fetchMediaProgressAndSeek();
        console.log("called");
        setupProgressSaving(); 
    createSubtitles();
}

function onPlayerStateChange(event) {
    if (event.data === YT.PlayerState.PLAYING && !mediaHasBeenPlayed) {
        mediaHasBeenPlayed = true;

        // Make a server-side request to add this media to the user's viewed_media
        fetch('/api/user/viewed-media/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken2 // Function to get the CSRF token from the cookie
            },
            body: JSON.stringify({
                mediaId: mediaId,
            })
        });
    }
}
// Load the YouTube Iframe API
var tag = document.createElement('script');
tag.src = 'https://www.youtube.com/iframe_api';
var firstScriptTag = document.getElementsByTagName('script')[0];
firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

// Define the player variable outside of the functions to have global scope
var player;
// Flag to track if the player is ready
var playerReady = false;

// This function seeks the player to a specific time
function seekToTimeStopped(timeStopped) {
    if (player && playerReady) {
        console.log("Seeking to time stopped:", timeStopped);
        player.seekTo(timeStopped, true);
    } else {
        console.log("Player not ready or player object not available.");
    }
}

// This function will be called by the YouTube Iframe API once it's ready
function onYouTubeIframeAPIReady() {
    player = new YT.Player('player', {
        videoId: mediaId, // Your video ID here
        events: {
            'onReady': onPlayerReady,
            'onStateChange': onPlayerStateChange
        }
    });
}

// Fetch media progress and seek if applicable
function fetchMediaProgressAndSeek() {
    fetch(`/api/user/media_progress/${mediaId}/`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken2
        },
    })
    .then(response => response.json())
    .then(data => {
        console.log("Fetched media progress:", data.time_stopped, data);
        // Seek to time stopped if applicable
        if (data && data.time_stopped != null) {
            seekToTimeStopped(data.time_stopped);
        } else {
            console.log("No progress found, starting from the beginning");
            player.seekTo(0, true);
        }
    })
    .catch(error => console.error('Error:', error));
}

//Global Variables
var highlightMap = {};
var transformedArray = [];
var currentSubtitleIndex = 0;
var framesArray = [];
var currentFrame = [];
var currentFrameCharCount = 0;

async function fetchHighlights(mediaId) {
    return new Promise((resolve, reject) => {
        fetch(`/api/user/get_highlights/${mediaId}/`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken2
            },
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            return response.json();
        })
        .then(data => {
            if (!Array.isArray(data)) {
                data = JSON.parse(data);
            }
            transformedArray = data.map(item => {
                // Log the id here

                return {
                    media: item.fields.media,
                    id: item.pk,
                    start_time: item.fields.start_time,
                    end_time: item.fields.end_time,
                    highlighted_text: item.fields.highlighted_text,
                    start_index: item.fields.start_index,
                    end_index: item.fields.end_index,
                    start_sentence_index: item.fields.start_sentence_index,
                    end_sentence_index: item.fields.end_sentence_index,
                    frame_index: item.fields.frame_index // add this line
                };
            });

            updateHighlightMap();
            resolve();
        })
        .catch(error => {
            reject(error);
        });
    });
}




function addHighlightToMap(frameIndex, sentenceIndex, charIndex, highlight) {
  const key = `${frameIndex}_${sentenceIndex}_${charIndex}`; // construct a unique key
  if (!highlightMap[key]) {
    highlightMap[key] = [];
  }

  highlightMap[key].push({
    startTime: parseFloat(highlight.start_time),
    endTime: parseFloat(highlight.end_time)
  });
}

function updateHighlightMap() {
  highlightMap = {}; // clear previous data
  transformedArray.forEach(highlight => {
    let frameIndex = highlight.frame_index; // Use the frame index

    for (let sentenceIndex = highlight.start_sentence_index; sentenceIndex <= highlight.end_sentence_index; sentenceIndex++) {
      let startCharIndex = sentenceIndex == highlight.start_sentence_index ? highlight.start_index : 0;
      let endCharIndex = sentenceIndex == highlight.end_sentence_index ? highlight.end_index : framesArray[frameIndex][sentenceIndex].sentence.length - 1;
      for (let charIndex = startCharIndex; charIndex <= endCharIndex; charIndex++) {
        addHighlightToMap(frameIndex, sentenceIndex, charIndex, highlight);
      }
    }
  });
}


function applyPermanentHighlight(frameIndex, charIndex) {
  const sentenceElement = document.getElementById("s_" + frameIndex + "_" + charIndex);
  if (sentenceElement) {
    sentenceElement.classList.add('perm-highlight');
  }
}






function updateSidebarWithHighlight(highlight) {
    const ul = document.getElementById('highlight-list'); // Assuming your UL has this ID
    const li = document.createElement('li');

    const div = document.createElement('div');
    div.className = 'highlight-container';

    const a = document.createElement('a');
    a.href = "#"; // Since you can't use Django template tags, set href to "#" or the actual link if available
    a.setAttribute('data-start-time', highlight.start_time); // Set custom data attribute
    a.textContent = highlight.highlighted_text;
    div.appendChild(a);

    // Create the delete icon for the new highlight
    const img = document.createElement('img');
    // Ensure the path to the trash icon is correct for your static files setup
    img.src = '/static/subplayer/trash.png'; // Adjust the path as needed
    img.alt = "Delete";
    img.className = "delete-highlight";
    img.setAttribute('data-highlight-id', highlight.id); // Use setAttribute for data attributes
    img.style.cursor = "pointer";

    // Attach the event listener for deletion
    img.addEventListener('click', function() {
        deleteHighlight(this.dataset.highlightId);
    });

    div.appendChild(img);
    li.appendChild(div);
    ul.appendChild(li);
}































async function addHighlight(highlightData) {
  const response = await fetch(`/api/user/create_highlight`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken2 // Ensure you have the CSRF token
    },
    body: JSON.stringify(highlightData),
  });

  if (response.ok) {
    console.log("Highlight added successfully!");
    const addedHighlight = await response.json(); // Assuming the server returns the added highlight
    updateSidebarWithHighlight(addedHighlight); // Update the sidebar with the new highlight
    await fetchHighlights(highlightData.media); // Optionally refresh highlights if needed
    createSubtitles(); // Recreate subtitles to include new highlights
  } else {
    console.error('Failed to add highlight:', await response.text());
  }
}





// Your other functions (updateProgress, createSubtitles, etc.) go here...
// ...
var y=0;
      function findSubtitleIndex(time) {
    for (let i = 0; i < framesArray.length; i++) {
        let frameStartTime = parseFloat(framesArray[i][0].startTime);
        let frameEndTime = parseFloat(framesArray[i][framesArray[i].length - 1].endTime);
        if (time >= frameStartTime && time <= frameEndTime) {
            return i;
        }
    }
    return -1; // Return -1 if no suitable index is found
}


var subtitleTimes = [];
function createSubtitles() {

  if (currentSubtitleIndex < framesArray.length) {
    var currentFrame = framesArray[currentSubtitleIndex];

    subtitles.innerHTML = ""; // clear existing subtitles
    subtitleTimes = []; // reset times for new frame
    for (let i = 0; i < currentFrame.length; i++) {
      var element = document.createElement('span');
      element.setAttribute("id", "s_" + currentSubtitleIndex + "_" + i);
        element.classList.add('sentence-span'); // Add this line

      
      // Begin new highlight processing
      let highlightedSentence = "";
      let sentence = currentFrame[i].sentence;
      for (let k = 0; k < sentence.length; k++) {
        const character = sentence.charAt(k);
        const characterHighlights = highlightMap[`${currentSubtitleIndex}_${i}_${k}`];

        if (characterHighlights) {
          highlightedSentence += `<span class="perm-highlight">${character}</span>`;
        } else {
          highlightedSentence += character;
        }
      }
      element.innerHTML = highlightedSentence;
      // End new highlight processing
      
      subtitles.appendChild(element);

      // Save time information
      subtitleTimes.push({
        startTime: parseFloat(currentFrame[i].startTime),
        endTime: parseFloat(currentFrame[i].endTime),
      });
    }
  }

}




function updateProgress() {
    var currentTime = player.getCurrentTime();

    const correctIndex = findSubtitleIndex(currentTime);
    if (correctIndex !== -1 && correctIndex !== currentSubtitleIndex) {
        currentSubtitleIndex = correctIndex;
       
        createSubtitles();
    }

    if (currentSubtitleIndex < framesArray.length) {
        let frame = framesArray[currentSubtitleIndex];

        for (let j = 0; j < frame.length; j++) {
            const sentenceData = frame[j];
            const sentenceElement = document.getElementById("s_" + currentSubtitleIndex + "_" + j);

            if (sentenceElement) {
                if (currentTime >= parseFloat(sentenceData.startTime) && currentTime <= parseFloat(sentenceData.endTime)) {
                    sentenceElement.classList.add('active-highlight');
                } else {
                    sentenceElement.classList.remove('active-highlight');
                }
            }
        }
    }
}



// Fetch highlights when the page loads




// Fetch highlights when the page loads
fetchHighlights(mediaId);




function setupProgressSaving() {
    const saveInterval = 5000; // Continue saving every 5 seconds
    let lastUpdateMark = 0; // To track the last 100-second mark crossed

    setInterval(() => {
        if (!player || typeof player.getCurrentTime !== 'function') {
            console.error('Player not initialized or getCurrentTime not available');
            return;
        }

        const currentTime = player.getCurrentTime(); // Get the current time in seconds
        const currentMark = Math.floor(currentTime / 100) * 100; // Find the nearest 100-second mark below the currentTime

        // Check if we've passed a new 100-second mark since the last update
        if (currentMark > lastUpdateMark) {
            console.log('Passed a new 100-second mark, updating progress');
            lastUpdateMark = currentMark; // Update lastUpdateMark to the current mark
            
            // Calculate and update words and total minutes based on currentTime
            // For example, calculate the words and minutes to add, based on the video's progress
            // This could be included in your save-progress fetch call or require a separate API call

            // Example fetch to update total words and minutes, modify as needed
            fetch('/api/user/update-progress', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken2,
                },
                body: JSON.stringify({
                    mediaId: mediaId,
                    // Assuming you have a way to calculate these values based on currentMark
                    additionalWords: calculatedWords, 
                    additionalMinutes: calculatedMinutes,
                }),
            })
            .then(response => response.json())
            .then(data => {
                console.log('Additional progress saved successfully:', data);
            })
            .catch(error => {
                console.error('Error saving additional progress:', error);
            });
        }

        // Always save current playback time every 5 seconds
        fetch('/api/user/save-progress', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken2,
            },
            body: JSON.stringify({
                mediaId: mediaId,
                progress: currentTime,
            }),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Playback progress saved successfully:', data);
        })
        .catch(error => {
            console.error('Error saving playback progress:', error);
        });
    }, saveInterval);
}




        var subtitles = document.getElementById("subtitles");

    (async function(win, doc) {
        // JavaScript code


    let transcript;
    let syncData5 = null; // Assign an initial value to syncData5

    try {
  const response = await fetch(test2);
 
  const data = await response.json();
  transcript = data.transcript;
  syncData5 = data.words;
  
} catch (error) {
  console.error('Erroreeeee:', error);
}


    var syncData=syncData5;
    console.log(syncData);
      var syncData2 = []; // New array to track sentences
      
  function createFramesArray(syncData) {
    let currentFrame = [];
    let currentFrameCharCount = 0;
    const charLimit = 60; // Character limit for each frame

    syncData.forEach(wordItem => {
       

        let sentenceCharCount = wordItem.word.length;
        if ((currentFrameCharCount + sentenceCharCount) <= charLimit) {
            // Add wordItem to the current frame if within char limit
            currentFrame.push({
                startTime: wordItem.startTime,
                endTime: wordItem.endTime,
                sentence: wordItem.word
            });
            currentFrameCharCount += sentenceCharCount;
        } else {
            // Push the current frame to framesArray and start a new frame
            framesArray.push(currentFrame);
            currentFrame = [{
                startTime: wordItem.startTime,
                endTime: wordItem.endTime,
                sentence: wordItem.word
            }];
            currentFrameCharCount = sentenceCharCount;
        }
    });
    // Don't forget to add the last frame if it has content
    if (currentFrame.length > 0) {
        framesArray.push(currentFrame);
    }
}

// Call this function with your syncData
createFramesArray(syncData);

     
  var loopButton = doc.getElementById("loop-button");


    
createSubtitles();





  var selectedText = "";
  var frame_index;
var isLoopMode = false;
var loopingInterval = null;
var audioSpeedDisplay = document.getElementById('audio-speed-display');



function toggleLoopMode() {
    isLoopMode = !isLoopMode; // Toggle the state
    updateLoopIcon(); // Update the icon based on the new state

    if (!isLoopMode && loopingInterval) {
        clearInterval(loopingInterval); // Clear the interval when turning loop mode off
        loopingInterval = null; // Reset the interval ID
    }
}

function updateLoopIcon() {
    const loopIcon = document.getElementById('loop-icon');
    if (isLoopMode) {
        loopIcon.src = '/static/subplayer/loopon.png';
        loopIcon.alt = 'Loop On';
    } else {
        loopIcon.src = '/static/subplayer/loopoff.png';
        loopIcon.alt = 'Loop Off';
    }
}

document.getElementById('loop-icon').addEventListener('click', toggleLoopMode);

// Optional: Listen for Command key (or Control key for Windows) to toggle loop mode
document.addEventListener('keydown', function(event) {
    if (event.key === "Meta" || event.key === "Control") { // Meta for Mac Command key, Control for Ctrl key
        toggleLoopMode();
    }
});

// Optional: Reset loop mode when key is released
document.addEventListener('keyup', function(event) {
    if (event.key === "Meta" || event.key === "Control") {
        toggleLoopMode();
    }
});

document.addEventListener('keydown', function(e) {
    if (isLoopMode) {
        if (e.keyCode === 38) { // Up key
            // Increase speed
            let currentRate = player.getPlaybackRate();
            let availableRates = player.getAvailablePlaybackRates();
            let newRateIndex = availableRates.indexOf(currentRate) + 1;
            let newRate = availableRates[Math.min(newRateIndex, availableRates.length - 1)];
            player.setPlaybackRate(newRate);
        } else if (e.keyCode === 40) { // Down key
            // Decrease speed
            let currentRate = player.getPlaybackRate();
            let availableRates = player.getAvailablePlaybackRates();
            let newRateIndex = availableRates.indexOf(currentRate) - 1;
            let newRate = availableRates[Math.max(newRateIndex, 0)];
            player.setPlaybackRate(newRate);
        }
    }
});



document.addEventListener('keyup', function(e) {

    if (e.keyCode === 91) { // Command key on Mac
        isLoopMode = false;
        player.setPlaybackRate(1); // reset speed to normal

        if (loopingInterval) {
            clearInterval(loopingInterval);
            loopingInterval = null;
        }
    }
});

//tried here
subtitles.addEventListener("mouseup", function() {
    if (isLoopMode) {
        const selection = window.getSelection();
        const selectedText = selection.toString().trim();
        if (!selectedText) return;

        // Find the frame index that matches the current time
        const currentTime = player.getCurrentTime();
        const currentFrameIndex = findSubtitleIndex(currentTime);
        if (currentFrameIndex === -1) return; // Exit if no matching frame found

        // Attempt to match the selected text with the subtitles in the current frame
        let startLoopTime = null;
        let endLoopTime = null;

        const frameSubtitles = framesArray[currentFrameIndex];
        let concatenatedSubtitles = frameSubtitles.map(sub => sub.sentence).join('');
        
        if (concatenatedSubtitles.includes(selectedText)) {
            // If the selected text matches part of the concatenated subtitles, set loop times
            startLoopTime = parseFloat(frameSubtitles[0].startTime);
            endLoopTime = parseFloat(frameSubtitles[frameSubtitles.length - 1].endTime);

            // Adjust loop times if the selection is within a smaller range
            for (let i = 0; i < frameSubtitles.length; i++) {
                if (frameSubtitles[i].sentence.includes(selectedText.slice(0, Math.floor(selectedText.length / 2)))) {
                    startLoopTime = Math.max(startLoopTime, parseFloat(frameSubtitles[i].startTime));
                }
                if (frameSubtitles[i].sentence.includes(selectedText.slice(Math.floor(selectedText.length / 2)))) {
                    endLoopTime = Math.min(endLoopTime, parseFloat(frameSubtitles[i].endTime));
                    break; // Found the end of the selection within the frame
                }
            }
        }

        // Implement the looping based on the start and end times found
        if (startLoopTime !== null && endLoopTime !== null) {
            if (loopingInterval) clearInterval(loopingInterval); // Clear existing interval

            player.seekTo(startLoopTime, true);
            player.playVideo();

            loopingInterval = setInterval(() => {
                if (player.getCurrentTime() >= endLoopTime) {
                    player.seekTo(startLoopTime, true);
                }
            }, 100); // Check every 100ms to loop back if needed
        }
    }
});



let saveProgressInterval;

// Set up interval to save progress every 5 seconds when the video is playing
function onPlayerStateChange(event) {
    if (event.data === YT.PlayerState.PLAYING) {
        // Set an interval to save progress every 5 seconds while the video is playing
        saveProgressInterval = setInterval(() => saveProgress(player.getCurrentTime()), 5000);
    } else if (event.data === YT.PlayerState.PAUSED || event.data === YT.PlayerState.ENDED) {
        // When the video is paused or ended, clear the interval and immediately save progress
        clearInterval(saveProgressInterval);
        saveProgress(player.getCurrentTime()); // Save the current progress immediately
    }
}

function saveProgress(progress) {
    fetch('/api/user/save-progress', { // Adjust the URL to match your Django view for updating media progress
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken2, // Ensure csrftoken2 contains the correct CSRF token
        },
        body: JSON.stringify({
            mediaId: mediaId, // Ensure mediaId is correctly defined elsewhere in your script
            progress: progress,
        }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => console.log('Progress saved successfully:', data))
    .catch((error) => {
        console.error('Error saving progress:', error);
    });
}











fetch('/api/user/viewed_media_list/read')
    .then(response => response.json())
    .then(data => {
        const container = document.getElementById('viewed-media-container');
        data.viewed_media.forEach(mediaId => {
            const span = document.createElement('span');
            span.textContent = "mediaId:" + mediaId;
            container.appendChild(span);
        });
    });

fetch(`/api/user/media_progress/${mediaId}/`, {
    method: 'GET',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken2
    },
})
.then(response => {
    if (!response.ok) {
        throw Error(response.statusText);
    }
    else{
        console.log(response);
    }
    return response.json();
})
.then(data => {
        console.log("Fetched media progress:", data.time_stopped, data);

    // Check if there's a MediaProgress object for the current media and user
    if (data && data.time_stopped != null) {
        // If so, set the currentTime of the player to the last stopped time
        if (playerReady) {
    player.seekTo(data.time_stopped, true);
} else {
    console.log("Player not ready.");
}
    } else {
        // If not, the media should start playing from the beginning
        console.log("No progress found, starting from the beginning");
        player.seekTo(0, true);
    }
})
.catch(error => console.error('Error:', error));

document.addEventListener('keydown', async function (event) {
    if (event.shiftKey) {
        let selection = window.getSelection();

        if (selection.rangeCount === 0) return;

        let range = selection.getRangeAt(0);
        let selectedText = selection.toString().trim();

        if (!selectedText) return;

        let calculateOffset = function (container, offset, span) {
            let walker = document.createTreeWalker(span, NodeFilter.SHOW_TEXT);
            let totalOffset = 0;
            let node;
            while ((node = walker.nextNode())) {
                if (node === container || node.contains(container)) {
                    totalOffset += offset;
                    break;
                }
                totalOffset += node.textContent.length;
            }
            return totalOffset;
        };
        // ... (rest of your existing code for handling text selection and highlighting) ...


let findParentWithClass = function (node, className) {
      if (node.nodeType !== Node.ELEMENT_NODE) {
        node = node.parentNode;
      }
      while (node && (!node.classList || !node.classList.contains(className))) {
        node = node.parentNode;
      }
      return node;
    };

    let startSpan = findParentWithClass(range.startContainer, 'sentence-span');
    let endSpan = findParentWithClass(range.endContainer, 'sentence-span');

    let start_char_index = calculateOffset(range.startContainer, range.startOffset, startSpan);
    let end_char_index = calculateOffset(range.endContainer, range.endOffset, endSpan) - 1;

    if (start_char_index < 10) {
        start_char_index = '0' + start_char_index;
    }

    if (end_char_index < 10) {
        end_char_index = '0' + end_char_index;
    }





    let highlightStartSentenceIndex = parseInt(startSpan.id.split('_')[2]);
    let highlightEndSentenceIndex = parseInt(endSpan.id.split('_')[2]);
    let highlightStartTime = subtitleTimes[highlightStartSentenceIndex].startTime;
    let highlightEndTime = subtitleTimes[highlightEndSentenceIndex].endTime;
    console.log("start " + start_char_index);
        console.log("end " + end_char_index);


    // Check if the selection overlaps an existing highlight
const overlappingHighlight = transformedArray.find(item =>
    parseFloat(`${item.start_sentence_index}.${item.start_index.toString().padStart(2, '0')}`) <= parseFloat(`${highlightEndSentenceIndex}.${end_char_index}`) &&
    parseFloat(`${item.end_sentence_index}.${item.end_index.toString().padStart(2, '0')}`) >= parseFloat(`${highlightStartSentenceIndex}.${start_char_index}`) &&
    item.frame_index === currentSubtitleIndex
);


if (overlappingHighlight) {
  if (overlappingHighlight.start_sentence_index!=overlappingHighlight.end_sentence_index){
        console.log("first"+overlappingHighlight.start_sentence_index);
        console.log(overlappingHighlight.end_sentence_index);
        await deleteHighlight(overlappingHighlight.id);
  }
  // Check if the selection exactly matches the existing highlight
  else if (overlappingHighlight.start_index === start_char_index &&
      overlappingHighlight.end_index === end_char_index) {
    // If it does, delete the entire highlight
    await deleteHighlight(overlappingHighlight.id);
    console.log("Deleted");
  } else {
        console.log("lo");
    console.log(start_char_index + " "+ end_char_index);

    // If it doesn't, split the highlight at the selected indices
    await splitHighlight(overlappingHighlight.id, start_char_index, end_char_index);
    console.log(start_char_index + ""+ end_char_index);
  }
} else {
            console.log("low");

  // Otherwise, create a new highlight
  if (start_char_index !== null && end_char_index !== null && highlightStartTime !== null && highlightEndTime !== null) {
    console.log("All indexes found");
    createHighlight(selectedText, mediaId, start_char_index, end_char_index, highlightStartSentenceIndex, highlightEndSentenceIndex, highlightStartTime, highlightEndTime, currentSubtitleIndex);
  }
}
  }
});

function createHighlight(selectedText, mediaId, highlightStartIndex, highlightEndIndex, highlightStartSentenceIndex, highlightEndSentenceIndex, startTime, endTime, frameIndex) {
    console.log("createHighlight triggered");

    // Add leading zero if start_index is a single digit
    if (highlightStartIndex.toString().length === 1) {
        highlightStartIndex = "0" + highlightStartIndex;
    }

    // Add leading zero if end_index is a single digit
    if (highlightEndIndex.toString().length === 1) {
        highlightEndIndex = "0" + highlightEndIndex;
    }

    let highlightData = {
        highlighted_text: selectedText,
        media: mediaId,
        start_index: highlightStartIndex,
        end_index: highlightEndIndex,
        start_sentence_index: highlightStartSentenceIndex,
        end_sentence_index: highlightEndSentenceIndex,
        start_time: startTime,
        end_time: endTime,
        frame_index: frameIndex,
    };
    addHighlight(highlightData);
    console.log("here " + highlightData.start_index);
}
async function deleteHighlight(highlightId) {
  try {
    const response = await fetch(`/api/user/delete_highlight/${highlightId}/`, { // Removed highlightId from the URL
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken2
      },
      body: JSON.stringify({ highlight_id: highlightId }), // Pass highlightId in the request body
    });

    if (response.ok) {
      console.log("Highlight deleted successfully!");
      // Optionally, refresh the highlights or make any necessary updates to the UI
      await fetchHighlights(mediaId);
      createSubtitles(); // Recreate subtitles after fetching new highlights

    } else {
      console.error('Failed to delete highlight:', await response.text());
    }
  } catch (error) {
    console.error('Error during delete highlight:', error);
  }
}






async function splitHighlight(highlightId, splitStartIndex, splitEndIndex) {
  console.log("highlightId:", highlightId);
  console.log("splitStartIndex:", splitStartIndex);
  console.log("splitEndIndex:", splitEndIndex);

  const originalHighlight = transformedArray.find(item => item.id === highlightId);
  const highlightStartIndexRelativeToHighlight = splitStartIndex - originalHighlight.start_index;
  const highlightEndIndexRelativeToHighlight = splitEndIndex - originalHighlight.start_index;

  console.log("originalHighlight:", originalHighlight);
  console.log("highlightStartIndexRelativeToHighlight:", highlightStartIndexRelativeToHighlight);
  console.log("highlightEndIndexRelativeToHighlight:", highlightEndIndexRelativeToHighlight);

  if (splitStartIndex <= originalHighlight.start_index && splitEndIndex >= originalHighlight.end_index) {
    console.log("1");
    await deleteHighlight(highlightId);
    return;
  }

  if (splitStartIndex <= originalHighlight.start_index && splitEndIndex < originalHighlight.end_index) {
        console.log("2");

    const newHighlight = {
      ...originalHighlight,
      start_index: parseInt(splitEndIndex, 10) + 1,
      highlighted_text: originalHighlight.highlighted_text.substring(highlightEndIndexRelativeToHighlight + 1)
    };

    await deleteHighlight(highlightId);
    await addHighlight(newHighlight);
    return;
  }

  if (splitStartIndex > originalHighlight.start_index && splitEndIndex >= originalHighlight.end_index) {
        console.log("3");

    const newHighlight = {
      ...originalHighlight,
      end_index: splitStartIndex - 1,
      highlighted_text: originalHighlight.highlighted_text.substring(0, highlightStartIndexRelativeToHighlight)
    };
        console.log("mon");

    await deleteHighlight(highlightId);
    await addHighlight(newHighlight);
    return;
  }

  if (splitStartIndex > originalHighlight.start_index && splitEndIndex < originalHighlight.end_index) {
            console.log("4");


    const firstHighlight = {
      ...originalHighlight,
      end_index: splitStartIndex - 1,
      highlighted_text: originalHighlight.highlighted_text.substring(0, highlightStartIndexRelativeToHighlight)
    };

    const secondHighlight = {
      ...originalHighlight,
    start_index: parseInt(splitEndIndex, 10) + 1,
      highlighted_text: originalHighlight.highlighted_text.substring(highlightEndIndexRelativeToHighlight + 1)
    };
        console.log(secondHighlight);
                console.log(firstHighlight);


    await deleteHighlight(highlightId);
    await addHighlight(secondHighlight);

    await addHighlight(firstHighlight);
    return;
  }

  console.error('Invalid split indices for highlight:', originalHighlight);
}


    })(window, document);