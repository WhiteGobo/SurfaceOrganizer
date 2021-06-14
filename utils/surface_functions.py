from collections import Counter
import bmesh
import itertools
import logging
logger = logging.getLogger( __name__ )

from typing import Iterable

def find_partialsurface_to_border( targetobject, border_indexlist ):
    all_faces_indiceslist = _get_faces_as_indextuples( targetobject )
    new_faces_indiceslist, new_to_all = _split_surface_at_border( \
                                        border_indexlist, all_faces_indiceslist)
    outerstartvertice = border_indexlist[0]
    innerstartvertice = { b:a for a, b in new_to_all.items() \
                        if b not in all_faces_indiceslist }[outerstartvertice]
    vert_to_face = _get_verttoface_dict( new_faces_indiceslist )
    found_surfaces = []
    for startvertice in ( outerstartvertice, innerstartvertice ):
        vertlist = _get_all_connected_vertices( startvertice, vert_to_face, \
                                                    new_faces_indiceslist )
        filter_faces = _filter_facelist( new_faces_indiceslist, vertlist )
        filter_faces = list( filter_faces )
        if _check_only_one_circle( filter_faces ):
            old_vertlist = [ new_to_all.get( v, v ) for v in vertlist ]
            found_surfaces.append( old_vertlist )
    return found_surfaces

def assign_vertexgroup_to_surface( targetobject, surfacename:str, \
                                                    surf:Iterable[int] ):
    allinfo = targetobject.partial_surface_information
    index = allinfo.active_surface_index 
    partsurf_info = allinfo.partial_surface_info[ index ]

    partsurf_name = "vertices_" + partsurf_info.name + "_auto"
    vgroup = targetobject.vertex_groups.new( name = surfacename )
    #_select_vertices( targetobject, surf )
    _add_vertices_to_vertexgroup( vgroup, targetobject, surf )
    partsurf_info.vertexgroup = vgroup.name

def _add_vertices_to_vertexgroup( vertexgroup, targetobject, vertice_indices ):
    import bpy
    mode = targetobject.mode
    bpy.ops.object.mode_set( mode='OBJECT' )
    assert targetobject.mode == 'OBJECT', "couldnt set objectmode, " \
                    "maybe c...active_object != c...view_layer.objects.active"
    weight, add_type = 1, "REPLACE"
    #vertexgroup = obj.vertex_groups.new( name=vertexgroupname )
    for i in vertice_indices:
        vertexgroup.add( [i], weight, add_type )
    #throws error if 0 in sequence as first place
    #vertexgroup.add( set(vertice_indices), weight, add_type )
    bpy.ops.object.mode_set( mode=mode )

def _filter_facelist( faces_indiceslist, vertlist ):
    for face in faces_indiceslist:
        if set( face ).intersection( vertlist ) != set():
            yield face

def _check_only_one_circle( filter_faces ):
    connected_verticesets = []
    vertice_use = Counter()
    edge_use = Counter()
    for edge in _yield_edges( filter_faces ):
        vertice_use.update( edge )
        edge_use.update( [ frozenset( edge ) ] )
    try:
        if min( vertice_use.values() ) < 2:
            return False
    except ValueError: #min used on empty vertice_use.values()
        return False

    for edge, uses in edge_use.items():
        if uses == 1:
            asdf = [ vertsets for vertsets in connected_verticesets \
                        if vertsets.intersection( edge ) ]
            if len( asdf ) == 0:
                connected_verticesets.append( set( edge ) )
            elif len( asdf ) == 1:
                asdf[0].update( edge )
            elif len( asdf ) == 2:
                asdf[0].update( asdf[1] )
                connected_verticesets.remove( asdf[1] )
    return len( connected_verticesets ) == 1
    

class NoPossibleSurfaceFromBorder( Exception ):
    pass

