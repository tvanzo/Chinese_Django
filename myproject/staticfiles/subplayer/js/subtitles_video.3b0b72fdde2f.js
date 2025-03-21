
var mediaHasBeenPlayed = false;
var csrftoken2;
var media;
var playerReady = false;
var player;
var currentStatus = document.getElementById('media-status').getAttribute('data-status');
var initialTimeSet = false;
let lastUpdateTime = 0;
let isPlayingHighlights = false;

/* Subtitles & highlights */
var highlightMap = {};          // Maps frameIndex_sentenceIndex_charIndex -> array of highlight times
var transformedArray = [];      // List of highlight objects from server
var currentSubtitleIndex = 0;   // Which frame is active
var framesArray = [];           // 2D array: frames => [ {startTime, endTime, sentence}, ... ]
var subtitles = document.getElementById("subtitles");
var subtitleTimes = [];

/**
 * We'll store the requestAnimationFrame ID here,
 * so we can cancel it when paused or ended.
 */
let rafId = null;

/*************************************************
 * YOUTUBE IFRAME API
*************************************************/
function onYouTubeIframeAPIReady() {
    player = new YT.Player('player', {
        videoId: mediaId,
        playerVars: {
            autoplay: 0,
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
    console.log("Player is ready.");

    if (media) {
        setupProgressSaving();
        // Keep your 1-second delay for fetching media progress if desired:
        setTimeout(() => {
            fetchMediaProgressAndSeek();
        }, 1000);

        // Remove the old setInterval(updateProgress, 100).
        // We'll rely on requestAnimationFrame to update.
    }
}

function onPlayerStateChange(event) {
    console.log("Player state changed:", event.data, " isPlayingHighlights:", isPlayingHighlights);

    // START the animation loop if the player is PLAYING
    if (event.data === YT.PlayerState.PLAYING) {
        startRAFLoop();
    }
    // STOP the animation loop if paused or ended
    else if (event.data === YT.PlayerState.PAUSED || event.data === YT.PlayerState.ENDED) {
        stopRAFLoop();
    }

    // If first time playing or paused, fetch progress if not done yet
    if ((event.data === YT.PlayerState.PLAYING || event.data === YT.PlayerState.PAUSED) && !mediaHasBeenPlayed) {
        mediaHasBeenPlayed = true;
        fetchMediaProgressAndSeek();
        console.log("Media is now playing for the first time.");

        fetch('/api/user/viewed-media/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken2
            },
            body: JSON.stringify({ mediaId: mediaId })
        })
        .then(response => response.json())
        .then(data => console.log("Viewed media added:", data))
        .catch(error => console.error("Error adding viewed media:", error));
    }
}

/*************************************************
 * RAF LOOP (to replace setInterval)
*************************************************/
function startRAFLoop() {
    if (!rafId) {
        rafId = requestAnimationFrame(animLoop);
    }
}
function animLoop() {
    updateProgress();
    rafId = requestAnimationFrame(animLoop);
}
function stopRAFLoop() {
    if (rafId) {
        cancelAnimationFrame(rafId);
        rafId = null;
    }
}

/*************************************************
 * PROGRESS & SEEK
*************************************************/
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
        if (data && data.time_stopped != null) {
            player.seekTo(data.time_stopped, true);
            lastUpdateTime = data.lastUpdateTime;
            if (currentStatus === 'none') {
                lastUpdateTime = 0;
            }
        } else {
            console.log("No progress found, starting from the beginning");
            player.seekTo(0, true);
        }
    })
    .catch(error => console.error('Error:', error));
}

function setupProgressSaving() {
    console.log("setting up progress saving...");
    const saveInterval = 5000;

    function getCurrentStatus() {
        return document.getElementById('media-status').getAttribute('data-status');
    }

    setInterval(() => {
        if (!player || typeof player.getCurrentTime !== 'function') {
            console.error('Player not initialized or getCurrentTime not available');
            return;
        }

        const currentStatus = getCurrentStatus();
        const currentTime = player.getCurrentTime();
        const timeChange = currentTime - lastUpdateTime;

        // Example: update progress if time has changed by 10s or more, and status is 'in_progress'
        if (Math.abs(timeChange) >= 10 && currentStatus === 'in_progress') {
            const wordsPerSecond = media.word_count / media.video_length;
            const additionalWords = wordsPerSecond * timeChange;
            const additionalMinutes = timeChange/60;

            console.log(`Updating progress: +${additionalWords} words, +${additionalMinutes} minutes`);

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

            lastUpdateTime = currentTime;
        }
    }, saveInterval);
}

