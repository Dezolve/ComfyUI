import json
import os
import time
import uuid
import urllib.request


SERVER_ADDRESS = os.environ.get("COMFY_SERVER_ADDRESS", "127.0.0.1:8190")
CLIENT_ID = str(uuid.uuid4())


def queue_prompt(prompt, prompt_id):
    payload = {"prompt": prompt, "client_id": CLIENT_ID, "prompt_id": prompt_id}
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(f"http://{SERVER_ADDRESS}/prompt", data=data)
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read())


def get_history(prompt_id):
    with urllib.request.urlopen(f"http://{SERVER_ADDRESS}/history/{prompt_id}") as response:
        return json.loads(response.read())


def load_prompt():
    with open("Qwen-Image-Edit.simple.api.json", "r", encoding="utf-8") as handle:
        return json.load(handle)


def run_prompt(prompt):
    prompt_id = str(uuid.uuid4())
    queue_prompt(prompt, prompt_id)
    deadline = time.monotonic() + 1800
    while time.monotonic() < deadline:
        history = get_history(prompt_id).get(prompt_id)
        if history is not None:
            status = history.get("status", {})
            if status.get("status_str") == "error":
                messages = status.get("messages", [])
                raise SystemExit(f"Prompt {prompt_id} failed: {messages}")
            if history.get("outputs"):
                return prompt_id
        time.sleep(1)
    raise SystemExit(f"Timed out waiting for prompt {prompt_id}")


def main():
    prompt = load_prompt()
    prompt_id = run_prompt(prompt)
    history = get_history(prompt_id).get(prompt_id, {})
    outputs = history.get("outputs", {})
    saved = []
    for output in outputs.values():
        for image in output.get("images", []):
            saved.append(f"{image['type']}/{image['subfolder']}/{image['filename']}")

    if not saved:
        raise SystemExit(f"Prompt {prompt_id} completed but produced no saved images")

    print(prompt_id)
    for item in saved:
        print(item)


if __name__ == "__main__":
    main()