import bpy

RIGHTUP_CORNER = "rightup"
LEFTUP_CORNER = "leftup"
RIGHTDOWN_CORNER = "rightdown"
LEFTDOWN_CORNER = "leftdown"
_CORNERS = ( RIGHTUP_CORNER, LEFTUP_CORNER, RIGHTDOWN_CORNER, LEFTDOWN_CORNER )
RIGHT_BORDER = "right"
LEFT_BORDER = "left"
UP_BORDER = "up"
DOWN_BORDER = "down"
_BORDERS = { \
            RIGHT_BORDER: (RIGHTUP_CORNER, RIGHTDOWN_CORNER), \
            LEFT_BORDER: (LEFTUP_CORNER, LEFTDOWN_CORNER), \
            UP_BORDER: (RIGHTUP_CORNER, LEFTUP_CORNER), \
            DOWN_BORDER: (RIGHTDOWN_CORNER, LEFTDOWN_CORNER), \
            }

def assign_cornerpoint( targetobject, targetcorner, surfacename, targetcorner ):
    if targetcorner not in _CORNERS:
        raise KeyError( f"targetcorner must be one of these: {_CORNERS}" )
    groupname = "_".join((surfacename, targetcorner))
    verticeindex = targetcorner.index
    try:
        vertgroup = targetobject.vertex_groups[ groupname ]
    except KeyError:
        targetobject.vertex_groups.new( name = groupname )
        vertgroup = targetobject.vertex_groups[ groupname ]
    #all_vertices = [ v.index for v in object.data.vertices ]
    all_vertices = range( len( targetobject.data.vertices ) )
    vertgroup.add( all_vertices, 1.0, "SUBTRACT" )
    vertgroup.add( [verticeindex,], 1.0, "ADD" )


def findborder_via_shortest_path( context, targetobject, \
                                                surfacename, targetborder ):
    if targetborder not in _BORDERS:
        raise KeyError( f"targetborder must be one of these: %s" \
                                                    % (tuple(_BORDERS.keys()))
    groupname = "_".join((surfacename, targetborder))
    first, second = ( "_".join((surfacename, name)) \
                        for name in _BORDER[ targetborder ] )
    firstvertice, = _get_vertices_of_vertexgroup( targetobject, first )
    secondvertice, = _get_vertices_of_vertexgroup( targetobject, second )
    _select_vertices( targetobject, [firstvertice, secondvertice] )
    context.changetoeditmode
    bpy.ops.mesh.shortest_path_select()
    context.changetooldmode
    selected_vertices = [v.index for v in targetobject.data.vertices \
                            if v.selected ]
    try:
        vertgroup = targetobject.vertex_groups[ groupname ]
    except KeyError:
        targetobject.vertex_groups.new( name = groupname )
        vertgroup = targetobject.vertex_groups[ groupname ]
    all_vertices = range( len( targetobject.data.vertices ) )
    vertgroup.add( all_vertices, 1.0, "SUBTRACT" )
    vertgroup.add( selected_vertices, 1.0, "ADD" )

def _get_vertices_of_vertexgroup( object, groupname ):
    groupindex = object.vertex_groups[ groupname ].index
    for v in object.data.vertices:
        for g in v.groups:
            if g.group == groupindex:
                yield v.index

def _select_vertices( targetobject, verticelist ):
    context.changetoobjectmode
    deselect.all_vertices
    for v in verticelist:
        select.vertice( v )
    context.changetoeditmode
    bpy.ops.mesh.shortest_path_select()
    context.changetooldmode
