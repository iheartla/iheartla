---
title: On Elastic Geodesic Grids and Their Planar to Spatial Deployment
author:
- name: STEFAN PILLWEIN
  affiliation: TU Wien
- name: KURT LEIMER
  affiliation: TU Wien
- name: MICHAEL BIRSAK
  affiliation: KAUST
- name: PRZEMYSLAW MUSIALSKI
  affiliation: NJIT and TU Wien
full_paper: False
sectionBase: [5]
---
# PHYSICAL SIMULATION
❤: elastic
To simulate the physical behavior of the deployed grid, we use a simulation based on discrete elastic rods [Bergou et al. 2010] and build upon the solution of [Vekhter et al. 2019]. We refer the reader to those papers for the details. Note, that the associated material frames of the rods do not need to be isotropic, which allows us also to model the exact cross sections of lamellas with a ratio of 1 : 10.

A central aspect of the kinematics of elastic geodesic grids is the ability of grid members to slide at connections, denoted in the following as $q$. In general, they do not coincide with the vertices of the discretized grid members. To handle them, we introduce <span class="def:β_q">barycentric coordinates $β_q$ to describe the location of a connection on a rod-edge</span>. We also take the physical thickness $t$ of the lamellas into account, which is modeled by an offset between the members $g$ and $h$ at each connection. Hence, a connection $q$ consists of two points $q_g$ and $q_h$ with an offset $t$. Apart from sliding, members are allowed to rotate around connections about an axis that is parallel to the cross product of the edges $q_g$ and $q_h$ lie on.

Simulation. Our aim is to find the equilibrium state of the given elastic grid, which corresponds to an optimization problem of minimizing the energy functional

``` iheartla_unnumbered
`E_q` from connection(`$q_g$`,`$q_h$`,`$m_g$`,`$m_h$`,`$\angle$`,`$λ_{q,1}$`,`$λ_{q,2}$`,t)
`E_a` from anchor(`$λ_{a,1}$`,`$λ_{a,2}$`,q,`$q_a$`,m,`$m_a$`, `$\angle$`)
`E_n` from notchlimit(`$δ^{(−)}$`,`$δ^{(+)}$`,`$β_q$`,`$β^{(−)}$`,`$β^{(+)}$`)
`E_p` from penalty(μ, ε, `$β_q$`)
E = `E_r` + `E_q` + `E_a` + `E_n` + `E_p`
where
`E_r` ∈ ℝ:the internal energy of the rods
where
`$q_g$` ∈ ℝ^n: point
`$q_h$` ∈ ℝ^n: point
`$m_g$` ∈ ℝ^n : the material vectors of $g$
`$m_h$` ∈ ℝ^n : the material vectors at $h$
`$\angle$` ∈ ℝ^n, ℝ^n -> ℝ^n
`$λ_{q,1}$` ∈ ℝ: the constraint weights for the position
`$λ_{q,2}$` ∈ ℝ: the constraint weights for the direction
t ∈ ℝ : offset
where
`$λ_{a,1}$` ∈ ℝ: weight
`$λ_{a,2}$` ∈ ℝ: weight
q ∈ ℝ^n 
`$q_a$` ∈ ℝ^n 
m ∈ ℝ^n 
`$m_a$` ∈ ℝ^n 
where
`$δ^{(−)}$` ∈ ℝ
`$δ^{(+)}$` ∈ ℝ
`$β_q$` ∈ ℝ :  barycentric coordinates 
`$β^{(−)}$` ∈ ℝ : the barycentric coordinates of the notch bounds on their corresponding edges
`$β^{(+)}$` ∈ ℝ : the barycentric coordinates of the notch bounds on their corresponding edges
where
μ ∈ ℝ: a weighting parameter
ε ∈ ℝ: denoting how far $q$ is allowed to move past the end of the edge
```
where <span class="def">$E_r$ is the internal energy of the rods</span>, <span class="def">$E_q$ is the energy of the connection constraints</span>, <span class="def">$E_a$ is the energy of the anchor constraints</span>, <span class="def">$E_n$ is the energy of the notch-limit constraints</span>, and <span class="def">$E_p$ is an additional notch penalty term that also serves to account for friction</span>. We perform the simulation by minimizing <span class="def:E">the entire energy $E$ for the rod centerline points $x$ </span>using a Gauss-Newton method in a similar fashion as proposed by Vekhter et al. [2019]. In Section 6.2 we perform an empirical evaluation of the accuracy of the simulation by comparing it to laser-scans of the makes.
<figure>
<img src="./img/img10.png" alt="Trulli" style="width:100%" class = "center">
<figcaption align = "center">Fig. 10. The influence of anchors and notches on the example Archway. Left: Anchors at the corners are not sufficient to push the grid into the right configuration. Center: Deployed state without notches, local buckling and irregularities in smoothness can be observed. Right: Notches relax the structure to a more natural, lower energy shape (cf. Sections 4.5 and 4.6).</figcaption>
</figure>
For the sake of readability, we will define the constraint energy terms only for a single constraint each. Er is the sum of stretching, bending and twisting energies of each individual rod. As a full explanation of the DER formulation is out of scope for this paper, we refer the reader to the work of [Bergou et al. 2010] for a detailed description of these terms.
❤: connection
The connection constraint energy $E_q$ is given by
``` iheartla_unnumbered
`E_q` = `$λ_{q,1}$`||`$q_g$`-`$q_h$`+t`$m_g$`||^2 + `$λ_{q,1}$`||`$q_h$`-`$q_g$`+t`$m_h$`||^2 + `$λ_{q,2}$`||`$\angle$`(`$m_g$`,`$m_h$`)||^2 
where
`$q_g$` ∈ ℝ^n : point
`$q_h$` ∈ ℝ^n : point
`$m_g$` ∈ ℝ^n : the material vectors of $g$
`$m_h$` ∈ ℝ^n : the material vectors at $h$
`$\angle$` ∈ ℝ^n, ℝ^n -> ℝ^n
`$λ_{q,1}$` ∈ ℝ : the constraint weights for the position
`$λ_{q,2}$` ∈ ℝ : the constraint weights for the direction
t ∈ ℝ
```
with <span class="def:m_g;m_h">$m_g$ and $m_h$ denoting the material vectors of $g$ and $h$ at $q$ respectively</span>. The term $tm$ accounts for the thickness of the rods, while <span class="def:λ_{q,1};λ_{q,2}">$λ_{q,1}$ and $λ_{q,2}$ are the constraint weights for the position and direction terms</span>.
❤: anchor
The anchor constraint energy $E_a$ ensures that both the position $q$ and material vector $m$ of the given connection do not deviate from the position $q_a$ and material vector $m_a$ of the corresponding anchor. It is given by

