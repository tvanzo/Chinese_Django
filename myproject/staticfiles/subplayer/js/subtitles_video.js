var mediaHasBeenPlayed = false;
// Existing code to parse media_json
var csrftoken2;
var media;
var playerReady = false;
var player;
var currentStatus=document.getElementById('media-status').getAttribute('data-status');
var initialTimeSet = false; // This flag will help us ensure we only set the time once after the desired point
let lastUpdateTime = 0;
    let isPlayingHighlights = false; // Flag to control highlight playback

function findCurrentSubtitleFrame(currentTime) {
    for (const word of subtitleData.words) { // Iterate over the "words" array
        if (currentTime >= word.startTime && currentTime <= word.endTime) {
            return word;
        }
    }
    console.log("ZZZ No matching word found for current time: " + currentTime);
    return null;
}


function onYouTubeIframeAPIReady() {
    player = new YT.Player('player', {
        videoId: mediaId,
        playerVars: {
            autoplay: 0, // Ensure autoplay is off
            controls: 1,
            start: 0,
            origin: window.location.origin
        },
        events: {
            'onReady': onPlayerReady,
            'onStateChange': onPlayerStateChange
        }
    });
}

function onPlayerReady(event) {
  playerReady = true;
  console.log("Player is ready. Player ready state:", playerReady);

  createSubtitles();

  if (media) {
    console.log("Media is defined, setting up progress saving and fetching media progress...");
    setupProgressSaving();

    // Introduce a delay before fetching progress
    setTimeout(() => {
      fetchMediaProgressAndSeek();
    }, 1000); // Delay of 1000 milliseconds (1 second)

    setInterval(updateProgress, 300);
  }
}
function fetchMediaProgressAndSeek() {
    fetch(`/api/user/media_progress/${mediaId}/`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken2,
        },
    })
    .then(response => response.json())
    .then(data => {
        console.log("Fetched media progress:", data.time_stopped, data);
        // Seek to time stopped if applicable
        if (data && data.time_stopped != null) {
            player.seekTo(data.time_stopped, true);
            lastUpdateTime = data.lastUpdateTime; // Use time_stopped as lastUpdateTime
            console.log("aaa" +lastUpdateTime);
             if (currentStatus==='none'){
        lastUpdateTime=0;
        console.log("It is true");
            }
            console.log("status" + currentStatus);
            console.log("LUT" + lastUpdateTime);
        } else {
            console.log("No progress found, starting from the beginning");
            player.seekTo(0, true);
        }
    })
    .catch(error => console.error('Error:', error));
}

function seekToTimeStopped(timeStopped) {
    if (player && playerReady) {
        player.seekTo(timeStopped, true);
        ensurePlaybackStartsAt(timeStopped);
    }
}

