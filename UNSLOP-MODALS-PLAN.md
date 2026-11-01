# UNSLOP-MODALS-PLAN — Unslop (UI) pass on the site's modals

Status: IMPLEMENTED (Option A — Modal truth pass, unified label "Exp Pts"). Verified: npm test
(all 6 engine tests + 4 resolvePlayerMetadata subtests pass), npm run check-copy PASS,
npm run build OK, and the live Transfer Breakdown modal now shows 4.05 vs 3.06 with a
−0.99 pill, "Gameweek 10 · -0.99 Projected Points Gain", and a tradeoff rationale sentence.
Handover modal changes are code-verified only (needs a synced FPL squad to render in demo mode).

Scope: the four modals in `frontend/src/components/` — OnboardingModal, LiveTeamSyncModal,
MatchdayHandoverModal, TransferBreakdownModal — plus the copy engine that feeds the transfer
modals (`frontend/src/utils/transferRationaleEngine.js`).

---

## 1. What I checked

All four modals rendered live on the dev server (onboarding on first load, Team Settings via the
header, Transfer Recommendation via "See the reasoning", Matchday Checklist via "Lock lineup"),
screenshots judged by eye, plus a computed-style read straight from the DOM and a sign sweep of
the code (color, type, icons, spacing, copy, components, motion).

## 2. Verdict: LIGHT SLOP — polish mode

These modals are already heavily de-slopped (the repo's earlier de-slop passes did their job).
Tokenized colors only, generous even spacing, no emoji, no fake pulses, no gradient/glow anywhere.
**One real finding**, and it's a serious one: the numbers contradict themselves.

### Finding 1 (the real one) — the modals claim a gain the data doesn't support

Verified in the live DOM: the Transfer Recommendation modal shows Calafiori OUT at
**4.05 Exp Pts** and Pedro Porro IN at **3.06 Exp Pts**, yet the subtitle says
**"+4.80 Projected Points Gain"**, the bridge pill says **+4.80**, and the reasoning card says
*"Pedro Porro projects for 3.06 pts vs 4.05 pts for Calafiori (+4.80 pts uplift)"*.
3.06 − 4.05 is **−0.99**, not +4.80. The Matchday Checklist modal repeats the same +4.80.

In layman's terms: the app tells you to sell a player who scores 4 points and buy one who scores
3 — and calls that a +4.8 improvement. For a "smart squad planner" this is the AI-slop that
matters: text that states things the data says are false. One contradiction is all it takes for a
manager to stop trusting every number in the app.

Root cause (pinned to the line):

- `frontend/src/components/TacticalPitch.jsx:265-268` — `netGain` is first read from the
  backend's action-summary TEXT via `parseNetGain` (+4.80). Because that parse succeeds, the
  fallback that computes the gain from the very two players being displayed never runs.
  The two sources use different xP bases, so they disagree — and the UI prints both.
- Same file, line 267: `Math.max(0.1, …)` floors the gain at +0.1, so even when the consistent
  path DOES run, the UI can never show a downgrade — every swap is forced to look positive.
- Sibling path with the same flaw: `TacticalPitch.jsx:287-289` uses the same `parseNetGain`
  for the headline gain on the matchday screen.
- `frontend/src/utils/transferRationaleEngine.js:142-146,174` — the reasoning text prints
  "(… uplift), offering high clean sheet probability and solid baseline points" and
  "Frees up £0.6m extra bank funds **while improving starting output**" without ever checking
  whether the in-player actually outscores the out-player. The engine's own header promises
  "mathematically and contextually truthful" reports; Pillars 2 and 3 don't check.

### Finding 2 (minor) — two names for the same number

The expected-points label is `Exp Pts` in TransferBreakdownModal (lines 205, 244) and
MatchdayHandoverModal (198, 237), but `Projected Pts` for the same metric in the captain/vice
cards (handover lines 269, 280). Two labels for one metric on one screen. Worth unifying while
we're in the file — you caught a smaller inconsistency than this one in the splash.

### Finding 3 (minor, optional) — mild hype wording in the reasoning engine

`transferRationaleEngine.js:72` "unlocks easy structural pivots" ("unlocks" is on the unslop
hype list), `:120` "offer a decisive edge", `:177` "immediate points boost". Only visible in the
roll-FT / neutral paths. Plainer FPL wording would match the tone guide.

## 3. Verified NOT slop — don't chase these ghosts

- The "neon green border" both screenshot reads reported: FALSE. Computed style is
  `1px solid rgba(255,255,255,0.08)` with a plain dark elevation shadow. The vision model was
  misreading the FDR pill's orange and the emerald accents.
- FDR fixture pills (e.g. CHE (H) in rgb(230,81,0)) use the official FDR matrix colours —
  allowed by the design rules, paired with the FDR number.
- OUT/IN and "YOUR SQUAD DETAILS" uppercase letterform badges (no boxes, transparent, 10px/800,
  0.08em tracking) are the app's deliberate Direction J signature (index.css:7185, :576) — a
  brand choice, not slop.
- The CONNECTED emerald dot is static (index.css:3770) — no pulse on a status that isn't live.
- No hype words or exclamation marks in any of the four components (grep: zero hits).

## 4. Direction (taken from the product, not trends)

- Product: a matchday cockpit that tells the manager what to do with their 15 players.
- Character: decisive, data-backed, plain-spoken — a touchline coach reading numbers.
- World: matchday chalk-on-charcoal (Direction J "Matchday Radio Wire", already in place).
- Moments: the delta pill and the "why" card — the two places the plan makes its case.
- Signature: uppercase mono data eyebrows (EXP PTS, FDR) — already the app's identity.

## 5. Options

**Option A — Modal truth pass (RECOMMENDED).** Make the modals internally consistent:
1. `TacticalPitch.jsx`: when the parsed summary gain disagrees with the gain computed from the
   two displayed players beyond a tolerance (0.5), use the computed one; drop the `Math.max(0.1,…)`
   floor so a downgrade can show as one (styled like the existing down-delta treatment, e.g.
   "−1.0 pts"). Apply the same fix to the sibling headline path (:287-289).
2. `transferRationaleEngine.js`: when the in-player projects fewer points, rewrite the Pillar 2
   sentence as a tradeoff (clean-sheet/baseline upside) instead of "uplift"; fix "improving
   starting output" in Pillar 3 to match the real direction.
3. Unify the xp label to one name across both modals (pick: `Exp Pts`).
4. Plainer wording for :72/:120/:177.
Tests to run: `npm run check-copy`, `npm test` (transferRationaleEngine has a suite), `npm run
build`, then re-render the modal and re-read the DOM to confirm the numbers agree.

**Option B — Hide the lie only.** Keep everything, just suppress the "+4.80" when it contradicts
the displayed players. Less honest — the reasoning card would still say "uplift". Not recommended.

**Option C — Also chase the backend basis.** Option A plus finding out why the backend
action-summary says +4.80 when dynamicXp says −0.99. That's the model/predictions pipeline
(okf-discipline gates apply) — bigger scope; better as its own task after A lands.

## 6. Decisions

(To be filled by you — taste calls recorded here with reasoning.)
