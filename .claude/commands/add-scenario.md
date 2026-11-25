---
description: Turn my description of a real specimen into a golden scenario test
argument-hint: <description of the specimen, observations and expected answer>
---

Create a new scenario file in scenarios/ from this description:

$ARGUMENTS

1. Use scenarios/_template.yaml as the format.
2. Map my observations onto existing characters and states. If an observation
   doesn't fit any state, tell me instead of forcing it.
3. Put my expected result as expectations on the final step (and on earlier
   steps if I said what I expect part-way).
4. Run the scenario. If it fails, explain in plain language what the engine
   concluded and why, and suggest whether the content or my expectation might
   need changing. Do not change content or the scenario without my approval.
