import random

_templates = {
    'DONT_KNOW': "I don't know you. Shush!",
    'DONT_UNDERSTAND': [
        "Excuse me?",
        "Sorry?",
        "Can you repeat?",
    ],
    'NO_CONTEXT': "No active context to quit.",
    'QUIT_CONTEXT': "Out of context: {}",
}

def get(key):
    value = _templates.get(key)
    if isinstance(value, list):
        return random.choice(value)
    return value
