import itertools
import math

class EpistemicState:
    """
    Represents an agent's belief about the probability of each agent voting 'yes'.
    """
    def __init__(self, probabilities_dict):
        # e.g., {'ag1': 0.0, 'ag2': 0.6, 'ag3': 0.6, ...}
        self.probs = probabilities_dict

    def get_outcome_probability(self) -> float:
        """
        Calculates the probability of the bill passing (>= 4 'yes' votes out of 7).
        """
        agents = list(self.probs.keys())
        pass_prob = 0.0
        
        # Iterate over all 2^7 possible voting combinations
        for i in range(len(agents) + 1):
            for yes_voters in itertools.combinations(agents, i):
                if len(yes_voters) >= 4:
                    world_prob = 1.0
                    for ag in agents:
                        if ag in yes_voters:
                            world_prob *= self.probs[ag]
                        else:
                            world_prob *= (1.0 - self.probs[ag])
                    pass_prob += world_prob
                    
        return pass_prob

class BlameCalculator:
    def __init__(self, agents, balance_parameter_N, pressure_effect=0.05, pressure_cost=100, switch_cost=2000):
        self.agents = agents
        self.N = balance_parameter_N
        self.pressure_effect = pressure_effect
        self.pressure_cost = pressure_cost
        self.switch_cost = switch_cost

    def delta(self, e1: EpistemicState, e2: EpistemicState) -> float:
        """
        Difference in the probability of the outcome (bill passing) between two states.
        """
        return max(0.0, e2.get_outcome_probability() - e1.get_outcome_probability())

    def simulate_action(self, coalition_ids, base_state: EpistemicState, switcher_id=None, target_id=None):
        """
        Simulates the effect of a coalition applying social pressure, and optionally the target agent switching their vote.
        """
        n = len(coalition_ids)
        new_probs = base_state.probs.copy()
        
        pressure_boost = n * self.pressure_effect
        for ag in self.agents:
            # exclude the target from passive pressure effects since they are the one being pressured to switch
            if ag != target_id:
                new_probs[ag] = min(1.0, new_probs[ag] + pressure_boost)
        
        cost = n * self.pressure_cost
        
        if switcher_id and switcher_id in coalition_ids:
            new_probs[switcher_id] = 1.0
            cost += self.switch_cost
            
        return EpistemicState(new_probs), cost

    def group_blameworthiness(self, coalition_ids, base_state: EpistemicState, target_agent=None) -> float:
        """
        Calculates the maximum blame for a specific subgroup by trying all their possible actions.
        """
        max_gb = 0.0
        # Cost of doing nothing is 0
        base_cost = 0 
        
        # The subgroup can either: 
        # A) Just apply social pressure
        # B) Apply social pressure AND the target agent changes their vote (if they are in the group)
        
        actions_to_try = [(coalition_ids, None)]
        if target_agent in coalition_ids:
            actions_to_try.append((coalition_ids, target_agent))
            
        for action_coalition, switcher in actions_to_try:
            e2, cost_e2 = self.simulate_action(action_coalition, base_state, switcher_id=switcher, target_id=target_agent)
            
            d = self.delta(base_state, e2)
            cost_penalty = max(cost_e2 - base_cost, 0)
            
            # gb formula from the paper
            gb = d * ((self.N - cost_penalty) / self.N)
            
            if gb > max_gb:
                max_gb = gb
                
        return max_gb

    def marginal_contribution(self, agent_id, coalition_ids, base_state) -> float:
        """
        Calculates how much blame an agent adds to a given coalition.
        """
        if agent_id in coalition_ids:
            coalition_without = [a for a in coalition_ids if a != agent_id]
            gb_with = self.group_blameworthiness(coalition_ids, base_state, target_agent=agent_id)
            gb_without = self.group_blameworthiness(coalition_without, base_state, target_agent=agent_id)
            return gb_with - gb_without
        else:
            coalition_with = coalition_ids + [agent_id]
            gb_with = self.group_blameworthiness(coalition_with, base_state, target_agent=agent_id)
            gb_without = self.group_blameworthiness(coalition_ids, base_state, target_agent=agent_id)
            return gb_with - gb_without

    def apportion_blame_shapley(self, target_agent_id, base_state: EpistemicState) -> float:
        """
        Distributes the group blame to an individual using the Shapley value equation.
        """
        n = len(self.agents)
        individual_blame = 0.0
        
        # All agents EXCEPT the target
        other_agents = [a for a in self.agents if a != target_agent_id]
        
        # Iterate through all possible coalitions that INCLUDE the target agent
        for i in range(len(other_agents) + 1):
            for subset in itertools.combinations(other_agents, i):
                coalition = list(subset) + [target_agent_id]
                k = len(coalition)
                
                # Calculate marginal contribution of the target agent to this specific coalition
                mc = self.marginal_contribution(target_agent_id, coalition, base_state)
                
                # Shapley weighting formula: (k-1)! * (n-k)! / n!
                weight = (math.factorial(k - 1) * math.factorial(n - k)) / math.factorial(n)
                
                individual_blame += weight * mc
                
        return individual_blame

