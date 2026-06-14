# ESV: Skyrim Alchemy

This project is mainly an exercise in *design of experiments*, as well as data presentation and general programming in python. The code is constitutes a simulation and experimentation infrastructure for analyzing optimization of the alchemy mechanic from *ESV: Skyrim*.

includes three main components: 

- ```alchemy/``` : Engine for emulating and gathering data from Skyrim's alchemy mechanic.
- ```monte_carlo/``` : Monte Carlo runner, defining the interface for experiments and the scenarios analyzed.
- ```experiments/``` : Scripts for analyzing and saving results of simple experiments and Monte Carlo simulations.

## Code Demo:
TODO: create jupyter notebook demo

## Experiments and Results:
TODO

Salmon Roe is by far the most valuable ingredient in skyrim, confirmed by its raw effect values as well as average performance in Monte Carlo simulations. This is due to its unusually high magnitudes for the 'Fortify Magicka' and 'Fortify Stamina' effects, which lead to extremely high value potions when both are expressed. 

The widely held belief is that the most valuable potion possible in skyrim is the combination (Salmon Roe, Garlic, Nordic Barnalce), though this misses the true best potion combination: (Chicken Egg, Hawks Egg, Salmon Roe). Other calculators seem to miss this combination because (contrary to confirmed in-game behavior) they do not allow a potion combination that adds an ingredient when its contributed effects are already expressed in the other two ingredients. For instance, the hawks egg and chickens egg are essentially identical, meaning their combination yeilds a potion with all four of their effects. Adding salmon roe to this combination doesn't add any new effects, so other calculators (notably powtions.com) seem to exclude the possibility, when in reality the added salmon roe increases the value dramatically by scaling the fortify magicka and fortify stamina effects.
