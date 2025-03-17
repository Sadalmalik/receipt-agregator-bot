import requests

troot = ""


def _get_commands(message):
    commands = []
    text = message["text"]
    for entity in message["entities"] or []:
        if entity["type"] == "bot_command":
            commands.append(text[entity["offset"]:entity["offset"]+entity["length"]])
    return commands


class TBot:
    def __init__(self, token, **kwarg):
        self._token = token
        self._running = False
        self._update = kwarg.get("update", 0)
        self._timeout = kwarg.get("polling", 300)
        self._command_handlers = {}

    def _call(self, method, data=None):
        response = requests.post(f"https://api.telegram.org/bot{self._token}/{method}", data=data)
        return response.json()

    def command(self, command):
        def decorator(func):
            self._command_handlers[command] = func
        return decorator

    def run(self):
        data = self._call("getWebhookInfo")
        print(data)

        self._running = True
        while self._running:
            data = self._call("getUpdates", {
                "offset": self._update,
                "timeout": self._timeout
            })
            if data["ok"] and data["result"] and len(data["result"]) > 0:
                for update in data["result"]:
                    idx = update["update_id"]
                    message = update["message"]
                    if self._update <= idx:
                        self._update = idx + 1
                    print(f"\nmessage: {message}")
                    commands = _get_commands(message)
                    print(f"\ncommands: {commands}")

    def stop(self):
        if self._running:
            self._running = False
        else:
            raise ValueError("Can't stop bot - it's not running!")
