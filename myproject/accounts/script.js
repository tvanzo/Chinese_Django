(async function(win, doc) {
    // JavaScript code
    var player; // global variable

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
        while (pattern.test(transcript[i])) {
            i++;
        }

        var punctuation = transcript[i + 1];
        while ((!isNaN(transcript[i]) || ["千", "万", "亿"].includes(transcript[i]) || ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "百", "千", "万", "亿", "两"].
            includes(syncData[counter].word)) && transcript[i] != word) {
            word = syncData[counter].word;

            if (["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "百", "千", "万", "亿", "两"].includes(syncData[counter].word) && (!isNaN(transcript[i]) || ["千", "万", "亿"].includes(transcript[i]))) {


                sentence += word;

                i++;
                counter++;
                word = syncData[counter].word;


            } else if (!isNaN(transcript[i]) || ["千", "万", "亿"].includes(transcript[i])) {
                i++;
            } else {
                word = syncData[counter].word;
                sentence += word;
                counter++;
                word = syncData[counter].word;
                punctuation = transcript[i + 1];

            }


        }

        if (["！", "，", "。"].includes(punctuation)) {
            sentence += word + "" + punctuation;
            endTime = syncData[counter - 1].endTime;
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

        else if (startTime === "" && i != 0) {
            startTime = syncData[counter - 1].startTime;
            sentence += word;
            counter++
        } else {
            sentence += word;
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
            // If adding this sentence exceeds 60 chars, start a new frame
            framesArray.push(currentFrame);
            currentFrame = [syncData2[i]];
            currentFrameCharCount = sentenceCharCount;
        }

        // If it's the last sentence, add it to the framesArray
        if (i === (syncData2.length - 1)) {
            framesArray.push(currentFrame);
        }
    }

    // On Document Ready
    win.onload = function() {
        var video = doc.getElementById("youtube-player");
        var loopButton = doc.getElementById("loop-button");
        var subtitlesDiv = doc.getElementById("subtitles");
        var isLooping = false;
        var loopingStart;
        var loopingEnd;

        loopButton.addEventListener('click', function() {
            isLooping = !isLooping;
            loopButton.textContent = isLooping ? 'Stop Looping' : 'Loop Mode';
        });

        function playVideoFrom(index) {
            video.seekTo(framesArray[index][0].startTime);
            subtitlesDiv.innerHTML = framesArray[index].map(subtitle => subtitle.sentence).join(" ");

            if (isLooping) {
                loopingStart = framesArray[index][0].startTime;
                loopingEnd = framesArray[index][framesArray[index].length - 1].endTime;
            }
        }

      var interval;

function updateSubtitles() {
    var currentTime = player.getCurrentTime();
    console.log(currentTime);
    if (isLooping && (currentTime < loopingStart || currentTime > loopingEnd)) {
        player.seekTo(loopingStart);
    } else {
        for (var i = 0; i < framesArray.length; i++) {
            var start = framesArray[i][0].startTime;
            var end = framesArray[i][framesArray[i].length - 1].endTime;

            if (currentTime >= start && currentTime <= end) {
                subtitlesDiv.innerHTML = framesArray[i].map(subtitle => subtitle.sentence).join(" ");
                break;
            }
        }
    }
}

function onPlayerStateChange(event) {
    if (event.data == YT.PlayerState.PLAYING) {
        interval = setInterval(updateSubtitles, 500);
    } else {
        clearInterval(interval);
    }
}

document.addEventListener('DOMContentLoaded', function () {
    window.onYouTubeIframeAPIReady = function() {
        player = new YT.Player('youtube-player', {
            events: {
                'onStateChange': onPlayerStateChange
            }
        });
    };
});




        // Start with the first frame
        playVideoFrom(0);
    }
})(window, document);