# ==========================================
# Run the Simulation for the Paper's Example
# ==========================================

if __name__ == "__main__":
    agents = ['ag1', 'ag2', 'ag3', 'ag4', 'ag5', 'ag6', 'ag7']
    N = 5000 # Kept high to ensure N > max(cost) for all scenarios
    
    # Define the subjective parameters for each agent based on the paper
    agent_configs = {
        # ag1: Baseline. 60% chance for others, $2000 switch cost.
        'ag1': {'base': 0.6, 'vote': 0.0, 'effect': 0.05, 'pcost': 100, 'scost': 2000},
        
        # ag2: Same as ag1, but lower switch cost ($500).
        'ag2': {'base': 0.6, 'vote': 0.0, 'effect': 0.05, 'pcost': 100, 'scost': 500},
        
        # ag3: Same as ag1, but believes social pressure is less effective (3%).
        'ag3': {'base': 0.6, 'vote': 0.0, 'effect': 0.03, 'pcost': 100, 'scost': 2000},
        
        # ag4: Same as ag1, but believes social pressure is more expensive ($150).
        'ag4': {'base': 0.6, 'vote': 0.0, 'effect': 0.05, 'pcost': 150, 'scost': 2000},
        
        # ag5: Same as ag1, but pessimistic baseline (40% chance for others).
        'ag5': {'base': 0.4, 'vote': 0.0, 'effect': 0.05, 'pcost': 100, 'scost': 2000},
        
        # ag6: Same as ag1, but actually voted 'yes' (1.0).
        'ag6': {'base': 0.6, 'vote': 1.0, 'effect': 0.05, 'pcost': 100, 'scost': 2000},
    }

    for ag_id, cfg in agent_configs.items():
        print(f"\n{'='*50}")
        print(f"Simulating Blameworthiness for {ag_id}")
        print(f"{'='*50}")
        
        # 1. Initialize the subjective calculator for this specific agent
        calculator = BlameCalculator(
            agents, 
            balance_parameter_N=N,
            pressure_effect=cfg['effect'],
            pressure_cost=cfg['pcost'],
            switch_cost=cfg['scost']
        )
        
        # 2. Build the baseline epistemic state
        baseline_probs = {}
        for other_ag in agents:
            baseline_probs[other_ag] = cfg['base']
            
        # Override their own vote (since they know what they voted)
        baseline_probs[ag_id] = cfg['vote'] 
        
        e1 = EpistemicState(baseline_probs)
        print(f"Baseline probability of bill passing: {e1.get_outcome_probability():.2%}")
        
        # 3. Calculate Total Group Blameworthiness
        total_group_blame = calculator.group_blameworthiness(agents, e1, target_agent=ag_id)
        print(f"Total Group Blameworthiness: {total_group_blame:.4f}")
        
        # 4. Apportion Blame to the Individual using Shapley
        num_coalitions = 2 ** (len(agents) - 1)
        print(f"Calculating Shapley value for {ag_id} (evaluating {num_coalitions} coalitions)...")
        ag_blame = calculator.apportion_blame_shapley(ag_id, e1)
        print(f"Individual Blame for {ag_id}: {ag_blame:.4f}")