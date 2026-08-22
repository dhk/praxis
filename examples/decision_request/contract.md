# Example: an executive decision request

Run the design layer over `input.md` with the contract that describes
the situation it was actually written for:

```bash
python -m praxis design examples/decision_request/input.md \
  --set genre="decision request" --set medium=email \
  --set primary_reader="VP Engineering" --set authority=approves \
  --set intent=request --set stakes=high --set urgency=today \
  --set time_available=low --set sensitivity=high --set power_distance=upward \
  --out artifacts/decision-request.html
```

The draft is deliberately a realistic bad one — not badly written, but
badly *designed*. It buries the request, hedges the deadline out of
existence, and never says what it wants approved. Praxis should report
a `bluf` structure, flag the missing ask, deadline, owner, and
verification, and offer a real tension between decisiveness and the
upward relationship.

Contrast it with the same contract minus the stakes:

```bash
python -m praxis design examples/decision_request/input.md \
  --set intent=request --set stakes=low --out artifacts/low-stakes.html
```

Fewer gaps, and no variants offered — at low stakes with a simple ask,
alternatives would differ cosmetically rather than strategically. The
difference between the two runs is the layer's whole argument: the same
words are fit or unfit depending on the situation, and the situation is
the thing worth writing down.
