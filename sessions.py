import os
import datetime
import json


class SessionsManager:
    def __init__(self, **kwargs):
        self._sessions = {}
        self._memorytime = kwargs.get("memorytime", 60*10)
        self._storage = kwargs.get("storage", "sessions")
        if not os.path.exists(self._storage):
            os.makedirs(self._storage)

    def get_session(self, sid) -> dict:
        if sid in self._sessions:
            session = self._sessions[sid]
        else:
            file = os.path.join(self._storage, f"{sid}.json")
            if os.path.exists(file):
                with open(file, "r", encoding="utf8") as f:
                    data = json.load(f)
                session = {"data": data}
            else:
                session = {"data": {}}
            self._sessions[sid] = session
        session["time"] = datetime.datetime.now() + datetime.timedelta(seconds=self._memorytime)
        return session["data"]

    def update(self):
        curr_time = datetime.datetime.now()
        items = list(self._sessions.items())
        for sid, session in items:
            if curr_time < session["time"]:
                continue
            file = os.path.join(self._storage, f"{sid}.json")
            if os.path.exists(file):
                with open(file, "w", encoding="utf8") as f:
                    json.dump(session["data"], f)
            self._sessions[sid] = None
            del self._sessions[sid]

    def save_all(self, clear_cache=True):
        for sid, session in self._sessions.items():
            file = os.path.join(self._storage, f"{sid}.json")
            if os.path.exists(file):
                with open(file, "w", encoding="utf8") as f:
                    json.dump(session["data"], f)
        if clear_cache:
            self._sessions.clear()

# end of class
