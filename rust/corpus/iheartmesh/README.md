# I❤️MESH paper examples

The ten example programs of the I❤️MESH paper's supplemental material
(<https://iheartla.github.io/iheartmesh/supplemental_material.zip>,
`examples/<name>/<name>.hlang`), fetched on 2026-11-02. The supplement also has
the C++ (`heartlib.h`) that the paper's compiler generated for each.

The Python compiler on `mesh` compiles all ten. Its C++ output for the four
examples below gives the same values as the paper's `heartlib.h` on the same
meshes (energies, gradients, Hessians, sets and normals), and so does its NumPy
output (normals up to the sign SVD leaves free).

The Rust compiler doesn't support these four yet:

- `mesh_deformation`, `mesh_parameterization`: derivatives (`∂e/∂x`,
  `∂²S_i(x)/∂x²`). C++ uses the autodiff library, and Python's NumPy output
  uses autograd. Both differentiate with respect to x flattened.
- `geodesic_distance`: `sequence(U, next)`, which appends to a copy of a
  sequence of sets.
- `point_cloud`: `m_i,* = d_i`, the rows of a matrix taken from a set of
  vectors, in sorted order.
