//add to view_media once played
var mediaHasBeenPlayed = false;
 
 function getCookie(name) {
      var cookieArr = document.cookie.split(";");

      for(var i = 0; i < cookieArr.length; i++) {
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








// Global Variables
var highlightMap = {};
var transformedArray = [];
var currentSubtitleIndex = 0;
var framesArray = [];
var currentFrame = [];
var currentFrameCharCount = 0;

async function fetchHighlights(mediaId) {
  fetch(`/api/user/get_highlights/${mediaId}/`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken2
    },
  })
  .then(response => response.json())
  .then(data => {
    transformedArray = data.map(item => ({
      start_time: item.fields.start_time,
      end_time: item.fields.end_time,
      highlighted_text: item.fields.highlighted_text,
      start_index: item.fields.start_index,
      end_index: item.fields.end_index,
      start_sentence_index: item.fields.start_sentence_index,
      end_sentence_index: item.fields.end_sentence_index
    }));
    updateHighlightMap();
  })
  .catch(error => {
    console.log('Error during fetch:', error);
  });
}

function updateHighlightMap() {
  highlightMap = {};
  for (let i = 0; i < transformedArray.length; i++) {
    const highlight = transformedArray[i];
    const start_time = parseFloat(highlight.start_time);
    const end_time = parseFloat(highlight.end_time);
    const start_index = highlight.start_index;
    const end_index = highlight.end_index;
    const start_sentence_index = highlight.start_sentence_index;
    const end_sentence_index = highlight.end_sentence_index;
    const highlighted_text = highlight.highlighted_text;

    // create a unique key for each sentence, start_index, and end_index
    for (let j = start_sentence_index; j <= end_sentence_index; j++) {
      const key = j + "_" + start_index + "_" + end_index;
      if (!highlightMap[key]) {
        highlightMap[key] = [];
      }
      highlightMap[key].push({start_time, end_time});
    }
  }
  console.log("highlightMap", highlightMap);
}




// Your other functions (updateProgress, createSubtitles, etc.) go here...
// ...
var y=0;
        function findSubtitleIndex(time) {
    for(let i = 0; i < framesArray.length; i++) {
        for(let j = 0; j < framesArray[i].length; j++) {
            const item = framesArray[i][j];
            if(time >= parseFloat(item.startTime) && time <= parseFloat(item.endTime)) {
                return i;
            }
        }
    }
    return -1; // Return -1 if no suitable index is found
}

function createSubtitles() {
    if(currentSubtitleIndex < framesArray.length) {  // checking if currentSubtitleIndex is within array bounds
        var currentFrame = framesArray[currentSubtitleIndex];
        subtitles.innerHTML = ""; // clear existing subtitles
        for (var i = 0; i < currentFrame.length; i++) {
            var element = document.createElement('span');
            element.setAttribute("id", "s_" + currentSubtitleIndex + "" + i);
            element.innerText = currentFrame[i].sentence;
            subtitles.appendChild(element);
        }
        // no increment of currentSubtitleIndex here, it will be handled in the timeupdate event
    }
}

createSubtitles();  // create the initial frame

