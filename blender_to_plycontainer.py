import bpy
import bmesh
import numpy as np
from .plyhandler.get_surfacemap_from_ply import plycontainer_from_arrays, export_plyfile
import itertools as it

def save( objects, filepath, global_matrix, use_ascii ):
                                #use_normals, use_uv_coords, use_colors ):
    all_vertices = []
    all_edges = []
    all_faces = []
    for blender_object in objects:
        vertex_index_offset = len( all_vertices )
        vertices, edges, faces = get_vertices_edges_faces_from_blenderobject( \
                                                blender_object, global_matrix )
        all_vertices.extend( vertices )
        for e in edges:
            all_edges.append( tuple( v + vertex_index_offset for v in e ) )
        for f in faces:
            all_faces.append( tuple( v + vertex_index_offset for v in f ) )
    save_meshdata_to_ply( filepath, all_vertices, all_edges, all_faces, \
                                                use_ascii )


def save_meshdata_to_ply( filepath, vertices, edges, faces, use_ascii ):
    vertexpipeline = ( \
                        ( b"float", b"x" ), \
                        ( b"float", b"y" ), \
                        ( b"float", b"z" ), \
                        )
    facespipeline = ((b"list", b"uchar", b"uint", b"vertex_indices" ), )
    vert = np.array( vertices ).T
    faces = ( np.array( faces ), )
    myobj = plycontainer_from_arrays( [\
                        ("vertex", vertexpipeline, vert ), \
                        ("faces", facespipeline, faces ), \
                        ])
    myformat = "ascii" if use_ascii else "binary_little_endian"
                #theoreticly "binary_big_endian" is also possible
    export_plyfile( filepath , myobj, myformat )


def get_vertices_edges_faces_from_blenderobject( blender_object, global_matrix):
    """
    :todo: use of global_matrix
    """
    mybmesh = bmesh.new()
    mybmesh.from_mesh( blender_object.data )
    mybmesh.faces.ensure_lookup_table()
    mybmesh.verts.ensure_lookup_table()
    mybmesh.edges.ensure_lookup_table()
    edges = [tuple( v.index for v in e.verts ) for e in mybmesh.edges ]
    faces = [tuple( v.index for v in f.verts ) for f in mybmesh.faces ]
    # space of v.co will be freed and reused later. So to ensure 
    # vertexcoordinates stay the same the coordinates will be 'exported'
    vertices = [ np.array(v.co) for v in mybmesh.verts ] #v.co 
    mybmesh.free()
    return vertices, edges, faces
