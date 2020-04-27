import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

L = 0.1  # LArgeur du mur
n = 10  # Numero de nodos utilizados
T0 = 20  # Temperatura inicial
T1s = 40  # Temperatura superficial en cara 1
T2s = 20  # Temperatura superficial en cara 2
dx = L / n
alpha = 0.000000054713  # Difusividad termica K/(Rho*C_p)
t_final = 1800  # Tiempo final en segundos
dt = 60


x = np.linspace(dx / 2, L - dx / 2, n)

T = np.ones(n) * T0
dTdt = np.empty(n)

t = np.arange(0, t_final, dt)


for j in range(1, len(t)):
    plt.clf()
    for i in range(1, n - 1):
        dTdt[i] = alpha * (-(T[i] - T[i - 1]) / dx ** 2 + (T[i + 1] - T[i]) / dx ** 2)
    dTdt[0] = alpha * (-(T[0] - T1s) / dx ** 2 + (T[1] - T[0]) / dx ** 2)
    dTdt[n - 1] = alpha * (
        -(T[n - 1] - T[n - 2]) / dx ** 2 + (T2s - T[n - 1]) / dx ** 2
    )
    T = T + dTdt * dt
    print(x)
    print(T)


# Cooling Law
# dT/dt = -k(T-Tr)

# temp melange = (Vol1*T1 + Vol2*T2) / (Vol1+Vol2)

# deltaT chauffage ddcmath.heating heating_deltaT_c
