# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

import re
import itertools
import bpy
import time


#see also: http://paulbourke.net/dataformats/ply/
type_specs = {
    b'char': 'b',
    b'uchar': 'B',
    b'short': 'h',
    b'ushort': 'H',
    b'int': 'i',
    b'uint': 'I',
    b'float': 'f',
    b'double': 'd',
}


def load_ply(filepath):
    t = time.time()
    ply_name = bpy.path.display_name_from_filepath(filepath)

    obj_spec, obj, texture = read(filepath)
    # XXX28: use texture
    if obj is None:
        print("Invalid file")
        return

    verts, edgeinfo, mesh_faces, uvindices, colindices, \
            vindices_x, vindices_y, vindices_z, mesh_colors, borderrectangle \
            = load_ply_data( ply_name, obj_spec, obj, texture )
    mesh = generate_blender_mesh( ply_name, verts, edgeinfo, mesh_faces, \
                                    uvindices, \
                                    colindices, vindices_x, vindices_y, \
                                    vindices_z, mesh_colors )
    if not mesh:
        return {'CANCELLED'}

    for ob in bpy.context.selected_objects:
        ob.select_set(False)

    obj = bpy.data.objects.new(ply_name, mesh)

    if borderrectangle:
        bordervert_leftup, bordervert_rightup, bordervert_rightdown, \
                                        bordervert_leftdown = borderrectangle
        create_vertexgroup_with_vertices( obj, "leftup", [bordervert_leftup] )
        create_vertexgroup_with_vertices( obj, "rightup", [bordervert_rightup] )
        create_vertexgroup_with_vertices( obj, "rightdown", \
                                        [bordervert_rightdown])
        create_vertexgroup_with_vertices( obj, "leftdown", \
                                        [bordervert_leftdown] )

    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    print("\nSuccessfully imported %r in %.3f sec" \
            % (filepath, time.time() - t))

    return {'FINISHED'}


def load(operator, context, filepath=""):
    return load_ply(filepath)




class iterable_to_stream:
    def __init__(self, iterable):
        self.iter = iter(iterable)

    def read(self, n=1 ):
        mystring = bytearray()
        for i in range( n ):
            try:
                mystring.append( self.iter.__next__() )
            except StopIteration:
                pass
        return mystring

    def readline( self ):
        mystring = bytearray()
        try:
            mystring.append( self.iter.__next__() )
            while mystring[-1] not in (bytes('\n', encoding="utf-8")):
                mystring.append( self.iter.__next__() )
        except StopIteration:
            pass
        return mystring


class ElementSpec:
    __slots__ = (
        "name",
        "count",
        "properties",
    )

    def __init__(self, name, count):
        self.name = name
        self.count = count
        self.properties = []

    def load(self, format, stream):
        if format == b'ascii':
            stream = stream.readline().split()
        return [x.load(format, stream) for x in self.properties]

    def index(self, name):
        for i, p in enumerate(self.properties):
            if p.name == name:
                return i
        return -1


class PropertySpec:
    __slots__ = (
        "name",
        "list_type",
        "numeric_type",
    )
    def __repr__( self ):
        return f"yeah {self.name}, {self.list_type}, {self.numeric_type}"


    def __init__(self, name, list_type, numeric_type):
        self.name = name
        self.list_type = list_type
        self.numeric_type = numeric_type


    def read_format(self, format, count, num_type, stream):
        if format == b'ascii':
            return self.read_format_ascii( format, count, num_type, stream )
        else:
            return self.read_format_binary( format, count, num_type, stream )


    def read_format_ascii(self, format, count, num_type, stream):
        if num_type == 's':
            ans = []
            for i in range(count):
                s = stream[i]
                if not (len(s) >= 2 and s.startswith(b'"') and s.endswith(b'"')):
                    print("Invalid string", s)
                    print("Note: ply_import.py does not handle "\
                            "whitespace in strings")
                    return None
                ans.append(s[1:-1])
            stream[:count] = []
            return ans
        if num_type == 'f' or num_type == 'd':
            mapper = float
        else:
            mapper = int
        ans = [mapper(x) for x in stream[:count]]
        stream[:count] = []
        return ans


    def read_format_binary(self, format, count, num_type, stream):
        import struct
        if num_type == 's':
            ans = []
            for i in range(count):
                fmt = format + 'i'
                data = stream.read(struct.calcsize(fmt))
                length = struct.unpack(fmt, data)[0]
                fmt = '%s%is' % (format, length)
                data = stream.read(struct.calcsize(fmt))
                s = struct.unpack(fmt, data)[0]
                ans.append(s[:-1])  # strip the NULL
            return ans
        else:
            fmt = '%s%i%s' % (format, count, num_type)
            data = stream.read(struct.calcsize(fmt))
            return struct.unpack(fmt, data)


    def load(self, format, stream):
        if self.list_type is not None:
            count = int(self.read_format(format, 1, self.list_type, stream)[0])
            return self.read_format(format, count, self.numeric_type, stream)
        else:
            return self.read_format(format, 1, self.numeric_type, stream)[0]