``` iheartla_unnumbered
`E_a` = `$λ_{a,1}$`||q-`$q_a$`||^2 + `$λ_{a,2}$`||`$\angle$`(m,`$m_a$`)||^2 
where
`$λ_{a,1}$` ∈ ℝ : weight
`$λ_{a,2}$` ∈ ℝ : weight
q ∈ ℝ^n 
`$q_a$` ∈ ℝ^n 
m ∈ ℝ^n 
`$m_a$` ∈ ℝ^n 
`$\angle$` ∈ ℝ^n, ℝ^n -> ℝ^n
```

with <span class="def:λ_{a,1};λ_{a,2}">$λ_{a,1}$ and $λ_{a,2}$ as weights</span>. This constraint applies to the grid corners and anchors.

❤: notchlimit
<span class="def:E_n">The notch-limit constraint energy $E_n$ </span>ensures that the connection point remains within the bounds of the notch. They are specified by the notch length l and the sliding direction (cf. Section 4.5):

``` iheartla_unnumbered
`E_n` = `$δ^{(−)}$`(1/10 log((`$β_q$`-`$β^{(−)}$`)))^2 + `$δ^{(+)}$`(1/10 log((`$β^{(+)}$`-`$β_q$`)))^2
where
`$δ^{(−)}$` ∈ ℝ 
`$δ^{(+)}$` ∈ ℝ
`$β_q$` ∈ ℝ :  barycentric coordinates 
`$β^{(−)}$` ∈ ℝ : the barycentric coordinates of the notch bounds on their corresponding edges
`$β^{(+)}$` ∈ ℝ : the barycentric coordinates of the notch bounds on their corresponding edges
```


with <span class="def:β^{(−)};β^{(+)}">$β^{(−)}$ and $β^{(+)}$ denoting the barycentric coordinates of the notch bounds on their corresponding edges</span>. The term is only active when the connection lies on the same rod-edge as one of the notch bounds, so $δ^{(−)} = 1$ or $δ^{(+)} = 1$ when the connection lies on one of these edges, and 0 otherwise.
❤: penalty
The additional notch penalty term $E_p$ controls the movement of a connection q between two adjacent edges. If $q$ switches edges, it needs to be reprojected to the neighboring edge at the next iteration of the simulation. Within an iteration, $E_p$ prevents $q$ from moving too far beyond the end of the current edge:

``` iheartla_unnumbered
`E_p` = (μ log((ε + `$β_q$`)))^2 + (μ log((ε + 1 - `$β_q$`)))^2
where
μ ∈ ℝ : a weighting parameter
ε ∈ ℝ : denoting how far $q$ is allowed to move past the end of the edge
`$β_q$` ∈ ℝ :  barycentric coordinates 
```
with <span class="def:ε">$ε$ denoting how far $q$ is allowed to move past the end of the edge</span> and <span class="def:μ">$μ$ acting as a weighting parameter</span>(we choose $ε = 0.0001$, $μ = 0.1$).

<figure>
<img src="./img/img11.png" alt="Trulli" style="width:100%" class = "center">
<figcaption align = "center">Fig. 11. The effect of the weighting parameter $μ$ in $E_p$ (from left to right): surface shaded with K and geodesics; $μ = 0.01$, rods slide onto geodesics; $μ = 0.1$, sliding in high $K$ areas reduced (our setting); $μ = 1$, sliding is heavily reduced. Refer to Section 7.3 for a further discussion on $μ$.</figcaption>
</figure>

Since $E_p$ is not 0 even inside the edge, it penalizes very small sliding movements that would otherwise accumulate over many iterations. In other words, $E_p$ creates a pseudo-frictional effect, which is controlled by $μ$. In a physical grid, friction creates a force acting against the sliding movement of a connection. If the driving force of the movement and the frictional force counterbalance, the movement stops. This situation has an analogy in our grids. A connection stops moving inside a notch if

$$\frac{\partial E_q }{\partial β_q } + \frac{\partial E_p }{\partial β_q } = 0 $$

is fulfilled. Figure 11 depicts the effects of different values for $μ$.








