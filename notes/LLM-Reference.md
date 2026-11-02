# I❤️LA language reference (one page)

This page summarizes the whole current I❤️LA language (the `mesh` branch, which includes the H❤️rtDown and I❤️MESH extensions) on one page, so that it can be given to an LLM as context. The [wiki](https://github.com/iheartla/iheartla/wiki) has the details, and its [LLM-Reference](https://github.com/iheartla/iheartla/wiki/LLM-Reference) page is a copy of this file. Update both together.

## What it is

I❤️LA is a Unicode, chalkboard-style math language. The compiler type-checks the math, then generates NumPy, C++/Eigen, MATLAB, LaTeX and MathJax.
A file is one **module**. It compiles to a Python class, a C++ struct, or a MATLAB function returning a struct. Undeclared symbols the program uses are **parameters** of the constructor. Every definition becomes a **field**, and every local function becomes a **method**.

```
given
A ∈ ℝ^(3×n)
x ∈ ℝ^n
y = Ax
c = ‖y‖²
```

## Statements

* **Declaration:** `name ∈ type` (or `name: type`). An optional `: description` may follow. Several names can share one: `i, j ∈ ℤ`. `where` or `given` may introduce a block of declarations, and a file can have several blocks.
* **Definition:** `name = expr`. Single assignment, so a name is never redefined. Destructuring: `a, b = f(x)`.
* **Local function:** `f(x, y) = expr where x ∈ ℝ, y ∈ ℝ^3, local = …, …`
* **Import:** `sin, cos from trigonometry`
* An anonymous last expression is returned as `ret`.
* **Order doesn't matter.** The compiler sorts the definitions (def-use analysis). Separate statements with newlines or `;`.
* There are no loops, no mutation and no comments, except the descriptions in declarations. Write a loop as a sum, a set builder, a piecewise definition, or recursion.
* A newline ends a statement, except inside a block matrix, a piecewise `{`, or a `where` list continued after a trailing comma.

## Names

* Prefer single letters. Juxtaposition means multiplication, so `AB` is `A⋅B` and `2a` is `2⋅a`.
* A name can be one letter with Unicode marks (`x̄`, `ṽ`, `θ`, `𝐩`). It can be several letters when declared or defined (`damping`), and it may start with a word keyword (`sumd`).
* Symbol keywords (`π ℝ ℤ ∑ ⊂ ∈ # Δ ∇ 𝕕`) never start a name, so `πd` is `π⋅d`.
* Backticks quote any name: `` `E_data` ``, `` `x'` ``, `` `cot(α)` ``. A backtick name of the form `` `$\LaTeX$` `` typesets verbatim.
* Subscripts index things. A comma separates them, and may be left out between single letters:
  * `x_i`, `A_ij` = `A_i,j`, `A_i,*` (a row), `A_*,j` (a column)
  * `x₂`, `A₁,₂`, `xᵢ`, `aₙ`
  * `x_(i+1)`, `x_(bx_j)`
* **Indexing is 1-based.** An `index` type (`ℤ index`, `ℤ^n index`, `{ℤ} index`) holds indices that are 0-based in C++/NumPy and 1-based in MATLAB, so they can be used directly.

## Types

| Type | Syntax |
|---|---|
| scalar | `ℝ`, `ℤ` |
| vector | `ℝ^n`, `ℝ³`, `ℝ^(2n+1)`, `ℤ^n index`, `ℝ^n sparse` |
| matrix | `ℝ^(m×n)`, `ℝ^(n×n) sparse`, `ℤ^(m×n) index` |
| sequence | declare with a subscript: `x_i ∈ ℝ³` (a sequence of 3-vectors), `s_j ∈ ℝ^(n_j)`. Sequences declared with the same subscript have the same length |
| set | `{ℤ}`, `{ℤ × ℤ}` = `{ℤ²}` (pairs), `{ℝ^(3)}` (vectors; `{ℝ³}` means triples), `{ℝ^(3) × ℤ}`, `S ⊂ T` (subset), `U_i ⊂ V` (a sequence of subsets) |
| tuple | `ℝ × ℝ^3` |
| function | `f ∈ ℝ^n, ℝ → ℝ^(n×n)`, `g ∈ ∅ → ℝ`, with several results `h ∈ ℝ → ℝ, ℝ^3`, `N ∈ ℤ → {ℤ}` |
| mesh | `EdgeMesh`, `FaceMesh`, `CellMesh`. Element sets: `VertexSet`, `EdgeSet`, `FaceSet`, `CellSet`, `CellularSet`. Elements: `v ∈ V`, `i ∈ ℤ vertices` |

* Only parameters need declarations. Definitions are typed by inference.
* Dimensions are symbolic and checked: `x + y` with `x ∈ ℝ^n` and `y ∈ ℝ^m` is an error.
* A dimension that only appears in a function type is generic (`f ∈ ℝ^k → ℝ^(k×k)`).
* `D_i ∈ ℝ³ → ℝ` declares one function `D ∈ ℤ × ℝ³ → ℝ`, and `D_i(u)` calls `D(i, u)`. Sequences of functions don't exist.

## Expressions

| Category | Syntax |
|---|---|
| arithmetic | `+ - ⋅ / ÷`, juxtaposition, `±` (only in conditions), `a^b`, `a²`, `aⁿ`, `√x`, fractions `½ ⅓ ¼ …` |
| linear algebra | `Aᵀ` or `A^T`, `A⁻¹`, `A⁺` (pseudo-inverse), `A\b` = `A⁻¹b` (solve), `a⋅b`, `⟨a,b⟩`, `⟨a,b⟩_M`, `a×b`, `A:B` (Frobenius), `A∘B` = `A⊙B` (Hadamard), `A⊗B` (Kronecker) |
| norms | `‖x‖`, `‖x‖₁`, `‖x‖_∞`, `‖x‖_M`, `‖A‖_F`, `‖A‖_*`, `\|a\|` (absolute value), `\|A\|` (determinant), `\|S\|` (set size), `‖x‖²` |
| vector | `(a, b, c)` |
| block matrix | rows end with newlines or `;`; entries are separated by spaces or commas:<br>`[A I; 0 B]`, `[x_j-x_i x_k-x_i]`, `⎡ … ⎦` |
| special matrices | `I`, `I_n`, `I₃`, `0_(m×n)`, `1_n`, `𝟙_m,n`. Inside a block matrix, a block's size can be inferred; if nothing determines an `I`'s size, write `I_n` |
| element-wise definition | `A_ij = { 1 if (i,j) ∈ E` / `0 otherwise` (declare `A`'s type) |
| piecewise | `{ e₁ if cond₁` / `e₂ if cond₂` / `e₃ otherwise` (the `otherwise` is optional) |
| conditions | `< ≤ > ≥ = ≠ ∈ ∉` (also `<= >= == !=`), `(i,j) ∈ E`, `and`, `or`, `( )` |
| sum | `∑_i x_i` (the range comes from `x`'s length), `∑_(i ∈ S)`, `∑_(i,j ∈ E)`, `∑_(i=1)^n`, `∑_(i=a)^(b-1)`, `∑_(i for i < 10)`. A sum binds tightly: `∑_i a_i + b` adds `b` once. Write `∑_i (a_i + b)` to sum both |
| local defs in a sum | `∑_(e ∈ E) ‖x_i - x_j‖² where i, j = Vertices(e)`. Wrap the sum in `( … )` to end the scope |
| sets | `{1, 2}`, `{x_i for i ∈ S if c}`, `{x ∀ x ∈ S if c}`, `{i \| i ∈ S, c}`, `S ∪ T` = `S + T`, `S ∩ T`, `S - T` = `S \ T`, `∪_i U_i`, `∪_(i ∈ T) N(i)`, `S_1` (the smallest element), `min(S)`, `max(S)`, `sequence(U, s)` (appends `s`) |
| calls | `f(x, y)`, `f_i,j(x)` = `f(i, j, x)`, `θ_v,f` (subscript-only call), `sin²(x)` = `sin(x)²`, `tuple(a, b)` |
| optimization | `min_(x ∈ ℝ^n) expr`, `argmin_(…)`, `max`, `argmax`, `u, v = argmin_(u ∈ ℝ³, v ∈ ℝ) …`, then `s.t.` and one constraint per line |
| integral | `∫_a^b f 𝕕t`, `∫_[a,b] f 𝕕t` (use `𝕕`, not `∂`) |
| derivative | `∂f/∂x`, `∂/∂x f`, `∂²f/∂x²` (the Hessian of a scalar with respect to one variable), `∂²f(x)/∂x²`. The variable must be a parameter. A vector, matrix or sequence variable is flattened (`vec`). Mixed partials aren't supported. `∇ Δ` are typeset only |
| constants | `π`, `∞` |
| builtins without an import | `exp`, `log`, `ln`, `log₂` / `log_2`, `log₁₀` / `log_10`, `sqrt`, `min(a,b,…)`, `max(…)`, `tuple`, `sequence`, `vertexset` / `edgeset` / `faceset` / `cellset(…)`, `CellularSet(…)` |

## Local functions

```
f(x) = x² + 1 where x ∈ ℝ
F(n) = { 1 if n ≤ 1
         n F(n-1) otherwise where n ∈ ℤ          ← recursion; the `where` goes after the last branch
θ(i, f) = arccos((x_j-x_i)⋅(x_k-x_i)/(‖x_j-x_i‖ ‖x_k-x_i‖)) where i ∈ V, f ∈ F,
j, k = NeighborVerticesInFace(f, i)               ← local definitions, in any order
θ_i,f = …                                         ← subscript parameters: θ_1,2 or θ(1, 2)
g(x) = tuple(x, 2x) where x ∈ ℝ                   ← several results: a, b = g(3)
a(m) = … where m ∈ ℤ                              ← overloading: same name, different
a(m) = … where m ∈ ℝ                                 parameter types
h(U) = … where U ⊂ V                              ← subset, set, sequence (x_i ∈ ℝ³), or element (v ∈ V) parameters
```

A local function can use the program's parameters and definitions.

## Imports and modules

```
sin, cos, atan2 from trigonometry     ← also asin/arcsin…, sinh…, cosh, tanh, cot, sec, csc
* from trigonometry
sin as s from trigonometry            ← rename (builtin packages only)
tr, diag, vec, vec⁻¹, det, rank, inv, null, orth, svd from linearalgebra
E, f from spring(a, b, s, r)          ← spring.ihla (or .hlang) in the same directory
```

* A file module's arguments are names, matched **by position** to the parameters in the order that file declares them. All of them are required.
* Old syntax `from trigonometry: sin` is invalid.
* `vec⁻¹_x(v)` (or `inversevec(x, v)`) reshapes `v` like `x`. `U, Σ, V = svd(A)`.

## Meshes (I❤️MESH)

```
ElementSets, BoundaryMatrices, UnsignedBoundaryMatrices, IndicatorVector, NonZeros from MeshConnectivity
Faces, Vertices, VertexOneRing, NeighborVerticesInFace, OrientedVertices from Neighborhoods(M)
arccos from trigonometry
M ∈ FaceMesh
x_i ∈ ℝ³
V, E, F = ElementSets(M)                  ← CellMesh: V, E, F, C;  EdgeMesh: V, E
K(v) = 2π - ∑_(f ∈ Faces(v)) θ_v,f where v ∈ V
area(f) = ½ ‖(x_j-x_i)×(x_k-x_i)‖ where f ∈ F, i, j, k = OrientedVertices(f)
θ(i, f) = arccos((x_j-x_i)⋅(x_k-x_i)/(‖x_j-x_i‖ ‖x_k-x_i‖)) where i ∈ V, f ∈ F,
j, k = NeighborVerticesInFace(f, i)
```

* Element sets of different dimensions, and of different meshes, are different types. Passing the wrong one is a compile-time error.
* Accessors (overloaded by dimension, for an element, a set of elements, or a `CellularSet`): `Vertices`, `Edges`, `Faces`, `Cells`.
* `Neighborhoods(M)` (`FaceMesh`) also provides `VertexOneRing`, `EdgeIndex(i,j)`, `FaceIndex(i,j,k)`, `NeighborVerticesInFace(f,v)` (the other two vertices, counterclockwise), `NextVerticeInFace`, `OrientedVertices(f)`, `OppositeVertices`, `OppositeFaces`, `OrientedOppositeFaces(i,j)`, `Diamond(e)`.
* The other modules are `FundamentalMeshAccessors`, `PolygonNeighborhoods`, `TetrahderonNeighborhoods` (sic) and `FundamentalTetrahedronAccessors` (`CellMesh`), and `PointCloudNeighborhoods` (`EdgeMesh`).
* `BoundaryMatrices(M)` gives the signed `∂⁰`, `∂¹`(, `∂²`). Write them as backtick names, e.g. `` `∂⁰`, `∂¹` = BoundaryMatrices(M) ``.
* `IndicatorVector(S)` and `NonZeros(x)` convert between a set and a sparse vector.

## Common mistakes

* Every parameter needs a declaration, including integers used only as sizes (`n ∈ ℤ`).
* Write `x_i ∈ ℝ³` for per-vertex data, not `x ∈ ℝ^(n×3)`, when using it as `x_i`.
* `∑_i a_i + b` adds `b` once. Parenthesize the summand to sum it.
* Juxtaposed multi-letter names are ambiguous. Use spaces or backticks.
* Use `𝕕t` in integrals, `∂` in derivatives. Use `|S|` for set size, `‖x‖` for a norm.
* Comment lines don't exist. Only a declaration may carry a `: description`.
* Not working yet, so avoid them:
  * `#x`
  * `with initial`
  * `+=`
  * `f[x] = …`
  * the constant `e` (use `exp(1)`)
  * renaming (`as`) symbols from file modules
  * code generation for `∇` and `Δ`
* Generated code needs NumPy/SciPy (and autograd for derivatives), or Eigen (autodiff for derivatives, LBFGSpp for optimization). MATLAB output generates no code for derivatives or `svd`, and its mesh support is less tested.