def _fill_facelist_with_adjacent_faces( firstface, secondface, faces ):
    """
    As source uses set of faces which connect at 1 vertice.
    uses startfacelist of two faces which are adjacent to one another
    if all faces connect to 1 point and this is a regular surface in each step
    only one face can be added to the facelist
    """
    #assert all( type(face)==tuple for face in faces ), "faces must be tuples"
    are_adjacent = lambda x, y: len( set(x).intersection( y ) ) == 2
    order_faces = [ firstface ]
    nextface = secondface
    not_used_faces = set(faces).difference( order_faces )
    while nextface is not None:
        neighs = [ face for face in not_used_faces \
                    if are_adjacent( nextface, face ) ]
        not_used_faces.discard( nextface )
        order_faces.append( nextface )
        try:
            nextface = neighs[0]
        except IndexError:
            break
    return order_faces

def _get_left_and_right_face_to_edge( nextfaces, lastfaces, border_indexlist, \
                                        lastleft, lastright ):
                                        #facelistleft, facelistright ):
    #neighbourfaces are the next possibly two faces to choose from
    neighbourfaces = [ face for face in nextfaces if face in lastfaces ]

    firstface, secondface = lastleft, lastright
    if secondface is not None:
        order_faces = _fill_facelist_with_adjacent_faces( firstface,secondface,\
                                                                    lastfaces )
        if all( face in order_faces for face in neighbourfaces ):
            if any( face in (lastleft, ) for face in neighbourfaces ):
                neighbourfaces.sort( key=order_faces.index, reverse=True )
            else:
                neighbourfaces.sort( key=order_faces.index )
            neighbourfaces.append( None ) # left can be not existent
            right, left = neighbourfaces[0], neighbourfaces[1]
            maxrightindex = order_faces.index( right )
            minrightindex = order_faces.index( lastright )
            righties = order_faces[ minrightindex : maxrightindex+1 ]
            lefties = set( lastfaces ).difference( righties )
            return lefties, righties, left, right

    firstface, secondface = lastright, lastleft
    if secondface is not None:
        order_faces = _fill_facelist_with_adjacent_faces( firstface,secondface,\
                                                                    lastfaces )
        if all( face in order_faces for face in neighbourfaces ):
            if any( face in (lastright, ) for face in neighbourfaces ):
                neighbourfaces.sort( key=order_faces.index, reverse=True )
            else:
                neighbourfaces.sort( key=order_faces.index )
            neighbourfaces.append( None ) # right can be not existent
            left, right = neighbourfaces[0], neighbourfaces[1]
            maxleftindex = order_faces.index( left )
            minleftindex = order_faces.index( lastleft )
            lefties = order_faces[ minleftindex : maxleftindex+1 ]
            righties = set( lastfaces ).difference( lefties )
            return lefties, righties, left, right
    raise NoPossibleSurfaceFromBorder( "Surface has holes along the border on"\
                                    "each side. Cant find surface withoutholes")


    qq_neighbour = lambda x, y: len( set(x).intersection( y ) ) == 2
    #get faces clockwise
    asdf = [ facelistleft[-1], facelistright[-1] ]
    asdf2 = [ set(face) for face in asdf if face is not None ]
    clockwise = True
    while not all( set( face ) in asdf2 for face in neighbourfaces ):
        neighs = [ face for face in lastfaces \
                    if set(face) not in asdf2 \
                    and qq_neighbour( asdf[-1], face ) ]
        if len( neighs ) == 1:
            asdf.append( neighs[0] )
            asdf2.append( set(neighs[0]) )
        else:
            break
    if not all( set(face) in asdf2 for face in neighbourfaces ):
        clockwise = False
        asdf = [ facelistright[-1], facelistleft[-1] ]
        asdf2 = [ set(face) for face in asdf if face is not None ]
        while not all( set( face ) in asdf2 for face in neighbourfaces ):
            neighs = [ face  for face in lastfaces \
                        if set(face) not in asdf2 \
                        and qq_neighbour( asdf[-1], face ) ]
            if len( neighs ) == 1:
                asdf.append( neighs[0] )
                asdf2.append( set(neighs[0]) )
            else:
                break
    if not all( set(face) in asdf2 for face in neighbourfaces ):
        raise Exception( asdf2, neighbourfaces )
    neighbours_as_faces = [ set(face) for face in neighbourfaces \
                            if face is not None ]
    asdf = [ face for face in asdf if face is not None ]
    returnarray = [ face for face in asdf \
                    if set(face) in neighbours_as_faces ] + [None]
    if clockwise:
        return returnarray[1], returnarray[0]
    else:
        return returnarray[0], returnarray[1]
    #raise NoPossibleSurfaceFromBorder( "Closed Surface with border "
    #                                    "only possible if on border every"
    #                                    "edge has adjacent face" ) from err

