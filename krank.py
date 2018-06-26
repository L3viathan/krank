import os
import json
import operator
import datetime
from functools import partial
from collections import Counter
from urllib.parse import parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
from html import unescape

try:
    with open("hidden.json") as f:
        HIDDEN = set(json.load(f))
except:
    HIDDEN = []

scores = {}

times_played = Counter()

bytes = partial(bytes, encoding="utf8")

LOGS = []

LIMIT = os.environ.get("LIMIT", 8)

playerhtml = "<span class=\"player\" title=\"{0}\" style=\"background-image: url(avatars/{0}.jpeg);\"></span>"

class KickerAPI(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/table"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(
                {k: v
                    for k, v in scores.items()
                    if k not in HIDDEN
                    and times_played[k] > 1
                    or self.path == "/table_{}".format(os.environ.get("KICKER_KEY", "secret"))
                }
            ).encode())
        elif self.path == "/logs.json":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            for data, _ in zip(reversed(LOGS), range(LIMIT)):
                data.pop("date", None)
                self.wfile.write(bytes(json.dumps(data)))
                self.wfile.write(b"\n")
        elif self.path == "/logs.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            for data, _ in zip(reversed(LOGS), range(LIMIT)):
                data.pop("date", None)
                self.wfile.write(
                    b"".join(map(lambda x: bytes(playerhtml.format(x)), data["winners"])) +
                    bytes(" ⚔️ ") +
                    b"".join(map(lambda x: bytes(playerhtml.format(x)), data["losers"])) +
                    bytes(" (±") + bytes(str(data["value"])) + b")" +
                    b"<br><br>"
                )
                self.wfile.write(b"\n")
        else:
            if self.path == "/":
                self.path = "/index.html"
            elif self.path in ("/index.html", "/", "/style.css", "/app.js") or self.path.startswith("/avatars/"):
                if self.path.count("/") > 2:
                    return
            try:
                with open("www" + self.path, "rb") as f:
                    content = f.read()
                    self.send_response(200)
                    self.send_header("Cache-Control", "max-age=1209600")
                    self.end_headers()
                    self.wfile.write(content)
            except FileNotFoundError:
                print("Missing file: ", self.path)
                self.send_response(404)
                self.end_headers()


    def do_POST(self):
        self.make_post_parameters()
        print("Got a POST request", self.post_data)
        elo_kicker(
            winners=self.post_data["winners"].split(","),
            losers=self.post_data["losers"].split(","),
        )
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def make_post_parameters(self):
        length = int(self.headers.get("Content-Length"))
        data = self.rfile.read(length)
        self.post_data = {
            key: (value[0] if value else None)
            for key, value in parse_qs(
                data.decode("utf-8")
            ).items()
        }


def elo(wins, loses, k=16):
    # Should return adjustments
    """
    Return the new ELO ranks.

    Given two winners and two losers, return the new elo scores in the same
    order.
    """

    winners = sum(scores.get(winner, 1000) for winner in wins) / len(wins)
    losers = sum(scores.get(loser, 1000) for loser in loses) / len(loses)

    R_w = 10**(winners/400)
    R_l = 10**(losers/400)

    E_w = R_w/(R_w+R_l)

    game_value = round(k*(1-E_w))
    data = {
        winner: game_value for winner in wins
    }
    data.update({
        loser: -game_value for loser in loses
    })
    return data

def elo_kicker(winners, losers, nowrite=False):
    """
    Given four users, mutate the global register of user scores.
    """
    game_value = None
    for player, change in elo(winners, losers).items():
        scores[player] = change + scores.get(player, 1000)
        game_value = abs(change)
        times_played[player] += 1
    game = {
        "date": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "winners": winners,
        "losers": losers,
    }
    LOGS.append({"value": game_value, **game})
    if nowrite:
        return
    with open("scores.json", "a") as f:
        f.write(json.dumps(game))
        f.write("\n")

    return game_value

def load_data():
    with open("scores.json") as f:
        for line in f:
            data = json.loads(line)
            elo_kicker(winners=data["winners"], losers=data["losers"], nowrite=True)

def print_ranks():
    """Show a table of scores, sorted by rank."""
    print("Name   | Score")
    print("--------------")
    for name, score in sorted(
            scores.items(),
            key=operator.itemgetter(1),
            reverse=True,
            ):
        print("{:<7}|{:<5}".format(name, score))

def run(server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
    server_address = ("", 5006)
    httpd = server_class(server_address, handler_class)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()

if __name__ == "__main__":
    load_data()
    run(HTTPServer, KickerAPI)
