(async function(win, doc) {
  // JavaScript code
  restructureJson('/static/subplayer/test.json', '/static/subplayer/test2.json');
  let transcript, syncData5;

  try {
    const response = await fetch('/static/subplayer/test2.json');
    const data = await response.json();
    transcript = data.transcript;
    syncData5 = data.words;
  } catch (error) {
    console.error('Error:', error);
  }

  var syncData = syncData5;
  console.log(syncData.length);
  console.log(transcript[0]);
    


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

     
var framesArray = [];
var currentFrame = [];
var currentFrameCharCount = 0;

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
     
 var audioPlayer = doc.getElementById("audiofile");
  var subtitles = doc.getElementById("subtitles");
  var loopButton = doc.getElementById("loop-button");

     var currentSubtitleIndex = 0;
     var y=0;

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

audioPlayer.addEventListener("timeupdate", function(e) {
    // Check if the currentSubtitleIndex is still correct, update it if necessary
    const correctIndex = findSubtitleIndex(audioPlayer.currentTime);
    if(correctIndex !== -1 && correctIndex !== currentSubtitleIndex) {
        currentSubtitleIndex = correctIndex;
        createSubtitles();
    } 
    if(currentSubtitleIndex < framesArray.length) {
        let frame = framesArray[currentSubtitleIndex];
        let isFrameDone = true;
        
        for (let j = 0; j < frame.length; j++) {
            const item = frame[j];
            const sentenceElement = document.getElementById("s_" + currentSubtitleIndex + "" + j);
            
            if (audioPlayer.currentTime >= parseFloat(item.startTime) && audioPlayer.currentTime <= parseFloat(item.endTime)) {
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
        
        // Move to next frame
        if(isFrameDone) {
            currentSubtitleIndex++;
            // Clear and repopulate the subtitles with the next frame, only if not the last frame
            if(currentSubtitleIndex < framesArray.length) {
                createSubtitles();
            }
        }
    }
});








    // Variable to store the selected highlighted text
   var selectedText = "";
  var loopingInterval = null;
  var isLoopMode = false; // Initialize loop mode as false
  
  loopButton.addEventListener("click", function() {
    isLoopMode = !isLoopMode; // Toggle loop mode

    if (!isLoopMode && loopingInterval) {
      // Stop the current loop and let the audio play normally
      clearInterval(loopingInterval);
      loopingInterval = null;
      selectedText = "";
    }

    loopButton.textContent = isLoopMode ? "Loop Mode: ON" : "Loop Mode: OFF"; // Update button text based on loop mode status
  });

 subtitles.addEventListener("mouseup", function() {
    if (isLoopMode) {
        var selection = window.getSelection();
        selectedText = selection.toString().trim();
        
        // Find start and end time for selected text
        var startLoopTime = null;
        var endLoopTime = null;
        var selectedTextIndex = 0;

        for (var i = 0; i < syncData.length; i++) {
            var currentWord = syncData[i].word;
            var currentWordIndex = 0;

            while (currentWordIndex < currentWord.length && selectedTextIndex < selectedText.length) {
                if (currentWord[currentWordIndex] === selectedText[selectedTextIndex]) {
                    if (selectedTextIndex === 0) { // The start of selected text
                        startLoopTime = parseFloat(syncData[i].startTime);
                    }
                    if (selectedTextIndex === selectedText.length - 1) { // The end of selected text
                        endLoopTime = parseFloat(syncData[i].endTime);
                        break;
                    }
                    currentWordIndex++;
                    selectedTextIndex++;
                } else {
                    currentWordIndex = currentWord.length; // Skip this word as it's not part of the selected text
                }
            }

            if (endLoopTime !== null) {
                break;
            }
        }

        // Loop the selected text
        if (startLoopTime !== null && endLoopTime !== null) {
            audioPlayer.currentTime = startLoopTime;
            audioPlayer.play();

            if (loopingInterval) {
                clearInterval(loopingInterval);
            }

            loopingInterval = setInterval(function() {
                if (audioPlayer.currentTime >= endLoopTime) {
                    audioPlayer.currentTime = startLoopTime;
                }
            }, 100);
        }
    }
});
})(window, document);