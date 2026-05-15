# Formal Object Catalog — Friedenberg & Halpern (2019)

Dependency-ordered inventory of every formal object requiring a code counterpart.

---

## Section 2: Causal Models

```
[DEF] Signature          — S = (U, V, R): exogenous vars, endogenous vars, range function — Section 2
[DEF] CausalModel        — M = (S, F): signature + set of structural equations F_X — Section 2
[DEF] ActionVariables    — A ⊆ V: special subset of endogenous variables, one per agent — Section 2
[DEF] AgentSignature     — S = (U, V, R, G): augments signature with G: A → agents — Section 2
[DEF] Context            — u⃗: assignment of values to all exogenous variables — Section 2
[DEF] CausalSetting      — (M, u⃗): model + context pair — Section 2
[DEF] Outcome            — φ: Boolean combination of primitive events X = x — Section 2
[DEF] Intervention       — [A ← a]φ: counterfactual "if action a were taken, outcome φ" — Section 2
[DEF] SemanticEval       — [[ψ]]_K: set of causal settings in K where ψ holds — Section 3.1
```

---

## Section 3.1: Single-Agent Blameworthiness (HK)

```
[DEF] EpistemicState     — E = (Pr, K): probability Pr over set K of causal settings — Section 3.1
[DEF] BeliefSupport      — K: the set of causal settings (M, u⃗) the agent considers possible; the support of Pr — Section 3.1
                           [implicit] K is never iterated over directly; only Pr([[φ]]_K) is needed as a callable.
[DEF] CostFunction_SA    — c(a): expected cost agent ascribes to individual action a — Section 3.1
[DEF] BalanceParameter   — N: scalar, N > max_{a'} c(a'), weights cost vs. delta — Section 3.1
[DEF] AlternativeAction  — a': the counterfactual action against which blame is measured; in committee, a'=yes when agent voted no — Section 3.1
[EQ]  InterventionProb   — Pr([[A=a]φ]_K): probability under Pr that forcing A←a leads to φ; in committee, = OutcomeProb with the acting agent's p_i fixed to 1.0 (a=yes) or 0.0 (a=no) — Section 3.1 [implicit]
[EQ]  delta_sa           — δ^E_{a,a',φ} = max(0, Pr([[A=a]φ]_K) − Pr([[A=a']φ]_K)) — Section 3.1
[EQ]  db_relative        — db^c_N(a, a', E, φ) = δ^E_{a,a',φ} · (N − max(c(a')−c(a), 0)) / N — Section 3.1
[EQ]  db                 — db^c_N(a, E, φ) = max_{a'} db^c_N(a, a', E, φ) — Section 3.1
```

---

## Section 3.2: Group Blameworthiness

```
[DEF] AgentSet           — Ag = {ag_1,...,ag_M}: the full set of M agents; M=7 in the committee example — Section 3.2
[DEF] Coalition          — Ag' ⊆ Ag: any subset of agents (frozenset); |Ag'| = its size;
                           Ag' \ {j} = set minus agent j; Ag' ∪ {j} = set plus agent j — Section 3.2
[DEF] ReferenceState     — E1: the agent's actual epistemic state (the "do-nothing" baseline);
                           c(Ag', E1) = 0 by convention; δ_{E1,E1,φ} = 0 so gb ≥ 0 always — Section 3.2 [implicit]
[DEF] EmptyGroupBlame    — gb(∅, E, φ) = 0: empty group has no coordination power; the only E2 with
                           finite cost is E1 itself, and δ_{E1,E1,φ} = 0 — Section 3.2
[DEF] CostFunction_Group — c(Ag', E): cost for coalition Ag' to bring about epistemic state E — Section 3.2
                           [?] Abstract; no closed-form derivation rule given. Specified concretely per example.
[DEF] EpistemicState_Rep — In the committee example, an epistemic state E2 is fully represented by a vector of
                           per-agent vote probabilities p = (p_1,...,p_7) ∈ [0,1]^7; the general (Pr, K) structure
                           collapses to a single causal model with independent Bernoulli exogenous variables — Section 3.4 [implicit]
[EQ]  OutcomeProb        — Pr([[φ]]_K) for committee: P(Σ Bernoulli(p_i) ≥ 4) — Poisson-binomial CDF,
                           computed exactly via convolution over all 2^7 vote combinations — Section 3.4 [implicit]
[EQ]  delta_group        — δ_{E1,E2,φ} = max(0, Pr1([[φ]]_{K1}) − Pr2([[φ]]_{K2})) — Section 3.2
[EQ]  gb_relative        — gb^c_N(Ag', E1, E2, φ) = δ_{E1,E2,φ} · (N − max(c(Ag',E2)−c(Ag',E1), 0)) / N — Section 3.2
[EQ]  gb                 — gb^c_N(Ag', E1, φ) = max_{E2: c(Ag',E2) finite} gb^c_N(Ag', E1, E2, φ) — Section 3.2
                           [?] Maximization over potentially infinite set of E2; enumeration strategy unspecified.
[THM] GroupMonotonicity  — Ag'' ⊆ Ag' ⊆ Ag ⟹ gb(Ag'', E, φ) ≤ gb(Ag', E, φ) — Section 3.2
```

---

## Section 3.3: Apportioning Blame (Shapley Value)

