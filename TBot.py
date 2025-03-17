import re
import requests
import os


def _get_commands(message):
    commands = []
    if "text" in message and "entities" in message:
        text = message["text"]
        for entity in message["entities"]:
            if entity["type"] == "bot_command":
                args = re.split("/|[\r\n]+", text[entity["offset"] + entity["length"]:])[0].split(' ')
                args = [arg for arg in args if arg]
                command = {
                    "command": text[entity["offset"]:entity["offset"] + entity["length"]],
                    "args": args,
                    "entity": entity
                }
                commands.append(command)
    return commands


class TBot:
    def __init__(self, token, **kwarg):
        self._token = token
        self._running = False
        self._update = kwarg.get("update", 0)
        self._timeout = kwarg.get("polling", 300)
        self._download_path = kwarg.get("download_path", "downloads")
        self._command_handlers = {}
        self._photo_handler = None

    def _call(self, method, data=None):
        response = requests.post(f"https://api.telegram.org/bot{self._token}/{method}", data=data)
        return response.json()

    def _download_file(self, file):
        if "file_path" not in file:
            return None
        r = requests.get(f"https://api.telegram.org/file/bot{self._token}/{file["file_path"]}", allow_redirects=True)
        fpath = f"{self._download_path}/{file["file_path"]}"
        folder = os.path.dirname(fpath)
        if not os.path.exists(folder):
            os.makedirs(folder)
        with open(fpath, 'wb') as file:
            file.write(r.content)
        return fpath

    def _handle_photos(self, message):
        if "photo" not in message:
            return None
        files = {}
        for photo in message["photo"]:
            result = self._call("getFile", {"file_id": photo["file_id"]})
            if result["ok"]:
                file = result["result"]
                files[file["file_id"]] = file
        result = []
        for uid, file in files.items():
            file["local_path"] = self._download_file(file)
            result.append(file)
        return result

    def _handle_message(self, message):
        commands = _get_commands(message)
        photos = self._handle_photos(message)
        if self._photo_handler is not None and photos is not None:
            for file in photos:
                self._photo_handler(file, message)
        if len(self._command_handlers) > 0:
            for command in commands:
                if command["command"] in self._command_handlers:
                    self._command_handlers[command["command"]](command=command, message=message)
                else:
                    print(f"Unknown command:\n{command}\n")

    def on_command(self, command):
        def decorator(func):
            self._command_handlers[command] = func

        return decorator

    def on_photo(self, func):
        if self._photo_handler is not None:
            raise Exception("Photo handler already defined!")
        self._photo_handler = func

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
                    message = update["message"]
                    self._handle_message(message)
                    idx = update["update_id"]
                    if self._update <= idx:
                        self._update = idx + 1

        print("Bot polling complete")

    def stop(self):
        if self._running:
            self._running = False
        else:
            raise Exception("Can't stop bot - it's not running!")