class ObjectSpec:
    __slots__ = ("specs",)

    def __init__(self):
        # A list of element_specs
        self.specs = []

    def load(self, format, stream):
        return {
            i.name: [
                i.load(format, stream) for j in range(i.count)
            ]
            for i in self.specs
        }

def get_header_line_iterator( custom_line_sep ):
    # Work around binary file reading only accepting "\n" as line separator.
    plyf_header_line_iterator = lambda plyf: plyf
    if custom_line_sep is not None:
        def _plyf_header_line_iterator( plyf ):
            buff = plyf.peek(2**16)
            while len(buff) != 0:
                read_bytes = 0
                buff = buff.split(custom_line_sep)
                for line in buff[:-1]:
                    read_bytes += len(line) + len(custom_line_sep)
                    if line.startswith(b'end_header'):
                        # Since reader code might (will) break iteration 
                        # at this point,
                        # we have to ensure file is read up to here, 
                        # yield, amd return...
                        plyf.read(read_bytes)
                        yield line
                        return
                    yield line
                plyf.read(read_bytes)
                buff = buff[-1] + plyf.peek(2**16)
        plyf_header_line_iterator = _plyf_header_line_iterator
    return plyf_header_line_iterator




class MyPlyInfo():
    def __init__( self, format=None, texture=None, version=None, \
                                                    valid_header=None, \
                        element_specs=[], property_specs=[] ):
        self.format = format
        self.texture = texture
        self.version = version
        self.valid_header = valid_header
        self.element_specs=element_specs
        self.property_specs=property_specs

    def __add__( self, other ):
        format, texture, version, valid_header = None, None, None, None
        def xorproperty( selfproperty, otherproperty ):
            if selfproperty and not otherproperty:
                return selfproperty
            elif not selfproperty and otherproperty:
                return otherproperty
            elif selfproperty and otherproperty:
                raise Exception()
            else:
                return None
        valid_header = xorproperty( self.valid_header, other.valid_header )
        format = xorproperty( self.format, other.format )
        texture = xorproperty( self.texture, other.texture )
        version = xorproperty( self.version, other.version )
        if not self.element_specs and other.property_specs:
            print("Invalid element line")
            raise InvalidPlyFormat()
        if (other.element_specs and other.property_specs) \
                or self.property_specs:
            raise Exception( "failure in algorithm. This program doesnt work." )
        for prop in other.property_specs:
            self.element_specs[-1].properties.append( prop )
        element_specs = self.element_specs + other.element_specs
            
        return type( self )( format=format, texture=texture, \
                            version=version, valid_header=valid_header, \
                            element_specs=element_specs )


def _read_headerline_comment( tokens ):
    try:
        if tokens[1] == b'TextureFile':
            if len(tokens) < 4:
                print("Invalid texture line")
            else:
                texture = tokens[2]
                return MyPlyInfo( texture=texture )
    except IndexError:
        pass
    return MyPlyInfo()

def _read_headerline_end_header( tokens ):
    return MyPlyInfo( valid_header = True )
def _read_headerline_obj_info( tokens ):
    return MyPlyInfo()
class InvalidPlyFormat( Exception ):
    pass
def _read_headerline_format( tokens ):
    format_specs = {
        b'binary_little_endian': '<',
        b'binary_big_endian': '>',
        b'ascii': b'ascii',
    }
    if len(tokens) < 3:
        print("Invalid format line")
        raise InvalidPlyFormat()
    if tokens[1] not in format_specs:
        print("Unknown format", tokens[1])
        raise InvalidPlyFormat()
    #try:
    #    version_test = float(tokens[2])
    #except Exception as ex:
    #    print("Unknown version", ex)
    #    version_test = None
    #if version_test != float(version):
    #    print("Unknown version", tokens[2])
    #    raise InvalidPlyFormat()
    #del version_test
    return MyPlyInfo( format = tokens[1] )

