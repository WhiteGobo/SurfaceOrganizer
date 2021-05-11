import time
import bpy
import bmesh
from .datacontainer import plycontainer_from_arrays
from .myexport_ply import export_plyfile
import itertools as it

def save(
                context,
                filepath="",
                use_ascii=False,
                use_selection=False,
                use_normals=True,
                use_uv_coords=True,
                use_colors=True,
                global_matrix=None,
            ):
    t = time.time()

    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    if use_selection:
        obs = context.selected_objects
    else:
        obs = context.scene.objects

    #depsgraph = context.evaluated_depsgraph_get()


    if len( obs ) > 1:
        print( "can only export single mesh" )
        return {'CANCELLED'}
    blender_object = obs[0]

    myobj = blender_to_plycontainer( blender_object, use_normals=use_normals, \
                                    use_uvmaps=use_uv_coords, \
                                    use_vertex_colors=use_colors )


    if not use_ascii:
        print( "only supports ascii")
        return {'CANCELLED'}
    export_plyfile( filepath, myobj, "ascii" )

    t_delta = time.time() - t
    print(f"Export completed {filepath!r} in {t_delta:.3f}")




def blender_to_plycontainer( blender_object, use_normals=False, \
                                use_uvmaps=False, use_vertex_colors=False ):
    coordinates, normals, color_dictionary, active_color, uvmap_dictionary, \
                active_uvmap, faces \
                = extract_all_info_from_object( blender_object )
    weight_vertex_groups = extract_weight_of_vertex_groups( blender_object )
    number_vertices = len( coordinates )
    
    fl = "float"
    sh = "short"
    CH = "char"
    dataforvertices = list( it.zip_longest(*coordinates) )#xyz,xyz->xx,yy,zz
    datapipeline = [ (fl,"x"), (fl,"y"), (fl,"z") ]
    if use_normals:
        dataforvertices.extend( it.zip_longest( *normals ))
        datapipeline.extend( ( (fl,"nx"), (fl,"ny"), (fl,"nz")) )
    if use_uvmaps and active_uvmap != None: #len( uvmap_dictionary )>0:
        dataforvertices.extend( \
                            it.zip_longest( *uvmap_dictionary[ active_uvmap ]) )
        datapipeline.extend( ((fl,"s"), (fl,"t")) )
    if use_vertex_colors and active_color!=None: #len( color_dictionary )>0:
        dataforvertices.extend( it.zip_longest(\
                            *(color_dictionary[ active_color ]) ))
        tmp = { 3: ((CH,"r"), (CH,"g"), (CH,"b")), \
                4: ((CH,"r"), (CH,"g"), (CH,"b"), (CH,"alpha"))\
                }[len( color_dictionary[ active_color ][0] )]
        datapipeline.extend( tmp )

    form_list = "uchar"
    form_vert = "uint"
    reform_array = lambda f: f[:]
    data_for_faces = [ tuple( reform_array(f) for f in faces ) ]
    facepipeline = [ ("list", form_list, form_vert, "vertex_indices"), ]

    (vertex_rightup,) = weight_from_vertexgroup_to_vertice_index_array( \
                                        weight_vertex_groups['rightupcorner'] )
    (vertex_leftup,) = weight_from_vertexgroup_to_vertice_index_array( \
                                        weight_vertex_groups['leftupcorner'] )
    (vertex_rightdown,) = weight_from_vertexgroup_to_vertice_index_array( \
                                        weight_vertex_groups['rightdowncorner'])
    (vertex_leftdown,) = weight_from_vertexgroup_to_vertice_index_array( \
                                        weight_vertex_groups['leftdowncorner'] )
    data_for_rand = [( vertex_leftup,), (vertex_rightup,), \
                        (vertex_rightdown,), (vertex_leftdown,), ]
    randpipeline = [(form_vert, "rightup"), (form_vert, "leftup"), \
                    (form_vert, "leftdown"), (form_vert, "rightdown") ]

    myplycontainer = plycontainer_from_arrays([\
                            ("vertex", datapipeline, dataforvertices ), \
                            ("face", facepipeline, data_for_faces ), \
                            ("rand", randpipeline, data_for_rand ), \
                            ])
    return myplycontainer

def extract_all_info_from_object( blender_object ):
    mymesh = blender_object.data
    coordinates, normals = extract_coordinates( mymesh )
    color_dictionary, active_color = extract_vertexcolor( mymesh )
    uvmap_dictionary, notimplemented, active_uvmap \
                = extract_uvcoordinates( mymesh )
    faces = extract_faces( mymesh )
    return coordinates, normals, color_dictionary, active_color, \
                uvmap_dictionary, active_uvmap, faces

