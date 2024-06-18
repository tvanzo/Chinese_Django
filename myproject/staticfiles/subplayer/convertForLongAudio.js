function restructureJson(inputFile, outputFile) {
            // Read the input JSON file
            fetch(inputFile)
                .then(response => response.json())
                .then(data => {
                    // Combine all the transcripts into one string
                    const transcripts = data.results.map(result => result.alternatives[0].transcript);
                    const combinedTranscript = transcripts.join(' ');

                    // Combine all the word objects into one array
                    const words = data.results.flatMap(result => result.alternatives[0].words);

                    // Restructure the JSON with one transcript and one array of words
                    const restructuredData = {
                        transcript: combinedTranscript,
                        words: words
                    };

                    // Save the restructured JSON file
                    const outputJson = JSON.stringify(restructuredData, null, 4);
                    const outputBlob = new Blob([outputJson], { type: 'application/json' });
                    const outputUrl = URL.createObjectURL(outputBlob);
                    const downloadLink = document.createElement('a');
                    downloadLink.href = outputUrl;
                    downloadLink.download = outputFile;
                    downloadLink.click();
                })
                .catch(error => console.error('Error:', error));
        }