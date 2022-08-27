---
title: SIERE a hybrid semi-implicit exponential integrator for efficiently simulating stiff deformable objects
author:
- name: YU JU (EDWIN) CHEN
  affiliation: University of British Columbia
- name: SEUNG HEON SHEEN
  affiliation: University of British Columbia
- name: URI M. ASCHER
  affiliation: University of British Columbia
- name: DINESH K. PAI
  affiliation: University of British Columbia and Vital Mechanics Research
full_paper: False
sectionBase: [3]
eqBase: 6
---
❤: siere
# METHOD
## Model reduction and subspace splitting

Next, we define the splitting $G$ and $H$, crucial to the success of our method. The idea is to apply ERE in the subspace of the first s modes ($s ≪ n$: typically, $5 ≤ s ≤ 20$) and project it back to the original full space. In the bridge example of Figure 1, $n ≈ 100, 000$, so this is a rather large reduction.

Then we use SI on the remaining unevaluated part, as per Eq. (5). We use mass-PCA to find our reduced space. That is, considering at the beginning of each time step a solution mode of the form $q(t) = w exp(ı\sqrt{λ}t)$ for the ODE $M q  + K q = 0$, we solve the generalized eigenvalue problem

$$ K w = λ M w 
\notag$$

for the $s$ smallest eigenvalues $λ$ and their corresponding eigenvectors $w$ (dominant modes). In Matlab, for instance, this can be achieved by calling the function eigs. In our implementation, we use the C++ Spectra library [Qiu 2019]. Denote this partial spectral decomposition by

$$K U_s =M U_s Λ_s$$

where the “long and skinny” $U_s$ is $n × s$, has the first s eigenvectors $w$ as its columns, and the small $Λ_s$ is a diagonal $s × s$ matrix with the eigenvalues $λ_1, ..., λ_s$ on the diagonal. Notice that both $K$ and $M$ are large sparse symmetric matrices. In addition, $M$ is positive definite, so $U_s$ has M-orthogonal columns:

$$U_s ^T M U_s = I_s, U_s ^T K U_s = Λ_s. $$

Next, we write Eq. (2) in the split form Eq. (3), with the splitting $H$ and $G$ defined based on the partial spectral decomposition Eq. (6). We define at each time step


``` iheartla
`$G(u)$` = [`$v_G$`
          M⁻¹`$f_G$`]
`$H(u)$` = [`$v_H$`
          M⁻¹`$f_H$`]
`$v_G$` = `$U_s$``$U_s$`^T Mv
`$v_H$` =  v - `$v_G$`
`$f_G$` =  M`$U_s$``$U_s$`^T f
`$f_H$` =  f - `$f_G$`

where 
`$U_s$` : ℝ^(n × s)
M : ℝ^(n × n)
v : ℝ^n
f : ℝ^n
K : ℝ^(n × n)
```


We also need the Jacobian matrices

``` iheartla
 
`$J_G$` = [0    `$U_s$``$U_s$`^TM
      -`$U_s$``$U_s$`^TK`$U_s$``$U_s$`^TM 0 ]
`$J_H$` =  [0     I_n
            -M⁻¹K 0] - `$J_G$` 

```

Notice that the ERE expression, $h φ_1 ( h J_G ) G(u) $, can be evaluated in the subspace first, and then projected back to the original space.

The additive method defined by inserting Eqs. (8) and (9) into Eq.(5) has three advantages:

- (1) At each time step, the majority of the update comes from ERE in the dominating modes. Thus it is less affected by artificial damping from SI.
- (2) The computation load of ERE is greatly reduced, because the stiff part is handled by SI (or BE for that matter). Furthermore, the evaluation of the exponential function in the subspace has only marginal cost since the crucial matrix involved has been diagonalized.
- (3) The “warm start” for SI makes its result closer to that of BE.


ERE update in the subspace: To evaluate the update in the subspace of dimension s we rewrite Eq. (5) as
 
