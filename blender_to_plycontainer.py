import bmesh
import numpy as np
#from .plyhandler.get_surfacemap_from_ply import plycontainer_from_arrays, export_plyfile
import itertools as it
import logging
logger = logging.getLogger( __name__ )

# for documentation:
from typing import Iterator
_vertices = Iterator[tuple[float,float,float]]
_edges = Iterator[tuple[int,int]]
_faces = Iterator[list[int]]

#mainpart

RIGHTUP, LEFTUP, LEFTDOWN, RIGHTDOWN \
            = "rightup", "leftup", "leftdown", "rightdown"

from .exceptions import SurfaceNotCorrectInitiated

def save( blenderobject, filepath, global_matrix, use_ascii ):
    from .custom_properties import get_all_partialsurfaceinfo
    from .surfacedivide import RIGHTUP_CORNER, LEFTUP_CORNER, \
                                LEFTDOWN_CORNER, RIGHTDOWN_CORNER

    vertices, edges, faces = get_vertices_edges_faces_from_blenderobject( \
                                            blenderobject, global_matrix )
    infodict_all = get_all_partialsurfaceinfo( blenderobject )
    infodict_all = list( infodict_all )
    cornlist =(RIGHTUP_CORNER, LEFTUP_CORNER, LEFTDOWN_CORNER,RIGHTDOWN_CORNER)
    cornerdata = tuple( \
                        tuple(inf[ corn ] for corn in cornlist ) \
                        for inf in infodict_all \
                        )
    surfacenames = tuple( infodict[ "Name" ] for infodict in infodict_all )
    extra = {}
    if "Vertexgroup" in infodict_all[0]:
        extra["partialsurface_vertices"] = [info[ "Vertexgroup" ] \
                                            for info in infodict_all ]


    vertices = list( vertices )
    faces = list( faces )
    from . import plysurfacehandler
    vertices_asdf = [ plysurfacehandler.vertex( *v ) for v in vertices ]
    faces_asdf = [ plysurfacehandler.face( f ) for f in faces ]
    surfaces_asdf = []
    qqq = { RIGHTUP_CORNER: "rightup", LEFTUP_CORNER: "leftup", \
            LEFTDOWN_CORNER:"leftdown", RIGHTDOWN_CORNER: "rightdown", \
            "Name": "surfacename", "Vertexgroup": "vertexlist" }
    for info in infodict_all:
        inputdict = { qqq[a]: b for a,b in info.items() if a in qqq }
        surfaces_asdf.append( plysurfacehandler.surface(**inputdict, \
                                faceindices=faces ))
    qwer = plysurfacehandler.plysurfacehandler( vertices_asdf, faces_asdf, surfaces_asdf )
    qwer.save_to_file( filepath, use_ascii=use_ascii )



def get_cornerdata( object ):
    extras = dict()
    if "_subrectanglesurfaces" in object.data:
        tmp = object.data[ "_subrectanglesurfaces" ]
        #extras["surfacenames"] = tmp
        tmpsurfacenames = tmp
        create_filter = lambda name: lambda vgroup: name == vgroup.name
        #extras["used_vertices"] = [\
        used_vertices = [\
                filter( create_filter(surf), iter(object.vertex_groups)) \
                for surf in tmp ]
        del( tmp, create_filter )
    else:
        tmpsurfacenames = (None,)
    cornerdata = []
    targetobject = object
    from .custom_properties import get_all_partialsurfaceinfo
    from .surfacedivide import RIGHTUP_CORNER, LEFTUP_CORNER, \
                                LEFTDOWN_CORNER, RIGHTDOWN_CORNER
    for partialsurface_info in get_all_partialsurfaceinfo( targetobject ):
        name = partialsurface_info["Name"]
        rightup = partialsurface_info[ RIGHTUP_CORNER ]
        leftup = partialsurface_info[ LEFTUP_CORNER ]
        leftdown = partialsurface_info[ LEFTDOWN_CORNER ]
        rightdown = partialsurface_info[ RIGHTDOWN_CORNER ]
    for groupname in tmpsurfacenames:
        if groupname is not None:
            rightup, leftup, leftdown, rightdown \
                    = [ "_".join((groupname, direction)) \
                    for direction in (RIGHTUP, LEFTUP, LEFTDOWN, RIGHTDOWN)]
        else:
            rightup, leftup, leftdown, rightdown \
                    = RIGHTUP, LEFTUP, LEFTDOWN, RIGHTDOWN
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
    if tmpsurfacenames == (None,):
        cornerdata = cornerdata[0]
    return cornerdata, tmpsurfacenames

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
