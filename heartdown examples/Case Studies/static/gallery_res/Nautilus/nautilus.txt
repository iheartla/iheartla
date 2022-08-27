---
title: Nautilus Recovering Regional Symmetry Transformations for Image Editing
author:
- name: MICHAL LUKÁČ
  affiliation: Adobe Research and Czech Technical University in Prague
- name: DANIEL SÝKORA
  affiliation: Czech Technical University in Prague
- name: KALYAN SUNKAVALLI
  affiliation: Adobe Research
- name: ELI SHECHTMAN
  affiliation: Adobe Research
- name: ONDŘEJ JAMRIŠKA
  affiliation: Czech Technical University in Prague
- name: NATHAN CARR
  affiliation: Adobe Research 
- name: TOMÁŠ PAJDLA
  affiliation: Czech Technical University in Prague
full_paper: False
sectionBase: [6]
eqBase: 8
---
# APPLICATIONS
To demonstrate the practical utility and versatility of our method, we have implemented several image editing applications where the knowledge of the symmetric transformation and its spatial support simplifies the task or removes the need for manual input. We compare our results on each of these applications to their current state-of-the-art methods, and demonstrate that our general framework is able to replicate and improve upon their quality.


❤: nautilus
## Image Rectification
Previous techniques for removing perspective distortion and shear from a photograph require the manual specification or detection of corresponding points, right angles, vanishing lines [Liebowitz and Zisserman 1998], congruent line segments [Aiger et al. 2012], global measurements such as the rank of the image matrix [Zhang et al. 2012] or change of scale [Pritts et al. 2014].

In our solution we rectify the image using one of our <span class="def:H">detected global symmetry homographies, $H$</span>. The key is to assume that $H$ has the following structure:

``` iheartla
H = PSP⁻¹
```
where
``` iheartla
P = [1 x₁ 0
     0 x₂ 0
     x₃ x₄ 1]
S = [x₅ x₆ x₇
     x₈ x₉ x₁₀
     0 0 1]
where
x ∈ ℝ^n
```
<span class="def:P">$P$ is the pure perspective part of $H$ </span> and <span class="def:S">$S$ is an in-plane symmetry</span> which we assume to be a general similarity transform, i.e., uniform scale, rotation, and translation. In addition, we assume that this similarity transformation has a non-zero rotational component, failing which the decomposition can become under-constrained.

To obtain the rectified image we need to estimate $P$ and then apply its inverse. To do that we formulate the task as a non-linear optimization problem, with the following objective function:
``` iheartla
E(x) = λ||(x₅, x₈) - (x₉, x₆)||^2 + sum_i ||H v_i - PSP⁻¹ v_i||^2 where x ∈ ℝ^n

where
λ ∈ ℝ
v_i ∈ ℝ^(3 × 3)
```
The first term of (10) enforces $S$ to be as close to a similarity as possible, and the second term ensures that the decomposition is close to the input homography $H$ (measured using the re-projection error of the four image corners $v_{1...4}$).

Minimizing $E(x)$ is feasible only when the rotation angle of the underlying similarity is away from 0◦ and 180◦. This can be verified by finding the closest similarity $S^′$ to the input homography $H$ and computing $α = arctan(x₈/x₅)$. When $α ∈ (10◦, 170◦)$ we initialize $P$ with the identity matrix, $S = S^′$ and then run a non-linear optimization using the L-BFGS algorithm [Liu and Nocedal 1989; Nocedal 1980] where exact partial derivatives of $E(x)$ are computed using dual numbers [Piponi 2004]. To avoid getting stuck in an inappropriate local minima, we allow for greater freedom at the beginning of the optimization. We start with $λ = 1$ to let the algorithm explore a fruitful direction, and gradually increase it until it reaches $λ = 109$ which allows us to strictly enforce $S$ to be a similarity transform. To ensure that the resulting decomposition is meaningful we use the value of $E(x)$. In practice, we observed $E(x) < 1$ indicates a good rectification (see Fig. 8).
<figure>
<img src="./img/img8.png" alt="Trulli" style="width:100%" class = "center">
<figcaption align = "center">Fig. 8. Rectification of images captured under perspective (a). We compare Aiger et al. [2012] (b), Zhang et al. [2012] (c), and Pritts et al. [2014] (d) against our approach (e, used symmetry inset). Source images: © Isabella Josie.
</figcaption>

 









