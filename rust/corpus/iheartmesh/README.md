# I❤️MESH paper examples

The ten example programs of the I❤️MESH paper's supplemental material
(<https://iheartla.github.io/iheartmesh/supplemental_material.zip>,
`examples/<name>/<name>.hlang`), fetched on 2026-11-02. The supplement also has
the C++ (`heartlib.h`) that the paper's compiler generated for each, which is
a reference for features the current compilers lack:

- `mesh_deformation`, `mesh_parameterization`: derivatives (`∂e/∂x`,
  `∂²S_i(x)/∂x²`), generated with the autodiff library in C++.
- `geodesic_distance`: `sequence(U, next)`, appending to a sequence of sets.
- `point_cloud`: `m_i,* = d_i`, rows taken from a set of vectors (`m.row(i-1) = d[i-1]`).

The Python compiler on `mesh` accepts all of them, but its NumPy output for
those three features doesn't work. The Rust compiler rejects them.
