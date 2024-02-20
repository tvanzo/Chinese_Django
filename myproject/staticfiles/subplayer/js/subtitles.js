console.log("lmao");
var mediaHasBeenPlayed = false;
 
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

 audioPlayer.addEventListener('loadedmetadata', function() {
  // Call createSubtitles when the metadata for the audio is loaded
  createSubtitles();
});



audioPlayer.addEventListener('play', function() {
    if (!mediaHasBeenPlayed) {
        // This is the first time the media is played
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
});

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
            frame_index: item.fields.frame_index // add this line
        }));


            updateHighlightMap();
            resolve();
        })
        .catch(error => {
            console.log('Error during fetch:', error);
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
  li.id = `highlight-${highlight.id}`; // Give each highlight a unique ID
  const a = document.createElement('a');
  a.href = `#highlight-${highlight.id}`; // Create a link or identifier (modify as needed)
  a.textContent = highlight.highlighted_text;
  li.appendChild(a);
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
    var currentTime = audioPlayer.currentTime;

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
































        
        audioPlayer.addEventListener('timeupdate', updateProgress);

        var subtitles = document.getElementById("subtitles");

    (async function(win, doc) {
        // JavaScript code


    let transcript;
    let syncData5 = null; // Assign an initial value to syncData5
    console.log("test2"+ test2);
    try {
  const response = await fetch(test2);
  console.log(test2);
console.log("poop");
  const data = await response.json();
  transcript = data.transcript;
  syncData5 = data.words;
  
} catch (error) {
  console.error('Erroreeeee:', error);
}


    var syncData=syncData5;

      var syncData2 = []; // New array to track sentences
      
  function createFramesArray(syncData) {
    let currentFrame = [];
    let currentFrameCharCount = 0;
    const charLimit = 60; // Character limit for each frame

    syncData.forEach(wordItem => {
        console.log(wordItem);
         console.log(wordItem.word);

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

document.addEventListener('keydown', function(e) {

    if (e.keyCode === 91) { // 91 is the keyCode for 'Command' key on Mac
        isLoopMode = true;
    }
});

document.addEventListener('keydown', function(e) {

    if (isLoopMode) {
        if (e.keyCode === 38) { // 38 is the keyCode for 'Up' key
            // Increase speed by 10%, with a maximum of 2x
            audioSpeed = Math.min(audioSpeed + 0.1, 2);
        } else if (e.keyCode === 40) { // 40 is the keyCode for 'Down' key
            // Decrease speed by 10%, with a minimum of 0.1x
            audioSpeed = Math.max(audioSpeed - 0.1, 0.1);
        }

        e.preventDefault();  // prevent the default action (scroll)

        audioSpeedDisplay.innerText = "Speed: " + audioSpeed.toFixed(1) + "x";
        audioSpeedDisplay.style.display = "block";

        setTimeout(function() {
            audioSpeedDisplay.style.display = "none";
        }, 1000);  // hide the display after 1 second
    }
});


document.addEventListener('keyup', function(e) {

    if (e.keyCode === 91) { // 91 is the keyCode for 'Command' key on Mac
        isLoopMode = false;
        audioSpeed = 1;
        audioPlayer.playbackRate = 1;  // reset speed to normal

        if (loopingInterval) {
            clearInterval(loopingInterval);
            loopingInterval = null;
        }
    }
});

subtitles.addEventListener("mouseup", function() {
    if (isLoopMode) {
        var selection = window.getSelection();
        var selectedText = selection.toString().trim();

        // Find start and end time for selected text
        var startLoopTime = null;
        var endLoopTime = null;

        for (let i = 0; i < syncData.length; i++) {
            var currentCharacter = syncData[i].word;

            // If we find a match of the first character of the selected text
            if (currentCharacter === selectedText.charAt(0)) {
                var potentialMatch = '';
                var potentialStart = syncData[i].startTime;
                var potentialEnd = '';

                // Construct the potential match string
                for (var j = i; j < i + selectedText.length; j++) {
                    if (j < syncData.length) {
                        potentialMatch += syncData[j].word;
                        potentialEnd = syncData[j].endTime;
                    } else {
                        break;
                    }
                }

                // Check if we have a perfect match
                if (potentialMatch === selectedText) {
                    startLoopTime = potentialStart;
                    endLoopTime = potentialEnd;
                    break; // We've found our perfect match, no need to keep looping
                }
            }
        }

        // Loop the selected text
        if (startLoopTime !== null && endLoopTime !== null) {
            // If only one character is selected, extend start and end times by 0.1 seconds
            if (selectedText.length === 1) {
                startLoopTime = Math.max(0, parseFloat(startLoopTime) - 0.1);
                endLoopTime = parseFloat(endLoopTime) + 0.1;
            }

            audioPlayer.currentTime = parseFloat(startLoopTime);
            audioPlayer.playbackRate = audioSpeed;
            audioPlayer.play();

            if (loopingInterval) {
                clearInterval(loopingInterval);
            }

            loopingInterval = setInterval(function() {
                if (audioPlayer.currentTime >= parseFloat(endLoopTime)) {
                    audioPlayer.currentTime = parseFloat(startLoopTime);
                    audioPlayer.playbackRate = audioSpeed;
                    audioPlayer.play();
                }
            }, 100);
        }
    }


});
let saveProgressInterval;

// Set up interval to save progress every 5 seconds when the media is playing
audioPlayer.addEventListener('play', function () {
    saveProgressInterval = setInterval(saveProgress, 5000);
});

// Clear the interval when the media is paused or ended
audioPlayer.addEventListener('pause', function () {
    clearInterval(saveProgressInterval);
});
audioPlayer.addEventListener('ended', function () {
    clearInterval(saveProgressInterval);
});

function saveProgress() {
    const progress = audioPlayer.currentTime;
    
    fetch('/api/user/save-progress', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            mediaId: mediaId,
            progress: progress
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => console.log(data))
    .catch((error) => {
        console.error('Fetch error:', error);
    });
}


fetch('/api/user/viewed_media_list/read')
    .then(response => response.json())
    .then(data => {
        const container = document.getElementById('viewed-media-container');
        data.viewed_media.forEach(mediaId => {
            const span = document.createElement('span');
            span.textContent = "mediaId:"+mediaId;
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
    return response.json();
})
.then(data => {
    // Check if there's a MediaProgress object for the current media and user
    if (data && data.time_stopped != null) {
        // If so, set the currentTime of the audioPlayer to the last stopped time
        audioPlayer.currentTime = data.time_stopped;
    } else {
        // If not, the media should start playing from the beginning
        console.log("No progress found, starting from the beginning");
        audioPlayer.currentTime = 0;
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
   console.log(overlappingHighlight);

} else {
  console.log("No overlapping highlight found.");
}

if (overlappingHighlight) {
console.log("startindex of " + overlappingHighlight.start_index + " endindex " + overlappingHighlight.end_index + " highlight start "+start_char_index);
    console.log("fuck");
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