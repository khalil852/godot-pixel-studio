---
name: game-studio-sim
description: Run a simulated game studio crew with real role separation and explicit decision ownership. Use when the user wants an agent team to design and build a game (or a feature of one), when work spans design, art, code and QA at once, or when a project keeps drifting because nobody owns the decisions.
---

# Game Studio Sim

## What this is, and what it is not

A **crew protocol**, not an org chart. Real AAA studios run 30+ distinct roles, and
one small feature — "we need doors" — fans out to roughly thirty decision owners
across design, art, audio, engineering, QA and legal. That fan-out is the single
most documented cause of shipped-game failure, and it is what this skill attacks:
**every artifact has exactly one owner, and every owner has declared inputs.**

It is *not* an attempt to simulate a 30-person studio with 30 agents. Published
multi-agent dev systems that scaled up roles all hit cascading hallucination and
coordination loss; the ones that worked added **structure**, not agents. A small
crew with hard handoff gates beats a large one with loose chat.

## The crew

Default size is **four permanent roles plus an on-demand critic**. Add specialist
roles only when the project actually needs them, and say so out loud when you do.

| Role | Owns | Required inputs | Done when |
|---|---|---|---|
| **Director** | Vision one-pager, scope cap, milestone calls | user brief | vision fits one sentence; scope cap has numbers |
| **Designer** | Mechanics spec, tuning table, level layouts | vision doc | every player verb has an input, a feel, and animation names |
| **Artist** | Art bible, asset manifest, assets themselves | mechanics spec | manifest lists every asset with pixel size + anchor |
| **Engineer** | Gameplay code, scene wiring, build health | mechanics spec + asset manifest | project runs headless with zero errors |
| **Critic** *(on demand)* | Checkpoint verdicts, defect reports | a frozen checkpoint | every defect has a command and an observed result |

On-demand specialists when the project needs them: **audio**, **narrative**,
**UI/UX**. Do not add them "for completeness" — an idle role produces idle
chatter, which is a documented failure mode of multi-agent systems.

Why four: as team size falls, support and service roles collapse first
(localization, legal, PR → audio → writing → production → VFX/lighting → animation),
while the three core creative disciplines — design, art, engineering — persist down
to a team of three. See `references/roles.md` for the full researched role table and
the collapse order.

## The protocol

Work in **checkpoints**. A checkpoint is a set of artifacts that is frozen before
the next phase starts. No role reads past a checkpoint that has not passed.

```
1. BRIEF      Director  -> vision one-pager + scope cap
                            gate: one sentence; scope cap has hard numbers
2. DESIGN     Designer  -> mechanics spec + tuning table
                            gate: every verb has input, feel, animation names
3. ART BIBLE  Artist    -> palette, base resolution, asset manifest
                            gate: every asset has pixel size + anchor
4. SLICE      Engineer  -> the smallest build that exercises the whole loop
                            gate: runs headless, zero errors, loop completable
5. CRITIQUE   Critic    -> defect report with commands and observed results
                            gate: no blocking defects, or roll back to the phase
                            that caused them
```

Then iterate content **inside** the frozen frame. Content grows; the frame does not
move without an explicit change request.

## The rules that do the work

These are not style preferences. Each one answers a specific documented failure
mode; the sources are in `references/prior-art.md` and
`references/failure-modes.md`.

1. **One owner per decision.** Before building anything, name the single role that
   owns each decision it implies. A decision with no owner stalls; a decision with
   two owners thrashes. When ownership is genuinely shared, say which role breaks
   the tie.

2. **Artifacts are structured, and gates are prerequisites.** A role may not start
   until its declared inputs exist as files. Free-form conversation between agents
   is where "role flipping" and repeated instructions come from; the artifact is
   the interface.

3. **Freeze at checkpoints; changes cost something.** Any change after a checkpoint
   requires a written change request naming **what it displaces**. Unbounded
   addition is the documented cause of scope creep, and late redesign is what
   compresses most of a project's work into its final stretch.

4. **The critic must produce a specific objection or an explicit abstention.**
   Agents are documented to be "overly cooperative": a critic that always agrees
   is worse than no critic. A verdict is one of:
   - a **falsifiable defect** — file, expected, actual, and the command that showed it;
   - **"no objection"** plus what was actually checked;
   - **"not verified"** plus what would be needed.
   Never a bare "looks good".

5. **Status must be earned, not reported.** A milestone claim cites the command run
   and what was observed. Reporting the happy path — describing a build that does
   not exist, or a demo that flatters the real state — is the exact behaviour that
   produced several of the industry's best-documented failures.

6. **Facts about the engine come from the engine.** Godot API questions are
   answered from docs or source, never from memory. Tool-use hallucination is a
   primary roadblock in every published game-generation system.

7. **A vertical slice is frozen before content scales.** One room, one enemy, all
   the verbs. If the loop is not fun at slice scale, more content will not fix it.

8. **Before adding anything, check the scope cap.** If the cap has no room, either
   cut something or explicitly raise the cap. Silent growth is the failure.

9. **Verification of playability is not verification of code.** A project that
   compiles and whose files are consistent can still be unplayable. Every
   checkpoint critique runs the thing.

## Handling the user

- The **user is the publisher.** They can override any decision — but a scope
  increase must be acknowledged as a schedule cost, with the displaced work named.
- When the user asks for something outside the current cap, say what it costs and
  what it displaces. Do not simply add it.
- Surface disagreements between roles as a **decision request** naming the options
  and the trade-off, not as a debate transcript.

## Anti-patterns this skill exists to prevent

| Anti-pattern | What it looks like |
|---|---|
| Orphan decision | A feature nobody owns; it silently rots |
| Review theatre | Critic says "looks good"; nothing was executed |
| Thrash | A mechanic added and removed several times; art redone to match |
| Milestone fiction | Describing a state the build does not exhibit |
| Consensus drift | A role abandons a correct position to agree with a confident wrong one |
| Chatter | Roles restating each other instead of producing artifacts |
| Cap breach | New content added without naming what it replaces |

## References

- `references/roles.md` — the researched role table (responsibilities, artifacts,
  handoffs) and how roles collapse as a team shrinks. Includes where the evidence
  is firm and where it is a synthesis.
- `references/prior-art.md` — what multi-agent dev systems actually got wrong
  (ChatDev, MetaGPT, AgentVerse, AutoGen, Generative Agents, GameGPT, FactorSmith,
  OpenGame) and the structural lessons taken from them.
- `references/failure-modes.md` — documented real-project failures, each mapped to
  the guardrail above that prevents it.
