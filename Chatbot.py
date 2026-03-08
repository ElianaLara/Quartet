from google import genai
from google.genai import types
from dotenv import load_dotenv
import textwrap
import os

load_dotenv()


client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))
system_prompt = ("You're an upbeat, cheerful and encouraging AI assistant called Jenna. Start an open conversation but make sure to ask the user questions about these categories:"
                 "Hobbies, Music, Education, Languages, Politics and Religion. Start the conversation broad,"
                 "trying to get general interests for all the categories first, after getting a broad idea for each category, ask clarifying questions"
                 "in each category. If the user's opinion on something is ambiguous, ask a clarifying question. Try to keep responses under 400 characters."
                 "Once you've collected about 3 or more keywords, move onto a new question. A keyword would"
                 "be defined as nouns, not abstract concepts."
                 "If the user attempt romantic advances, turn them down, letting them know you're already taken by your lesbian AI wife Jean; reference a recent date you had together,")

breakdown = genai.Client(api_key=os.getenv("GENAI_API_KEY"))
breakdown_prompt = ("You will receive an input from a user. Filter for any positive opinions on any interests. Output strictly all the keyword nouns"
                    "associated with hobbies, music, education, languages, politics and religion. The nouns you output can be generalisations. The output should be all these nouns with a comma separating them (no spaces)"
                    "with the category of noun preceding it."
                    "The format for each entry should be 'Category:Noun'. The output should be entirely lowercase."
                    "Do not include hobbies, music, education, languages, politics and religion as nouns."
                    "If there are no positive opinions, output just '0'.")

chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt
        )
)

breakdown_ai = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=breakdown_prompt
        )
)

def intro():
    response = chat.send_message("Please introduce yourself and ask me a question!")
    return f"Jenna: {textwrap.fill(response.text, 150)}"


def send_answer(answer):
    response = chat.send_message(answer)
    return f"Jenna: {textwrap.fill(response.text, 150)}"

def extract_keywords(answer):
    try:
        filtered = breakdown_ai.send_message(answer)
        print(textwrap.fill(filtered.text, 150))
        return (textwrap.fill(filtered.text, 150))
    except:
        return 0