def _read_headerline_element( tokens ):
    if len(tokens) < 3:
        print("Invalid element line")
        raise InvalidPlyFormat()
    return MyPlyInfo( element_specs=[ElementSpec(tokens[1], int(tokens[2]))] )
    #obj_spec.specs.append(ElementSpec(tokens[1], int(tokens[2])))

def _read_headerline_property( tokens ):
    if tokens[1] == b'list':
        return MyPlyInfo( property_specs = [ \
                PropertySpec(tokens[4], type_specs[tokens[2]], type_specs[tokens[3]])] )
        #obj_spec.specs[-1].properties.append(\
        #                    PropertySpec(tokens[4], type_specs[tokens[2]], \
        #                    type_specs[tokens[3]]))
    else:
        return MyPlyInfo( property_specs = [ \
                            PropertySpec(tokens[2], None, type_specs[tokens[1]])] )
        #obj_spec.specs[-1].properties.append(PropertySpec(tokens[2], None, \
        #                    type_specs[tokens[1]]))


def divide_tokennestedlist_to_header_and_data( tokennestedlist ):
    mysplit = lambda line: re.split(br'[ \r\n]+', line)
    headerlist = []
    data = []
    inheader = True
    for line in tokennestedlist:
        if inheader:
            tokens = mysplit( line )
            if len(tokens) > 0:
                headerlist.append( tokens )
                if tokens[0] == b'end_header':
                    inheader = False
        else:
            data.append( line )
    return headerlist, data


def test_signature( mystream ):
    signature = mystream.peek(5)

    if not signature.startswith(b'ply') or not len(signature) >= 5:
        raise InvalidPlyFormat()

    custom_line_sep = None
    if signature[3] != ord(b'\n'):
        if signature[3] != ord(b'\r'):
            print("Unknown line separator")
            return invalid_ply
        if signature[4] == ord(b'\n'):
            custom_line_sep = b"\r\n"
        else:
            custom_line_sep = b"\r"

    return custom_line_sep

def read(filepath):

    format = b''
    texture = b''
    version = b'1.0'
    format_specs = {
        b'binary_little_endian': '<',
        b'binary_big_endian': '>',
        b'ascii': b'ascii',
    }
    obj_spec = ObjectSpec()
    invalid_ply = (None, None, None)
    
    with open(filepath, 'rb') as plyf:

        try:
            custom_line_sep = test_signature( plyf )
        except InvalidPlyFormat:
            print("Signature line was invalid")
            return invalid_ply

        plyf_header_line_iterator = get_header_line_iterator( custom_line_sep )
        tokenlines = [ line for line in plyf_header_line_iterator(plyf) ]
        headerlines, datalines = divide_tokennestedlist_to_header_and_data( 
                                                            tokenlines )

    temp_info = MyPlyInfo()
    try:
        for tokens in headerlines:
            if tokens[0] == b'end_header':
                temp_info += _read_headerline_end_header( tokens )
            elif tokens[0] == b'comment':
                temp_info += _read_headerline_comment( tokens )
            elif tokens[0] == b'obj_info':
                temp_info += _read_headerline_obj_info( tokens )
            elif tokens[0] == b'format':
                temp_info += _read_headerline_format( tokens )
            elif tokens[0] == b'element':
                temp_info += _read_headerline_element( tokens )
            elif tokens[0] == b'property':
                temp_info += _read_headerline_property( tokens )

            if temp_info.valid_header:
                break
    except InvalidPlyFormat:
        return invalid_ply
    if not temp_info.valid_header:
        print("Invalid header ('end_header' line not found!)")
        return invalid_ply

    format = temp_info.format
    texture = temp_info.texture
    version = temp_info.version
    obj_spec.specs = temp_info.element_specs

    dataiterator = iterable_to_stream( \
                                itertools.chain( *datalines ) \
                                )
    obj = obj_spec.load(format_specs[format], dataiterator)

    return obj_spec, obj, texture