def _split_surface_at_border( border_indexlist, all_faces_indiceslist ):
    vert_to_face = _get_verttoface_dict( all_faces_indiceslist )
    startfaces = vert_to_face[ border_indexlist[0] ]
    nextfaces = vert_to_face[ border_indexlist[1] ]
    # There could be only one neighbouring face, so then i use 'None' as second 
    neighbourfaces = [ face for face in nextfaces if face in startfaces ]+[None]
    lastfaces = nextfaces
    lastleft, lastright = neighbourfaces[0], neighbourfaces[1]
    facelistleft, facelistright = [lastleft], [lastright]
    for v in border_indexlist[2:]+border_indexlist[:1]:
        nextfaces = vert_to_face[ v ]
        leftface, rightface, lastleft, lastright \
                            = _get_left_and_right_face_to_edge( nextfaces, \
                                                lastfaces, border_indexlist, \
                                                lastleft, lastright )
        lastfaces = nextfaces
        facelistleft.extend( leftface )
        facelistright.extend( rightface )
    facelistleft = list( set(facelistleft))
    facelistright = list( set(facelistright))
    
    new_to_all = { v:v for v in itertools.chain( *all_faces_indiceslist ) }
    startindex = max( new_to_all.keys() ) + 1
    nextindex = iter( range( startindex+1, startindex+1+len(border_indexlist)) )
    border_to_new = { v: nextindex.__next__() for v in border_indexlist }
    new_to_all.update( { b:a for a,b in border_to_new.items() } )
    new_faces_indiceslist = [ face for face in all_faces_indiceslist \
                                if face not in facelistright ]
    get_newindex = lambda index: border_to_new.get( index, index )
    for face in facelistright:
        if face is not None:
            new_faces_indiceslist.append( tuple( get_newindex(index) \
                                            for index in face ))
    return new_faces_indiceslist, new_to_all

def _are_neighbours( face1, face2 ):
    return 2 <= len( set( face1 ).intersection( face2 ) )

def _get_all_connected_vertices( startvertice, vert_to_face, \
                                                    new_faces_indiceslist ):
    vertlist = [ startvertice ]
    for vert in vertlist:
        for face in vert_to_face.get( vert, list() ):
            new_verts = set( face ).difference( vertlist )
            vertlist.extend( new_verts )
    return vertlist

def find_possible_partialsurfaces_to_border( targetobject, partialsurfaceinfo ):
    rightup, leftup, leftdown, rightdown, border_indices\
            = _extract_info_from_partialsurfaceinfo( targetobject, \
                                                    partialsurfaceinfo )
    all_faces_indiceslist = _get_faces_as_indextuples( targetobject )

    faces_indiceslist = [ face for face in all_faces_indiceslist \
                        if set( border_indices ).intersection( face ) == set() ]
    faces_vertexindices_set = [ set( face ) for face in all_faces_indiceslist ]
    vert_to_face = _get_verttoface_dict( faces_vertexindices_set )

    rightup_neighbours, possible_leftup, possible_leftdown, possible_rightdown \
            = _get_neighbours_to_border( vert_to_face, border_indices, \
                                    [rightup, leftup, leftdown, rightdown])

    foundcycles = _find_cycles_next_to_border( \
                        faces_indiceslist, rightup_neighbours, \
                        possible_leftup, possible_leftdown, possible_rightdown )

    _complete_surfaces_verticelist \
                        = _complete_cycles_next_to_border( \
                        foundcycles, faces_indiceslist, border_indices )

    exclude_criteria_edges = set(_find_boundaryedges(all_faces_indiceslist))\
                                .difference( border_indices )
    exclude_criteria_vertices = set( itertools.chain(*exclude_criteria_edges) )
    for vertlist in _complete_surfaces_verticelist:
        if not vertlist.intersection( exclude_criteria_vertices ):
            yield( vertlist )
    #return list( _complete_surfaces_verticelist )


