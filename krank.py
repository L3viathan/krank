import json
import shelve
import operator
import datetime
from urllib.parse import parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
from html import unescape

class KickerAPI(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/table":
            with shelve.open("elodata") as scores:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(
                    {k: v
                        for k, v in scores.items()
                    }
                    # dict(scores)
                ).encode())
        elif self.path == "/logs":
            with open("scores.log", "rb") as f:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(b"<br>".join(list(
                    bstr.split(b"- ")[1] for bstr in reversed(f.readlines())
                )[:5]))
        # elif self.path == "/bootstrap":
        #     load_data()
        #     self.send_response(200)
        #     self.send_header("Content-Type", "application/json")
        #     self.send_header("Access-Control-Allow-Origin", "*")
        #     self.end_headers()
        #     self.wfile.write(b"Success")
        elif self.path in ("/index.html", "/", "/style.css", "/app.js") or self.path.startswith("/avatars/"):
            if self.path == "/":
                self.path = "/index.html"
            elif self.path.startswith("/avatars/"):
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
        elo_kicker(*(self.post_data[key] for key in ("w1","w2","l1","l2")))
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


def elo(w1, w2, l1, l2, k=16):
    """
    Return the new ELO ranks.

    Given two winners and two losers, return the new elo scores in the same
    order.
    """
    winners = (w1+w2)/2
    losers = (l1+l2)/2

    R_w = 10**(winners/400)
    R_l = 10**(losers/400)

    E_w = R_w/(R_w+R_l)

    game_value = round(k*(1-E_w))
    return (
        w1+game_value,
        w2+game_value,
        l1-game_value,
        l2-game_value,
    )

def elo_kicker(w1, w2, l1, l2):
    """
    Given four users, mutate the global register of user scores.
    """
    with shelve.open("elodata") as scores:
        s1 = scores.get(w1, 1000)
        s2 = scores.get(w2, 1000)
        s3 = scores.get(l1, 1000)
        s4 = scores.get(l2, 1000)
        s1, s2, s3, s4 = elo(s1, s2, s3, s4)
        scores[w1] = s1
        scores[w2] = s2
        scores[l1] = s3
        scores[l2] = s4
    with open("scores.log", "a") as f:
        f.write(datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
        f.write(" - ")
        f.write(w1 + "+" + w2 + " defeat " + l1 + "+" + l2 + "\n")

def load_data():
    with open("kicker.txt") as f:
        for line in f:
            w, l = line.strip().split("-")
            w1, w2 = w.split("+")
            l1, l2 = l.split("+")
            elo_kicker(w1, w2, l1, l2)

def print_ranks():
    """Show a table of scores, sorted by rank."""
    with shelve.open("elodata") as scores:
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
    run(HTTPServer, KickerAPI)