class index_info():
    def __init__( self, \
                        vindices_x=None, vindices_y=None, vindices_z=None, \
                        uvindices_s=None, uvindices_t=None, \
                        colindices=None, colmultiply=None, \
                        findex=None, \
                        rtindex=None, \
                        borderrectangle_leftup = None, \
                        borderrectangle_rightup = None, \
                        borderrectangle_rightdown = None, \
                        borderrectangle_leftdown = None, \
                        eindex1=None, eindex2=None ):
        self.vindices_x, self.vindices_y, self.vindices_z \
                    = vindices_x, vindices_y, vindices_z
        self.uvindices_s, self.uvindices_t = uvindices_s, uvindices_t
        #self.colindices_r, self.colindices_b, self.colindices_g \
        #        = colindices_r, colindices_b, colindices_g
        #self.colindices_alpha = colindices_alpha
        self.colindices = colindices
        self.colmultiply=colmultiply
        self.findex = findex
        self.rtindex = rtindex
        self.eindex1, self.eindex2 = eindex1, eindex2
        self.borderrectangle_leftup = borderrectangle_leftup
        self.borderrectangle_rightup = borderrectangle_rightup
        self.borderrectangle_rightdown = borderrectangle_rightdown 
        self.borderrectangle_leftdown = borderrectangle_leftdown

    def __add__( self, other ):
        def xorproperty( selfproperty, otherproperty ):
            if selfproperty!=None and not otherproperty!=None:
                return selfproperty
            elif not selfproperty!=None and otherproperty!=None:
                return otherproperty
            elif selfproperty!=None and otherproperty!=None:
                raise Exception()
            else:
                return None
        vindices_x = xorproperty( self.vindices_x, other.vindices_x )
        vindices_y = xorproperty( self.vindices_y, other.vindices_y )
        vindices_z = xorproperty( self.vindices_z, other.vindices_z )
        uvindices_s = xorproperty( self.uvindices_s, other.uvindices_s )
        uvindices_t = xorproperty( self.uvindices_t, other.uvindices_t )
        colindices = xorproperty( self.colindices, other.colindices )
        #colindices_b = xorproperty( self.colindices_b, other.colindices_b )
        #colindices_g = xorproperty( self.colindices_g, other.colindices_g )
        #colindices_alpha = xorproperty( self.colindices_alpha, \
        #                                other.colindices_alpha )
        colmultiply = xorproperty( self.colmultiply, other.colmultiply )
        findex = xorproperty( self.findex, other.findex )
        rtindex = xorproperty( self.rtindex, other.rtindex )
        eindex1 = xorproperty( self.eindex1, other.eindex1 )
        eindex2 = xorproperty( self.eindex2, other.eindex2 )
        leftup = xorproperty( self.borderrectangle_leftup, \
                                                other.borderrectangle_leftup )
        rightup = xorproperty( self.borderrectangle_rightup, \
                                                other.borderrectangle_rightup )
        rightdown = xorproperty(self.borderrectangle_rightdown,\
                                                other.borderrectangle_rightdown)
        leftdown = xorproperty( self.borderrectangle_leftdown,\
                                                other.borderrectangle_leftdown)
        return type(self)( \
                        vindices_x, vindices_y, vindices_z, \
                        uvindices_s, uvindices_t, \
                        colindices, \
                        colmultiply, \
                        findex, \
                        rtindex, \
                        leftup, rightup, rightdown, leftdown, \
                        eindex1, eindex2 )

def process_vertex( el ):
    vindices_x, vindices_y, vindices_z, colindices, colmultiply \
                    = None, None, None, None, None

    vindices_x, vindices_y, vindices_z \
                    = el.index(b'x'), el.index(b'y'), el.index(b'z')
    # noindices = (el.index('nx'), el.index('ny'), el.index('nz'))
    # if -1 in noindices: noindices = None
    uvindices = (el.index(b's'), el.index(b't'))
    if -1 in uvindices:
        uvindices = (None, None )
    # ignore alpha if not present
    if el.index(b'alpha') == -1:
        colindices = el.index(b'red'), el.index(b'green'), el.index(b'blue')
    else:
        colindices = el.index(b'red'), el.index(b'green'), el.index(b'blue'), \
                                                        el.index(b'alpha')
    if -1 in colindices:
        if any(idx > -1 for idx in colindices):
            print("Warning: At least one obligatory color channel "\
                    "is missing, ignoring vertex colors.")
        colindices = None
    else:  # if not a float assume uchar
        colmultiply = [1.0 if el.properties[i].numeric_type in {'f', 'd'} \
                        else (1.0 / 255.0) for i in colindices]
    return  index_info( vindices_x=vindices_x, vindices_y=vindices_y, \
                        vindices_z=vindices_z, colindices=colindices, \
                        uvindices_s=uvindices[0], uvindices_t=uvindices[1], \
                        colmultiply=colmultiply )
