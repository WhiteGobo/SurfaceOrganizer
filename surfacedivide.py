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


def add_new_partial_surface( targetobject, surfacename ):
    allinfo = targetobject.partial_surface_information
    surfacelist = allinfo.partial_surface_info
    surfacelist.add()
    index = len( surfacelist ) - 1
    allinfo.active_surface_index = index
    surfacelist[ index ].name = surfacename if surfacename is not None else ""

def ensure_partial_surface( targetobject ):
    allinfo = targetobject.partial_surface_information
    index = allinfo.active_surface_index
    surfacelist = allinfo.partial_surface_info
    if len( surfacelist ) < 1:
        surfacelist.add()
        allinfo.active_surface_index = 0


def assign_cornerpoint( targetobject, targetvertice, targetcorner ):
    assert targetcorner in _CORNERS, f"targetcorner ({targetcorner}) "\
                                        +f"must be one of these: {_CORNERS}"
    allinfo = targetobject.partial_surface_information
    index = allinfo.active_surface_index
    try:
        surfaceinfo = allinfo.partial_surface_info[ index ]
    except IndexError as err:
        raise Exception( "no active partialsurface" ) from err
    surfacename = surfaceinfo.name

    vertindex = targetvertice.index
    if targetcorner == RIGHTUP_CORNER:
        surfaceinfo.rightup_corner = vertindex
    elif targetcorner == LEFTUP_CORNER:
        surfaceinfo.leftup_corner = vertindex
    elif targetcorner == LEFTDOWN_CORNER:
        surfaceinfo.leftdown_corner = vertindex
    elif targetcorner == RIGHTDOWN_CORNER: 
        surfaceinfo.rightdown_corner = vertindex

def assign_rightup_cornerpoint( targetobject, targetvertice ):
    assign_cornerpoint( targetobject, targetvertice, RIGHTUP_CORNER )
def assign_leftup_cornerpoint( targetobject, targetvertice ):
    assign_cornerpoint( targetobject, targetvertice, LEFTUP_CORNER )
def assign_leftdown_cornerpoint( targetobject, targetvertice ):
    assign_cornerpoint( targetobject, targetvertice, LEFTDOWN_CORNER )
def assign_rightdown_cornerpoint( targetobject, targetvertice ):
    assign_cornerpoint( targetobject, targetvertice, RIGHTDOWN_CORNER )

def asdf_assign_cornerpoint( targetobject, targetvertice, targetcorner, \
                                                    surfacename = None ):
    if targetcorner not in _CORNERS:
        raise KeyError( f"targetcorner must be one of these: {_CORNERS}" )
    if surfacename is not None:
        groupname = "_".join((surfacename, targetcorner))
    else:
        groupname = targetcorner
    verticeindex = targetvertice.index
    try:
        vertgroup = targetobject.vertex_groups[ groupname ]
    except KeyError:
        targetobject.vertex_groups.new( name = groupname )
        vertgroup = targetobject.vertex_groups[ groupname ]
    #all_vertices = [ v.index for v in object.data.vertices ]
    all_vertices = range( len( targetobject.data.vertices ) )

    mode = bpy.context.active_object.mode
    bpy.ops.object.mode_set( mode='OBJECT' )
    vertgroup.add( all_vertices, 1.0, "SUBTRACT" )
    vertgroup.add( [verticeindex,], 1.0, "ADD" )
    bpy.ops.object.mode_set( mode=mode )


def findborder_via_shortest_path( context, targetobject, \
                                                surfacename, targetborder ):
    override = {}
    if targetborder not in _BORDERS:
        raise KeyError( f"targetborder must be one of these: %s" \
                                                    % (tuple(_BORDERS.keys())))
    groupname = "_".join((surfacename, targetborder))
    first, second = ( "_".join((surfacename, name)) \
                        for name in _BORDER[ targetborder ] )
    firstvertice, = _get_vertices_of_vertexgroup( targetobject, first )
    secondvertice, = _get_vertices_of_vertexgroup( targetobject, second )
    _select_vertices( override, targetobject, [firstvertice, secondvertice] )

    mode = bpy.context.active_object.mode
    bpy.ops.object.mode_set( mode='EDIT' )
    bpy.ops.mesh.shortest_path_select() #Try this with override
    bpy.ops.object.mode_set( mode=mode )
    
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

def _select_vertices( override, targetobject, verticelist ):
    mode = bpy.context.active_object.mode
    bpy.ops.object.mode_set( mode='EDIT' )
    bpy.ops.mesh.select_mode( type='VERT' )
    bpy.ops.mesh.select_all( action='DESELECT' )
    bpy.ops.object.mode_set( mode='OBJECT' )
    for v in verticelist:
        v.select = True
    bpy.ops.object.mode_set( mode=mode )