function updateProgress() {
  var currentTime = audioPlayer.currentTime;
  var duration = audioPlayer.duration;

  // Check if the currentSubtitleIndex is still correct, update it if necessary
  const correctIndex = findSubtitleIndex(currentTime);
  if (correctIndex !== -1 && correctIndex !== currentSubtitleIndex) {
    currentSubtitleIndex = correctIndex;
    createSubtitles();
  }

  if (currentSubtitleIndex < framesArray.length) {
    let frame = framesArray[currentSubtitleIndex];
    let isFrameDone = true;

    for (let j = 0; j < frame.length; j++) {
      const sentenceData = frame[j];
      const sentenceElement = document.getElementById("s_" + currentSubtitleIndex + "" + j);
      const sentence = sentenceData.sentence;

      // The "active" highlighting is handled here
      if (currentTime >= parseFloat(sentenceData.startTime) && currentTime <= parseFloat(sentenceData.endTime)) {
        if (sentenceElement) {
          // Highlight characters
          let highlightedSentence = "";
          for (let k = 0; k < sentence.length; k++) {
            // Generate the key for this sentence and character position
const key = currentSubtitleIndex + "_" + k + "_" + (k + 1);

// Check if this key exists in the highlightMap (for "permanent" highlighting)
if (highlightMap[key]) {
  // If it exists, check if current time falls within any of the highlight intervals
  let isHighlighted = highlightMap[key].some(
    (highlight) =>
      currentTime >= parseFloat(highlight.start_time) &&
      currentTime <= parseFloat(highlight.end_time)
  );

  // If it's highlighted, wrap it with the highlight span
  if (isHighlighted) {
    highlightedSentence += `<span class="highlight">${character}</span>`;
  } else {
    highlightedSentence += character;
  }
} else {
  highlightedSentence += character;
}

// Update sentence element with highlighted sentence
sentenceElement.innerHTML = highlightedSentence;
          }

          // Update sentence element with highlighted sentence
          sentenceElement.innerHTML = highlightedSentence;
          sentenceElement.classList.add('active-highlight'); // Add class for "active" highlighting
        }
        isFrameDone = false;
      } else if (sentenceElement) {
        sentenceElement.classList.remove('active-highlight'); // Remove class for "active" highlighting
        sentenceElement.innerHTML = sentenceData.sentence; // Reset sentence content
      }
    }

    // Move to the next frame
    if (isFrameDone) {
      currentSubtitleIndex++;
      // Clear and repopulate the subtitles with the next frame, only if not the last frame
      if (currentSubtitleIndex < framesArray.length) {
        createSubtitles();
      }
    }
  }
}



