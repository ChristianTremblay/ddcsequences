ddcsequences 
=====================================

This project is an attempt to provide mechanisms that will simulate real HVAC equipments that will be read from and write back
to BACnet controllers under test.

This way, it is possible to program a DDC controller using the tool provided by the manufacturer, then using this library, 
virtually connect the different inputs and outputs and see how the control sequence operates.

Typical examples are starting a fan and getting a status back or opening a valve and see the impact on the water temperature.

This library is made to work with BAC0. The connections to inputs are made using a BACnet property named `out_of_service`. 
When true, this property allows a user to write to the present value of a BACnet object. This will make the controller think
that a real sensor is connected to its input and the sequence will operate accordingly.

The library can then use any output from the controller by simply reading it. The value of those outputs will then have 
an impact on the systems defined (what we call equipment from now on).