def _find_border( partialsurfaceinfo, targetobject ):
    rightup = partialsurfaceinfo.rightup_corner
    leftup = partialsurfaceinfo.leftup_corner
    leftdown = partialsurfaceinfo.leftdown_corner
    rightdown = partialsurfaceinfo.rightdown_corner

    up_group = targetobject.vertex_groups[ partialsurfaceinfo.up_border ].index
    left_group = targetobject.vertex_groups[ partialsurfaceinfo.left_border ].index
    down_group = targetobject.vertex_groups[ partialsurfaceinfo.down_border ].index
    right_group = targetobject.vertex_groups[ partialsurfaceinfo.right_border ].index
    all_groups = set((up_group, left_group, down_group, right_group))
    is_in_group = lambda v: all_groups.intersection( [g.group for g in v.groups] ) != set()
    #contextswitch objectmode
    border_indices = set(( v.index for v in targetobject.data.vertices \
                            if is_in_group( v ) ))
    return rightup, leftup, leftdown, rightdown, border_indices

def _get_faces_as_indextuples( targetobject ):
    workmesh = bmesh.new()
    workmesh.from_mesh( targetobject.data )
    workmesh.faces.ensure_lookup_table()
    all_faces_indiceslist = [ tuple( vert.index for vert in face.verts ) \
                            for face in workmesh.faces ]
    workmesh.free()
    return all_faces_indiceslist


def _extract_info_from_partialsurfaceinfo( targetobject, partialsurfaceinfo ):
    rightup = partialsurfaceinfo.rightup_corner
    leftup = partialsurfaceinfo.leftup_corner
    leftdown = partialsurfaceinfo.leftdown_corner
    rightdown = partialsurfaceinfo.rightdown_corner

    up_group = targetobject.vertex_groups[ partialsurfaceinfo.up_border ].index
    left_group = targetobject.vertex_groups[ partialsurfaceinfo.left_border ].index
    down_group = targetobject.vertex_groups[ partialsurfaceinfo.down_border ].index
    right_group = targetobject.vertex_groups[ partialsurfaceinfo.right_border ].index
    all_groups = set((up_group, left_group, down_group, right_group))
    is_in_group = lambda v: all_groups.intersection( [g.group for g in v.groups] ) != set()
    #contextswitch objectmode
    border_indices = set(( v.index for v in targetobject.data.vertices \
                            if is_in_group( v ) ))
    return rightup, leftup, leftdown, rightdown, border_indices


def _complete_cycles_next_to_border( foundcycles, faces_indiceslist, \
                                        borderindices ):
    for singlecycle in foundcycles:
        innervertices = _complete_boundary_to_surfaceindices( singlecycle, \
                                                            faces_indiceslist )
        allvertices = innervertices.union( borderindices )
        yield allvertices


def _yield_edges( faces_indiceslist ):
    for face in faces_indiceslist:
        for i in range( len(face) ):
            edge = frozenset((face[i-1], face[i]))
            yield edge

def _find_boundaryedges( faces_indiceslist ):
    all_edges = _yield_edges( faces_indiceslist )
    edgecounter = Counter( all_edges )
    boundaryedges = [ edge for edge, times in edgecounter.items() if times==1 ]
    return boundaryedges


def _find_possible_innercircles( boundaryedges, neigh_list_rightup, \
                                neigh_list_leftup, neigh_list_leftdown, \
                                neigh_list_rightdown ):
    vert_to_edges = { \
                **{ edge[0]: edge for edge in boundaryedges },
                **{ edge[1]: edge for edge in boundaryedges },
                }

    is_neighbour = lambda circle_indices: all(( \
                            set() != neighs_leftup.union( circle_indices ), \
                            set() != neighs_leftdown.union( circle_indices ), \
                            set() != neighs_rightdown.union( circle_indices ), \
                            ))
    for singlecircle in foundboundaries:
        if len( borderindices.intersection( singlecircle ) ) == 4:
            tmpindices = [ singlecircle.index( i ) \
                            for i in borderindices_tuple ]
            if isclockwise( *tmpindices ) or iscounterclockwise( *tmpindices ):
                returncircle = singlecircle
                break
    return returncircle


