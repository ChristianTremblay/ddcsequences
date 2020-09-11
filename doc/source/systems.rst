Systems
========

First part of this library are systems. Systems are black boxes that can take an input, apply some algorithm to input
and generate an output based on the input.

Different types of systems are provided : 

- PASSTHRU
- SELECT
- ADD
- SUB
- HEAT
- MIX
- LINEAR
- SPAN
- TRANSIENT

Those systems are meant to be pluggable in whatever order we need to mimic any equipment. For example, it could be 
required to take a MIX block and use it as an input for a TRANSIENT block. This way, the output generated would be 
affected by an exponential curve instead of changing instantaneoulsy.

Each system is 
