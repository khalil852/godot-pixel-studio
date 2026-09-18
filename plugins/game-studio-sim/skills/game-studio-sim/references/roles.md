# Roles: what studios actually have, and how they collapse

## The role table

Real roles, their responsibilities, the artifacts they produce, and who they hand
off to. This is the map the crew protocol is compressed from.

| Discipline | Titles | Responsibility | Artifacts | Hands off to |
|---|---|---|---|---|
| Creative direction | Creative Director / Game Director | Sets the vision; final arbiter of what the game is | Vision one-pager, greenlight calls, creative constraints | All discipline leads |
| Production | Producer / PM | "the top person in charge of overseeing development"; schedules and risk | Schedule, milestones, budget, status | Publisher, leads |
| Game design | Designer / Design Director | Concept, mechanics, rules, themes; iterates on feedback | Design doc, mechanics spec, tuning values | Engineering, level design, art, audio, QA |
| Systems design | Systems Designer | Economy, balance, progression maths | Balance tables, formulas | Engineering, live-ops |
| Level design | Level Designer | Builds locales/stages in an editor; places and gates content | Level blockouts, encounter placement | Environment art, gameplay/AI engineering, narrative, QA |
| Combat design | Combat Designer | Enemy behaviour, spawn logic, pacing | Encounter specs, spawn rules, AI requests | Gameplay/AI engineering, level design |
| UI/UX | UI Designer / UX Researcher | HUD, menus, objective markers; usability testing | UI specs, wireframes, usability findings | UI engineering, art, design |
| Narrative | Writer / Narrative Designer | Script and interactive narrative; often freelance | Script, dialogue, story bible, localisation strings | Design, audio, localisation |
| Monetisation | Monetisation Designer | Paywalls, pricing, funnels | Monetisation design, funnel specs | Live-ops, analytics, legal |
| Art direction | Art Director / Lead Artist | Cohesion; approves style; distributes art work | Style guide, art bible, approvals | Concept, 2D/3D artists, technical art, vendors |
| Concept art | Concept Artist / Storyboarder | Shapes "the look of the game" with designers | Concept paintings, sketches, storyboards | Art director, modellers, environment/character artists |
| Character art | Character Artist | Characters, props, weapons | Meshes/UVs/textures | Riggers, animators, VFX, lighting |
| Environment art | Environment Artist | Environments, terrain, buildings | Environment meshes, texture sets | Level design, lighting, technical art |
| Technical art | Technical Artist / Rigger / Shader Artist | **The bridge between art and programming**: tools, rigs, materials, optimisation, standards | Shaders, rigs, pipeline tools, performance budgets | Art workflow, engineering integration |
| VFX | VFX Artist | Particles, cached sims | Particle systems, sim caches | Technical art, gameplay engineering |
| Animation | Animator | "brings life to the characters, the environment, and anything that moves" | Animation clips, rigs, state machine handoff | Gameplay engineering, technical art |
| Lighting | Lighting Artist | Light dynamics, colour/brightness for mood | Lighting setups, lightmaps | Environment art, VFX, level design |
| Audio | Audio Director / Sound Designer / Composer | "specifying, acquiring and creating audio" | SFX, ambience, score, mix, implementation data | Audio programming, engineering, design |
| Engineering — engine | Engine Programmer | Engine core, physics, graphics integration | Engine systems, engine modifications | Graphics/gameplay/tools engineers |
| Engineering — graphics | Graphics Programmer | Renderers, shaders, GPU work; scarce and highly paid | Renderer, shaders, optimisations | Technical art, engine team |
| Engineering — gameplay | Gameplay Programmer / Scripter | Mechanics, logic, game feel | Gameplay systems, tuning hooks | Design, level design, QA, audio |
| Engineering — AI | AI Programmer | Pathfinding, enemy tactics; ~10–20% of programming staff in contemporary studios | AI/behaviour systems, navigation | Design, combat design, level design |
| Engineering — tools | Tools Programmer | Script compilation, art import, level and dialogue editors | Internal editors, exporters | Art, design, level design |
| Engineering — network | Network Programmer | Netcode, latency, reconnect; frequently pushed to the final months | Netcode, replication | Gameplay/engine, QA |
| Engineering — UI/audio/input/porting | UI / Sound / Input / Porting Programmer | UI framework; audio engine and designer-facing tools; input mapping; platform ports | UI framework, audio hooks, input configs, port builds | Design, sound design, platform holders |
| QA | QA Tester / QA Lead / Certification | Finds and documents defects before alpha, by tedious method | Bug reports, test plans, regression suites, cert checklists | Engineering, triage |
| Localisation | Localisation / LQA | Strings and localised-build testing | Localised strings, LQA reports | Writing, UI, engineering |
| Community / Live-ops | Community Manager / Live-ops Producer | Live service content stream; player comms | Patch notes, content calendar, telemetry postmortems | Production, design, engineering |
| Legal | Legal / Business Affairs | IP clearance; "removes the Starbucks logo from the door before you get sued" | Clearance, contracts, ratings | Art, publishing, production |

