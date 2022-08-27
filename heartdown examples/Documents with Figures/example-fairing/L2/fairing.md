---
full_paper: False
---
# Surface Fairing
❤: fairing

Surface fairing given boundary constraints depends on the order of the Laplacian. A simple <span class="def">graph Laplacian $L$</span> can be written in terms of the adjacency matrix $A$ and the <span class="def">degree matrix $D$</span>. Those matrices can be derived purely from the <span class="def">the edges of the mesh $E$</span>.
```iheartla
A_ij = { 1 if (i,j) ∈ E
         1 if (j,i) ∈ E
         0 otherwise
D_ii = ∑_j A_ij
L = D⁻¹ ( D - A )
where
E ∈ { ℤ×ℤ } index
A ∈ ℝ^(n×n): The adjacency matrix
n ∈ ℤ: The number of mesh vertices
```

We then solve a system of equations $Lx = 0$ for free vertices to obtain the fair surface. We can write <span class="def">the fair mesh vertices $V'$</span> directly given <span class="def">boundary constraints provided as a binary vector $B$ with 1's for boundary vertices</span>, a large scalar <span class="def:w">constraint weight</span> ❤w=10^6❤, and <span class="def">3D vertices for the constrained mesh $V$</span>:
```iheartla
diag from linearalgebra

`V'` = (L² + w diag(B))⁻¹ (w diag(B) V)
where
B ∈ ℤ^n
V ∈ ℝ^(n × 3)
```

<figure>
```python
from lib import *
import make_cylinder

# Load cylinder with n vertices
mesh = make_cylinder.make_cylinder( 10, 10 )
make_cylinder.save_obj( mesh, 'input.obj', clobber = True )
V = mesh.v
F = mesh.fv
n = len(V)

# Extract the mesh edges
edges = set()
for face in F:
    for fvi in range(3):
        vi,vj = face[fvi], face[(fvi+1)%3]
        edges.add( ( min(vi,vj), max(vi,vj) ) )

# The constraint vector is all vertices with z < 1/4 or z > 3/4
B = np.zeros( n, dtype = int )
B[ V[:,2] < 1/4 ] = 1
B[ V[:,2] > 3/4 ] = 1

# Rotate the top around the z axis by 90 degrees.
R = np.array([[ 1, 0, 0 ],
              [ 0, 0, 1 ],
              [ 0, -1, 0 ]])
for vi in np.where(V[:,2] > 3/4)[0]: V[vi] = R @ V[vi] + (0,1,2)

# Solve for new positions
result = fairing( E = edges, n = n, B = B, V = V )
mesh.v = result.V_apostrophe
make_cylinder.save_obj( mesh, 'solved.obj', clobber = True )

import plotly.graph_objects as go
fig = go.Figure(data=[go.Mesh3d(
    x=mesh.v[:,0], y=mesh.v[:,1], z=mesh.v[:,2],
    i=mesh.fv[:,0], j=mesh.fv[:,1], k=mesh.fv[:,2]
    )])
fig.update_layout( scene_camera={'eye':dict(x=2.5,y=0,z=0), 'up':dict(x=0,y=0,z=1)}, margin=dict(t=0, r=0, l=0, b=0) )
fig.write_html( 'cylinder.html' )
```
<img src="cylinder.html" alt="a fair cylinder surface">
<figcaption>Fairing the middle half of a cylinder.</figcaption>
</figure>
