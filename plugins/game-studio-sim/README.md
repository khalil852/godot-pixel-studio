# game-studio-sim

A **crew protocol** for game projects, not an org chart.

Real studios run 30+ distinct roles, and one trivial feature — "we need doors" —
fans out to roughly thirty decision owners. That fan-out is the best documented
structural cause of shipped-game failure, and it is what this skill attacks: every
artifact has exactly one owner, and every owner has declared inputs.

## The crew

Four permanent roles plus a critic invoked at checkpoints:

| Role | Owns | Done when |
|---|---|---|
| **Director** | Vision one-pager, scope cap, milestone calls | vision fits one sentence; the cap has numbers |
| **Designer** | Mechanics spec, tuning table, level layouts | every player verb has input, feel, animation names |
| **Artist** | Art bible, asset manifest, assets | every asset has pixel size and anchor |
| **Engineer** | Gameplay code, scene wiring, build health | the project runs headless with zero errors |
| **Critic** *(on demand)* | Checkpoint verdicts, defect reports | every defect has a command and an observed result |

Small on purpose. Published multi-agent dev systems that scaled up their rosters hit
cascading hallucination and coordination loss; the ones that worked added
*structure*, not agents.

## The five checkpoints

```
1. BRIEF      Director  -> vision + scope cap
2. DESIGN     Designer  -> mechanics spec + tuning table
3. ART BIBLE  Artist    -> palette, resolution, asset manifest
4. SLICE      Engineer  -> smallest build that exercises the whole loop
5. CRITIQUE   Critic    -> defect report with commands and observed results
```

A checkpoint is frozen before the next phase starts. No role reads past a
checkpoint that has not passed.

## The rules that do the work

Each answers a specific documented failure mode — the references name the source.

1. **One owner per decision.** No owner stalls; two owners thrash.
2. **Structured artifacts, gates as prerequisites.** Free-form agent chat is where
   role flipping and repeated instructions come from.
3. **Freeze at checkpoints; changes cost something.** Any change names what it
   displaces.
4. **The critic returns a falsifiable defect, an explicit "no objection" with what
   was checked, or "not verified".** Never a bare "looks good" — agents are
   documented to agree too readily.
5. **Status must be earned, not reported.** A milestone claim cites the command run.
6. **Engine facts come from the engine**, never from memory.
7. **A vertical slice is frozen before content scales.**
8. **Check the scope cap before adding anything.**
9. **Verification of playability is not verification of code. Critiques execute.**

## References

- `references/roles.md` — the researched role table and how roles collapse as a team
  shrinks. Marks clearly which parts are sourced and which are synthesis.
- `references/prior-art.md` — what ChatDev, MetaGPT, AgentVerse, AutoGen, Generative
  Agents, GameGPT and FactorSmith actually got wrong, and the structural lessons.
- `references/failure-modes.md` — twelve documented real-project failures (Anthem,
  Andromeda, Fallout 76, Cyberpunk 2077, Daikatana, Star Citizen, No Man's Sky …),
  each mapped to the rule that prevents it.

## An honest note

No published multi-agent system simulates a full game studio; existing work is 5–8
pipeline agents for code generation. That means this fills a real gap **and** that
its role definitions are a starting protocol to be revised against what actually
happens — not a validated design.

## License

MIT.
