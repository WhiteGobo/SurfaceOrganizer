import bpy

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
    scene.tool_settings.mesh_select_mode == (Falsem True, False)
    """
    #is_edgemode = (scene.tool_settings.mesh_select_mode ==(False, True, False))
    mode = targetobject.mode
    cond = (mode != 'OBJECT')
    if cond:
        #ensure active_object == active_layer.active_object
        bpy.ops.object.mode_set( mode='OBJECT' )

    for e in targetobject.data.edges:
        if e.select:
            yield ( e.vertices[0], e.vertices[1] )

    if cond:
        bpy.ops.object.mode_set( mode=mode )


from collections import Counter
import itertools
class NotThreadLikeEdgesError( Exception ):
    pass
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