function ensurePlaybackStartsAt(expectedStart) {
    if (!initialTimeSet) {
        initialTimeSet = true; // Prevent multiple intervals
        const checkInterval = setInterval(() => {
            if (Math.abs(player.getCurrentTime() - expectedStart) > 1) {
                console.log("Adjusting playback to correct start time");
                player.seekTo(expectedStart, true);
            } else {
                clearInterval(checkInterval);
                player.playVideo(); // Start playing only after confirming the correct start time
            }
        }, 100);
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
    .then(data => console.log('Progress seek saved successfully:', data))
    .catch((error) => {
        console.error('Error saving progress:', error);
    });
}

let saveProgressInterval;

// Set up interval to save progress every 5 seconds when the video is playing
function onPlayerStateChange(event) {
    console.log("Player state changed:", event.data);
    console.log("isplayinghiglights"+ isPlayingHighlights);
    if ((event.data === YT.PlayerState.PLAYING || event.data === YT.PlayerState.PAUSED) && !mediaHasBeenPlayed) {
        mediaHasBeenPlayed = true;
        fetchMediaProgressAndSeek();
        console.log(event.data);
        console.log("Media is now playing for the first time.");

        fetch('/api/user/viewed-media/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken2
            },
            body: JSON.stringify({
                mediaId: mediaId,
            })
        }).then(response => response.json())
          .then(data => console.log("Viewed media added:", data))
          .catch(error => console.error("Error adding viewed media:", error));
    }


}

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
function setupProgressSaving() {
    console.log("settingupprogresssaving");
    const saveInterval = 5000; // Continue saving every 5 seconds

    function getCurrentStatus() {
        // This function ensures fetching the latest status dynamically
        return document.getElementById('media-status').getAttribute('data-status');
    }

    setInterval(() => {
        if (!player || typeof player.getCurrentTime !== 'function') {
            console.error('Player not initialized or getCurrentTime not available');
            return;
        }

        const currentStatus = getCurrentStatus(); // Fetch the current status
        const currentTime = player.getCurrentTime();
        const timeChange = currentTime - lastUpdateTime; // Calculate the time change since last update

        console.log("currentStatus: " + currentStatus);
        console.log("currentTime: " + currentTime);
        console.log("timeChange: " + timeChange);

        // Call update-progress endpoint if the time change is 60 seconds or more and status is 'in_progress'
        if (Math.abs(timeChange) >= 10 && currentStatus === 'in_progress') {
            const wordsPerSecond = media.word_count / media.video_length; // Assuming these values are correctly initialized
            const additionalWords = wordsPerSecond * timeChange; // Calculate additional words
            const additionalMinutes = timeChange; // Calculate additional minutes

            console.log(`Updating progress: Additional Words: ${additionalWords}, Additional Minutes: ${additionalMinutes}, Last Update Time: ${lastUpdateTime}`);

            fetch('/api/user/update-progress', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken2,
                },
                body: JSON.stringify({
                    mediaId: mediaId,
                    additionalWords: additionalWords,
                    additionalMinutes: additionalMinutes,
                    progressTime: currentTime,
                }),
            })
            .then(response => response.json())
            .then(data => console.log('Update progress successful:', data))
            .catch(error => console.error('Error updating progress:', error));

            lastUpdateTime = currentTime; // Update lastUpdateTime to the current time after sending update
        }


    }, saveInterval);
}






document.addEventListener('DOMContentLoaded', function() {
    csrftoken2 = getCookie('csrftoken');
    // Parse media JSON. Ensure server-side rendering fills '{{ media_json|escapejs }}' in

    // Check if player is ready before calling setupProgressSaving
    if (playerReady) {
        setupProgressSaving();
    }

    // Additional DOMContentLoaded logic
});


// Load the YouTube Iframe API
var tag = document.createElement('script');
tag.src = 'https://www.youtube.com/iframe_api';
var firstScriptTag = document.getElementsByTagName('script')[0];
firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);






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
 function checkHighlightExistence() {
        const ul = document.getElementById('highlight-list');
        const noHighlightsMsg = document.getElementById('no-highlights');
        if (ul.children.length === 0) {
            if (!noHighlightsMsg) {
                const li = document.createElement('li');
                li.id = 'no-highlights';
                li.textContent = 'No highlights found.';
                ul.appendChild(li);
            }
        } else {
            if (noHighlightsMsg) {
                noHighlightsMsg.remove();
            }
        }
    }