def _reduce_edgeset_more_than_2_edges( edgeset ):
    assert type( edgeset ) == set, "reduce_edgeset... should use set " \
                                    +f"of frozenset as input"
    vertcount = Counter( itertools.chain( *edgeset ))
    for edge in edgeset:
        if all((vertcount[ v ] <=2 for v in edge )):
            yield edge

def _reduce_edgeset_noncircles( nojunction_edges ):
    assert type( nojunction_edges ) == set, "reduce_edgeset... should use set "\
                                    +"of frozenset as input"
    vertcount = Counter( itertools.chain( *nojunction_edges ) )
    assert max( vertcount.values()) <= 2,"there are junctions in no junctionset"
    reduced_set = set( nojunction_edges )
    vert_to_edge = dict()
    for edge in reduced_set:
        for v in edge:
            tmplist = vert_to_edge.setdefault( v, list() )
            tmplist.append( edge )
    removed_verts = set()
    used_edges = set()
    for vert, number in vertcount.items():
        if number == 1 and vert not in removed_verts:
            removed_verts.add( vert )
            tmpedge = [ edge for edge in vert_to_edge[ vert ] \
                        if edge not in used_edges ][0]
            nextverts = [ vert for vert in tmpedge \
                        if vert not in removed_verts ]
            used_edges.add( tmpedge )
            while nextverts:
                nextvert = nextverts[0]
                removed_verts.add( nextvert )
                tmpedge = [ edge for edge in vert_to_edge[ nextvert ] \
                            if edge not in used_edges ][0]
                nextverts = [ vert for vert in tmpedge \
                            if vert not in removed_verts ]
                used_edges.add( tmpedge )
    return reduced_set.difference( used_edges )

def _create_circles_without_junction( boundaryedges ):
    boundaryedges = set( frozenset(edge) for edge in boundaryedges )
    nojunction_edges = set(_reduce_edgeset_more_than_2_edges( boundaryedges ))
    onlycircles_edges = set(_reduce_edgeset_noncircles( nojunction_edges ))
    removed_verts = set()
    used_edges = set()
    remaining_verts = list( set(itertools.chain( *onlycircles_edges )))

    vert_to_edge = dict()
    for edge in onlycircles_edges:
        for v in edge:
            tmplist = vert_to_edge.setdefault( v, list() )
            tmplist.append( edge )
    # I will remove verts from list while running other the list
    # seems strange but works. removed verts wont be called
    for vert in remaining_verts:
        circle = [ vert ]
        remaining_verts.remove( vert )
        removed_verts.add( vert )
        tmpedge = [ edge for edge in vert_to_edge[ vert ] \
                    if edge not in used_edges ][0]
        nextverts = [ vert for vert in tmpedge \
                    if vert not in removed_verts ]
        used_edges.add( tmpedge )
        while nextverts:
            nextvert = nextverts[0]
            circle.append( nextvert )
            remaining_verts.remove( nextvert )
            removed_verts.add( nextvert )
            tmpedge = [ edge for edge in vert_to_edge[ nextvert ] \
                        if edge not in used_edges ][0]
            nextverts = [ vert for vert in tmpedge \
                        if vert not in removed_verts ]
            used_edges.add( tmpedge )
        yield circle


def _find_innersurface( boundaryedges, rightup, leftup, leftdown, rightdown):

    raise Exception( rightup, leftup, leftdown, rightdown )

    borderindices_tuple = ( rightup, leftup, leftdown, rightdown )
    borderindices = { rightup, leftup, leftdown, rightdown }
    foundboundaries = _find_all_boundaries( rightup, vert_to_edges )
    isclockwise = lambda a,b,c,d: all(a<b, b<c, c<d)
    iscounterclockwise = lambda a,b,c,d: all(a>b, b>c, c>d)
    returncircle = None
    for singlecircle in foundboundaries:
        if len( borderindices.intersection( singlecircle ) ) == 4:
            tmpindices = [ singlecircle.index( i ) \
                            for i in borderindices_tuple ]
            if isclockwise( *tmpindices ) or iscounterclockwise( *tmpindices ):
                returncircle = singlecircle
                break
    return returncircle

