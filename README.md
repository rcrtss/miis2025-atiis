# An Empirical Study of Blameworthiness in LLM-based Multi-agent Settings

This project implements and empirically tests the group blameworthiness framework from [Friedenberg & Halpern (2019)](https://doi.org/10.1609/aaai.v33i01.3301525). The framework defines how to ascribe blameworthiness to groups of agents using causal models, then apportions it to individuals via the Shapley value. We first reproduce the paper's 7-voter-committee example computationally, then place LLM-based agents under the same scenario to see whether their behavior correlates with the theory's predictions.

![Illustrative Example Summary](./docs/img/rm_illustrative_ex.png)

## Research Questions

**Q1.** Can we reproduce the numerical results of the 7-voter-committee example, and what implicit assumptions must be made?

**Q2.** When LLM agents are placed in the same scenario under varying context (believed probability, cost), does their behavior shift in the direction the framework predicts?

![Sweep p0 in the reimplementation of Friedenberg & Halpern (2019)](./docs/img/sweep_p0_oracle.png)

## Key Reference

Friedenberg, M., & Halpern, J. Y. (2019). Blameworthiness in Multi-Agent Settings. *Proceedings of the AAAI Conference on Artificial Intelligence*, 33(01), 525–532.