function updateSidebarWithHighlight(highlight) {
    const ul = document.getElementById('highlight-list');
    const li = document.createElement('li');
    li.className = 'highlight-item';

    const div = document.createElement('div');
    div.className = 'highlight-container';

    const a = document.createElement('a');
    a.href = "#";
    a.textContent = highlight.highlighted_text;
    a.dataset.startTime = highlight.start_time.toString();
    a.dataset.endTime = highlight.end_time.toString();  // Ensure end time is also set
    a.dataset.frameIndex = highlight.frame_index;
    a.dataset.startSentenceIndex = highlight.start_sentence_index;
    a.dataset.startIndex = highlight.start_index;

    const img = document.createElement('img');
    img.src = '/static/subplayer/trash.png';
    img.alt = "Delete";
    img.className = "delete-highlight";
    img.setAttribute('data-highlight-id', highlight.id);
    img.addEventListener('click', function() {
        deleteHighlight(this.dataset.highlightId);
    });

    div.appendChild(a);
    div.appendChild(img);
    li.appendChild(div);

    // Find correct position based on frame index, sentence index, and start index
    let inserted = false;
    const existingHighlights = Array.from(ul.getElementsByClassName('highlight-item'));
    for (let i = 0; i < existingHighlights.length; i++) {
        const existingHighlight = existingHighlights[i];
        const existingFrameIndex = parseInt(existingHighlight.querySelector('a').dataset.frameIndex);
        const existingSentenceIndex = parseInt(existingHighlight.querySelector('a').dataset.startSentenceIndex);
        const existingStartIndex = parseInt(existingHighlight.querySelector('a').dataset.startIndex);

        if ((highlight.frame_index < existingFrameIndex) ||
            (highlight.frame_index === existingFrameIndex && highlight.start_sentence_index < existingSentenceIndex) ||
            (highlight.frame_index === existingFrameIndex && highlight.start_sentence_index === existingSentenceIndex && highlight.start_index < existingStartIndex)) {
            ul.insertBefore(li, existingHighlight);
            inserted = true;
            break;
        }
    }

    if (!inserted) {
        ul.appendChild(li);
    }

    checkHighlightExistence();
    setupHighlightLinks();  // Re-setup links to ensure new highlight is interactive
}




function handleHighlightClick(e) {
    e.preventDefault();
}














async function addHighlight(highlightData) {
    const response = await fetch(`/api/user/create_highlight`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken2
        },
        body: JSON.stringify(highlightData),
    });

    if (response.ok) {
        const addedHighlight = await response.json();
        highlightData.id = addedHighlight.id;
        updateSidebarWithHighlight(highlightData); // Adds the new highlight to the sidebar
        await fetchHighlights(highlightData.media); // Refresh highlights data
        createSubtitles(); // This needs to refresh or recreate subtitles based on new data
        setupHighlightLinks(); // Re-setup links to ensure new highlights are interactive
    } else {
        console.error('Failed to add highlight:', await response.text());
    }
}