def process_face( el ):
    findex = el.index(b'vertex_indices')
    return index_info( findex =findex )
def process_tristrips( el ):
    trindex = el.index(b'vertex_indices')
    return index_info( trindex=trindex )
def process_edge( el ):
    eindex1, eindex2 = el.index(b'vertex1'), el.index(b'vertex2')
    return index_info( eindex1=eindex1, eindex2=eindex2 )
def process_cornerrectangle( el ):
    return index_info( \
                        borderrectangle_leftup = el.index(b'leftup'), \
                        borderrectangle_rightup = el.index(b'rightup'), \
                        borderrectangle_rightdown = el.index(b'rightdown'), \
                        borderrectangle_leftdown = el.index(b'leftdown'), \
            )


def add_face_tolists(vertices, indices, uvindices, colindices, \
                        mesh_faces, mesh_uvs, mesh_colors ):
    mesh_faces.append(indices)
    if uvindices:
        mesh_uvs.extend([(vertices[index][uvindices[0]], \
                            vertices[index][uvindices[1]]) \
                            for index in indices])
    if colindices:
        if len(colindices) == 3:
            mesh_colors.extend([
                (
                    vertices[index][colindices[0]] * colmultiply[0],
                    vertices[index][colindices[1]] * colmultiply[1],
                    vertices[index][colindices[2]] * colmultiply[2],
                    1.0,
                )
                for index in indices
            ])
        elif len(colindices) == 4:
            mesh_colors.extend([
                (
                    vertices[index][colindices[0]] * colmultiply[0],
                    vertices[index][colindices[1]] * colmultiply[1],
                    vertices[index][colindices[2]] * colmultiply[2],
                    vertices[index][colindices[3]] * colmultiply[3],
                )
                for index in indices
            ])

def decorator_resort_vertices( my_add_face ):
    def new_add_face(vertices, indices, uvindices, colindices):
        if len(indices) == 4:
            if indices[2] == 0 or indices[3] == 0:
                indices = indices[2], indices[3], indices[0], indices[1]
        elif len(indices) == 3:
            if indices[2] == 0:
                indices = indices[1], indices[2], indices[0]

        my_add_face(vertices, indices, uvindices, colindices)
    return new_add_face


def generate_blender_mesh( ply_name, vertinfo, edgeinfo, mesh_faces, \
                                    uvindices, \
                                    colindices, vindices_x, vindices_y, \
                                    vindices_z, mesh_colors ):
    mesh = bpy.data.meshes.new(name=ply_name)

    mesh.vertices.add(len(vertinfo))#obj[b'vertex']))

    mesh.vertices.foreach_set("co", [a for v in vertinfo \
                        for a in (v[vindices_x], v[vindices_y], v[vindices_z])])

    if edgeinfo:
        mesh.edges.add(len(edgeinfo))#obj[b'edge']))
        mesh.edges.foreach_set("vertices", [a for e in edgeinfo \
                                            for a in (e[eindex1], e[eindex2])])

    if mesh_faces:
        loops_vert_idx = []
        faces_loop_start = []
        faces_loop_total = []
        lidx = 0
        for f in mesh_faces:
            print( f)
            nbr_vidx = len(f)
            loops_vert_idx.extend(f)
            faces_loop_start.append(lidx)
            faces_loop_total.append(nbr_vidx)
            lidx += nbr_vidx

        mesh.loops.add(len(loops_vert_idx))
        mesh.polygons.add(len(mesh_faces))

        mesh.loops.foreach_set("vertex_index", loops_vert_idx)
        mesh.polygons.foreach_set("loop_start", faces_loop_start)
        mesh.polygons.foreach_set("loop_total", faces_loop_total)

        if uvindices:
            uv_layer = mesh.uv_layers.new()
            for i, uv in enumerate(uv_layer.data):
                uv.uv = mesh_uvs[i]

        if colindices:
            vcol_lay = mesh.vertex_colors.new()

            for i, col in enumerate(vcol_lay.data):
                col.color[0] = mesh_colors[i][0]
                col.color[1] = mesh_colors[i][1]
                col.color[2] = mesh_colors[i][2]
                col.color[3] = mesh_colors[i][3]

    mesh.update()
    mesh.validate()
    return mesh


