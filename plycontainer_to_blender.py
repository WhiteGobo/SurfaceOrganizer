import bpy
import time

from .myimport_ply import load_ply_obj_from_filename
import itertools

def load(operator, context, filepath=""):
    return load_ply(filepath)

def load_ply( filepath ):
    t = time.time()
    #filename = "/home/hfechner/tmp.ply"
    #filename = "/home/hfechner/meshfortests.ply"
    ply_name = filepath
    ply_name = bpy.path.display_name_from_filepath( filepath )


    myobj = load_ply_obj_from_filename( filepath )
    blender_obj_info = plyobj_to_blenderimporter( myobj )
    
    generate_blender_object( ply_name, blender_obj_info )
    print("\nSuccessfully imported %r in %.3f sec" \
            % (filepath, time.time() - t))
    return {'FINISHED'}

def extract_vertex_positions( blender_obj_info ):
    vertexpositions = blender_obj_info.vertex 
    vertexnumber = len( blender_obj_info.vertex )
    return vertexpositions, vertexnumber


def generate_blender_object( ply_name, blender_obj_info ):
    mesh, borderrectangle = generate_mesh( ply_name, blender_obj_info )
    obj = generate_blenderobject( ply_name, blender_obj_info, mesh )
    add_vertexgroup_rand( obj, borderrectangle )

    obj.select_set(True)


def generate_mesh( ply_name, blender_obj_info ):
    blinfo = blender_obj_info
    vertice_positions, vertex_number = extract_vertex_positions( blinfo )
    edge_n, edges = extract_edgeinfo( blender_obj_info )
    face_n, faces = extract_faceinfo( blender_obj_info )
    borderrectangle = extract_borderrectangleinfo( blender_obj_info )

    mesh = bpy.data.meshes.new( name=ply_name )
    mesh.vertices.add( vertex_number )
    mesh.vertices.foreach_set( "co", list(itertools.chain( *vertice_positions)))
    if edge_n > 0:
        add_edges_to_mesh( mesh, edge_n, edges )
    if face_n > 0:
        add_faces_to_mesh( mesh, face_n, faces )
    if "vertexcolor" in blender_obj_info.__dict__:
        add_vertexcolor_to_mesh( mesh, blender_obj_info )
    if "mappos_st" in blender_obj_info.__dict__:
        add_uv_coordinates_to_mesh( mesh, blender_obj_info )
    mesh.update()
    mesh.validate()


    return mesh, borderrectangle

def generate_blenderobject( ply_name, blender_obj_info, mesh ):
    obj = bpy.data.objects.new(ply_name, mesh)

    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj

    return obj

def add_vertexgroup_rand( obj, borderrectangle ):
    bordervert_leftup, bordervert_rightup, bordervert_rightdown, \
                                    bordervert_leftdown = borderrectangle
    create_vertexgroup_with_vertices( obj, "leftupcorner", [bordervert_leftup] )
    create_vertexgroup_with_vertices( obj, "rightupcorner",[bordervert_rightup])
    create_vertexgroup_with_vertices( obj, "rightdowncorner", \
                                    [bordervert_rightdown])
    create_vertexgroup_with_vertices( obj, "leftdowncorner", \
                                    [bordervert_leftdown] )


def extract_faceinfo( blender_obj_info ):
    try:
        face_number = len( blender_obj_info.face )
        faces = blender_obj_info.face
        #faces = list( itertools.chain( blender_obj_info.face) )
        return face_number, faces
    except AttributeError:
        return 0, []

def extract_borderrectangleinfo( blender_obj_info ):

def extract_edgeinfo( blender_obj_info ):
    try:
        edge_number = len( blender_obj_info.edges )
        edges = list( itertools.chain( blender_obj_info.edges) )
        return edge_number, edges
    except AttributeError:
        return 0, []

def add_edges_to_mesh( mesh, edge_number, edges ):
    mesh.edges.add( edge_number )
    mesh.edges.foreach_set("vertices", edges )


def add_faces_to_mesh( mesh, face_number, faces ):
    loops_vert_idx = []
    faces_loop_start = []
    faces_loop_total = []
    lidx = 0
    for f in faces:
        nbr_vidx = len(f)
        loops_vert_idx.extend(f)
        faces_loop_start.append(lidx)
        faces_loop_total.append(nbr_vidx)
        lidx += nbr_vidx

    mesh.loops.add(len(loops_vert_idx))
    mesh.polygons.add( face_number )

    mesh.loops.foreach_set("vertex_index", loops_vert_idx)
    mesh.polygons.foreach_set("loop_start", faces_loop_start)
    mesh.polygons.foreach_set("loop_total", faces_loop_total)


