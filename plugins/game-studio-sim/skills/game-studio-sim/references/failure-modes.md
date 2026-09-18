# Documented failure modes, and the guardrail for each

Each entry is a real, sourced project failure — not generic advice. The right-hand
column is the rule in `SKILL.md` that exists because of it.

## 1. No locked creative direction

**Anthem.** The project lead pitched it as "the future of storytelling", but
"according to Darrah, **no one at BioWare, including Hudson, had a firm idea of what
that meant**." The project also "did not have any strong ideas at the start of
Anthem's development cycle."

**Guardrail:** rule 1 (one owner per decision) and the BRIEF checkpoint gate — the
vision must fit one sentence before design starts. If nobody can write the sentence,
the direction is not locked and no downstream work is safe.

## 2. Features thrashing in and out

**Anthem.** The flying mechanic "had been added and removed several times over the
course of development", and was re-added specifically to make a six-week demo look
good for a visiting executive. That demo became the E3 2017 reveal — a **milestone
build that did not represent the real game state**.

**Guardrail:** rule 3 (freeze at checkpoints; changes cost something) and rule 5
(status must be earned). A demo that flatters the real state is the documented
predecessor of a public failure.

## 3. Direction churn cascading into other disciplines

**Anthem.** "the narrative shifts put further strain on the artists and level
designers to match with the story's direction" — and then reverted.

**Guardrail:** the ART BIBLE checkpoint's prerequisite gate. Art may not start from
an unlocked direction, because art is the most expensive thing to redo.

## 4. Tooling chosen by decree, not by fit

**Anthem / Mass Effect: Andromeda.** EA management "wanted all its studios using the
same technology"; Frostbite "was not originally designed for the purposes that the
team had in mind", forcing systems to be scrapped. Andromeda "required that BioWare
construct all systems, tools, and assets from scratch".

**Guardrail:** rule 2 (gates are prerequisites). Engine and tooling decisions are
artifacts owned by the Engineer at the SLICE checkpoint, and are frozen with it.

## 5. Redesign so late the schedule collapses

**Andromeda.** Planned "hundreds of explorable planets by using procedural
generation, but ultimately scrapped the idea", and "due in part to the decision to
abandon this concept so late in development… ended up **building most of the game
during the ensuing 18 months**."

**Guardrail:** rule 7 (freeze a vertical slice before scaling content). The slice is
where "does this loop work" is answered, precisely so the answer does not arrive
years late.

## 6. Leadership and ownership vacuum

**Andromeda.** "development was plagued by internal instability, with its lead
writer, senior editor, and other members of its leadership team all departing";
animation problems were "due in part to… an **understaffed development team**, and a
delayed production cycle."

**Fallout 76.** "reportedly subject to a troubled development, which included a
**restrictive crunch schedule.** It saw a **high turnover of staff, attributed to
both a lack of leadership and clarity about the game's design.**"

**Guardrail:** rule 1, and the crew table's *owner* column — every artifact has
exactly one role accountable for it. If a role is removed, its artifacts must be
explicitly reassigned, not orphaned.

## 7. Schedule decisions made without the team

**Cyberpunk 2077.** The final delay was "decided suddenly, with discussions
commencing a day before the initial announcement"; roughly "**ninety per cent were
not informed until the last minute**."

**Guardrail:** rule 9 (the user is the publisher — a scope increase must be
acknowledged as a schedule cost with displaced work named). Silent schedule changes
are the failure; surfaced trade-offs are not.

## 8. Scope creep

**Definition.** "continuous or uncontrolled growth in a project's scope… when the
scope of a project is not properly defined, documented, or controlled."

**Star Citizen.** Announced for 2014, "repeatedly delayed", ~US$900M raised by
Nov 2025, still no official release date.

**Guardrail:** the scope cap with hard numbers at the BRIEF checkpoint, and rule 8
(check the cap before adding; if it has no room, cut or explicitly raise it).

## 9. Promotion and engine churn instead of production

**Daikatana.** "underwent a troubled development that saw a change in its engine,
release date delays, and the departure of several staff members"; marketing focused
on the lead developer "something later regretted by several of its staff", drawing
him away from production. Shipped to negative reviews, ~40,351 copies sold.

**Guardrail:** rule 5 — the artifact is the status. Promotion of a person or vision
is not evidence that a milestone exists.

## 10. Rotating leadership and incompatible visions

**Development hell.** "A work may move between many sets of artistic leadership,
crews, scripts, game engines, or studios", because attached people "**find they have
conflicting interpretations of it or visions for it**."

**Final Fantasy XV.** Six years as a PS3 spin-off; the director was replaced, the
platform changed, and "**the story needed to be rewritten** and some scenes and
characters were repurposed or removed."

**Guardrail:** rule 1 (name the tie-breaker when ownership is shared) and rule 3
(changes are written, priced, and attributed). Conflicts that are never resolved
surface as churn.

## 11. Marketing that outruns the build

**No Man's Sky.** Launched "marred by the lack of several features that had been
reported to be in the game"; the studio "had failed to control hype" and went silent
post-launch, producing backlash. It "has been cited as an example of what to avoid
in video game marketing."

**Guardrail:** rule 5. A milestone claim cites the command run and the observed
result. Anything not observed is "not verified" (rule 4's third verdict).

## 12. Decision ownership is structurally ambiguous — by default

**The Door Problem.** One trivial feature touches roughly thirty owners across every
discipline, and concludes "SOMEONE has to solve The Door Problem, and that someone is
a designer." The industry itself confirms there is no standard: "the video game
industry **does not have a standard methodology**. Instead developers and publishers
have their own methods."

**Guardrail:** this is the reason the skill exists. Rule 1 is not a formality — it is
the answer to the single most documented structural cause of failure.

## Using this list

- **Before a checkpoint**, name the failure mode that checkpoint is defending
  against, and say what evidence would show it is happening.
- **When work is going badly**, the failure usually matches one of these twelve
  before it matches any technical cause. Ask which.
- **Do not treat this as a checklist to satisfy.** These are the ways projects die;
  citing the list is not evidence you are avoiding them. Running the build is.