``` iheartla

`$u_+$` =  u + (`$\boldsymbol{I}$` -h`$J_H$`)⁻¹(h `$H(u)$` + h[`$U_s$` 0
                                               0   `$U_s$`] `$φ_1$`(h`$J_G^r$`) `$G^r(u)$`)
where 
`$\boldsymbol{I}$` : ℝ^(2n × 2n)
h : ℝ
`$φ_1$` : ℝ^(k×k) -> ℝ^(k×k)
u : ℝ^(2n × 1)
```


where
``` iheartla
 
`$J_G^r$` = [0     I_s
            -`$U_s$`^TK`$U_s$` 0]
`$G^r(u)$` = [`$U_s$`^TMv
            `$U_s$`^Tf]

```
 

The evaluation of the action of the matrix function $φ_1$ involves only matrices of size $2s × 2s$. Furthermore, the matrix function $φ_1$ can be evaluated directly through the eigenpairs of $J_G^r$
 $$ 
\Bigg\{ ı\sqrt{λ_l}, \begin{bmatrix} e_l \\ ı\sqrt{λ_l}e_l  \end{bmatrix}  \Bigg\} , 
\Bigg\{ -ı\sqrt{λ_l}, \begin{bmatrix} -e_l \\ ı\sqrt{λ_l}e_l  \end{bmatrix}  \Bigg\},
l = 1,...,s,
 $$
 

with $e_l$ being the $l^{th}$ column of the identity matrix.

The large $n×n$ linear system solved in Eq. (10) is not sparse due to the fill-in introduced by the small subspace projection. Specifically, the off-diagonal blocks of the Jacobian matrix $J_G$ defined in Eq. (9a) are not sparse. If not treated carefully, solving the linear system in Eq. (5) and Eq. (10) can be prohibitively costly. Fortunately, this modification matrix has the low rank $s$. We can write


❤: second
``` iheartla_unnumbered
`$J_G$` = `$Y_1$``$Z_1$`^T + `$Y_2$``$Z_2$`^T 
``` 
 
where 
``` iheartla_unnumbered
`$Y_1$` =  [`$U_s$`
             0]
`$Z_1$` =  [ 0
             M`$U_s$`] 
`$Y_2$` =  [0
            -`$U_s$``$U_s$`^TK`$U_s$`]
`$Z_2$` =  [ M`$U_s$`
             0] 

where 
`$U_s$` : ℝ^(n × s)
M : ℝ^(n × n) 
K : ℝ^(n × n)
``` 

The linear system in Eq. (10) becomes

$$ I−h J_H =(I−h J)+h Y_1 Z_1 ^T +h Y_2 Z_2 ^T $$

where the four matrices $Y_i$ and $Z_i$ are all “long and skinny” like $U_s$, while the matrix $J$ is square and large, but very sparse. Figure 3 illustrates this situation. For the linear system to be solved in Eq. (10) we may employ an iterative method such as conjugate gradient, whereby the matrix-vector products involving $J$ or $Y_iZ_i^T$ are all straightforward to carry out efficiently. However, we have often found out that a direct solution method is more appropriate for these linear equations in our context. In our implementation we use pardiso [De Coninck et al. 2016; Kourounis et al. 2018; Verbosio et al. 2017]. For this we can employ the formula of Sherman, Morrison and Woodbury (SMW) [Nocedal and Wright 2006], given by
<figure>
<img src="./img/img3.png" alt="Trulli" style="width:100%" class = "center">
<figcaption align = "center">Fig. 3. The matrix $I − h J_H$ in the linear system eq. (10) is not sparse (c). Fortunately, by Eq. (13) the fill-in to the original sparse matrix $I − h J (a)$ has low rank (b) allowing us to use the SMW formula $E_q$. (14).
</figcaption>
</figure>
$$ (A+YZ^T)^{−1} =A^{−1}−A^{−1}Y(I +Z^TA^{−1}Y)^{−1}Z^TA^{−1} $$

to solve the linear system in Eq. (10). In our specific notation we set at each time step $A = I − h J_H$ in Eq. (14), and apply the formula twice:once for $Y = Y_1$, $Z = Z_1$, and once for $Y = Y_2$, $Z = Z_2$. Note that the matrices $I + Z^T A^{−1}Y$ in Eq. (14) are only $2s × 2s$, and this results in an efficient implementation, so long as the subspace dimension s remains small.















