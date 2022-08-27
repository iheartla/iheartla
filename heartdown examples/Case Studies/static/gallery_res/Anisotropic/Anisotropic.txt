---
title: Anisotropic Elasticity for Inversion-Safety and Element Rehabilitation
author:
- name: THEODORE KIM
  affiliation: Pixar Animation Studios
- name: FERNANDO DE GOES
  affiliation: Pixar Animation Studios
- name: HAYLEY IBEN
  affiliation: Pixar Animation Studios
full_paper: False
sectionBase: [4]
eqBase: 5
---
❤: Anisotropic
# AN EIGENANALYSIS OF $I_5$
## The Eigensystem of $I_5$
 
We will now show that the eigensystem of any energy expressed solely in terms of $I_5$ can be written down in closed form. The $I_5$ invariant can be written in several forms,

``` iheartla
tr from linearalgebra
`$I_5$` = tr(CA)

where

a ∈ ℝ^3
C ∈ ℝ^(3×3)
```
where ❤ A = a a^T ❤ and $\|\cdot\|_{2}^{2}$ denotes the squared Euclidean norm. The <span class='def:\frac{∂I₅}{∂F}'>PK1</span> and <span class='def:\frac{∂²I₅}{∂f²}'>Hessian in 3D</span> are

``` iheartla
`$\frac{∂I₅}{∂F}$` = 2FA
F ∈ ℝ^(3×3): scaling and rotation matrix

```
``` iheartla
`$\frac{∂²I₅}{∂f²}$` = 2[A₁,₁I₃  A₁,₂I₃  A₁,₃I₃
               A₂,₁I₃  A₂,₂I₃  A₂,₃I₃
               A₃,₁I₃  A₃,₂I₃  A₃,₃I₃] 


```
where $I _{3×3}$ is a 3×3 identity matrix,and $A _{ij}$ is the $(i, j)$ scalar entry of $A$. (Appendix A shows the matrix explicitly.) Since Eqn. 7 is constant in $a$, it is straightforward to state its eigensystem in closed form. In 3D, it contains three identical <span class='def:\lambda_{0,1,2}'>non-zero eigenvalues</span>, ❤`$\lambda_{0,1,2}$`=2||a||_2^2❤, and since fiber directions are usually normalized, this simplifies to $\lambda_{0,1,2}=2$. The eigenvalue is repeated, so <span class='def:\mathbf{Q}_{0};\mathbf{Q}_{1};\mathbf{Q}_{2}'>the eigenmatrices</span> are arbitrary up to rotation, but one convenient phrasing is:
``` iheartla_unnumbered
`$\mathbf{Q}_{0}$` = [a^T
               0
               0] 
`$\mathbf{Q}_{1}$` = [0
                    a^T
               0] 
`$\mathbf{Q}_{2}$` = [ 0
               0
               a^T] 


```
 
 
This eigenstructure has a straightforward interpretation. $I_5$ introduces scaling constraints along the anisotropy direction, so the three eigenvectors encode this rank-three phenomenon. The remaining eigenvalues are all zero, so the Hessian contains a rank-six null space. We have provided supplemental Matlab/Octave code that validate these expressions.


❤: Anisotropic2D
The 2D case follows similarly. <span class='def:\frac{∂²I₅}{∂f²}'>The Hessian</span> is


``` iheartla
tr from linearalgebra
`$\frac{∂²I₅}{∂f²}$` = 2[A₁,₁I_2  A₁,₂I_2
               A₂,₁I_2  A₂,₂I_2] 

where

a ∈ ℝ^2
A ∈ ℝ^(2×2)
```

<span class='def:\lambda_{0,1}'>the eigenvalues</span> are ❤`$\lambda_{0,1}$`=2||a||_2^2❤, and <span class='def:\mathbf{Q}_{0};\mathbf{Q}_{1}'>the eigenmatrices</span> become

``` iheartla_unnumbered
`$\mathbf{Q}_{0}$` = [a^T
               0] 
`$\mathbf{Q}_{1}$` = [0
                    a^T] 
```







