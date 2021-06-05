import bpy
import bmesh
from collections import Counter
import itertools

def get_border_indexlist( targetobject, startcorner="rightup" ):
    partsurf_info = _get_active_partial_surface_info( targetobject )
    startcorner_dict = { \
                "rightup": ( partsurf_info.rightup_corner, 0 ), \
                "leftup": ( partsurf_info.rightup_corner, 1 ), \
                "leftdown": ( partsurf_info.rightup_corner, 2 ), \
                "rightdown": ( partsurf_info.rightup_corner, 3 ), \
                }
    try:
        startindex, bi = startcorner_dict[ startcorner ]
    except KeyError as err:
        raise KeyError( f"startcorner must be one of {startcorner}" ) from err
    up = partsurf_info["up_border_indexlist"]
    left = partsurf_info["left_border_indexlist"]
    down = partsurf_info["down_border_indexlist"]
    right = partsurf_info["right_border_indexlist"]
    borderlist = (up, left, down, right)[ bi: ] + (up, left, down, right)[ :bi ]
    last_vertex_index = startindex
    for subborder in borderlist:
        if last_vertex_index == subborder[-1]:
            subborder = list( reversed( subborder ) )
        last_vertex_index = subborder[-1]
        for i in subborder[:-1]:
            yield i


def _get_active_partial_surface_info( targetobject ):
    allinfo = targetobject.partial_surface_information
    index = allinfo.active_surface_index 
    return allinfo.partial_surface_info[ index ]

def get_selected_vertices( targetobject ):
    #assert targetobject.mode == "OBJECT", "targetobject must be in objectmode"
    mode = targetobject.mode
    cond = (mode != 'OBJECT')
    if cond:
        #ensure active_object == active_layer.active_object
        bpy.ops.object.mode_set( mode='OBJECT' )

    for v in targetobject.data.vertices:
        if v.select:
            yield v.index

    if cond:
        bpy.ops.object.mode_set( mode=mode )

def get_selected_edges_as_indextuples( targetobject ):
    """
    scene containing targetobject must be in edge selectmode
    scene.tool_settings.mesh_select_mode == (False, True, False)
    """
    #is_edgemode = (scene.tool_settings.mesh_select_mode ==(False, True, False))
    mode = targetobject.mode
    if mode == 'OBJECT':
        for e in targetobject.data.edges:
            if e.select:
                yield ( e.vertices[0], e.vertices[1] )
    elif mode == 'EDIT':
        helpmesh = bmesh.from_edit_mesh( targetobject.data )
        for e in helpmesh.edges:
            if e.select:
                yield ( e.verts[0].index, e.verts[1].index )


class NotThreadLikeEdgesError( Exception ):
    pass
def selected_edges_is_threadlike( targetobject ):

    edges = list( get_selected_edges_as_indextuples( targetobject ) )
    edgecounter = Counter( itertools.chain(*edges) )
    return 2 == len( [ v for v, number in edgecounter.items() if number == 1 ] )

def get_thread_from_selected_edges( targetobject ):
    edges = list( get_selected_edges_as_indextuples( targetobject ) )
    edgecounter = Counter( itertools.chain(*edges) )
    try:
        start, end = [ v for v, number in edgecounter.items() if number == 1 ]
    except ValueError as err:
        #This happens if selected edges doesnt exactly represent one line with
        #no junctions
        raise NotThreadLikeEdgesError() from err
    neighbours = dict()
    for v1, v2 in edges:
        neighbours.setdefault( v1, set() ).add( v2 )
        neighbours.setdefault( v2, set() ).add( v1 )
    unvisited = set( edgecounter.keys() )
    current = iter( neighbours[ start ] ).__next__()
    thread = [ start, current ]
    while current != end :
        current, = neighbours[ current ].difference( thread[ -2: ] )
        thread.append( current )
    return thread

