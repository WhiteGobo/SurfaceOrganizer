import bmesh
import numpy as np
#from .plyhandler.get_surfacemap_from_ply import plycontainer_from_arrays, export_plyfile
import itertools as it
import logging
logger = logging.getLogger( __name__ )
from . import plysurfacehandler

# for documentation:
from typing import Iterator
_vertices = Iterator[tuple[float,float,float]]
_edges = Iterator[tuple[int,int]]
_faces = Iterator[list[int]]

#mainpart

from .surfacedivide import RIGHTUP_CORNER, LEFTUP_CORNER, \
                                LEFTDOWN_CORNER, RIGHTDOWN_CORNER
RIGHTUP, LEFTUP, LEFTDOWN, RIGHTDOWN \
            = "rightup", "leftup", "leftdown", "rightdown"
infodict_to_plysurfaceshandler = { RIGHTUP_CORNER: "rightup", \
            LEFTUP_CORNER: "leftup", \
            LEFTDOWN_CORNER:"leftdown", RIGHTDOWN_CORNER: "rightdown", \
            "Name": "surfacename", "Vertexgroup": "vertexlist" }

from .exceptions import SurfaceNotCorrectInitiated

def save( blenderobject, filepath, global_matrix, use_ascii ):
    from .custom_properties import get_all_partialsurfaceinfo
    from .surfacedivide import RIGHTUP_CORNER, LEFTUP_CORNER, \
                                LEFTDOWN_CORNER, RIGHTDOWN_CORNER

    vertices, edges, faces = get_vertices_edges_faces_from_blenderobject( \
                                            blenderobject, global_matrix )
    infodict_all = get_all_partialsurfaceinfo( blenderobject )

    surfaces_info = [{ infodict_to_plysurfaceshandler[ a ]:b \
                        for a, b in infodict.items() \
                        if a in infodict_to_plysurfaceshandler.keys() }
                        for infodict in infodict_all ]
    save_data( filepath, vertices, faces, surfaces_info, use_ascii )



def save_data( filepath, vertices, faces, surfaces_info:Iterator[dict], \
                                                                use_ascii ):
    vertices = list( vertices )
    faces = list( faces )
    vertices_asdf = [ plysurfacehandler.vertex( *v ) for v in vertices ]
    faces_asdf = [ plysurfacehandler.face( f ) for f in faces ]
    surfaces_asdf = []
    #qqq = infodict_to_plysurfacehandler
    for info in surfaces_info:
        #inputdict = { qqq[a]: b for a,b in info.items() if a in qqq }
        surfaces_asdf.append( plysurfacehandler.surface( **info, \
                                faceindices=faces ))
    qwer = plysurfacehandler.plysurfacehandler( vertices_asdf, faces_asdf, surfaces_asdf )
    qwer.save_to_file( filepath, use_ascii=use_ascii )


def get_vertices_of_vertexgroup( object, groupname ):
    groupindex = object.vertex_groups[ groupname ].index
    for v in object.data.vertices:
        for g in v.groups:
            if g.group == groupindex:
                yield v.index


def _pack_partialsurfaceinfo( surfacenames, cornerdata ):
    borderpipeline = [ ("uint", "rightup"), ("uint", "leftup"), \
                            ("uint", "leftdown"), ("uint", "rightdown") ]
    borderindices = list( 
            np.array( cornerdata ).T.reshape((4, len(surfacenames))) )
    if surfacenames != (None,):
        borderpipeline.append( ("list", "uchar", "uchar", "surfacename" ) )
        sn = [ bytes(name, encoding="utf8") for name in surfacenames ]
        borderindices.append( sn )
    return ("cornerrectangle", tuple(borderpipeline), tuple(borderindices) )


def get_vertices_edges_faces_from_blenderobject( blender_object, \
                        global_matrix) -> tuple[_vertices,_edges,_faces]:
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
