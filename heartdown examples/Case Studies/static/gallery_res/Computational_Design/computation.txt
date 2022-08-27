---
title: Computational Design of Transforming Pop-up Books
author:
- name: NAN XIAO and ZHE ZHU
  affiliation: TNList, Tsinghua University
- name: RALPH R. MARTIN
  affiliation: Cardiff University
- name: KUN XU and JIA-MING LU and SHI-MIN HU
  affiliation: TNList, Tsinghua University
full_paper: False
sectionBase: [4, 2]
---
# ALGORITHM
## Optimization
### Energy function
❤: computation
We define the optimisation problem in terms of minimising <span class="def:E">an energy function $E(x)$, where $x$ represents the linkage configuration and geometric parameters of the transforming pop-up</span>. For simplicity of presentation, we leave the dependence on $x$ implicit in the following.

Ensuring freedom from collisions is enforced as a hard constraint. Given a configuration $x$, we first check for collision during transformation, and if detected, we give the energy function $E$ a value certain to be greater than the energy for any non-colliding configuration. Our implementation uses the OBB-tree algorithm [Gottschalk et al. 1996] for collision detection, like other recent mechanical modeling works such as [Zhu et al. 2012]. Optionally, to avoid collision with the ground, we add a dummy ground patch of large enough area to enclose the design, and include it during collision checking. Users may choose whether to enable this option or not: if the goal is to place the pop-up inside a book, this option should be enabled, but if the goal is to make a free-standing pop-up, it is unnecessary.

If there is no collision, the energy function $E$ is defined as the sum of a shape term and a flip term:

``` iheartla
E = `$λ_s$``$E_s$` + (1 - `$λ_s$`)`$E_f$` 
where
`$λ_s$` ∈ ℝ 
```

<span class="def:E_s">The shape term $E_s$ represents the shape constraint</span>, i.e. it favors shapes of pop-up for which the untransformed and transformed states are good matches to the user given patterns. <span class="def:E_f">The flip term $E_f$ represents the flip constraint, penalizing any patch areas which do not flip and are visible in both untransformed and transformed states</span>. <span class="def:λ_s">$λ_s$ is a weight to control the relative contributions of the two terms, and is set to 0.4</span>.

Shape term. The shape term accounts for how well the pop-up in the untransformed and transformed states $S_1$ and $S_2$ match the shapes of the user given source and target patterns $U_1$ and $U_2$. The shape matching cost is defined in terms of a contour matching cost and an area matching cost:
``` iheartla

`$E_s$` = `$E_c$` + `$E_a$` 
where
`$E_a$` ∈ ℝ
```
The contour matching cost is computed using the shape context method [Belongie et al. 2002], and is given by:
``` iheartla

`$E_c$` = D(`$S_1$`, `$U_1$`) + D(`$S_2$`, `$U_2$`)
where
D ∈ ℝ, ℝ -> ℝ
`$S_1$` ∈ ℝ
`$S_2$` ∈ ℝ
`$U_1$` ∈ ℝ
`$U_2$` ∈ ℝ
```
where $D(·)$ denotes the shape context matching cost. In our implementation, we sample 100 points on each contour to perform this computation.

The area matching cost measures the difference of region coverage between the pop-up and user given patterns. It is computed as:

$$E_a = \sum_i \prosedeflabel{\lambda_a} ||S_i \setminus U_i|| + (1-\lambda_a)||U_i \setminus S_i||$$

where \ is the set difference operator, $∥ · ∥$ denotes the normalized area of a region, i.e. its area divided by the sum of the areas of all patches, and $\prosedeflabel{\lambda_a}$ is a relative weight. $S_i \setminus U_i$ are redundant regions, i.e. regions covered by the pop-up but not covered by the user given pattern. $U_i \setminus S_i$ are unrepresented regions, i.e. regions covered by the user given pattern but not covered by the pop-up. Redundant regions are relatively unimportant, since the later patch refinement step can crop them. However, unrepresented regions will show the ground patch as they will not be included in the transforming pop-up. Hence, in our implementation, we set $\prosedeflabel{\lambda_a} = 0.1$ to more strongly penalize unrepresented regions.

Flip term. Since visible regions in untransformed and transformed states are painted with source and target pattern textures respectively, to avoid conflicts in texture painting, we should minimise regions which are visible in both untransformed and transformed states which do not show different sides of the paper. The flip term is simply defined as the sum of the areas of all regions which violate this constraint (again normalized as in Equation 4):

``` iheartla

`$E_f$` = sum_i ||R_i||
where

R_i ∈ ℝ^3
```

where <span class="def:R">$R_i$ is any region of a patch which is visible from the same side in both states</span>.





















