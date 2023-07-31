     var currentSubtitleIndex = 0;
        var y=0;
        var framesArray = [];
var currentFrame = [];
var currentFrameCharCount = 0;
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
    console.log(currentSubtitleIndex);
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
    var currentTime = player.getCurrentTime();
    console.log("current time" + currentTime);
    var duration = player.getDuration();
    var progressText = formatTime(currentTime) + ' / ' + formatTime(duration);

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
            const item = frame[j];
            const sentenceElement = document.getElementById("s_" + currentSubtitleIndex + "" + j);

            if (currentTime >= parseFloat(item.startTime) && currentTime <= parseFloat(item.endTime)) {
                if (sentenceElement) {
                    sentenceElement.style.color = '#E4E4E4';
                    sentenceElement.style.fontWeight = 'bold';
                }
                isFrameDone = false;
            } else if (sentenceElement) {
                sentenceElement.style.color = '#595757';
                sentenceElement.style.fontWeight = 'normal';
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
        // Load the YouTube Iframe API
        var tag = document.createElement('script');
        tag.src = 'https://www.youtube.com/iframe_api';
        var firstScriptTag = document.getElementsByTagName('script')[0];
        firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

        // Create the YouTube player
        var player;
        function onYouTubeIframeAPIReady() {
            player = new YT.Player('player', {
                videoId: 'N8gSMCWMlDw',
                events: {
                    'onReady': onPlayerReady,
                    'onStateChange': onPlayerStateChange
                }
            });
        }







        // When the player is ready, start updating the progress
        function onPlayerReady(event) {
            setInterval(updateProgress, 1000); // Update every second
        }

        // Update the progress based on the current time of the video
       

        // Format the time in HH:MM:SS format
        function formatTime(time) {
            var hours = Math.floor(time / 3600);
            var minutes = Math.floor((time % 3600) / 60);
            var seconds = Math.floor(time % 60);

            var formattedTime = '';
            if (hours > 0) {
                formattedTime += hours + ':';
            }
            formattedTime += (minutes < 10 ? '0' : '') + minutes + ':';
            formattedTime += (seconds < 10 ? '0' : '') + seconds;

            return formattedTime;
        }

        // When the player state changes, update the progress (to handle video seek)
        function onPlayerStateChange(event) {
            if (event.data === YT.PlayerState.PLAYING) {
                updateProgress();
            }
        }























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

    console.log(syncData5);

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
    console.log(transcript[i] + "" + word);
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
     
  var subtitles = doc.getElementById("subtitles");
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
var audioSpeed = 1;

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
            player.setPlaybackRate(audioSpeed);
        } else if (e.keyCode === 40) { // 40 is the keyCode for 'Down' key
            // Decrease speed by 10%, with a minimum of 0.1x
            audioSpeed = Math.max(audioSpeed - 0.1, 0.1);
            player.setPlaybackRate(audioSpeed);
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
        player.setPlaybackRate(1);  // reset speed to normal

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

            player.seekTo(parseFloat(startLoopTime));
            player.setPlaybackRate(audioSpeed);
            player.playVideo();

            if (loopingInterval) {
                clearInterval(loopingInterval);
            }

            loopingInterval = setInterval(function() {
                if (player.getCurrentTime() >= parseFloat(endLoopTime)) {
                    player.seekTo(parseFloat(startLoopTime));
                    player.setPlaybackRate(audioSpeed);
                    player.playVideo();
                }
            }, 100);
        }
    }
});
    })(window, document);
