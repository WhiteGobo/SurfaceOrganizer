import bpy
import bmesh
import numpy as np
from .plyhandler.get_surfacemap_from_ply import plycontainer_from_arrays, export_plyfile
import itertools as it
import logging
logger = logging.getLogger( __name__ )

RIGHTUP, LEFTUP, LEFTDOWN, RIGHTDOWN \
            = "rightup", "leftup", "leftdown", "rightdown"

class SurfaceNotCorrectInitiated( Exception ):
    pass

def save( object, filepath, global_matrix, use_ascii ):
    extras = dict()

    if "_subrectanglesurfaces" in object.data:
        tmp = object.data[ "_subrectanglesurfaces" ]
        extras["surfacenames"] = tmp
        create_filter = lambda name: lambda vgroup: name == vgroup.name
        extras["used_vertices"] = [\
                filter( create_filter(surf), iter(object.vertex_groups)) \
                for surf in tmp ]
        del( tmp, create_filter )
    if "surfacenames" in extras:
        tmpsurfacenames = extras["surfacenames"]
    else:
        tmpsurfacenames = (None,)
    cornerdata = []
    for groupname in tmpsurfacenames:
        if groupname is not None:
            rightup, leftup, leftdown, rightdown \
                    = [ "_".join((groupname, direction)) \
                    for direction in (RIGHTUP, LEFTUP, LEFTDOWN, RIGHTDOWN)]
        else:
            rightup, leftup, leftdown, rightdown \
                    = RIGHTUP, LEFTUP, LEFTDOWN, RIGHTDOWN
        vertices, edges, faces = get_vertices_edges_faces_from_blenderobject( \
                                            object, global_matrix )
        try:
            rightup, = get_vertices_of_vertexgroup( object, rightup )
            leftup, = get_vertices_of_vertexgroup( object, leftup )
            rightdown, = get_vertices_of_vertexgroup( object, rightdown )
            leftdown, = get_vertices_of_vertexgroup( object, leftdown )
        except KeyError as err:
            raise SurfaceNotCorrectInitiated( f"Tried to export Surface from "\
                                +"Object with not correct initiated "\
                                +f"surfacedata. Object: {object}" ) from err
        cornerdata.append((leftup, rightup, rightdown, leftdown))
    if "surfacenames" not in extras:
        cornerdata = cornerdata[0]

    save_meshdata_to_ply( filepath, vertices, edges, faces, \
                                        cornerdata,\
                                        use_ascii, **extras )

def get_vertices_of_vertexgroup( object, groupname ):
    groupindex = object.vertex_groups[ groupname ].index
    for v in object.data.vertices:
        for g in v.groups:
            if g.group == groupindex:
                yield v.index


def save_meshdata_to_ply( filepath, vertices, edges, faces, \
                            cornerdata, use_ascii, surfacenames = (None,), \
                            used_vertices = (None,)):
    surfacenames = list( surfacenames ) #[(ru(rightup), lu, ld, rd), ...]

    vertexpipeline = ( ( b"float", b"x" ), ( b"float", b"y" ), ( b"float",b"z"))
    facespipeline = ((b"list", b"uchar", b"uint", b"vertex_indices" ), )
    vert = np.array( vertices ).T
    faces = ( np.array( faces ), )

    #leftup, rightup, rightdown, leftdown = cornerdata
    if surfacenames[0] == None and len(surfacenames) == 1:
        borderpipeline = ( (b"uint", b"rightup"), (b"uint", b"leftup"), \
                            (b"uint", b"leftdown"), (b"uint", b"rightdown") )
        borderindices = np.array( cornerdata ).reshape((4,1))
    elif all( type(n)==str for n in surfacenames ) \
                            and len( cornerdata ) == len( surfacenames ):
        borderpipeline = ( (b"list", b"uchar", b"uchar", b"surfacename" ), \
                            (b"uint", b"rightup"), (b"uint", b"leftup"), \
                            (b"uint", b"leftdown"), (b"uint", b"rightdown") )
        borderindices = np.array( cornerdata ).reshape((4,len( surfacenames )))
        borderindices = [ surfacenames, *borderindices ]
    else:
        raise SurfaceNotCorrectInitiated("surfacenames must be iterablestrings",
                all( type(n)==str for n in surfacenames ), cornerdata )

    myobj = plycontainer_from_arrays( [\
                        ("vertex", vertexpipeline, vert ), \
                        ("faces", facespipeline, faces ), \
                        ("cornerrectangle", borderpipeline, borderindices ), \
                        ])
    #theoreticly "binary_big_endian" is also possible
    myformat = "ascii" if use_ascii else "binary_little_endian" 
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