def extract_weight_of_vertex_groups( blender_object ):
    tmpdict = dict( blender_object.vertex_groups )
    def miniextract( vertgroup, number_vertices ):
        q = []
        for i in range( number_vertices ):
            try:
                q.append( vertgroup.weight( i ) )
            except RuntimeError:
                q.append( None )
        return q
    mymesh = blender_object.data
    vertices = mymesh.vertices
    numb_vertices = len( vertices )
    vertex_groups = { key: miniextract( value, numb_vertices ) \
                for key, value in tmpdict.items() }
    return vertex_groups


def weight_from_vertexgroup_to_vertice_index_array( weight_array ):
    indexarray = []
    for i, weight in enumerate( weight_array ):
        if weight != None:
            indexarray.append( i )
    return indexarray


def extract_coordinates( mesh_obj ):
    vertices = mesh_obj.vertices
    numb_vertices = len( vertices )
    coordinates = [ v.co[:] for v in vertices ]
    normals = [ v.normal[:] for v in vertices ]
    return coordinates, normals


def extract_vertexcolor( mymesh ):
    """
    returns a dictionary with all available vertexcolor-paintings. Acces via 
    name used in blender.
    Also returns name of currently active vertexcolor.
    """
    numb_vertices = len( mymesh.vertices )
    colorlist = dict()
    miniextract = lambda face: list( face.vertices )
    faces = [ miniextract( f ) for f in mymesh.polygons ]
    facecorner_chain = list( it.chain(*faces) )
    #if faces= [ (1,2,3),(2,3,4) ] -> facecorner_chain=[ 1,2,3,2,3,4 ]

    available_schemes = mymesh.vertex_colors
    try:
        active_index = available_schemes.active.name
    except AttributeError:
        active_index = None
    miniextract = lambda paint: [ x.color[:] for x in paint.data ]
    facecorner_colors = { key: miniextract( color ) \
                for key, color in mymesh.vertex_colors.items() }
    all_vertexcolor = dict()
    for key, singlefacecolorlist in facecorner_colors.items():
        colordict = { facecorner_chain[i]: color \
                        for i, color in enumerate( singlefacecolorlist ) }
        defaultcolor = iter( colordict.values() ).__next__()
        colorlist = [ colordict.get( i, defaultcolor ) \
                        for i in range(numb_vertices) ]
        all_vertexcolor[key] = colorlist
    all_vertexcolor = { key: _colorlist_quotient_to_char( colorlist ) \
                        for key, colorlist in all_vertexcolor.items() }
    return all_vertexcolor, active_index


def _colorlist_quotient_to_char( quotient_superlist ):
    listtrans = lambda xlist: [ int( 255.9*x ) for x in xlist ]
    return [ listtrans( l ) for l in quotient_superlist ]


    
def extract_uvcoordinates( mymesh ):
    numb_vertices = len( mymesh.vertices )
    colorlist = dict()
    miniextract = lambda face: list( face.vertices )
    faces = [ miniextract( f ) for f in mymesh.polygons ]
    facecorner_chain = list( it.chain(*faces) )
    #if faces= [ (1,2,3),(2,3,4) ] -> facecorner_chain=[ 1,2,3,2,3,4 ]

    available_maps = mymesh.uv_layers
    try:
        active_index = available_maps.active.name
    except AttributeError:
        active_index = None
    miniextract = lambda uvmap: [ vert.uv[:] for vert in uvmap.data ]
    uvmaps = { key: miniextract( uvmap ) \
                for key, uvmap in mymesh.uv_layers.items() }

    all_uvcoordinates_vertex = dict()
    all_uvcoordinates_facecorners = dict()
    for key, singleface_uvcoords in uvmaps.items():
        uv_dict = { facecorner_chain[i]: st_pos \
                        for i, st_pos in enumerate( singleface_uvcoords ) }
        default_coord = iter( uv_dict.values() ).__next__()
        uv_coords_list = [ uv_dict.get( i, default_coord ) \
                        for i in range(numb_vertices) ]

        if _check_if_all_uv_pos_are_unambiguously( uv_dict, \
                                    singleface_uvcoords, facecorner_chain ):
            all_uvcoordinates_vertex[key] = uv_coords_list
    # check if uv coordinates was removed
    if active_index not in all_uvcoordinates_vertex:
        active_index = None

    return all_uvcoordinates_vertex, all_uvcoordinates_facecorners, active_index


def _check_if_all_uv_pos_are_unambiguously( uv_dict, singleface_uvcoords, \
                                                        facecorner_chain ):
    for i, st_pos in enumerate( singleface_uvcoords ):
        vertex_index = facecorner_chain[i]
        if uv_dict[ vertex_index ] != st_pos:
            return False
    return True


def extract_faces( mymesh ):
    miniextract = lambda face: list( face.vertices )
    faces = [ miniextract( f ) for f in mymesh.polygons ]
    return faces
