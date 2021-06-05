from collections import Counter
import bmesh
import itertools

def find_partialsurface_to_border( targetobject, border_indexlist ):
    all_faces_indiceslist = _get_faces_as_indextuples( targetobject )
    new_faces_indiceslist, new_to_all = _split_surface_at_border( \
                                        border_indexlist, all_faces_indiceslist)
    outerstartvertice = border_indexlist[0]
    innerstartvertice = set( new_to_all.keys() ) \
                        .difference( all_faces_indiceslist ).pop()
    vert_to_face = _get_verttoface_dict( new_faces_indiceslist )
    found_surfaces = []
    for startvertice in ( outerstartvertice, innerstartvertice ):
        vertlist = _get_all_connected_vertices( startvertice, vert_to_face, \
                                                    new_faces_indiceslist )
        filter_faces = _filter_facelist( new_faces_indiceslist, vertlist )
        filter_faces = list( filter_faces )
        if _check_only_one_circle( filter_faces ):
            found_surfaces.append( vertlist )
    return found_surfaces

def _filter_facelist( faces_indiceslist, vertlist ):
    for face in faces_indiceslist:
        if set( face ).intersection( vertlist ) != set():
            yield face

def _check_only_one_circle( filter_faces ):
    connected_verticesets = []
    vertice_use = Counter()
    for edge in _yield_edges( filter_faces ):
        vertice_use.update( edge )
        asdf = [ vertsets for vertsets in connected_verticesets \
                    if vertsets.intersection( edge ) ]
        if len( asdf ) == 0:
            connected_verticesets.append( set( edge ) )
        elif len( asdf ) == 1:
            asdf[0].update( edge )
        elif len( asdf ) == 2:
            asdf[0].update( asdf[1] )
            connected_verticesets.remove( asdf[1] )
    try:
        return all((\
                min( vertice_use.values() ) >= 2, \
                len( connected_verticesets ) == 1, \
                ))
    except ValueError: #min used on empty vertice_use.values()
        return False
    

class NoPossibleSurfaceFromBorder( Exception ):
    pass

def _split_surface_at_border( border_indexlist, all_faces_indiceslist ):
    vert_to_face = _get_verttoface_dict( all_faces_indiceslist )
    startfaces = vert_to_face[ border_indexlist[0] ]
    nextfaces = vert_to_face[ border_indexlist[1] ]
    # There could be only one neighbouring face, so then i use 'None' as second 
    neighbourfaces = [ face for face in nextfaces if face in startfaces ]+[None]
    lastfaces = nextfaces
    facelistright, facelistleft = [neighbourfaces[0]], [neighbourfaces[1]]
    for v in border_indexlist[2:]:
        nextfaces = vert_to_face[ border_indexlist[1] ]
        neighbourfaces = [ face for face in nextfaces if face in lastfaces ]
        lastfaces = nextfaces
        try:
            A = neighbourfaces[0]
        except IndexError as err:
            raise NoPossibleSurfaceFromBorder( "Closed Surface with border "
                                            "only possible if on border every"
                                            "edge has adjacent face" ) from err
        try:
            B = neighbourfaces[1]
        except IndexError:
            B = None
        if _are_neighbours( A, facelistright[-1] ):
            #facelistleft.append( B )
            facelistright.append( A )
        else:
            #facelistleft.append( A )
            facelistright.append( B )
    
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
            new_faces_indiceslist.append( [ get_newindex(index) \
                                            for index in face ])
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