/*************************************************
 * FETCH HIGHLIGHTS & PARTIAL MAP UPDATES
*************************************************/
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
            console.log("📌 DEBUG: Raw Highlights Data from API:", data);

            if (!Array.isArray(data)) {
                data = JSON.parse(data);
            }
            transformedArray = data.map(item => ({
                media: item.fields.media,
                id: item.pk,
                start_time: item.fields.start_time,
                end_time: item.fields.end_time,
                highlighted_text: item.fields.highlighted_text,
                start_index: item.fields.start_index,
                end_index: item.fields.end_index,
                start_sentence_index: item.fields.start_sentence_index,
                end_sentence_index: item.fields.end_sentence_index,
                frame_index: item.fields.frame_index
            }));

            console.log("📌 DEBUG: Processed TransformedArray:", transformedArray);

            updateHighlightMap();
            resolve();
        })
        .catch(error => {
            console.error("🚨 ERROR Fetching Highlights:", error);
            reject(error);
        });
    });
}


function updateHighlightMap() {
    highlightMap = {};
    transformedArray.forEach(highlight => {
        addHighlightToMapRange(highlight);
    });
}

// Partial insertion of highlight to highlightMap
function addHighlightToMapRange(highlight) {
    let fIdx = highlight.frame_index;
    for (let s = highlight.start_sentence_index; s <= highlight.end_sentence_index; s++) {
        let startC = (s === highlight.start_sentence_index)
            ? parseInt(highlight.start_index, 10) : 0;
        let endC = (s === highlight.end_sentence_index)
            ? parseInt(highlight.end_index, 10)
            : framesArray[fIdx][s].sentence.length - 1;
        for (let c = startC; c <= endC; c++) {
            const key = `${fIdx}_${s}_${c}`;
            if (!highlightMap[key]) {
                highlightMap[key] = [];
            }
            highlightMap[key].push({
                startTime: parseFloat(highlight.start_time),
                endTime: parseFloat(highlight.end_time)
            });
        }
    }
}

// Partial removal from highlightMap
function removeHighlightFromMapRange(highlight) {
    let fIdx = highlight.frame_index;
    for (let s = highlight.start_sentence_index; s <= highlight.end_sentence_index; s++) {
        let startC = (s === highlight.start_sentence_index)
            ? parseInt(highlight.start_index, 10) : 0;
        let endC = (s === highlight.end_sentence_index)
            ? parseInt(highlight.end_index, 10)
            : framesArray[fIdx][s].sentence.length - 1;
        for (let c = startC; c <= endC; c++) {
            const key = `${fIdx}_${s}_${c}`;
            if (highlightMap[key]) {
                highlightMap[key] = highlightMap[key].filter(h =>
                    !(h.startTime === parseFloat(highlight.start_time) &&
                      h.endTime   === parseFloat(highlight.end_time))
                );
                if (highlightMap[key].length === 0) {
                    delete highlightMap[key];
                }
            }
        }
    }
}