def _find_all_boundaries( rightup, vert_to_edges ):
    current_vertice = rightup
    info = [{ \
            "visited":set(), "used_edges":set(), \
            "vertlist":[], "next_vertice":rightup, \
            }]
    foundlassos = []
    get_unvisited = lambda edge, visited: \
                        iter( v for v in edge if v not in visited ).__next__()
    while info:
        nextinfo = info.pop()
        visited = nextinfo[ "visited" ]
        used_edges = nextinfo[ "used_edges" ]
        vertlist = nextinfo[ "vertlist" ]
        next_vertice = nextinfo[ "next_vertice" ]
        while next_vertice is not None:
            vertlist.append( next_vertice )
            visited.add( next_vertice )
            nextedges = iter( edge for edge in vert_to_edges[ next_vertice ] \
                            if edge not in used_edges )
            nextedge = nextedges.__next__()
            for e in nextedges: #remaining edges
                tmpvisited = visited.copy()
                tmpvertlist = vertlist.copy()
                tmpused_edges = used_edges.copy()
                tmpused_edges.add( e )
                tmpnextvertice = iter( v for v in e \
                                if v not in visited ).__next__()
                try:
                    tmpnextvertice = get_unvisited( e, tmpvisited )
                    info.append({
                                "visited": tmpvisited, \
                                "used_edges": tmpused_edges, \
                                "vertlist": tmpvertlist, \
                                "next_vertice": tmpnextvertice, \
                                })
                except Exception:
                    if rightup in e:
                        yield tmpvertlist
            try:
                next_vertice = get_unvisited( nextedge, visited )
                used_edges.add( nextedge )
            except Exception:
                if rightup in nextedge:
                    yield vertlist
                next_vertice = None


def _find_cycles_next_to_border( faces_indiceslist, rightup_neighbours, \
                        possible_leftup, possible_leftdown, possible_rightdown):
    boundaryedges = _find_boundaryedges( faces_indiceslist )
    neighs_rightup = set( rightup_neighbours )
    neighs_leftup = set( possible_leftup )
    neighs_leftdown = set( possible_leftdown )
    neighs_rightdown = set( possible_rightdown )
    is_neighbour = lambda circle_indices: all(( \
                    set() != neighs_rightup.intersection( circle_indices ), \
                    set() != neighs_leftup.intersection( circle_indices ), \
                    set() != neighs_leftdown.intersection( circle_indices ), \
                    set() != neighs_rightdown.intersection( circle_indices ), \
                    ))
    circles = _create_circles_without_junction( boundaryedges )
    for circle in circles:
        if is_neighbour( circle ):
            yield circle


def _complete_boundary_to_surfaceindices( boundary, surface_indexlist ):
    vert_to_face = dict()
    for face in surface_indexlist:
        face_set = set( face )
        for v in face:
            tmplist = vert_to_face.setdefault( v, list() )
            tmplist.append( face_set )

    all_vertices = list( boundary )
    all_vertices_set = set( boundary )
    i = 0
    while i < len( all_vertices ):
        for face in vert_to_face[ all_vertices[i] ]:
            smallface = face.difference( all_vertices_set )
            for v in smallface:
                all_vertices.append( v )
                all_vertices_set.add( v )
        i = i+1
    return all_vertices_set

def _get_verttoface_dict( faces_vertexindices_set ):
    vert_to_face = dict()
    for face_indices in faces_vertexindices_set:
        for v in face_indices:
            tmplist = vert_to_face.setdefault( v, list() )
            tmplist.append( face_indices )
    return vert_to_face


def _get_neighbours_to_border( vert_to_face, border_indices, cornpoints ):
    """
    :param faces_vertexindices_set: A list of all the faces. Each face is
                represented by a set of the verticeindices
    """
    neighbours = { v:set() for v in cornpoints }

    tobevisited = list( neighbours.keys() )
    for v_source in tobevisited:
        for face in vert_to_face[ v_source ]:
            notborderindices = set(face).difference( border_indices )
            if notborderindices != set():
                neighbours[ v_source ].update( notborderindices )
            else:
                for v in face:
                    if v not in neighbours.keys():
                        tobevisited.append( v )
                        neighbours[ v ] = neighbours[ v_source ]
    for point in cornpoints:
        yield set( neighbours[ point ] ).difference( border_indices )
