# I❤️MESH paper examples

The ten example programs of the I❤️MESH paper's supplemental material
(<https://iheartla.github.io/iheartmesh/supplemental_material.zip>,
`examples/<name>/<name>.hlang`), fetched on 2026-11-02. The supplement also has
the C++ (`heartlib.h`) that the paper's compiler generated for each.

Both compilers compile all ten. Four use features checked nowhere else:

- `geodesic_distance`: `sequence(U, next)`, which appends to a copy of a
  sequence of sets, and unions over a subscript (`∪_i U_i`, `∪_(i=a)^b U_i`).
- `point_cloud`: a set of vectors (`{x_v - p̄ for v ∈ N}`), a matrix defined
  row by row from it (`m_i,* = d_i`, in sorted order), and `svd`.
- `mesh_deformation`, `mesh_parameterization`: gradients and Hessians
  (`∂e/∂x`, `∂²S_i(x)/∂x²`) with respect to a sequence of vectors, flattened.
  C++ uses the autodiff library, and NumPy uses autograd.

`rust/tools/paper_check.py <supplement>` runs the Rust compiler's C++ and
NumPy output for these four on small meshes and compares every value with the
paper's `heartlib.h` (normals up to the sign SVD leaves free). The Python
compiler's output agrees too.
