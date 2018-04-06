import json
import operator
import datetime
from functools import partial
from urllib.parse import parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
from html import unescape

try:
    with open("hidden.json") as f:
        HIDDEN = set(json.load(f))
except:
    HIDDEN = []

scores = {}

bytes = partial(bytes, encoding="utf8")


class KickerAPI(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/table":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(
                {k: v
                    for k, v in scores.items()
                    if k not in HIDDEN
                }
                # dict(scores)
            ).encode())
        elif self.path == "/logs.json":
            with open("scores.json", "r") as f:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                for line in f:
                    data = json.loads(line)
                    data.pop("date")
                    self.wfile.write(bytes(json.dumps(data)))
                    self.wfile.write(b"\n")
        elif self.path == "/logs.html":
            with open("scores.json", "r") as f:
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                for line in reversed(f.read().split("\n")):
                    if not line:
                        continue
                    data = json.loads(line)
                    self.wfile.write(
                        b",".join(map(bytes, data["winners"])) +
                        b" defeat " +
                        b",".join(map(bytes, data["losers"])) +
                        b"<br>"
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
    for player, change in elo(winners, losers).items():
        scores[player] = change + scores.get(player, 1000)
    if nowrite:
        return
    with open("scores.json", "a") as f:
        f.write(json.dumps({
            "date": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "winners": winners,
            "losers": losers,
        }))
        f.write("\n")

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