**The load-bearing fact.** A published cross-discipline write-up of a single trivial
feature ("The Door Problem", Liz England, 2014) shows one door touching creative
direction, production, design, concept art, art direction, environment art,
animation, sound design, audio engineering, composing, FX, writing, lighting, legal,
character art, six kinds of programmer, level design, UI, combat design, systems
design, monetisation, QA, UX, localisation, PR, community, support — and concludes
that "SOMEONE has to solve The Door Problem, and that someone is a designer."

That is why this skill's first rule is *one owner per decision*. Role fan-out is not
a staffing curiosity; it is where decisions go to die.

## How roles collapse

**Evidence grade: partly firm, partly synthesis.** No source states a canonical
collapse sequence with headcount thresholds. What *is* documented:

- Division of labour scales with complexity: "The desire for adding more depth and
  assets to games necessitated a division of labor. Initially, art production was
  relegated to full-time artists. Next game programming became a separate discipline
  from game design."
- Small studios use generalists: "Small gaming companies tend to not have as many
  artists… meaning that their artist must be skilled in several types of art
  development, whereas the larger the company… the roles each artist plays becomes
  more specialized."
- Producers can be absent entirely: "Some game developers may have no internal
  producers, however, and may rely solely on the publisher's producer."
- QA is typically absent in small studios: "Small developers do not generally have
  QA staff."
- Writing is external: "it is typically a freelance profession."
- Live-ops exists only for live-service games.

The order below is a **synthesis** from those anchors — treat the numbers as
illustrative, not measured:

```
~100+  near-full separation, including sub-specialists
~30-50 localisation, legal, PR -> outsourced
       audio -> one person or outsourced; composer contracted
       QA -> one embedded tester, or publisher QA
       character + environment + texture art -> generalist 3D artists
       writing -> freelance
       graphics+engine merge; AI folds into gameplay; network last (netcode is hard)
~10    QA, localisation, PR, community, legal -> gone
       audio, writing -> outsourced
       VFX, lighting, animation -> fold into the generalist artist pool
       production -> absorbed by the studio lead
       design sub-roles merge -> one or two generalist designers
       engineering -> 2-3 generalists (gameplay/systems, tools, tech art)
~3     design + production + narrative -> one designer/owner
       art + animation + VFX + UI -> one artist
       engineering + technical art + tools -> one programmer
~1     one generalist, leaning on engine, middleware, asset stores, outsourcing
```

**Merging heuristic (inference):** the more "support/service" and the less "core
creative loop" a role is, the sooner it disappears:
QA/localisation/legal/PR → audio → writing → production → VFX/lighting → animation
→ technical art → specialist design/art/engineering sub-roles → the three core
disciplines themselves.

Two documented exceptions worth knowing:

- A **producer** can survive at very small size, because the founder usually *is*
  one.
- **Technical art** is often the last art specialism kept, because it unblocks
  everyone else.

## Why the default crew is four

Applying the collapse order to an agent crew: at ~3–5 people the surviving shape is
one designer/owner, one artist, one engineer, plus support. The protocol therefore
defaults to **Director, Designer, Artist, Engineer**, with a **Critic** invoked at
checkpoints rather than kept permanently — because a permanently-idle role produces
idle chatter, which published multi-agent systems list as a failure mode, and
because a permanently-present reviewer is documented to go soft.

The gap this fills: no published multi-agent system models creative direction, art,
audio, QA or live-ops as first-class agents. Existing "game studio" work is 5–8
pipeline agents for code/content generation.

## A note on sourcing

Role definitions were read from Wikipedia content via a mirror (`wikipedia.org`
direct was unreachable from the research environment) and from Liz England's essay
directly. The Anthem / Mass Effect: Andromeda process-failure details come from that
mirror's summaries of Kotaku and Bloomberg reporting — the primary articles exist
but returned HTTP 403 to automated fetches, so those specific claims are
**secondary-sourced**. Where a claim is inference rather than a source statement, it
is labelled above.