```
[EQ]  mb                 — mb^{c,E}_N(j, Ag', φ): marginal contribution of agent j to group Ag' — Section 3.3
                             = gb(Ag', E, φ) − gb(Ag'\{j}, E, φ)  if j ∈ Ag'
                             = gb(Ag'∪{j}, E, φ) − gb(Ag', E, φ)  if j ∉ Ag'
[EQ]  ShapleyWeight      — w(Ag') = (|Ag'|−1)!(|Ag|−|Ag'|)! / |Ag|!: coalition weight in Shapley formula;
                           sums to 1 over all Ag' ∋ j — Section 3.3
[THM] Efficiency_Axiom   — Σ_j db(j, φ) = gb(Ag, E, φ) — Section 3.3 (axiom, becomes test assertion)
[THM] Symmetry_Axiom     — Renaming agents via permutation π leaves blame unchanged — Section 3.3
[THM] StrongMono_Axiom   — Higher marginal contribution in all coalitions ⟹ higher individual blame — Section 3.3
[THM] ShapleyUniqueness  — Efficiency + Symmetry + Strong Monotonicity ⟹ unique solution = Shapley value (Young 1985) — Section 3.3
[EQ]  db_shapley         — db^{c,E}_N(j, φ) = Σ_{Ag'∋j} [(|Ag'|−1)!(|Ag|−|Ag'|)! / |Ag|!] · mb(j, Ag', φ) — Section 3.3
[THM] NonNegativity      — Group monotonicity ⟹ individual blameworthiness ≥ 0 for all agents — Section 3.3
[THM] HKAgreement        — In single-agent setting, db_shapley agrees with HK definition — Section 3.3
```

---

## Section 3.4: Worked Examples (Test Cases)

```
[EX]  TragCommons        — 100 fishermen, threshold 10, each δ≈0; group blame depends on coordination cost — Section 3.1–3.2 (qualitative only, no numbers)
[EX]  Committee_Setup    — 7 agents, bill passes if ≥4 vote yes; ag1–ag5 voted no; ag6–ag7 voted yes — Section 3.4
                           [?] Exact vote of ag7 not stated; paper says ag1–ag5 voted no, implies ag6 & ag7 voted yes.
[EX]  Committee_ag1      — base_p=0.60, pressure_effect=5%×n, pressure_cost=100×n, self_switch_cost=2000
                           → gb(full group) ≈ 0.390, ag1 ≈ 0.073 — Section 3.4
[EX]  Committee_ag2      — same as ag1 but self_switch_cost=500
                           → gb ≈ 0.390, ag2 ≈ 0.120 — Section 3.4
[EX]  Committee_ag3      — same as ag1 but pressure_effect=3%×n
                           → gb ≈ 0.317, ag3 ≈ 0.079 — Section 3.4
[EX]  Committee_ag4      — same as ag1 but pressure_cost=150×n
                           → gb ≈ 0.361, ag4 ≈ 0.068 — Section 3.4
[EX]  Committee_ag5      — same as ag1 but base_p=0.40
                           → gb ≈ 0.560, ag5 ≈ 0.125 — Section 3.4
[EX]  Committee_ag6      — same as ag1 but ag6 voted yes (one fixed yes vote in base state)
                           → gb ≈ 0.157, ag6 ≈ 0.022 — Section 3.4
[ALGO] EnumerateCoalitions — generate all 2^|Ag| subsets of Ag as frozensets; used in:
                             (a) gb: iterate as candidate E2 actions for a coalition
                             (b) db_shapley: sum over all Ag' ∋ j — Section 3.2–3.3 [implicit]
[ALGO] CommitteeEpistemicFn — maps (Ag', base_p, effect_per_agent, focal_agent) → probability vector p' where:
                              p'_i = min(base_p + |Ag'| × effect_per_agent, 1.0) for all i;
                              p'_{focal} = 1.0 if focal_agent ∈ Ag' (deterministic self-switch) — Section 3.4 [implicit]
[ALGO] CommitteeCostFn     — c(Ag', E2) = |Ag'| × pressure_cost_per_agent + (self_switch_cost if focal_agent ∈ Ag');
                              c(Ag', E1) = 0 (status quo costs nothing) — Section 3.4 [implicit]
```

---

## Open Ambiguities [?] Summary

1. **CostFunction_Group enumeration**: Resolved for committee via CommitteeEpistemicFn and CommitteeCostFn: E2 is indexed by coalition Ag' (which subset applies pressure). EnumerateCoalitions over all 2^|Ag| subsets provides the finite search space.
2. **Outcome probability computation**: Resolved by the Bernoulli collapse: `Pr([[φ]]_K)` = Poisson-binomial CDF evaluated at threshold 4 over 7 independent agents with per-agent probabilities `p_i`. Exact computation via sum over all $\binom{7}{k}$ vote combinations for $k \geq 4$.
3. **ag7 vote**: The setup says ag1–ag5 voted no; ag6 and ag7 presumably voted yes, but ag7's blameworthiness is never computed. Symmetry with ag6 is implied.
4. **N value**: The balance parameter N is never given a concrete value for the committee examples; it must be inferred or reverse-engineered from the reported numbers (δ ≈ 0.454 cited in CLAUDE.md suggests N plays into the reported gb ≈ 0.390).
5. **Self-switch semantics**: "if ag_i was in the coalition, for additional cost X she would have switched her vote to yes" — it is unclear whether this means: (a) the epistemic state assigns probability 1 to her voting yes, or (b) it increases her probability by some amount. The natural reading is (a): deterministic switch.