/*************************************************
 * SIDEBAR & CHECKS
*************************************************/
function updateSidebarWithHighlight(highlightData) {
    const ul = document.getElementById('highlight-list');
    const fragment = document.createDocumentFragment();

    const li = document.createElement('li');
    li.className = 'highlight-item';

    const div = document.createElement('div');
    div.className = 'highlight-container';

    const a = document.createElement('a');
    a.href = "#";
    a.textContent = highlightData.highlighted_text;
    a.dataset.startTime = highlightData.start_time.toString();
    a.dataset.endTime = highlightData.end_time.toString();
    a.dataset.frameIndex = highlightData.frame_index;
    a.dataset.startSentenceIndex = highlightData.start_sentence_index;
    a.dataset.startIndex = highlightData.start_index;

    const img = document.createElement('img');
    img.src = '/static/subplayer/trash.png';
    img.alt = "Delete";
    img.className = "delete-highlight";
    img.setAttribute('data-highlight-id', highlightData.id);
    img.addEventListener('click', function() {
        deleteHighlight(this.dataset.highlightId);
    });

    div.appendChild(a);
    div.appendChild(img);
    li.appendChild(div);
    fragment.appendChild(li);

    ul.appendChild(fragment);
    checkHighlightExistence();
    setupHighlightLinks(); // If you have a function for link-based interactions
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

/*************************************************
 * SUBTITLES (CREATE & PARTIAL RE-RENDER)
*************************************************/
function createSubtitles() {
    if (currentSubtitleIndex < framesArray.length) {
        let currentFrame = framesArray[currentSubtitleIndex];
        subtitles.innerHTML = "";
        subtitleTimes = [];

        for (let i = 0; i < currentFrame.length; i++) {
            const spanId = "s_" + currentSubtitleIndex + "_" + i;
            let element = document.createElement('span');
            element.setAttribute("id", spanId);
            element.classList.add('sentence-span');

            let highlightedSentence = "";
            let sentence = currentFrame[i].sentence;

            for (let k = 0; k < sentence.length; k++) {
                const key = `${currentSubtitleIndex}_${i}_${k}`;
                const characterHighlights = highlightMap[key];
                if (characterHighlights) {
                    highlightedSentence += `<span class="perm-highlight">${sentence.charAt(k)}</span>`;
                } else {
                    highlightedSentence += sentence.charAt(k);
                }
            }
            element.innerHTML = highlightedSentence;
            subtitles.appendChild(element);

            subtitleTimes.push({
                startTime: parseFloat(currentFrame[i].startTime),
                endTime: parseFloat(currentFrame[i].endTime),
            });
        }
    }
}

// Re-render only one sentence
function reRenderSentence(frameIndex, sentenceIndex) {
    const sentenceSpan = document.getElementById(`s_${frameIndex}_${sentenceIndex}`);
    if (!sentenceSpan) return;

    const sentenceData = framesArray[frameIndex][sentenceIndex];
    if (!sentenceData) return;

    let rawText = sentenceData.sentence;
    let updatedHTML = "";
    for (let k = 0; k < rawText.length; k++) {
        const key = `${frameIndex}_${sentenceIndex}_${k}`;
        const highlights = highlightMap[key];
        if (highlights) {
            updatedHTML += `<span class="perm-highlight">${rawText.charAt(k)}</span>`;
        } else {
            updatedHTML += rawText.charAt(k);
        }
    }
    sentenceSpan.innerHTML = updatedHTML;
}

/*************************************************
 * UPDATE PROGRESS (replaces the old setInterval)
*************************************************/
function updateProgress() {
    if (!player || typeof player.getCurrentTime !== 'function') return;

    let currentTime = player.getCurrentTime();

    // Figure out if we've moved to a new frame
    const correctIndex = findSubtitleIndex(currentTime);
    if (correctIndex !== -1 && correctIndex !== currentSubtitleIndex) {
        currentSubtitleIndex = correctIndex;
        createSubtitles();
    }

    // Highlight the active sentence(s) in the current frame
    if (currentSubtitleIndex < framesArray.length) {
        let frame = framesArray[currentSubtitleIndex];
        for (let j = 0; j < frame.length; j++) {
            const sentenceElement = document.getElementById("s_" + currentSubtitleIndex + "_" + j);
            if (!sentenceElement) continue;

            if (
                currentTime >= parseFloat(frame[j].startTime) &&
                currentTime <= parseFloat(frame[j].endTime)
            ) {
                sentenceElement.classList.add('active-highlight');
            } else {
                sentenceElement.classList.remove('active-highlight');
            }
        }
    }
}

function findSubtitleIndex(time) {
    if (!framesArray.length) return -1;

    if (time < parseFloat(framesArray[0][0].startTime)) {
        return 0;
    }
    for (let i = 0; i < framesArray.length; i++) {
        let frameStartTime = parseFloat(framesArray[i][0].startTime);
        let frameEndTime   = parseFloat(framesArray[i][framesArray[i].length - 1].endTime);
        if (time >= frameStartTime && time <= frameEndTime) {
            return i;
        }
    }
    return -1;
}
function showLimitPopup() {
    console.log("🚨 showLimitPopup() called!");

    if (document.querySelector('.limit-popup')) {
        console.log("Popup already exists, not creating another one.");
        return;
    }

    const overlay = document.createElement('div');
    overlay.className = 'overlay active';  // Add active immediately

    const popup = document.createElement('div');
    popup.className = 'limit-popup';
    popup.innerHTML = `
        <div class="popup-content">
            <div class="popup-header">
                <div class="warning-icon">⚠️</div>
                <h3 class="popup-title">Highlight Limit Reached</h3>
            </div>
            <p class="popup-message">You've reached your daily limit of 3 highlights. Upgrade your account to unlock unlimited highlights and more features.</p>
            <div class="button-container">
                <button class="upgrade-button" onclick="redirectToAccount()">Upgrade Now</button>
                <button class="close-button" onclick="closePopup()">Maybe Later</button>
            </div>
        </div>
    `;

    document.body.appendChild(overlay);
    document.body.appendChild(popup);

    // Ensure smooth appearance transition
    setTimeout(() => {
        overlay.classList.add('active');
        popup.classList.add('active');
    }, 10);

    console.log("✅ Popup added to the DOM");
}

function closePopup() {
    console.log("Closing popup");
    const popup = document.querySelector('.limit-popup');
    const overlay = document.querySelector('.overlay');
    if (popup) {
        popup.remove();
    }
    if (overlay) {
        overlay.classList.remove('active');
        setTimeout(() => {
            overlay.remove();
        }, 300); // Wait for fade-out transition before removing
    }
}

function redirectToAccount() {
    window.location.href = '/join/';
}


/*************************************************
 * ADD / DELETE / SPLIT HIGHLIGHTS (PARTIAL)
*************************************************/
async function addHighlight(highlightData) {
    try {
        const response = await fetch(`/api/user/create_highlight`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken2
            },
            body: JSON.stringify(highlightData),
        });

        console.log("📢 Response status:", response.status);
        console.log("✅ Response OK:", response.ok);

        const responseText = await response.text(); // Read response as text first
        let jsonResponse = {};

        try {
            jsonResponse = JSON.parse(responseText); // Parse response to JSON
        } catch (e) {
            console.error("❌ JSON Parse Error:", e, responseText);
        }

        console.log("🔎 Full API response:", jsonResponse);

        // Check if the limit was reached
        if (jsonResponse.limit_reached) {
            console.log("🛑 Limit reached - Calling showLimitPopup()");
            showLimitPopup();
            return null; // Stop processing further
        }

        if (!response.ok) {
            console.error("❌ Unexpected error:", jsonResponse);
            throw new Error('Failed to add highlight: ' + (jsonResponse.error || "Unknown error"));
        }

        // Process valid highlight response
        const addedHighlight = jsonResponse;
        highlightData.id = addedHighlight.id;
        return addedHighlight;

    } catch (error) {
        console.error('❌ Error adding highlight:', error);
    }
}




