#!/usr/bin/env python

from __future__ import print_function, division

from numpy import *

def make_cylinder( num_slices, num_stacks ):
    '''
    Make a cylinder whose axis is (0,0,0) to (0,0,1) and radius is 1. There are no end caps.
    
    The parameters are:
        num_slices: an integer >= 3 that determines how many vertices there should be around the circular cross section of the cylinder.
        num_stacks: an integer >= 2 that determines how many vertices there should be along the axis of the cylinder.
    
    Returns an object with the following properties:
        Three floating point arrays containing:
            v: positions (xyz)
            vt: uvs (uv)
            vn: normals (xyz)
        Three indexing arrays of faces containing:
            fv: [ face 0 vertex 0's position index, face 0 vertex 1's position index, face 0 vertex 2's position index ], ...
            fvt: [ face 0 vertex 0's uv index, face 0 vertex 1's uv index, face 0 vertex 2's uv index ], ...
            fvn: [ face 0 vertex 0's normal index, face 0 vertex 1's normal index, face 0 vertex 2's normal index ], ...
    
    Note that indices are 0-indexed.
    '''
    
    assert num_slices >= 3
    assert int( num_slices ) == num_slices
    
    assert num_stacks >= 1
    assert int( num_stacks ) == num_stacks
    
    print( 'make_cylinder():' )
    print( '\tnum_slices:', num_slices )
    print( '\tnum_stacks:', num_stacks )
    
    ## Let's use the following shape for UVs.
    ## Every slice of the cylinder will repeat this shape (1D).
    ## 0 1
    ## | |
    ## 2 3
    ## ...
    
    N = num_slices
    ## We want N thetas around the circle from [0,2*pi);
    ## for texture coordinates we want N+1 samples from [0,1].
    around_ts = linspace( 0, 1, N+1 )
    ## Parameter around the circle from [0,2*pi).
    thetas = 2*pi*around_ts[:-1]
    assert len( thetas ) == N
    circle = array([ cos(thetas), sin(thetas) ]).T
    
    ## Parameter along the cylinder
    M = num_stacks
    ## One stack is a special case.
    stack_zs = linspace( 0, 1, M )
    stack_vs = linspace( 0, 1.0, M )
    assert len( stack_zs ) == M
    assert len( stack_vs ) == M
    
    ## There will be `num_stacks` copies of the circle.
    ## Therefore, there will be num_stacks*N vertices.
    ## There is one additional texture coordinate per circle, because while
    ## the last triangle around will share positions with the first triangle around,
    ## the last texture coordinate won't.
    vs = zeros( ( num_stacks*N, 3 ) )
    vts = zeros( ( num_stacks*(N+1), 2 ) )
    for i, ( z, v ) in enumerate( zip( stack_zs, stack_vs ) ):
        ## Every N vertices are the circles.
        vs[ i*N : (i+1)*N ] = append( circle, z*ones( ( N, 1 ) ), axis = 1 )
        vts[ i*(N+1) : (i+1)*(N+1) ] = append( around_ts[:,newaxis], v*ones( ( N+1, 1 ) ), axis = 1 )
    
    ## Vertex normals don't need two copies of the circle, so only len(circle) vertices.
    vns = zeros( ( N, 3 ) )
    ## The first N normals are the outward normals.
    vns[:] = append( circle, zeros( ( N, 1 ) ), axis = 1 )
    
    
    ### Stitch together faces.
    ### For each vertex in the circle, make a quad connecting the top and bottom to the next vertex around the circle's top and bottom.
    fv = []
    fvn = []
    fvt = []
    
    ## Add two triangles to form a quad.
    def add_quad_triangles_to_list( the_quad, the_list ):
        the_list.append( ( the_quad[0], the_quad[1], the_quad[2] ) )
        the_list.append( ( the_quad[0], the_quad[2], the_quad[3] ) )
    for stack in range( num_stacks-1 ):
        for i in range( N ):
            ## The face will be two triangles made from the quad: top, bottom, bottom+1, top+1
            ## The relevant vs indices are:
            fvi = [ stack*N + i, stack*N + (i+1)%N, (stack+1)*N + (i+1)%N, (stack+1)*N + i ]
            ## The relevant vns indices are:
            fvni = [ i, i, (i+1)%N, (i+1)%N ]
            ## The relevant vts indices are similar to the fvi indices, but with a different modulus:
            fvti = [ stack*(N+1) + i, (stack+1)*(N+1) + i, (stack+1)*(N+1) + (i+1)%(N+1), stack*(N+1) + (i+1)%(N+1) ]
            
            add_quad_triangles_to_list( fvi, fv )
            add_quad_triangles_to_list( fvni, fvn )
            add_quad_triangles_to_list( fvti, fvt )
    
    class Struct( object ): pass
    result = Struct()
    result.v = asfarray(vs)
    result.vt = asfarray(vts)
    result.vn = asfarray(vns)
    
    result.fv = asarray(fv)
    result.fvt = asarray(fvt)
    result.fvn = asarray(fvn)
    
    result.extra = [ 'num_slices: %s' % num_slices, 'num_stacks: %s' % num_stacks ]
    
    return result

