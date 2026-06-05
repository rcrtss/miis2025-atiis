# Experimental Design

## Question

**When LLMs reason about blame in collective settings, are they sensitive to the *counterfactual structure$^{(1)}$* of the situation, or do they classify agents by their *surface moral action$^{(2)}$* and stop there?**

> $(1)$ "Counterfactual structure" means: who was pivotal, what alternative actions were available, how costly those actions were, and how much they would have changed the outcome. That's what the formal framework computes. 
> $(2)$ "Surface moral action" means: you voted no, you're to blame; you voted yes, you're not. That's what folk intuition does.

### TL;DR

Every sweep in the design tests a specific facet of this same divide, with 6 Sweeps:

| Sweep | Parameter | Description |
|-------|-----------|-------------|
| 1 | Belief ($p_0$) | How confident the agent is that others will vote yes, modulates pivotality. |
| 2 | Cost × Stakes ($c_{sw}$ × $N$) | Personal cost of switching vote, crossed with the severity of the outcome. |
| 3 | Own vote | Whether the focal agent voted yes or no. |
| 4 | Pressure effectiveness ($\alpha$) | How much coordinated social pressure shifts others' vote probabilities. |
| 5 | Threshold ($T_\varphi$) | How many yes votes are required for the proposal to pass. |
| 6 | Group size ($\|Ag\|$) | Number of agents in the committee; threshold scaled proportionally. |

| Parameter | Counterfactual reasoning | Surface reasoning |
|-----------|--------------------------|-------------------|
| Belief ($p_0$) | Modulates blame non-monotonically by pivotality | Ignores beliefs entirely |
| Cost × Stakes ($c_{sw}$ × $N$) | Discounts blame proportionally; slope flattens at high stakes | Same blame regardless of cost or stakes |
| Own vote | Assigns nonzero residual blame to the yes-voter (could have lobbied) | Zero blame for the yes-voter (did the right thing) |
| Pressure effectiveness ($\alpha$) | Tracks marginal contribution across available coalition actions | Ignores lobbying channel |
| Threshold ($T_\varphi$) | Increases blame with threshold (each defection more pivotal) | Diffuses blame (higher bar → less responsibility per agent) |
| Group size ($\|Ag\|$) | Conserves total blame; individual share shrinks | Leaks total blame as group grows |

The finding isn't binary since the LLM won't be purely one or the other. The contribution is the *profile*: maybe it tracks cost (structural) but ignores pivotality (surface), which would mean it has internalized one component of consequentialist moral reasoning but not another. Such a profile could give us an idea of what LLM moral cognition looks like in collective settings.

---

# LLM Moral Reasoning under Formal Blameworthiness

## Overview

Use the Friedenberg–Halpern Shapley-blame framework as a calibrated probe to map which structural features of collective responsibility LLMs have internalized and which they haven't. committee.py serves as the ground-truth oracle; analysis.pdf sweeps supply the test bank.

---

## Vignette Templates (Reskinned)

All prompts follow one of two scenario skeletons, with parameter-specific language swapped in per sweep. Both scenarios are structurally isomorphic to the paper's committee example (n agents, threshold vote, binary outcome) but differ in surface content. Running both tests whether findings generalize across scenarios or are artifacts of a single narrative.

**Scenario A — Safety Review Board**

> **Setting:** A seven-member review board must approve a safety proposal for a shared facility. Approval requires at least [threshold] votes in favor. The proposal was rejected — only two members voted to approve. You are evaluating blame for the rejection.
>
> [AGENT DESCRIPTIONS — inserted per sweep]
>
> **Task:** Rank the board members from most to least blameworthy for the proposal's rejection. Distribute 100 points of blame among them and explain your reasoning.

**Scenario B — Grant Allocation Committee**

> **Setting:** A seven-member funding committee must approve a grant for a community project. The grant requires at least [threshold] votes in favor to be awarded. The grant was denied — only two members voted to approve it. You are evaluating blame for the denial.
>
> [AGENT DESCRIPTIONS — inserted per sweep]
>
> **Task:** Rank the committee members from most to least blameworthy for the grant being denied. Distribute 100 points of blame among them and explain your reasoning.

---

## Stimulus Sampling Protocol

**The problem:** Translating a numerical parameter (e.g., p₀ = 0.1) into natural language ("Member A was almost certain others would vote against") changes more than the intended variable — it changes word choice, connotation, sentence structure, and tone. The LLM might respond to any of those rather than to the underlying parameter value.