// Your other functions (updateProgress, createSubtitles, etc.) go here...
// ...
var y=0;
function findSubtitleIndex(time) {
    if (framesArray.length === 0) return -1;

    // Handle time before the start of the first frame
    if (time < parseFloat(framesArray[0][0].startTime)) {
        return 0; // Consider it as the first frame
    }

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
    console.log("datga" + syncData);
      var syncData2 = []; // New array to track sentences

  function createFramesArray(syncData) {
    let currentFrame = [];
    let currentFrameCharCount = 0;
    const charLimit = 60; // Character limit for each frame

    syncData.forEach(wordItem => {
        let sentenceCharCount = wordItem.word.length;
        if ((currentFrameCharCount + sentenceCharCount) <= charLimit) {
            currentFrame.push({
                startTime: wordItem.startTime,
                endTime: wordItem.endTime,
                sentence: wordItem.word
            });
            currentFrameCharCount += sentenceCharCount;
        } else {
            framesArray.push(currentFrame);
            currentFrame = [{
                startTime: wordItem.startTime,
                endTime: wordItem.endTime,
                sentence: wordItem.word
            }];
            currentFrameCharCount = sentenceCharCount;
        }
    });

    // Add the last frame if it has content
    if (currentFrame.length > 0) {
        framesArray.push(currentFrame);
    }

    // Ensure the first frame starts at 0 seconds
    if (framesArray.length > 0 && framesArray[0][0].startTime > 0) {
        framesArray[0][0].startTime = 0;
    }
}


// Call this function with your syncData
createFramesArray(syncData);


  var loopButton = doc.getElementById("loop-button");



createSubtitles();





  var selectedText = "";
  var frame_index;
var isLoopMode = false;
var isCmdPressed = false; // Track the Command/Control key state
var loopingInterval = null;

function toggleLoopMode() {
    isLoopMode = !isLoopMode; // Toggle the state
    updateLoopIcon(); // Update the icon based on the new state

    if (!isLoopMode && loopingInterval) {
        clearInterval(loopingInterval); // Clear the interval when turning loop mode off
        loopingInterval = null; // Reset the interval ID
    }

    if (isLoopMode) {
        const currentTime = player.getCurrentTime();
        const currentFrameIndex = findSubtitleIndex(currentTime);

        if (currentFrameIndex === 0) {
            player.seekTo(0, true); // Ensure it starts from the very beginning
            player.playVideo();
        }
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

// Add event listeners for the Command/Control key
document.addEventListener('keydown', function(event) {
    if ((event.key === "Meta" || event.key === "Control") && !isCmdPressed) { // Meta for Mac Command key, Control for Ctrl key
        isCmdPressed = true;
        if (!isLoopMode) {
            toggleLoopMode(); // Enable loop mode when Command/Control key is pressed
        }
    }
});

document.addEventListener('keyup', function(event) {
    if ((event.key === "Meta" || event.key === "Control") && isCmdPressed) {
        isCmdPressed = false;
        if (isLoopMode) {
            toggleLoopMode(); // Disable loop mode when Command/Control key is released
        }
    }
});

document.getElementById('loop-icon').addEventListener('click', function() {
    toggleLoopMode(); // Toggle loop mode when the loop button is clicked
});

// Existing code for mouseup event listener
subtitles.addEventListener("mouseup", function() {
    if (isLoopMode) {
        const selection = window.getSelection();
        const selectedText = selection.toString().trim();
        if (!selectedText) return;

        const currentTime = player.getCurrentTime();
        const currentFrameIndex = findSubtitleIndex(currentTime);

        if (currentFrameIndex === -1) return;

        const frameSubtitles = framesArray[currentFrameIndex];
        let concatenatedSubtitles = frameSubtitles.map(sub => sub.sentence).join('');

        let startLoopTime = null;
        let endLoopTime = null;

        if (concatenatedSubtitles.includes(selectedText)) {
            startLoopTime = parseFloat(frameSubtitles[0].startTime);
            endLoopTime = parseFloat(frameSubtitles[frameSubtitles.length - 1].endTime);

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

        if (startLoopTime !== null && endLoopTime !== null) {
            if (loopingInterval) {
                clearInterval(loopingInterval);
            }

            player.seekTo(startLoopTime, true);
            player.playVideo();

            loopingInterval = setInterval(() => {
                if (player.getCurrentTime() >= endLoopTime) {
                    player.seekTo(startLoopTime, true);
                }
            }, 100);
        }
    }
});














fetch('/api/user/viewed_media_list/read')
    .then(response => response.json())
    .then(data => {
        const container = document.getElementById('viewed-media-container');

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

function handleHighlightCreation() {
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
        if (overlappingHighlight.start_sentence_index != overlappingHighlight.end_sentence_index) {
            console.log("first" + overlappingHighlight.start_sentence_index);
            console.log(overlappingHighlight.end_sentence_index);
            deleteHighlight(overlappingHighlight.id);
        } else if (overlappingHighlight.start_index === start_char_index &&
            overlappingHighlight.end_index === end_char_index) {
            deleteHighlight(overlappingHighlight.id);
            console.log("Deleted");
        } else {
            console.log("lo");
            console.log(start_char_index + " " + end_char_index);
            splitHighlight(overlappingHighlight.id, start_char_index, end_char_index);
            console.log(start_char_index + "" + end_char_index);
        }
    } else {
        console.log("low");
        if (start_char_index !== null && end_char_index !== null && highlightStartTime !== null && highlightEndTime !== null) {
            console.log("All indexes found");
            createHighlight(selectedText, mediaId, start_char_index, end_char_index, highlightStartSentenceIndex, highlightEndSentenceIndex, highlightStartTime, highlightEndTime, currentSubtitleIndex);
        }
    }
}

// Event listener for shift key down
document.addEventListener('keydown', function (event) {
    if (event.shiftKey) {
        handleHighlightCreation();
    }
});

// Event listener for highlight icon click
document.getElementById('highlight-icon').addEventListener('click', function () {
    console.log("fired");
    handleHighlightCreation();
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