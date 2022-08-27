# Mesh Smoothing
❤: MeshSmoothing

We consider the problem of smoothing <span class="def">a mesh with vertices $V$ and edges $S$</span>. We can express the <span class="def">smoothed vertex positions $U$</span> as a least squares problem with a data term and a smoothness term:

``` iheartla
trace from linearalgebra

min_( U ∈ ℝ^(n×3) ) `E_\text{data}`(U) + λ `E_\text{smoothness}`(U)
where
V ∈ ℝ^(n×3): The vertices of the mesh
L ∈ ℝ^(n×n) sparse: The Laplacian matrix
λ ∈ ℝ
```

where  ❤`E_\text{data}`(U) = ‖ U - V ‖² where U ∈ ℝ^(n×3)❤ <span class="def:E_\text{data}">measures the change in vertex values,</span> ❤`E_\text{smoothness}`(U) = trace( Uᵀ L U ) where U ∈ ℝ^(n×3)❤ <span class="def:E_\text{smoothness}">measures the Laplacian smoothness,</span> and the scalar <span class="def">$λ$ balances the two terms.</span> Here, <span class="def">$L$ is the cotangent Laplacian matrix,</span> which is different from the $\proselabel{ImageTools}{L}$ in Section 2.

<figure>
```python
import make_cylinder, igl, numpy
from lib import *

# Create a cylinder
mesh = make_cylinder.make_cylinder( 10, 10 )
V = mesh.v * [[1,1,2]]
F = mesh.fv
L = -igl.cotmatrix(V,F)

# Add xy noise
numpy.random.seed(0)
V[:,:2] += .1 * numpy.random.randn( len(V), 2 ).clip(-1,1)

# A row of plots
from plotly.subplots import make_subplots
import plotly.graph_objects as go
spec = {'type': 'surface'}
fig = make_subplots( rows=2, cols=2, specs=[[spec,spec],[spec,spec]], vertical_spacing = 0 )

# The input data on the left
fig.add_trace( go.Mesh3d(
        x=V[:,0], y=V[:,1], z=V[:,2],
        i=mesh.fv[:,0], j=mesh.fv[:,1], k=mesh.fv[:,2]
        ), 1, 1 )

for offset, λ in enumerate( ( .1, 1, 10 ) ):
    # Smooth the mesh
    U = MeshSmoothing( V, L, λ ).U
    
    # Plot it
    fig.add_trace( go.Mesh3d(
        x=U[:,0], y=U[:,1], z=U[:,2],
        i=mesh.fv[:,0], j=mesh.fv[:,1], k=mesh.fv[:,2]
        ), 1+(1+offset)//2, 1+(1+offset)%2 )

fig.update_layout( margin = dict(r=0, l=0, b=0, t=0) )
fig.update_scenes( aspectmode='cube', xaxis = dict(range=[-1.1,1.1],), yaxis = dict(range=[-1.1,1.1],), zaxis = dict(range=[-.1,2.1],) )
fig.write_html( 'smoothed.html' )
```
<img src="smoothed.html" alt="A noisy cylinder and increasingly smoothed versions.">
<figcaption>Clockwise from upper-left: The input noisy surface, the surface smoothed with $λ=1, 10, 100$.</figcaption>
</figure>
