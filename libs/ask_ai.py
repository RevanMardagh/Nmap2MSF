# ai_overview.py
from google import genai
import json
import threading
import sys
import time
import os
from typing import Any, List


def normalize_ai_response(text: str) -> Any:
    """
    Convert `text` (possibly:
      - a raw JSON object text,
      - a JSON string containing an object (double-encoded),
      - or a code-fenced block around the JSON)
    into a Python object (dict/list).
    Raises json.JSONDecodeError if it can't parse.
    """
    # 1) strip possible fenced-code-blocks (``` or ```json)
    lines = text.splitlines()
    if lines and lines[0].lstrip().startswith("```"):
        # remove first fence
        lines = lines[1:]
        # if there's a closing fence at the end, remove it
        if lines and lines[-1].lstrip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)

    # 2) try to parse. If result is a str, it was double-encoded, so parse again.
    parsed = json.loads(text)            # may raise json.JSONDecodeError
    if isinstance(parsed, str):
        # second parse turns the inner JSON string into a Python object
        parsed = json.loads(parsed)     # may raise json.JSONDecodeError
    return parsed


def _bouncing_caps_frames(phrase: str) -> List[str]:
    """
    Build a list of frames where each frame is the phrase with one letter
    capitalized; it walks left-to-right then right-to-left (bounce).
    Non-letter characters are left as-is but count as positions (so the
    capital moves across spaces/punctuation too for consistent effect).
    Example (phrase="hi"): ['Hi', 'hI', 'Hi'] (bounce)
    """
    n = len(phrase)
    frames = []

    # forward pass (0 .. n-1)
    for i in range(n):
        chars = list(phrase)
        if chars[i].isalpha():
            chars[i] = chars[i].upper()
        frames.append("".join(chars))

    # backward pass (n-2 .. 1) to avoid repeating endpoints too quickly
    for i in range(n - 2, 0, -1):
        chars = list(phrase)
        if chars[i].isalpha():
            chars[i] = chars[i].upper()
        frames.append("".join(chars))

    # if phrase is very short, ensure at least one frame exists
    if not frames:
        frames = [phrase]

    return frames


def _pretty_spinner_worker(stop_event: threading.Event,
                          phrase: str = "Waiting for AI response",
                          min_width: int = 20,
                          fps: float = 12.0):
    """
    Animated console spinner that capitalizes one letter at a time in a bouncing motion.
    - phrase: base text to animate
    - fps: frames per second
    """
    # Build frames up front
    frames = _bouncing_caps_frames(phrase)
    frame_delay = 1.0 / fps

    # If terminal too small, fallback to simple spinner
    try:
        cols = os.get_terminal_size().columns
    except OSError:
        cols = 80

    use_simple = cols < max(min_width, len(phrase) + 8)

    simple_symbols = ["|", "/", "-", "\\"]
    simple_idx = 0
    frame_idx = 0

    try:
        while not stop_event.is_set():
            if use_simple:
                ch = simple_symbols[simple_idx % len(simple_symbols)]
                msg = f"Waiting for AI response {ch}"
                simple_idx += 1
            else:
                msg = frames[frame_idx % len(frames)]
                frame_idx += 1

            # Print on single line, padded to clear previous content
            padded = msg.ljust(cols - 1)[: cols - 1]
            sys.stdout.write("\r" + padded)
            sys.stdout.flush()
            time.sleep(frame_delay)
    finally:
        # clear the line on finish
        sys.stdout.write("\r" + " " * (cols - 1) + "\r")
        sys.stdout.flush()


def generate_ai_modules(services, api_key: str) -> Any:
    """
    Request Gemini for recommended Metasploit modules for `services`.
    While waiting for the network/API response, show a bouncing-capitals spinner.
    Returns the parsed Python object (dict) produced by normalize_ai_response.
    Raises exceptions from the API or JSON parsing to the caller.
    """
    prompt_template = """You are a cybersecurity assistant. I will provide a JSON array of service names running on a host. Return **JSON only** (no explanation, no extra text) that maps each service name to an array of recommended Metasploit auxiliary modules for enumerating that service.

    Rules:
    1. Output must be valid JSON and follow this schema:
       {
         "<service>": [
           {
             "module": "<metasploit module path>",
             "action": "run",
             "use_setg": <true|false>,
             "rhost_param": "<RHOSTS or RHOST>",
             "extra_options": { /* string keys and string values */ },
             "flag": "<safe|bruteforce|vuln>"
           },
           ...
         ],
         ...
       }
    2. Include at least one module per provided service if known; include multiple when appropriate.
    3. "use_setg" should be true for modules that accept global RHOSTS (so they can be used with `setg RHOSTS`) and false otherwise.
    4. Keep fields exact and types consistent (booleans for use_setg, objects for extra_options).
    5. Do not include comments, metadata, or any text outside the JSON.
    6. If you don't know modules for a service, dont write it in the response.
    7. If the module uses some kind of bruteforcing, set the flag to bruteforce.
    8. Assume seclists is installed, and set the wordlists using the correct path if the module requires one. Dont set wordlists that would take longer than 5 minutes
    9. Provide the keys in the order provided to you in the example. 
    10. If exists, provide vulnerability scanning modules 

    Generate results for these services: 
    """

    prompt = prompt_template + f"{services}"

    client = genai.Client(api_key=api_key)

    # prepare spinner
    stop_event = threading.Event()
    spinner_thread = threading.Thread(
        target=_pretty_spinner_worker,
        kwargs={
            "stop_event": stop_event,
            "phrase": "waiting for ai response...",
            "fps": 8.0,
        },
        daemon=True,
    )

    try:
        spinner_thread.start()
        # The blocking API call; spinner runs while this is in progress
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        # stop spinner before processing output
        stop_event.set()
        spinner_thread.join(timeout=1.0)

        # normalize & save
        text_obj = normalize_ai_response(response.text)

        # ensure database folder exists and write (relative path as in your original)
        out_dir = os.path.join("..", "database")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "ai_lookup.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(text_obj, f, indent=2, ensure_ascii=False)

        # Print a confirmation line (small, non-fancy)
        print(f"AI response saved to: {out_path}")

        return text_obj

    except Exception:
        # Make sure spinner is stopped on exceptions too
        stop_event.set()
        spinner_thread.join(timeout=1.0)
        raise


if __name__ == "__main__":
    services = ['netbios-ssn', 'microsoft-ds', 'telnet']

    # IMPORTANT: do not hardcode API keys in source committed to VCS.
    api_key = "AIzaSyBfIbqkLpHsxZdubj-_IVk-t2OOPKw47r4"

    ai_modules = generate_ai_modules(services, api_key=api_key)

    import pprint
    pprint.pprint(ai_modules)