def load_ply_data( ply_name, obj_spec, obj, texture ):
    # TODO import normals
    # noindices = None

    myinfo = index_info()
    for el in obj_spec.specs:
        if el.name == b'vertex':
            myinfo += process_vertex( el )
        elif el.name == b'face':
            myinfo += process_face( el )
        elif el.name == b'tristrips':
            myinfo += process_tristrips( el )
        elif el.name == b'edge':
            myinfo += process_edge( el )
        elif el.name == b'cornerrectangle':
            myinfo += process_cornerrectangle( el )
        else:
            print( f"found element \"{el.name.decode('utf-8')}\" "\
                    "which is not handled" )


    vindices_x, vindices_y, vindices_z = \
                        myinfo.vindices_x, myinfo.vindices_y, myinfo.vindices_z
    if myinfo.uvindices_s:
        uvindices = (myinfo.uvindices_s, myinfo.uvindices_t)
    else:
        uvindices = None
    colindices = myinfo.colindices
    colmultiply = myinfo.colmultiply
    findex = myinfo.findex
    rtindex = myinfo.rtindex
    eindex1, eindex2 = myinfo.eindex1, myinfo.eindex2
    if myinfo.borderrectangle_leftup != None:
        borderrectangle = ( myinfo.borderrectangle_leftup, \
                            myinfo.borderrectangle_rightup, \
                            myinfo.borderrectangle_rightdown, \
                            myinfo.borderrectangle_leftdown )
    else:
        borderrectangle = None


    mesh_faces = []
    mesh_uvs = []
    mesh_colors = []

    add_face = lambda vertices, indices, uvindices, colindices: \
                    add_face_tolists(vertices, indices, uvindices, colindices,\
                                        mesh_faces, mesh_uvs, mesh_colors )
    if uvindices or colindices:
        add_face = decorator_resort_vertices( add_face )

    verts = obj[b'vertex']
    try:
        edgeinfo = obj[b'edge']
    except KeyError:
        edgeinfo = None
    if b'face' in obj:
        for f in obj[b'face']:
            ind = f[findex]
            add_face(verts, ind, uvindices, colindices)
    if b'tristrips' in obj:
        for t in obj[b'tristrips']:
            ind = t[trindex]
            len_ind = len(ind)
            for j in range(len_ind - 2):
                add_face(verts, (ind[j], ind[j + 1], ind[j + 2]), \
                                    uvindices, colindices)

    return verts, edgeinfo, mesh_faces, uvindices, \
                                    colindices, vindices_x, vindices_y, \
                                    vindices_z, mesh_colors, borderrectangle
    mesh = generate_blender_mesh( ply_name, verts, edgeinfo, mesh_faces, \
                                    uvindices, \
                                    colindices, vindices_x, vindices_y, \
                                    vindices_z, mesh_colors )

    return mesh
    if texture and uvindices:
        pass
        # TODO add support for using texture.

        # import os
        # import sys
        # from bpy_extras.image_utils import load_image

        # encoding = sys.getfilesystemencoding()
        # encoded_texture = texture.decode(encoding=encoding)
        # name = bpy.path.display_name_from_filepath(texture)
        # image = load_image(encoded_texture, os.path.dirname(filepath), recursive=True, place_holder=True)

        # if image:
        #     texture = bpy.data.textures.new(name=name, type='IMAGE')
        #     texture.image = image

        #     material = bpy.data.materials.new(name=name)
        #     material.use_shadeless = True

        #     mtex = material.texture_slots.add()
        #     mtex.texture = texture
        #     mtex.texture_coords = 'UV'
        #     mtex.use_map_color_diffuse = True

        #     mesh.materials.append(material)
        #     for face in mesh.uv_textures[0].data:
        #         face.image = image

    return mesh

def create_vertexgroup_with_vertices( motherobject, groupname, vertices ):
    """
    :type vertices: list
    :type *vertices: integer
    """
    weight = 0
    my_vertgroup = motherobject.vertex_groups.new( name=groupname )
    my_vertgroup.add( vertices, weight, "ADD" )