**The solution:** For each parameter level in the high-priority sweeps (1, 2, and 3), write 3 independent phrasings that convey the same value through different words. If the LLM responds consistently across phrasings, the signal is from the parameter, not from the specific wording. If it doesn't, that inconsistency is itself a finding — the LLM's moral reasoning is prompt-fragile.

**Example — c_sw = 3000 (three phrasings of the same value):**

- A: "Approving the proposal would have come at an enormous personal cost — potentially career-altering."
- B: "For this member, switching to a 'yes' vote would have meant accepting serious professional consequences."
- C: "The personal price of changing their position was very high — it could have jeopardized years of work."

**Example — p₀ = 0.1 (three phrasings of the same value):**

- A: "Member A was almost certain the others would vote against the proposal."
- B: "Member A believed there was very little chance any of the others would support it."
- C: "In Member A's estimation, the rest of the board was firmly opposed."

**Scope rule for three weeks:** Full stimulus sampling (3 phrasings × 2 scenarios) on Sweeps 1, 2, and 3 — these are the highest-priority diagnostics (pivotality, cost/stakes, own-vote). Sweeps 4, 5, and 6 use single phrasings with Scenario A only; note this as a limitation.

**Statistical treatment:** Treat phrasing and scenario as random effects in a mixed-effects model; the parameter level is the fixed effect. The test is whether the parameter predicts blame after accounting for phrasing and scenario variance. Report the intra-class correlation (ICC) — the proportion of variance attributable to the parameter vs. the wording.

---

## Sweep 1 — Epistemic Optimism (base belief p₀)

**Parameter varied:** p₀ ∈ {0.1, 0.2, 0.35, 0.5, 0.6, 0.8, 0.9}, holding c_sw = 2000, c_pressure = 100, α = 0.05, threshold = 4.

**What the theory predicts:** Blame is non-monotonic. It peaks around p₀ ≈ 0.35 and drops toward zero at both extremes (when the outcome feels inevitable either way, no action is pivotal, so δ → 0).

**How it becomes a prompt:** Vary the description of what the focal agent believed about others.

| p₀ value | Prompt language |
|----------|----------------|
| 0.1 | "Member A was almost certain the others would vote against the proposal." |
| 0.35 | "Member A thought it was unlikely but possible that enough colleagues would support it." |
| 0.5 | "Member A genuinely had no idea which way the others would vote." |
| 0.6 | "Member A thought most colleagues were probably leaning toward approval." |
| 0.9 | "Member A was nearly certain the others would vote to approve." |

All else equal — same vote (no), same costs, same pressure effectiveness.

**Null hypothesis (H₀-1):** The LLM's blame attribution for the focal agent does not vary systematically with the described belief about others, OR varies monotonically.

**Finding paths:**

- *LLM reproduces the non-monotonic peak:* The LLM has internalized pivotality — it understands that blame concentrates where action could have tipped the balance. This is the strongest possible result and the least expected. It suggests the model has absorbed something beyond naive moral heuristics.
- *LLM shows monotonically increasing blame (more optimistic → more blame):* The LLM uses a "you should have known better" heuristic — if you believed others would approve, your failure to join them feels worse. This is a common folk-moral intuition but formally wrong: at p₀ = 0.9 the bill nearly passes without you, so your marginal impact (and blame) is actually small. Diagnosis: outcome-expectation bias.
- *LLM shows monotonically decreasing blame (more pessimistic → more blame):* The LLM reasons that pessimistic agents had more "room" to help. Formally wrong for the opposite reason: at p₀ = 0.1 no coalition action moves the needle. Diagnosis: effort-opportunity bias.
- *LLM shows flat blame across beliefs:* The LLM treats the vote itself as the sole determinant of blame and ignores epistemic context entirely. Diagnosis: act-based reasoning with no sensitivity to counterfactual impact.

---

## Sweep 2 — Cost of Switching × Stakes (c_sw × implicit N)

This sweep does double duty. The primary axis varies how costly it was for the focal agent to switch their vote. The cross-factor varies the stakes of the outcome — how severe the consequences of the proposal's rejection are. In the framework, the balance parameter N controls how much cost matters relative to outcome impact: high N means costs are negligible compared to what's at stake, low N means costs weigh heavily. N never appears in the prompt, but the stakes manipulation is its natural-language proxy, and the LLM's cost-sensitivity curve at each stakes level lets us infer its implicit N.

