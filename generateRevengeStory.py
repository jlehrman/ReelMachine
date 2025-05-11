import google.auth
from google import genai
from google.genai import types

def generate(prompt):
    # Load credentials with the proper scope
    credentials, project = google.auth.load_credentials_from_file(
        "./TTS_key.json",
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    
    client = genai.Client(
        vertexai=True,
        project=project,
        location="us-central1",
        credentials=credentials
    )
    
    si_text1 = """Please make a ~4000 character long story based on the prompt given. The story should be in first person about revenge. Before the story, there should be a quick sentence for the title that summarizes how someone wronged you and how they will regret it. For example, if the story was about an angry customer who threw a tantrum, the title could be: "Crazy Customer Tries to Ruin My Night but Ends Up Learning A Lesson". Next, the intro to the story should give background information about you that is relevant to the plot. The first word of the story should be "I" or "My". Then you should introduce the person in the story who somehow wrongs you. Then get into detail as to how they wronged you and finally get into how you finally decided to get revenge. If there are any companies in your story, do not give them a name, simply just refer to what they are."""
    
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)]
        )
    ]
    
    generate_content_config = types.GenerateContentConfig(
        temperature=0.8,
        top_p=0.8,
        max_output_tokens=2000,
        response_modalities=["TEXT"],
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF")
        ],
        system_instruction=[types.Part.from_text(text=si_text1)]
    )
    
    response_text = ""
    for chunk in client.models.generate_content_stream(
        model="gemini-2.0-flash-001",
        contents=contents,
        config=generate_content_config,
    ):
        response_text += chunk.text
        print(chunk.text, end="")  # Optionally print the streaming result

    # Split the response into lines; the first line is the title.
    lines = response_text.splitlines()
    if lines:
        title = lines[0]
        story = "\n".join(lines[1:])
    else:
        title = ""
        story = response_text

    # Write the title and story to separate files.
    with open("title.txt", "w", encoding="utf-8") as f_title:
        f_title.write(title)
    with open("story.txt", "w", encoding="utf-8") as f_story:
        f_story.write(story)

prompt = input("Story prompt for revenge story: ")
generate(prompt)