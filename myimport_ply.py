from .datacontainer import *

def load_ply_obj_from_filename( filename ):
    header, data = get_header_and_data_from_file( filename )
    obj_spec = create_emptyobj_spec_from_header( header )
    obj_spec.load_data_for_elements( data )
    return obj_spec


class InvalidPlyFormat( Exception ):
    pass


def get_header_and_data_from_file( filename ):
    with open( filename, "rb" ) as plyfile:
        custom_lineseparator = test_signature( plyfile )
        mylineiterator = lineiterator( plyfile, custom_lineseparator )
    last=[None]
    header = []
    while last[0] != b"end_header":
        last = mylineiterator.__next__()
        header.append( last )
    header = [ line for line in header if len( line ) > 0 ]
    data = mylineiterator.get_remaining()
    return header, data


class lineiterator():
    def __init__( self, myfile, custom_lineseparator ):
        mybytes = bytearray()
        nextbytes = myfile.read(64)
        while nextbytes:
            mybytes.extend( nextbytes )
            nextbytes = myfile.read(64)

        self.custom_lineseparator = custom_lineseparator
        self.mybytes = mybytes
        self.byteit = iter( mybytes )

    def get_nextline( self ):
        a = self.byteit.__next__()
        if a == self.custom_lineseparator:
            return
        yield a
        try:
            while True:
                a = self.byteit.__next__()
                if a == self.custom_lineseparator:
                    return
                yield a
        except StopIteration:
            return

    def __next__( self ):
        asd = self.get_nextline()
        return bytearray( asd ).split()

    def get_remaining( self ):
        def helper():
            try:
                while True:
                    yield self.byteit.__next__()
            except StopIteration:
                return
        return bytearray( helper() )


def test_signature( mystream ):
    signature = mystream.peek(5)

    if not signature.startswith(b'ply') or not len(signature) >= 5:
        raise InvalidPlyFormat()

    custom_line_sep = ord(b"\n")
    if signature[3] != ord(b'\n'):
        if signature[3] != ord(b'\r'):
            print("Unknown line separator")
            return invalid_ply
        if signature[4] == ord(b'\n'):
            custom_line_sep = b"\r\n"
        else:
            custom_line_sep = b"\r"

    return custom_line_sep


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
def _read_headerline_format( tokens ):
    format_specs = {
        b'binary_little_endian', #: 'binary_little_endian',
        b'binary_big_endian', #: 'binary_big_endian',
        b'ascii', #: 'ascii',
    }
    if len(tokens) < 3:
        print("Invalid format line")
        raise InvalidPlyFormat()
    if bytes(tokens[1]) not in format_specs:
        print("Unknown format", tokens[1])
        raise InvalidPlyFormat()
    if tokens[2] != b'1.0':
        raise InvalidPlyFormat( "supported ply-version: '1.0' "\
                                +f"given: {tokens[2]}" )
    return MyPlyInfo( format = tokens[1] )


def _read_headerline_element( tokens ):
    if len(tokens) < 3:
        print("Invalid element line")
        raise InvalidPlyFormat()
    return MyPlyInfo( element_specs=[ElementSpec(tokens[1], int(tokens[2]))] )
    #obj_spec.specs.append(ElementSpec(tokens[1], int(tokens[2])))


def _read_headerline_property( tokens ):
    return MyPlyInfo( property_specs = [ PropertySpec( tokens[-1], tokens[1], *tokens[2:-1] ) ])
    if tokens[1] == b'list':
        return MyPlyInfo( property_specs = [ \
                            PropertySpec(tokens[4], tokens[2], \
                            tokens[3])] )
    else:
        return MyPlyInfo( property_specs = [ \
                            PropertySpec(tokens[2], None, \
                            tokens[1])] )


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
            raise Exception( "failure in algorithm. This program doesnt work.")
        for prop in other.property_specs:
            self.element_specs[-1].properties.append( prop )
        element_specs = self.element_specs + other.element_specs
            
        return type( self )( format=format, texture=texture, \
                            version=version, valid_header=valid_header, \
                            element_specs=element_specs )


def create_emptyobj_spec_from_header( headerlines ):
    obj_spec = ObjectSpec()

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

    obj_spec.specs = temp_info.element_specs
    obj_spec.set_load_format( temp_info.format )
    obj_spec.set_load_version( temp_info.version )

    return obj_spec


if __name__ == "__main__":
    #testing
    filename = "/home/hfechner/tmp.ply"
    filename = "/home/hfechner/meshfortests.ply"
    myobj = load_ply_obj_from_filename( filename )
    for el in myobj.specs:
        print( el.name )
        try:
            asd = iter( range(5) )
            for q in el.data:
                asd.__next__()
                print( q )
        except StopIteration:
            print( "..." )

    print( myobj.keys( encoding="utf-8" ) )
    a = myobj.keys( encoding="utf-8" )
    for el in myobj.specs:
        print( el.keys( encoding="utf-8" ) )
        b = el.keys( encoding="utf-8" )
        print( "brubru", el[b[0]] )

