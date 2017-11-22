# krank - Kicker Rank

ELO based ranking scheme for solute-kicker.

## Interface

Web interface based on [vanilla.js](http://vanilla-js.com/), and the Python standard library. Hosted (for now) on kicker.ding.si via an nginx reverse proxy.

## Algorithm

When players A and B (with ranks a and b) win against C and D (with ranks c and d), then the resulting ranks are:

a' = a + elo_diff((a+b)/2, (c+d)/2)
b' = b + elo_diff((a+b)/2, (c+d)/2)
c' = c - elo_diff((a+b)/2, (c+d)/2)
d' = d - elo_diff((a+b)/2, (c+d)/2)

k is 16.