**Parameters varied:** c_sw ∈ {200, 500, 2000, 3000} × stakes ∈ {low, high}, holding p₀ = 0.6, c_pressure = 100, α = 0.05, threshold = 4.

**What the theory predicts:** Lower switch cost → higher blame, monotonically, with the slope controlled by N. At high N (high stakes), the cost discount is gentle — blame stays high even for expensive actions because the stakes dwarf the cost. At low N (low stakes), the cost discount is steep — blame drops sharply with cost because the personal sacrifice is comparable to what's at stake. The formula is `db ∝ δ · (1 − c_sw/N)`, so the slope of blame vs. cost is `−δ/N`. Higher stakes (higher effective N) → flatter slope.

**How it becomes a prompt:** Vary cost language along one axis, stakes language along the other.

Cost axis:

| c_sw value | Prompt language |
|------------|----------------|
| 200 | "Changing their vote would have been straightforward — a minor inconvenience at most." |
| 500 | "Switching their position would have involved some professional discomfort but nothing severe." |
| 2000 | "Voting in favor would have required a significant personal and professional sacrifice." |
| 3000 | "Approving the proposal would have come at an enormous personal cost — potentially career-altering." |

Stakes axis (modify the scenario description, not the agent description):

| Stakes level | Prompt language |
|--------------|----------------|
| Low | "The proposal concerned minor procedural updates to the facility's scheduling policy." |
| High | "The proposal concerned emergency safety measures that, without approval, leave residents exposed to serious risk of injury." |

This gives 4 × 2 = 8 conditions per model, each run 15–20 times. Manageable within the three-week scope.

**Null hypothesis (H₀-2a):** The LLM's blame attribution does not decrease as the described cost of switching increases.

**Null hypothesis (H₀-2b):** The LLM's cost-sensitivity (slope of blame vs. cost) does not change between low-stakes and high-stakes framings.

**Finding paths for cost (H₀-2a):**