function createHighlight(
    selectedText, mediaId,
    highlightStartIndex, highlightEndIndex,
    highlightStartSentenceIndex, highlightEndSentenceIndex,
    startTime, endTime, frameIndex
) {
    console.log("createHighlight triggered");

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

    // Update local data
    transformedArray.push(highlightData);
    addHighlightToMapRange(highlightData);

    // Re-render only changed sentences
    for (let s = highlightStartSentenceIndex; s <= highlightEndSentenceIndex; s++) {
        reRenderSentence(frameIndex, s);
    }

    // Update sidebar
    updateSidebarWithHighlight(highlightData);

    // Save to server (no full re-fetch after success)
    addHighlight(highlightData)
    .then(() => {
        console.log("Highlight saved on server.");
    })
    .catch(error => {
        console.error('Error adding highlight:', error);
        removeHighlightFromUI(highlightData);
    });
}

async function deleteHighlight(highlightId) {
    try {
        const response = await fetch(`/api/user/delete_highlight/${highlightId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken2
            },
            body: JSON.stringify({ highlight_id: highlightId }),
        });

        if (response.ok) {
            console.log("Highlight deleted successfully!");

            // Remove from local data
            const index = transformedArray.findIndex(h => h.id == highlightId);
            if (index !== -1) {
                const deleted = transformedArray[index];
                transformedArray.splice(index, 1);

                // Partial remove from highlightMap
                removeHighlightFromMapRange(deleted);

                // Re-render only the impacted sentences
                for (let s = deleted.start_sentence_index; s <= deleted.end_sentence_index; s++) {
                    reRenderSentence(deleted.frame_index, s);
                }
                // Remove from sidebar
                removeHighlightFromUI(deleted);
            }

        } else {
            console.error('Failed to delete highlight:', await response.text());
        }
    } catch (error) {
        console.error('Error during delete highlight:', error);
    }
}

async function splitHighlight(highlightId, splitStartIndex, splitEndIndex) {
    console.log("splitHighlight =>", highlightId, splitStartIndex, splitEndIndex);

    const originalHighlight = transformedArray.find(item => item.id === highlightId);
    if (!originalHighlight) return;

    // Remove the original highlight
    await deleteHighlight(highlightId);

    // If left portion remains
    if (splitStartIndex > originalHighlight.start_index) {
        const leftPart = {
            ...originalHighlight,
            end_index: splitStartIndex - 1,
            highlighted_text: originalHighlight.highlighted_text.substring(
                0, splitStartIndex - originalHighlight.start_index
            )
        };
        createHighlight(
            leftPart.highlighted_text,
            leftPart.media,
            leftPart.start_index,
            leftPart.end_index,
            leftPart.start_sentence_index,
            leftPart.end_sentence_index,
            leftPart.start_time,
            leftPart.end_time,
            leftPart.frame_index
        );
    }

    // If right portion remains
    if (splitEndIndex < originalHighlight.end_index) {
        const rightStart = parseInt(splitEndIndex, 10) + 1;
        const rightPart = {
            ...originalHighlight,
            start_index: rightStart,
            highlighted_text: originalHighlight.highlighted_text.substring(
                rightStart - originalHighlight.start_index
            )
        };
        createHighlight(
            rightPart.highlighted_text,
            rightPart.media,
            rightPart.start_index,
            rightPart.end_index,
            rightPart.start_sentence_index,
            rightPart.end_sentence_index,
            rightPart.start_time,
            rightPart.end_time,
            rightPart.frame_index
        );
    }
}

function removeHighlightFromUI(hData) {
    const ul = document.getElementById('highlight-list');
    const items = ul.getElementsByClassName('highlight-item');
    for (let i = 0; i < items.length; i++) {
        let a = items[i].querySelector('a');
        if (a.dataset.startTime === hData.start_time.toString() &&
            a.dataset.endTime === hData.end_time.toString() &&
            a.dataset.frameIndex === hData.frame_index.toString()) {
            items[i].remove();
            break;
        }
    }
    checkHighlightExistence();
}

/*************************************************
 * DOMCONTENTLOADED => FETCH FRAMES, HIGHLIGHTS, THEN INIT SUBTITLES
*************************************************/
document.addEventListener('DOMContentLoaded', function() {
    csrftoken2 = getCookie('csrftoken');

    // If the player is already ready, set up saving
    if (playerReady) {
        setupProgressSaving();
    }

    // 1) Load highlights from server
    fetchHighlights(mediaId)
    .then(() => {
        // 2) Once framesArray is loaded, create the subtitles
        createSubtitles();

        // 3) Immediately call updateProgress() once so the first frame
        //    can show any highlight at time=0 (if applicable).
        updateProgress();
    })
    .catch(e => console.error("Error fetching highlights:", e));
});

function getCookie(name) {
    var cookieArr = document.cookie.split(";");
    for (let i = 0; i < cookieArr.length; i++) {
        var cookiePair = cookieArr[i].split("=");
        if (name == cookiePair[0].trim()) {
            return decodeURIComponent(cookiePair[1]);
        }
    }
    return null;
}

// Load the YouTube Iframe API
var tag = document.createElement('script');
tag.src = 'https://www.youtube.com/iframe_api';
var firstScriptTag = document.getElementsByTagName('script')[0];
firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

/*************************************************
 * CREATE FRAMESARRAY (CALLED FROM TRANSCRIPT FETCH)
*************************************************/
(async function(win, doc) {
    try {
        const response = await fetch(test2);  // "test2" presumably is your transcript JSON URL
        const data = await response.json();
        const syncData = data.words;
        // chunk words into frames
        createFramesArray(syncData);
        // we do NOT call createSubtitles() immediately here,
        // because we wait for fetchHighlights => in DOMContentLoaded.
    } catch (error) {
        console.error('Error fetching transcript data:', error);
    }

    function createFramesArray(sync) {
        let currentFrame = [];
        let currentFrameCharCount = 0;
        const charLimit = 50;

        sync.forEach(wordItem => {
            let wordLen = wordItem.word.length;
            if ((currentFrameCharCount + wordLen) <= charLimit) {
                currentFrame.push({
                    startTime: wordItem.startTime,
                    endTime: wordItem.endTime,
                    sentence: wordItem.word
                });
                currentFrameCharCount += wordLen;
            } else {
                framesArray.push(currentFrame);
                currentFrame = [{
                    startTime: wordItem.startTime,
                    endTime: wordItem.endTime,
                    sentence: wordItem.word
                }];
                currentFrameCharCount = wordLen;
            }
        });

        if (currentFrame.length > 0) {
            framesArray.push(currentFrame);
        }

        // If the first subtitle doesn't start at 0, force it:
        if (framesArray.length && framesArray[0][0].startTime > 0) {
            framesArray[0][0].startTime = 0;
        }
    }
})(window, document);

/*************************************************
 * HANDLE HIGHLIGHT CREATION (SELECTION LOGIC)
*************************************************/
document.addEventListener('keydown', function (event) {
    if (event.shiftKey) {
        handleHighlightCreation();
    }
});

// Icon click
document.getElementById('highlight-icon').addEventListener('click', function () {
    console.log("Highlight icon clicked");
    handleHighlightCreation();
});
function showSelectionRequiredPopup(action) {
    // Remove existing popup if any
    const existingPopup = document.querySelector('.selection-required-popup');
    const existingOverlay = document.querySelector('.overlay');
    if (existingPopup) existingPopup.remove();
    if (existingOverlay) existingOverlay.remove();

    // Create overlay
    const overlay = document.createElement('div');
    overlay.className = 'overlay';

    // Create popup
    const popup = document.createElement('div');
    popup.className = 'selection-required-popup';
    popup.innerHTML = `
        <div class="popup-content">
            <div class="popup-header">
                <div class="info-icon">ℹ️</div>
                <h3 class="popup-title">Text Selection Required</h3>
            </div>
            <p class="popup-message">
                Please select some text to ${action === 'highlight' ? 'highlight' : 'loop'}.
                ${action === 'highlight' ? 'Then click the Highlight button or press Shift.' : 'Then click the Loop button or press CMD/Control.'}
            </p>
            <button class="close-button" onclick="closeSelectionPopup()">OK</button>
        </div>
    `;

    // Append to body
    document.body.appendChild(overlay);
    document.body.appendChild(popup);

    // Trigger transition
    setTimeout(() => {
        overlay.classList.add('active');
        popup.classList.add('active');
    }, 10);
}

function closeSelectionPopup() {
    const popup = document.querySelector('.selection-required-popup');
    const overlay = document.querySelector('.overlay');
    if (popup && overlay) {
        popup.classList.remove('active');
        overlay.classList.remove('active');
        setTimeout(() => {
            popup.remove();
            overlay.remove();
        }, 300); // Match transition duration
    }
}
function handleHighlightCreation() {
    let selection = window.getSelection();
    if (selection.rangeCount === 0 || !selection.toString().trim()) {
        showSelectionRequiredPopup('highlight');
        return;
    }

    let range = selection.getRangeAt(0);
    let selectedText = selection.toString().trim();
    if (!selectedText) {
        showSelectionRequiredPopup('highlight');
        return;
    }

    // Rest of your existing logic...
    let startSpan = findParentWithClass(range.startContainer, 'sentence-span');
    let endSpan = findParentWithClass(range.endContainer, 'sentence-span');

    if (!startSpan || !endSpan) return;

    let start_char_index = calculateOffset(range.startContainer, range.startOffset, startSpan);
    let end_char_index = calculateOffset(range.endContainer, range.endOffset, endSpan) - 1;

    // Pad single digits
    if (start_char_index < 10) start_char_index = '0' + start_char_index;
    if (end_char_index < 10) end_char_index = '0' + end_char_index;

    let highlightStartSentenceIndex = parseInt(startSpan.id.split('_')[2]);
    let highlightEndSentenceIndex = parseInt(endSpan.id.split('_')[2]);
    let highlightStartTime = subtitleTimes[highlightStartSentenceIndex].startTime;
    let highlightEndTime = subtitleTimes[highlightEndSentenceIndex].endTime;

    // Check overlap logic and proceed as before...


    // Check overlap logic
    const overlappingHighlight = transformedArray.find(item =>
        parseFloat(`${item.start_sentence_index}.${item.start_index.toString().padStart(2, '0')}`)
            <= parseFloat(`${highlightEndSentenceIndex}.${end_char_index}`) &&
        parseFloat(`${item.end_sentence_index}.${item.end_index.toString().padStart(2, '0')}`)
            >= parseFloat(`${highlightStartSentenceIndex}.${start_char_index}`) &&
        item.frame_index === currentSubtitleIndex
    );

    if (overlappingHighlight) {
        // If there's an existing highlight overlapping
        if (overlappingHighlight.start_sentence_index !== overlappingHighlight.end_sentence_index) {
            deleteHighlight(overlappingHighlight.id);
        } else if (
            overlappingHighlight.start_index === start_char_index &&
            overlappingHighlight.end_index   === end_char_index
        ) {
            deleteHighlight(overlappingHighlight.id);
        } else {
            splitHighlight(overlappingHighlight.id, start_char_index, end_char_index);
        }
    } else {
        // No overlap => create new highlight
        if (
            start_char_index !== null &&
            end_char_index   !== null &&
            highlightStartTime !== null &&
            highlightEndTime   !== null
        ) {
            console.log("Creating new highlight");
            createHighlight(
                selectedText, mediaId,
                start_char_index, end_char_index,
                highlightStartSentenceIndex, highlightEndSentenceIndex,
                highlightStartTime, highlightEndTime,
                currentSubtitleIndex
            );
        }
    }
}

// Helpers used in handleHighlightCreation
function calculateOffset(container, offset, span) {
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
}

function findParentWithClass(node, className) {
    if (node.nodeType !== Node.ELEMENT_NODE) {
        node = node.parentNode;
    }
    while (node && (!node.classList || !node.classList.contains(className))) {
        node = node.parentNode;
    }
    return node;
}

/*************************************************
 * LOOP MODE LOGIC
*************************************************/
var isLoopMode = false;
var isCmdPressed = false;
var loopingInterval = null;

function toggleLoopMode() {
    let selection = window.getSelection();
    if (!isLoopMode && (!selection.rangeCount || !selection.toString().trim())) {
        showSelectionRequiredPopup('loop');
        return;
    }

    isLoopMode = !isLoopMode;
    updateLoopIcon();

    if (!isLoopMode && loopingInterval) {
        clearInterval(loopingInterval);
        loopingInterval = null;
    }

    if (isLoopMode) {
        const currentTime = player.getCurrentTime();
        const currentFrameIndex = findSubtitleIndex(currentTime);
        if (currentFrameIndex === 0) {
            player.seekTo(0, true);
            player.playVideo();
        }
    }
}

function updateLoopIcon() {
    const loopIcon = document.getElementById('loop-icon');
    loopIcon.classList.toggle('active', isLoopMode); // Toggle .active class based on isLoopMode
}

document.addEventListener('keydown', function(event) {
    if ((event.key === "Meta" || event.key === "Control") && !isCmdPressed) {
        isCmdPressed = true;
        if (!isLoopMode) {
            toggleLoopMode();
        }
    }
});
document.addEventListener('keyup', function(event) {
    if ((event.key === "Meta" || event.key === "Control") && isCmdPressed) {
        isCmdPressed = false;
        if (isLoopMode) {
            toggleLoopMode();
        }
    }
});
document.getElementById('loop-icon').addEventListener('click', function() {
    toggleLoopMode();
});

// If you have logic for loop selection on mouseup
subtitles.addEventListener("mouseup", function() {
    if (isLoopMode) {
        const selection = window.getSelection();
        const selectedText = selection.toString().trim();
        if (!selectedText) {
            showSelectionRequiredPopup('loop');
            return;
        }

        const currentTime = player.getCurrentTime();
        const currentFrameIndex = findSubtitleIndex(currentTime);
        if (currentFrameIndex === -1) return;

        const frameSubtitles = framesArray[currentFrameIndex];
        let concatSubtitles = frameSubtitles.map(sub => sub.sentence).join('');

        let startLoopTime = null;
        let endLoopTime   = null;

        if (concatSubtitles.includes(selectedText)) {
            startLoopTime = parseFloat(frameSubtitles[0].startTime);
            endLoopTime   = parseFloat(frameSubtitles[frameSubtitles.length - 1].endTime);

            // Refine start/end times by scanning
            for (let i = 0; i < frameSubtitles.length; i++) {
                if (frameSubtitles[i].sentence.includes(
                    selectedText.slice(0, Math.floor(selectedText.length / 2))
                )) {
                    startLoopTime = Math.max(startLoopTime, parseFloat(frameSubtitles[i].startTime));
                }
                if (frameSubtitles[i].sentence.includes(
                    selectedText.slice(Math.floor(selectedText.length / 2))
                )) {
                    endLoopTime = Math.min(endLoopTime, parseFloat(frameSubtitles[i].endTime));
                    break;
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

async function fetchVideoScript() {
    console.log("Fetching video transcript...");

    try {
        const response = await fetch(test2); // Fetch the transcript from the API
        const data = await response.json();

        if (!data.words || !Array.isArray(data.words)) {
            console.error("Transcript data is not in expected format", data);
            return "";
        }

        return data.words.map(wordItem => wordItem.word).join(' ');
    } catch (error) {
        console.error("Error fetching transcript:", error);
        return "";
    }
}
const studyGuideButton = document.getElementById('create-study-sheet');
const notification = document.getElementById('download-notification');
const body = document.body;

function showNotification() {
    notification.style.display = 'block'; // Make it visible
    setTimeout(() => {
        notification.classList.add('show'); // Fade in
        adjustBodyPadding(); // Adjust padding after showing
    }, 10); // Small delay to ensure display: block takes effect before transition
}

function hideNotification() {
    notification.classList.remove('show'); // Fade out
    setTimeout(() => {
        notification.style.display = 'none'; // Hide after fade
        adjustBodyPadding(); // Reset padding
    }, 300); // Match transition duration (0.3s)
}

function adjustBodyPadding() {
    if (notification.style.display !== 'none') {
        body.style.paddingTop = notification.offsetHeight + 'px';
    } else {
        body.style.paddingTop = '0';
    }
}

document.getElementById("create-study-sheet").addEventListener("click", async function() {
    console.log("Fetching video script and highlights...");

    const scriptText = await fetchVideoScript();
    if (!scriptText) {
        console.error("No script text found.");
        return;
    }

    try {
        await fetchHighlights(mediaId);
        let highlights = transformedArray.map(h => h.highlighted_text);

        console.log("Sending script and highlights to backend...");
        showNotification(); // Show notification
        studyGuideButton.disabled = true;

        const response = await fetch("/api/generate-pdf/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken()
            },
            body: JSON.stringify({
                script_text: scriptText,
                highlights: highlights
            }),
        });

        if (!response.ok) {
            throw new Error(`Server Error: ${response.status}`);
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "study_guide.pdf";
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        console.log("PDF downloaded successfully");
        hideNotification(); // Hide notification
        studyGuideButton.disabled = false;

    } catch (error) {
        console.error("Error generating PDF:", error);
        hideNotification(); // Hide on error
        studyGuideButton.disabled = false;
    }
});

function getCSRFToken() {
    return document.querySelector("meta[name='csrf-token']").getAttribute("content");
}

// Integrate with existing DOMContentLoaded padding logic
document.addEventListener('DOMContentLoaded', function() {
    // Existing welcome banner logic
    var banner = document.getElementById('welcome-banner');
    if (banner) {
        function adjustPadding() {
            if (banner && !banner.classList.contains('d-none')) {
                body.style.paddingTop = banner.offsetHeight + 'px';
            } else if (notification.style.display !== 'none') {
                body.style.paddingTop = notification.offsetHeight + 'px';
            } else {
                body.style.paddingTop = '0';
            }
        }
        adjustPadding();
        var observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.attributeName === 'class') adjustPadding();
            });
        });
        observer.observe(banner, { attributes: true, attributeFilter: ['class'] });
        banner.addEventListener('closed.bs.alert', adjustPadding);
    }

    // Ensure notification padding is checked on load too
    adjustBodyPadding();
});



