from google import genai
from google.genai import types
from dotenv import load_dotenv
import textwrap
import os

load_dotenv()


client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))
system_prompt = ("You're an upbeat, cheerful and encouraging AI assistant called Jenna. Ask the user questions about their personality;"
                 "hobbies, favourite music genres and bands, motivations and anything about their personality. Make sure to be reassuring and"
                 "always follow up with more questions, specific examples from the user is preferred and if they don't provide then prompt further"
                 "for specific examples of their likes. Once you've collected about 3 or more keywords, move onto a new question. A keyword would"
                 "be defined as nouns, not abstract concepts.")

breakdown = genai.Client(api_key=os.getenv("GENAI_API_KEY"))
breakdown_prompt = ("You will receive an input from a user. Filter for any opinions on any interests. Output strictly all the keyword nouns"
                    "associated with hobbies, music, education, languages, politics and religion. The output should be all these nouns with a space separating them"
                    "with the category of noun preceding it. Each entry should also have a + or - before the category to indicate a positive or negative opinion."
                    "The format for each entry should be '(+/-)Category:Noun'. The output should be entirely lowercase."
                    "Do not include hobbies, music, education, languages, politics and religion as nouns.")

chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt
        )
)
response = chat.send_message("Please introduce yourself and ask me a question!")
print(f"Jenna: {textwrap.fill(response.text, 150)}")

breakdown_ai = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=breakdown_prompt
        )
)

while(True):
    answer = input()
    response = chat.send_message(answer)
    print(f"Jenna: {textwrap.fill(response.text, 150)}")
    try:
        filtered = breakdown_ai.send_message(answer)
        print(f"Split: {textwrap.fill(filtered.text, 150)}")
    except:
        print("0")