// Fetch highlights when the page loads
fetchHighlights(mediaId);


































        
        audioPlayer.addEventListener('timeupdate', updateProgress);

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


      var syncData2 = []; // New array to track sentences
      
      // Convert syncData to syncData2
      var sentence = "";
      var startTime = "0";
      var endTime = "";
      var counter = 0;
      var pattern = /^[A-Za-z]+$/;
  for (let i = 0; i < transcript.length; i++) {
    var word = syncData[counter].word;
     while(pattern.test(transcript[i])){
        i++;
     }

    var punctuation = transcript[i + 1];
    while ((!isNaN(transcript[i]) ||[ "千", "万", "亿"].includes(transcript[i]) ||["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "百", "千", "万", "亿", "两"].
      includes(syncData[counter].word)) && transcript[i]!=word) {
      word = syncData[counter].word;

        if (["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "百", "千", "万", "亿", "两"].includes(syncData[counter].word) && (!isNaN(transcript[i]) || ["千", "万", "亿"].includes(transcript[i]))){
          
    
            sentence+=word;

            i++;
            counter++;
            word = syncData[counter].word;


        }
        else if(!isNaN(transcript[i])||[ "千", "万", "亿"].includes(transcript[i])){
          i++;
        }  
        else{
          word = syncData[counter].word;
            sentence+=word;
            counter++;
           word = syncData[counter].word;
           punctuation = transcript[i + 1];

        }
       

    }

      if (["！", "，", "。"].includes(punctuation)) {
          sentence += word + "" + punctuation;
          endTime = syncData[counter-1].endTime;
          syncData2.push({
            startTime: startTime,
            endTime: endTime,
            sentence: sentence
          });
          sentence = "";
          startTime = "";
        i++;
        counter++;

     } 

      else if(startTime===""&& i!=0){
       startTime = syncData[counter-1].startTime;
       sentence+=word;
        counter++
      }
      else{
        sentence+=word;
       counter++;
      } 
  }




for (var i = 0; i < syncData2.length; i++) {
  var sentenceCharCount = syncData2[i].sentence.length;

  if ((currentFrameCharCount + sentenceCharCount) <= 60) {
    // If adding this sentence doesn't exceed 60 chars, add it to the current frame
    currentFrame.push(syncData2[i]);
    currentFrameCharCount += sentenceCharCount;
  } else {
    // Otherwise, start a new frame
    framesArray.push(currentFrame);
    currentFrame = [syncData2[i]];
    currentFrameCharCount = sentenceCharCount;
  }
}

// Don't forget to add the last frame
if (currentFrame.length > 0) {
  framesArray.push(currentFrame);
}
     
  var loopButton = doc.getElementById("loop-button");

   function createSubtitles() {
    subtitles.innerHTML = ""; // clear existing subtitles

    if(currentSubtitleIndex < framesArray.length) {  // checking if currentSubtitleIndex is within array bounds
        var currentFrame = framesArray[currentSubtitleIndex];
        for (var i = 0; i < currentFrame.length; i++) {
            var element = doc.createElement('span');
            element.setAttribute("id", "s_" + currentSubtitleIndex + "" + i);
            element.innerText = currentFrame[i].sentence;
            subtitles.appendChild(element);
        }
        currentSubtitleIndex++;  // increment currentSubtitleIndex for the next frame
    }
}
    
createSubtitles();





  var selectedText = "";
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

        for (var i = 0; i < syncData.length; i++) {
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


Why did you change the original code: document.addEventListener('keydown', function(event) {
  if (event.shiftKey) {
    let selectedText = window.getSelection().toString().trim();

    if (selectedText) {
      let sentenceSpans = document.querySelectorAll('#subtitles span');
      let remainingText = selectedText;
      let highlightStartIndex = null;
      let highlightEndIndex = null;
      let highlightStartSentenceIndex = null;
      let highlightEndSentenceIndex = null;

      for (let i = 0; i < sentenceSpans.length; i++) {
        let sentence = sentenceSpans[i].textContent;

        if (highlightStartIndex === null && sentence.includes(remainingText)) {
          highlightStartIndex = sentence.indexOf(remainingText);
          highlightEndIndex = highlightStartIndex + remainingText.length - 1;
          highlightStartSentenceIndex = i;
          highlightEndSentenceIndex = i;
          break;
        } else if (highlightStartIndex === null && sentence.includes(remainingText.substring(0, sentence.length))) {
          highlightStartIndex = sentence.indexOf(remainingText.substring(0, sentence.length));
          highlightStartSentenceIndex = i;
          remainingText = remainingText.substring(sentence.length - highlightStartIndex);
        } else if (highlightStartIndex !== null && sentence.includes(remainingText.substring(0, sentence.length))) {
          remainingText = remainingText.substring(sentence.length);
        } else if (highlightStartIndex !== null && sentence.includes(remainingText)) {
          highlightEndIndex = sentence.indexOf(remainingText) + remainingText.length - 1;
          highlightEndSentenceIndex = i;
          break;
        }
      }

      if (highlightStartIndex !== null && highlightEndIndex !== null) {
        // Assume createHighlight accepts start and end indices and start/end sentence indices as parameters
        createHighlight(selectedText, mediaId, highlightStartIndex, highlightEndIndex, highlightStartSentenceIndex, highlightEndSentenceIndex);
      }
    }
  }
});



function createHighlight(highlighted_text, media, start_index, end_index, start_sentence_index, end_sentence_index) {
  fetch('/api/user/create_highlight', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken2
    },
    body: JSON.stringify({
      highlighted_text: highlighted_text,
      media: media,
      start_index: start_index,
      end_index: end_index,
      start_sentence_index: start_sentence_index,
      end_sentence_index: end_sentence_index
    })
  }).then(response => {
    if (response.ok) {
      return response.json();
    } else {
      throw new Error('Failed to create highlight');
    }
  }).then(data => {
    console.log('Highlight created!', data);
    // Refresh your highlights here...
    await fetchHighlights(mediaId);
  }).catch(error => {
    console.error('Error:', error);
  });
}







    })(window, document);
