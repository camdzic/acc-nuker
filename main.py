import requests
import time
import threading

user_token = "" # Put your user token here
author_id = ""  # Put your user ID here
channels_to_keep = [] # Put the channel IDs you want not to be deleted 
delete_delay = 5 # I recommend 5-10 seconds
fetch_delay = 0.1 # I recommend 0.1-0.5 seconds
max_threads = 5 # I recommend 3-5 threads

headers = {
    "Authorization": user_token,
}    

def get_dms():
    response = requests.get("https://discord.com/api/v10/users/@me/channels", headers=headers)
    data = response.json()
    return data

def get_messages(channel_id):
    last_message_id = None
    messages = []

    while True:
        response = requests.get(
            f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=100"
            f"{'' if last_message_id is None else f'&before={last_message_id}'}",
            headers=headers,
        )

        if response.ok:
            data = response.json()

            if not data:
                break

            messages.extend([
                message for message in data
                if message["author"]["id"] == author_id
                and message["type"] in [0, 19]
            ])

            last_message_id = data[-1]["id"]
        else:
            print(f"Failed to fetch messages for channel {channel_id}")
            break

        time.sleep(fetch_delay)

    return messages

def delete_message(message, channel):
    response = requests.delete(
        f"https://discord.com/api/v10/channels/{channel['id']}/messages/{message['id']}",
        headers=headers,
    )

    if not response.ok:
        print(
            f"Failed to delete message {message['id']} from channel {channel['id']}: {response.status_code}"
        )

    time.sleep(delete_delay)

def process_channels(channels):
    for channel in channels:
        print(f"Fetching messages for channel {channel['id']} ({channel.get('name', channel['recipients'][0]['username'])})")
        messages = get_messages(channel['id'])

        if messages:
            print(f"Deleting {len(messages)} messages in channel {channel['id']} ({channel.get('name', channel['recipients'][0]['username'])})...")
            for message in messages:
                delete_message(message, channel)

            print(f"Deleted {len(messages)} messages")
        else:
            print(f"No messages to delete in channel {channel['id']} ({channel.get('name', channel['recipients'][0]['username'])})")

def main():
    data = get_dms()
    print(f"Found {len(data)} channels")

    filtered_channels = [channel for channel in data if channel.get('id') not in channels_to_keep]

    print(f"Starting to delete {len(filtered_channels)} channels in {len(filtered_channels) / 3} threads")

    i = 0

    while i < len(filtered_channels):
        current_channels = filtered_channels[i:i+max_threads]

        threads = []
        for channel in current_channels:
            thread = threading.Thread(target=process_channels, args=([channel],))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        i += max_threads

if __name__ == "__main__":
    main()
