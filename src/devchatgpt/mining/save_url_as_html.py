import requests
from bs4 import BeautifulSoup
import json

def scrape_chatgpt_conversations(url):
    # Send a GET request to the ChatGPT webpage
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract conversation elements (modify the selector based on the HTML structure)
    conversation_elements = soup.select('.conversation')

    # Extract conversation data from each conversation element
    conversations = []
    for conversation_element in conversation_elements:
        # Extract relevant data from the conversation element
        conversation_data = {
            'user': conversation_element.select_one('.user').get_text(),
            'message': conversation_element.select_one('.message').get_text()
        }
        conversations.append(conversation_data)

    return conversations

def save_to_json(conversations, filename):
    # Save conversation data to a JSON file
    with open(filename, 'w') as file:
        json.dump(conversations, file, indent=4)

if __name__ == '__main__':
    # URL of the ChatGPT webpage with conversations
    chatgpt_url = 'https://chat.openai.com/share/e875af6c-d468-4174-9740-0f869e229047'

    # Scrape conversations from the ChatGPT webpage
    conversations = scrape_chatgpt_conversations(chatgpt_url)

    # Save conversations to a JSON file
    save_to_json(conversations, 'chatgpt_conversations.json')