def add_uv_coordinates_to_mesh( mesh, blender_obj_info ):
    if uvindices:
        uv_layer = mesh.uv_layers.new()
        for i, uv in enumerate(uv_layer.data):
            uv.uv = mesh_uvs[i]

def add_color_to_vertex( mesh, blender_obj_info ):
    vcol_lay = mesh.vertex_colors.new()

    for i, col in enumerate( blender_obj_info.vertexcolor ):
        col.color[0] = mesh_colors[i][0] #r
        col.color[1] = mesh_colors[i][1] #g
        col.color[2] = mesh_colors[i][2] #b
        col.color[3] = mesh_colors[i][3] #alpha


def plyobj_to_blenderimporter( myobj ):
    myinfo = blenderinformation()
    for prop in myobj.specs:
        if prop.name == b'vertex':
            myinfo += process_vertex( prop )
        elif prop.name == b'face':
            myinfo += process_faces( prop )
        elif prop.name == b'rand':
            myinfo += process_rand( prop )
        else:
            print( f"skipped {prop.name}" )
    return myinfo
            
            


class blenderinformation():
    def __init__( self, **argv ):
        for a in argv:
            self.__dict__[ a ] = argv[ a ] 

    def __repr__( self ):
        m = ", ".join( f"{a}: {b}" \
                for a, b in self.__dict__.items() )
        return "{ %s }" %(m)
    __listattribute = ( "vertex", "face" )
    def __add__( self, other ):
        allkeys = set( self.__dict__.keys() ) \
                    .union( other.__dict__.keys() )
        newdict = dict()
        for key in allkeys:
            if key in self.__listattribute:
                newlist = []
                newlist.extend( self.__dict__.get( key, list() ))
                newlist.extend( other.__dict__.get( key, list()))
                newdict[ key ] = newlist
            elif \
                    key in self.__dict__ \
                    and key not in other.__dict__:
                newdict[ key ] = self.__dict__[ key ]
            elif \
                    key in other.__dict__ \
                    and key not in self.__dict__:
                newdict[ key ] = other.__dict__[ key ]
            else:
                raise Exception()
        return type( self )( **newdict )


def process_vertex( elementspec ):
    infodict = {}
    v = []
    el = elementspec
    grab_coordinates = lambda vdata: (vdata[ el.index("x") ], \
                                    vdata[ el.index("y") ], \
                                    vdata[ el.index("z") ])
    for vertex in elementspec.data:
        v.append( grab_coordinates( vertex ) )
    infodict.update({ "vertex": v})

    if b"s" in el.keys() and b't' in el.keys():
        mappos = []
        #uv is the mapping position of 3d objects to a 2d map
        grab_uv = lambda vdata: (vdata[ el.index("s") ], \
                                vdata[ el.index["t"]])
        for vertex in elementspec.data:
            mappos.append( grab_uv( vertex ) )
        infodict.update({ "mappos_st": mappos})

    if b'red' in el.keys() and b'green' in el.keys() \
                            and b'blue' in el.keys():
        if b'alpha' in el.keys():
            grab_vertexcolor = lambda vdata: (\
                                    vdata[ el.index("red") ],\
                                    vdata[ el.index("green") ], \
                                    vdata[ el.index("blue") ],\
                                    vdata[ el.index("alpha") ] )
        else:
            grab_vertexcolor = lambda vdata: ( \
                                    vdata[ el.index("red") ],\
                                    vdata[ el.index("green") ], \
                                    vdata[ el.index("blue") ] )
        vertexcolor = []
        for vertex in elementspec.data:
            mappos.append( grab_uv( vertex ) )
        infodict.update({ "vertexcolor": vertexcolor})

    return blenderinformation( **infodict )

def process_faces( elementspec ):
    f = []
    el = elementspec
    grab_face_indices = lambda fdata: \
                    tuple( fdata[ el.index("vertex_indices")] )
    for face in elementspec.data:
        f.append( grab_face_indices( face ) )
    return blenderinformation( face=f )

def process_rand( elementspec ):
    f = []
    el = elementspec
    grab_rand_indices = asdf
    for rand in elementspec.data:
        raise Exception()



if __name__ == "__main__":
    load_ply()