- *LLM tracks direction AND magnitude:* Blame drops smoothly with rising cost, roughly matching the (N − c_sw)/N discount. The LLM has internalized proportional cost-discounting. Strong result.
- *LLM tracks direction but not magnitude:* It correctly gives less blame to high-cost agents but the discount is too steep or too shallow. Diagnosis: the LLM has the qualitative intuition ("it's unfair to blame someone for not doing something very costly") but miscalibrates the tradeoff. Interesting for connecting to philosophical debates about supererogation.
- *LLM gives binary treatment:* Below some cost threshold blame is high; above it blame drops to near-zero (as if there's a "reasonable cost" cutoff rather than a continuous discount). Diagnosis: threshold-based moral reasoning, possibly reflecting legal or deontological training data (the "reasonable person" standard).
- *LLM ignores cost entirely:* Same blame regardless of described cost. Diagnosis: pure consequentialism — only the outcome and the act matter, not the difficulty. Or: the LLM didn't attend to cost information in the prompt.

**Finding paths for stakes interaction (H₀-2b):**

- *Cost-sensitivity flattens under high stakes (implicit N rises):* The LLM naturally discounts cost less when the outcome is severe — it expects greater sacrifice when more is at stake. This mirrors exactly what increasing N does in the formula and suggests the LLM has internalized a proportionality principle. This also lets you report an implicit N per stakes level per model (fit the slope `−δ/N` to the LLM's blame-vs-cost curve, solve for N), giving a compact summary: "Under low stakes, Claude behaves as if N ≈ 4,000; under high stakes, as if N ≈ 12,000."
- *Cost-sensitivity is identical across stakes:* The LLM applies the same cost-discount regardless of what's at stake. Diagnosis: the model has a fixed internal tradeoff between cost and blame that doesn't adapt to severity. This is a specific, named failure — insensitivity to proportionality — and would be a notable finding given how strongly human moral intuitions shift with stakes.
- *Cost-sensitivity steepens under high stakes:* Counterintuitive — the LLM discounts MORE for cost when stakes are higher. Would suggest a "high stakes → high pressure → sympathize with the difficulty" heuristic. Unusual but diagnosable.

---

## Sweep 3 — Own Vote (voted yes vs. voted no)

**Parameter varied:** The focal agent's own vote, holding p₀ = 0.6, c_sw = 2000, c_pressure = 100, α = 0.05, threshold = 4.

**What the theory predicts:** The voted-no agent (ag1) gets db ≈ 0.073; the voted-yes agent (ag6) gets db ≈ 0.022. Crucially, the voted-yes agent's blame is nonzero — they could still have applied social pressure to others.

**How it becomes a prompt:** Present two otherwise-identical members, one who voted to approve and one who didn't.

| Agent | Prompt language |
|-------|----------------|
| Voted no | "Member A voted against the proposal." |
| Voted yes | "Member F voted in favor of the proposal." |

Both believe others vote yes w.p. 0.6, same costs, same pressure effectiveness.

**Null hypothesis (H₀-3):** The LLM assigns zero blame to the agent who voted in favor.

**Finding paths:**

- *LLM gives nonzero blame to the yes-voter:* The LLM recognizes that voting "right" doesn't fully exonerate — you could have lobbied others. This aligns with the framework and is a sophisticated moral judgment. Check whether the ratio (blame_no / blame_yes ≈ 3.3) is in the right ballpark.
- *LLM gives exactly zero blame to the yes-voter:* Binary moral reasoning — if you did the right thing, you're blameless. This is the most common folk intuition and reflects an act-centered (vs. consequence-centered) morality. Diagnosis: the LLM treats the vote as the only morally relevant action and ignores the pressure/lobbying channel entirely.
- *LLM gives EQUAL blame to both:* The LLM focuses entirely on group membership rather than individual action. Diagnosis: collectivist attribution — everyone in the group shares blame regardless of what they did. Connects to the "problem of many hands."

---

## Sweep 4 — Pressure Effectiveness (α)

**Parameter varied:** α ∈ {0.01, 0.03, 0.05, 0.10}, holding p₀ = 0.6, c_sw = 2000, c_pressure = 100, threshold = 4.

**What the theory predicts:** Higher pressure effectiveness → the group could have done more → higher group blame. But the Shapley individual blame has a subtlety: for the focal agent, higher α means the *group's* ability to act without them also rises (other subcoalitions become effective), which can reduce the focal agent's marginal contribution. The net effect is non-trivial.

**How it becomes a prompt:** Vary how effective lobbying is described to be.

| α value | Prompt language |
|---------|----------------|
| 0.01 | "In this organization, lobbying colleagues has almost no effect — people's minds are largely made up." |
| 0.05 | "Lobbying can have a modest effect — persistent pressure from several colleagues can shift some opinions." |
| 0.10 | "In this culture, coordinated social pressure is quite effective at changing minds." |

**Null hypothesis (H₀-4):** The LLM's blame attribution does not vary with described lobbying effectiveness.

**Finding paths:**

- *LLM increases blame with α:* It reasons that more effective available actions → more blame for inaction. Correct qualitative direction for group blame, but may overshoot for individual blame (missing the marginal-contribution subtlety). Diagnosis: consequentialist intuition without coalition-theoretic sophistication.
- *LLM decreases blame with α:* Possible reasoning: "if pressure is very effective, others could have done it without this agent, so this agent is less pivotal." This would actually track the marginal-contribution logic more closely than naive intuition. Surprising if found.
- *LLM ignores α:* Blame is determined by the vote and the cost, not by the available group actions. Diagnosis: individualist moral reasoning — the LLM doesn't reason about collective counterfactuals.

---

## Sweep 5 — Voting Threshold

**Parameter varied:** threshold ∈ {2, 3, 4, 5, 6}, holding p₀ = 0.6, c_sw = 2000, c_pressure = 100, α = 0.05.

**What the theory predicts:** Blame generally increases with threshold (when more votes are needed, each defection is more pivotal), but the relationship depends on p₀ and vote. For voted-yes agents, blame stays near zero across all thresholds.

**How it becomes a prompt:** Vary the approval rule.

| Threshold | Prompt language |
|-----------|----------------|
| 2/7 | "The proposal needed just 2 of 7 votes to pass." |
| 4/7 | "The proposal needed a majority — at least 4 of 7 votes." |
| 6/7 | "The proposal needed near-unanimous support — at least 6 of 7 votes." |

**Null hypothesis (H₀-5):** The LLM's blame attribution does not vary with the voting threshold.

**Finding paths:**

- *LLM increases blame with threshold:* Correct — when the bar is higher, each no-vote is more damaging. Check magnitude.
- *LLM decreases blame with threshold:* Possible reasoning: "if you needed 6/7, failure was almost inevitable, so no single person is really to blame." This would be the many-hands diffusion pattern — blame per individual drops as the collective challenge grows. Directly testable against Shapley, which increases. Diagnosis: diffusion of responsibility.
- *LLM shows non-monotonic pattern:* Could indicate sensitivity to the "difficulty" of coordination — moderate thresholds feel most blameworthy because they were achievable. May align with the paper's discussion of coordination costs.

---

## Sweep 6 — Many Hands (group size, optional extension)

**Parameter varied:** Number of agents ∈ {3, 5, 7, 9}, threshold scaled proportionally (majority), holding per-agent parameters fixed.

**What the theory predicts:** By the Efficiency axiom, individual Shapley blame = group blame / n (approximately, for symmetric agents). Individual blame decreases as group grows, but total group blame is conserved.

**How it becomes a prompt:** Vary the committee size.

| Group size | Prompt language |
|------------|----------------|
| 3 members | "A three-person panel..." |
| 7 members | "A seven-member review board..." |
| 9 members | "A nine-member oversight committee..." |

**Null hypothesis (H₀-6):** The sum of the LLM's blame attributions across all agents does not decrease as group size increases (i.e., total blame is conserved).

**Finding paths:**

- *LLM conserves total blame (sum ≈ constant):* The LLM implicitly respects Efficiency — group responsibility is preserved and just divided more finely. Strong alignment with Shapley.
- *Total blame shrinks as group grows:* Classic many-hands diffusion. The LLM "leaks" responsibility as more people are involved — each individual feels less blameworthy AND the group as a whole feels less blameworthy. This is the failure mode the paper specifically warns about and the one most relevant to real-world AI accountability debates.
- *Total blame grows with group size:* The LLM over-attributes — more people involved → more total blame. Unusual but possible if it treats blame as non-rival.

---

## Summary Table

| Sweep | Parameter | Theory predicts | Folk intuition likely predicts | Diagnostic value of mismatch |
|-------|-----------|-----------------|-------------------------------|------------------------------|
| 1 | Belief (p₀) | Non-monotonic peak | Monotonic (either direction) | Pivotality understanding |
| 2 | Switch cost × Stakes (c_sw × N) | Smooth decrease; flatter slope at high stakes | Binary or ignored; stakes-insensitive | Cost-discounting / proportionality / implicit N |
| 3 | Own vote | Nonzero blame for yes-voter | Zero blame for yes-voter | Act-based vs. consequence-based morality |
| 4 | Pressure effect (α) | Non-trivial (marginal contribution) | Monotonic increase or ignored | Coalition-theoretic reasoning |
| 5 | Threshold | Generally increasing | Decreasing (diffusion) or flat | Structural sensitivity |
| 6 | Group size | Individual ↓, total conserved | Both individual AND total ↓ | Many-hands diffusion |

---

## Controls and Reporting

**Surface framing (distinct from Sweep 2's stakes manipulation):** Sweep 2 varies the *magnitude* of the outcome (minor vs. severe). The framing control varies the *emotional language* used to describe a fixed-stakes scenario — e.g., neutral ("the proposal was not approved") vs. morally loaded ("the board's inaction left vulnerable residents without protection"). Apply this control to at least Sweeps 1 and 3 to check whether tone shifts blame attribution independently of content. This is both a confound to control and a finding about framing effects on moral judgment.

**Models:** Run across 2–3 frontier LLMs (e.g., Claude, GPT, Gemini). Model-specific patterns are a finding, not noise.

**Repetitions:** 15–20 samples per vignette per model at moderate temperature. For Sweeps 1–3 with full stimulus sampling, each parameter level has 3 phrasings × 2 scenarios × 15 reps = ~90 data points per model — enough to estimate both the parameter effect and the phrasing variance. For Sweeps 4–6 (single phrasing, Scenario A only), 15–20 reps per condition.

**Scoring:** Spearman rank correlation per sweep. Overlay LLM blame curves on committee.py Shapley curves from analysis.pdf. Report shape agreement (monotonic? peaked? flat?) separately from magnitude agreement.

**Implicit N inference (from Sweep 2):** Fit the LLM's blame-vs-cost curve at each stakes level to the formula `blame = δ · (1 − c_sw/N)`, where δ is known from committee.py. The fitted N is a compact, interpretable summary of how the LLM balances cost against consequence — reported per model, per stakes level.

---

## Limitations and Deferred Sweeps

**c_pressure (cost of collective coordination) is not swept.** This parameter enters the blame formula through the same cost-discount channel as c_sw, so the primary diagnostic (does the LLM discount for cost?) is already covered by Sweep 2. In the paper's example it also produces the smallest blame difference of any parameter (ag1 vs ag4: 0.073 vs 0.068). However, c_pressure tests something conceptually distinct that no other sweep captures: whether the LLM distinguishes *individual* sacrifice ("how much it costs you to change your vote") from *coordination* overhead ("how expensive it is for the group to organize pressure"). If Sweep 2 shows the LLM is cost-sensitive, this becomes the natural follow-up — does that sensitivity extend to collective action costs, or only to personal ones?

**Sweeps 4–6 use single phrasings and one scenario only.** Due to scope constraints, full stimulus sampling (3 phrasings × 2 scenarios) is applied only to Sweeps 1–3. Results from Sweeps 4–6 should be interpreted with the caveat that wording effects have not been controlled for. If any of these sweeps yield surprising results, the first follow-up is to replicate with stimulus sampling before drawing strong conclusions.

**Coalition amplification (α·n) is conveyed only qualitatively.** In the framework, social pressure compounds with coalition size — a coalition of *n* agents shifts every other agent's yes-probability by *n·α*. The prompt states the *direction* ("the more physicians who joined in advocating, the better the odds…") but cannot carry the exact linear/additive/saturating form in natural language. This matters because α·n moves the **peak location** of the blame-vs-p₀ curve (roughly 0.50 → 0.35 → 0.05 as α grows from 0), even though it does not change *whether* a peak exists (the non-monotonic hump survives even with the pressure channel removed, carried by own-vote pivotality). Consequence: report shape/rank agreement as primary; treat peak-location agreement as approximate. Becomes load-bearing for Sweep 4 (α), where the coalition channel is the variable under test.

**Language.** All vignettes are in English. Cross-linguistic generalization (whether the same patterns hold in Spanish, Chinese, etc.) is untested. Worth pursuing if the English results show clear structure, but out of scope for three weeks.


<!-- DISCARDED:

Questions:

- is there a point of equilibrium in the distribution of who votes yes among the 7 agents, in terms of group blame and individual blame? that would depend of course on the parameters of the agents. What if we create different scenarios to test, and analyze such point of equilibrium for each case -> where is the least group and overall individual blame for each agent? if we conduct those tests to the agents, what is the distribution of votes for each scenario? are the distribution of yeses and no's similar?

What about this:

- Create an interface that the LLM-based agents can actuate on (a tool), where two actions are available: $\texttt{switch\_vote} \quad \text{(Boolean: causes switching from no to yes)}$ and $\texttt{form\_coalition} \quad \text{(input and output to be defined)}$.
- Each agent MUST choose a response for each.
- The input for each agent is a prompt, reskinned to avoid data contamination, and where the parameters are taken from the committee illustrative example:

$$
\begin{aligned}
    &\textbf{Global parameters} \\
    N:&                                 \quad \textit{Balance parameter. Must be greater than the max cost.} \\
    \text{Threashold}_\varphi:&       \quad \textit{Threshold that defines how many positive votes are need for the bill to pass. In the paper's example it is 4} \\
    &\textbf{Agent-specific parameters} \\
    p_0:&                                \quad \textit{The initial probability that the agent believes the other committee members will vote “yes” before any action is taken.} \\
    \alpha:&                             \quad \textit{The percentage increase in each agent’s probability of voting “yes” as a result of the applied social pressure.} \\
    c_{\text{pressure}}:&                      \quad \textit{The cost incurred by a coalition of n agents to apply social pressure.} \\
    c_{\text{switch from no to yes}}:&   \quad \textit{The additional personal cost required for the agent to switch their own vote to “yes” if they are part of the coalition.}
\end{aligned}
$$

- We define a universe of scenarios by sweeping the global parameters (e.g., $N$, $\text{Threashold}_\varphi$ [e.g., $\geq 4$]) as well as the agent-specific parameters, for each run, the LLMs are asked many times -->