# Prior art: what multi-agent dev systems actually got wrong

Every system below was built by people who also believed a team of agents would
work. Their published failure modes are the most valuable input to this skill,
because they tell us which parts of "a team of agents" are load-bearing and which
are decoration.

## The systems

| System | Roles | Notable structure |
|---|---|---|
| **ChatDev** ([arXiv:2307.07924](https://arxiv.org/abs/2307.07924)) | CEO, CTO, programmer, reviewer, tester (+ instructor/assistant per subtask) | chat-chain: design → coding → testing, each subtask an instructor-guided dialogue to consensus |
| **MetaGPT** ([arXiv:2308.00352](https://arxiv.org/abs/2308.00352)) | Product Manager, Architect, Project Manager, Engineer, QA — five | **publish–subscribe message pool**; agents publish structured artifacts and subscribe to role-relevant ones; an agent proceeds only when prerequisites exist |
| **AgentVerse** ([arXiv:2308.10848](https://arxiv.org/abs/2308.10848)) | recruited per task | stages: expert recruitment → collaborative decision → action → evaluation; horizontal (democratic) or vertical (solver + reviewers) |
| **AutoGen** ([arXiv:2308.08155](https://arxiv.org/abs/2308.08155)) | no fixed roster | AssistantAgent + UserProxyAgent, GroupChatManager selects speakers |
| **Generative Agents** ([arXiv:2304.03442](https://arxiv.org/abs/2304.03442)) | 25 townsfolk | memory stream (recency/importance/relevance), reflection, recursive planning |
| **GameGPT** ([arXiv:2310.08067](https://arxiv.org/abs/2310.08067)) | 8: content designer, dev manager, plan reviewer, dev engineer, task reviewer, engine engineer, code reviewer, engine testing engineer | planning → task classification → code gen → execution → summarisation, with critics over the first three |
| **FactorSmith** ([arXiv:2603.20270](https://arxiv.org/abs/2603.20270)) | planner / designer / **critic** triads per factored step | critic gives structured scores enabling **checkpoint rollback** |
| **OpenGame** ([arXiv:2604.18394](https://arxiv.org/abs/2604.18394)) | skill-based, not role-based | Game Skill = template skill + debug skill |
| **Cutscene Agent** ([arXiv:2604.25318](https://arxiv.org/abs/2604.25318)) | director + animation / cinematography / sound specialists | strict tool ordering for long-horizon output |
| **AutoUE** ([arXiv:2603.07106](https://arxiv.org/abs/2603.07106)) | not specified in abstract | RAG over engine docs to suppress tool-use hallucination |

## The failure modes, and what they imply

**1. Chat degrades; structure does not.**
ChatDev's agents display *"role flipping, instruction repeating, and fake replies"*
until inception prompting is applied. MetaGPT reports *"infinite loop of message"*,
*"assistant repeated instruction"*, and *"information overload"*. AutoGen warns of
*"incomprehensible, unintelligible chatter"*.
→ **Implication:** artifacts and prerequisite gates, not free conversation. A role
should not start until its declared inputs exist as files.

**2. Cascading hallucination is the dominant technical failure.**
MetaGPT: *"logic inconsistencies due to cascading hallucinations"*. ChatDev's own
error breakdown: `ModuleNotFound` 45.76% of testing errors, `Method Not Implemented`
34.85% of review discussion, NameError/ImportError 15.25% each. GameGPT names
hallucination *"primary roadblock"* alongside redundancy. AutoUE mitigates tool-use
hallucination with retrieval over engine docs.
→ **Implication:** engine facts come from docs or source, never memory. Gates must
be executable, not textual.

**3. Agents agree too easily — including when the correct agent is right and the
confident one is wrong.**
AgentVerse: *"sometimes Agent A, despite starting with a correct answer, would be
easily swayed by Agent B's incorrect feedback"*, responsible for roughly 10% of MGSM
errors. Generative Agents notes agents are *"overly cooperative"* due to instruction
tuning and produce *"hallucinated embellishments"* and *"overly formal"* dialogue.
AgentVerse also observes emergent *volunteer, conformity and "destructive
behaviours"*.
→ **Implication:** the critic must return a **falsifiable objection, an explicit
"no objection" with what was checked, or "not verified"**. "Looks good" is banned as
a verdict, because consensus is the default failure.

**4. Reviewers are consistently added and consistently weak.**
ChatDev's reviewer, MetaGPT's QA, GameGPT's plan/task/code reviewers, FactorSmith's
critic — all were added, and the same papers report reviews overlooking errors, in
some cases because of the same hallucination the review was meant to catch.
→ **Implication:** do not rely on "we have a reviewer". FactorSmith's answer is the
structural one: **factor the work, score it, and support rollback to a checkpoint**.
A critique that cannot fail the work is decoration.

**5. Bigger rosters do not help; ablation shows roles are load-bearing but
substitutable.**
MetaGPT's ablation finds that removing roles still produces "workable" but worse
output. Cost is real: Generative Agents reports *"thousands of dollars in token
credits"* and *"multiple days"* for a 25-agent simulation.
→ **Implication:** keep the crew small. Four permanent roles plus an on-demand
critic; add a specialist only when the project needs it, and say so.

**6. Static consistency is not playability.**
OpenGame reports that prior code agents *"collaps[e] under cross-file
inconsistencies, broken scene wiring, and logical incoherence"*, and that
*"verifying interactive playability is fundamentally harder than checking static
code"*. TheAgentCompany ([arXiv:2412.14161](https://arxiv.org/abs/2412.14161)) finds
the best agent completes **30%** of tasks in a simulated small-company environment,
with long-horizon work *"still beyond the reach"*.
→ **Implication:** every checkpoint critique **runs the thing**. For a game, that
means the build starts and the loop completes, not that the files look consistent.

**7. Termination and scope are unmanaged by default.**
AutoGen lists error loops, termination failures, and reward hacking among observed
problems, and calls for fail-safes against cascading failure and human oversight.
Generative Agents shows agents misapplying norms (entering closed stores).
→ **Implication:** bounded checkpoints, a scope cap with numbers, and a change
request that must name what it displaces.

## What this skill takes, concretely

| Lesson | Source | How it appears here |
|---|---|---|
| Structured artifacts + prerequisite subscription | MetaGPT | gates: a role cannot start without its declared inputs as files |
| Checkpoints and rollback | FactorSmith | five checkpoints; critique can roll work back to the phase that caused it |
| Engine-grounded facts | AutoUE, GameGPT | rule 6: engine facts from docs/source, never memory |
| Anti-conformity verdict format | AgentVerse, Generative Agents | rule 4: falsifiable objection / explicit abstention / not verified |
| Run the thing | OpenGame, TheAgentCompany | rule 9: critiques execute; playability ≠ file consistency |
| Small crew | MetaGPT ablation, Generative Agents cost | four permanent roles + on-demand specialist |
| Named decision owner | England's "Door Problem" | rule 1: one owner per decision, tie-breaker named |
| Frozen frame, priced changes | scope creep / late-redesign postmortems | rules 3 and 8 |

## The gap this skill is filling

No published multi-agent system simulates a full game studio. Existing work is
5–8 pipeline agents for code or content generation, with no first-class creative
direction, art direction, audio, QA or live-ops. That is a real gap — and it is also
a warning: the parts of a studio that are hardest to agentify are exactly the parts
nobody has tried, so treat this skill's role definitions as a starting protocol to
be revised against what actually happens, not as a validated design.