def save_obj( mesh, filename, clobber = False ):
    import os, sys
    
    assert len( mesh.fv ) == len( mesh.fvt )
    assert len( mesh.fv ) == len( mesh.fvn )
    
    if os.path.exists( filename ) and not clobber:
        print( "ERROR: File exists; save_obj() will not clobber:", filename )
        return
    
    with open( filename, 'w' ) as out:
        print( '# Saved by:', *sys.argv, file = out )
        
        for line in mesh.extra:
            print( '#', line, file = out )
        
        print( '', file = out )
        for v in mesh.v:
            print( 'v', *v, file = out )
        
        print( '', file = out )
        for vt in mesh.vt:
            print( 'vt', *vt, file = out )
        
        print( '', file = out )
        for vn in mesh.vn:
            print( 'vn', *vn, file = out )
        
        print( '', file = out )
        for fvis, fvtis, fvnis in zip( mesh.fv, mesh.fvt, mesh.fvn ):
            print( 'f', end = '', file = out )
            
            ## The face index arrays must agree on the number of vertices in the face.
            assert len( fvis ) == len( fvtis )
            assert len( fvis ) == len( fvnis )
            
            for fvi, fvti, fvni in zip( fvis, fvtis, fvnis ):
                print( ' ', end = '', file = out )
                ## OBJ's are 1-indexed
                print( fvi+1, fvti+1, fvni+1, sep = '/', end = '', file = out )
            
            print( '', file = out )
    
    print( "Saved:", filename )

def load_obj( filename ):
    V = []
    F = []
    for line in open( filename ):
        sline = line.split()
        if len( sline ) == 0: continue
        elif sline[0] == 'v': V.append( tuple([ float(v) for v in sline[1:] ]) )
        elif sline[0] == 'f':
            # Simplest, doesn't handle negative indices.
            # F.append( [ int(c.split('/')[0])-1 for c in sline[1:] ] )
            
            face = []
            for c in sline[1:]:
                vi = int(c.split('/')[0])
                if vi > 0: vi -= 1
                elif vi < 0: vi += len(V)
                else: raise RuntimeError("Vertex index can't be 0.")
                face.append( vi )
            F.append( face )
    
    class Struct( object ): pass
    result = Struct()
    result.v = asfarray(V)
    result.vt = zeros(V.shape)
    result.vn = zeros(V.shape)
    result.fv = asarray(F)
    result.fvt = asarray(F)
    result.fvn = asarray(F)
    result.extra = [ filename ]
    return result

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser( description = 'Save a cylinder as an OBJ.' )
    parser.add_argument( 'num_slices', type = int, help = 'The number of vertices around the cylinder.' )
    ## Optional positional arguments: http://stackoverflow.com/questions/4480075/argparse-optional-positional-arguments
    parser.add_argument( 'num_stacks', type = int, default = 2, nargs='?', help = 'The number of vertices along the axis of the cylinder (default 2).' )
    parser.add_argument( 'filename', type = str, help = 'The path to save the resulting OBJ.' )
    args = parser.parse_args()
    
    cyl = make_cylinder( args.num_slices, args.num_stacks )
    save_obj( cyl, args.filename )
