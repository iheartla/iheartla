---
title: Stable Neo-Hookean Flesh Simulation
author:
- name: BREANNAN SMITH
  affiliation: Pixar Animation Studios
- name: FERNANDO DE GOES
  affiliation: Pixar Animation Studios
- name: THEODORE KIM
  affiliation: Pixar Animation Studios
full_paper: False
sectionBase: [4, 2]
eqBase: 18
---
❤: Stable
# ENERGY EIGENANALYSIS
## First Piola-Kirchhoff Stress (PK1)
 
We sart from the PK1 for Eqn. 14,

 

``` iheartla
`$P(F)$` = μ(1-1/(`$I_C$`+1))F + λ(J- α)`$\frac{\partial J}{\partial F}$`

where 
F: ℝ^(3×3): the deformation gradient
μ: ℝ : the Lamé constant
`$I_C$`: ℝ : the first right Cauchy-Green invariant
λ: ℝ : the Lamé constant
```

where ❤α = 1 + μ/λ - μ/(4λ)❤. We omit the subscript, as we only consider one model in this section. Using the column-wise notation for $F$ (Eqn.1) and the identity ❤J =`$f_0$`⋅(`$f_1$`×`$f_2$`)❤, we write <span class='def:\frac{\partial J}{\partial F}'> $\frac{\partial J}{\partial F}$ (a.k.a. the cofactor matrix)</span> as cross products:




``` iheartla
`$\frac{\partial J}{\partial F}$` = [`$f_1$`×`$f_2$` `$f_2$`×`$f_0$` `$f_0$`×`$f_1$`]

where 
`$f_0$`: ℝ^3: the first column of matrix F 
`$f_1$`: ℝ^3: the second column of matrix F
`$f_2$`: ℝ^3: the third column of matrix F

```

This is a convenient shorthand for computing $\frac{\partial J}{\partial F}$, and will be useful when analyzing $\frac{\partial^2 J}{\partial F^2}$.








