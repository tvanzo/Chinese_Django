import json

subtitles22 = [
    {
        "text": "2022年底前后我做过三个",
        "start": 0.0,
        "duration": 1.96
    },
    {
        "text": "对2023年投资市场有预测性的视频",
        "start": 1.96,
        "duration": 2.794
    },
    {
        "text": "然后评论区就收到了",
        "start": 4.754,
        "duration": 1.418
    },
    {
        "text": "很多不同的意见和问候",
        "start": 6.172,
        "duration": 1.669
    },
    {
        "text": "那我一直相信",
        "start": 8.8,
        "duration": 0.5
    },
    {
        "text": "只有通过时间和亲身经历",
        "start": 9.592,
        "duration": 1.919
    },
    {
        "text": "检验过的道理才有价值",
        "start": 11.511,
        "duration": 1.627
    },
    {
        "text": "现在是2023年年底",
        "start": 13.138,
        "duration": 1.877
    },
    {
        "text": "我就想做两件事",
        "start": 15.015,
        "duration": 1.292
    },
    {
        "text": "第一就是来验证一下",
        "start": 16.307,
        "duration": 1.293
    },
    {
        "text": "这一年来我的那些观点",
        "start": 17.6,
        "duration": 1.335
    },
    {
        "text": "是否能够hold得住",
        "start": 18.935,
        "duration": 1.251
    },
    {
        "text": "并结合我们的经历",
        "start": 20.186,
        "duration": 1.293
    },
    {
        "text": "来反思总结一下",
        "start": 21.479,
        "duration": 1.418
    },
    {
        "text": "2023年教给我们的",
        "start": 22.897,
        "duration": 2.127
    },
    {
        "text": "四个关于投资的重要课程",
        "start": 25.024,
        "duration": 2.211
    },
    {
        "text": "第二件事就是在我反思的过程中",
        "start": 27.235,
        "duration": 1.877
    }
]

# Initialize variables for transcript and words
transcript = ""
words = []

# Loop through each subtitle entry to create words and transcript
for subtitle in subtitles22:
    text = subtitle['text']
    start_time = subtitle['start']
    duration = subtitle['duration']
    
    # Calculate end time by adding duration to start time
    end_time = start_time + duration
    
    # Append the text to the transcript
    transcript += text

    # Split the text into words
    words_list = text.split()

    # Create word entries with start and end times
    for word in words_list:
        words.append({
            'startTime': f"{start_time:.3f}s",
            'endTime': f"{end_time:.3f}s",
            'word': word
        })

# Create the final JSON structure
output_data = {
    'transcript': transcript,
    'words': words
}

# Specify the file path where you want to save the JSON data
file_path = 'subtitles22.json'

# Convert to JSON and write to a file
with open(file_path, 'w', encoding='utf-8') as file:
    json.dump(output_data, file, ensure_ascii=False, indent=4)

print("Subtitles saved to subtitles22.json")
