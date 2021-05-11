import struct
import itertools

class DataLoadError( Exception):
    pass
class InvalidPlyFormat( Exception ):
    pass


def plycontainer_from_arrays( myarrays ):
    myobj_spec = ObjectSpec()
    for elementname, properties, dataforeachprop in myarrays:
        data = list( itertools.zip_longest( *dataforeachprop ) )
        tmpel = ElementSpec( elementname, len(data) )
        myobj_spec.specs.append( tmpel )
        for prop in properties:
            tmpprop = PropertySpec( prop[-1], *prop[:-1] )
            tmpel.properties.append( tmpprop )
        for singledata in data:
            tmpel.insert_element_with_data( *singledata )
    return myobj_spec


class ObjectSpec:
    __slots__ = (
            "specs",\
            "_loadformat", \
            "_loadversion", \
            )

    def __init__(self):
        # A list of element_specs
        self.specs = []

    def set_load_format( self, myformat ):
        self._loadformat = bytes( myformat )
    def set_load_version( self, version ):
        self._loadversion = version

    def load_data_for_elements(self, datapart_of_file_bytes):
        format = self._loadformat
        if format == b'ascii':
            alllines = ( line.split()
                        for line in datapart_of_file_bytes.splitlines() )
            filteredlines = ( tokens for tokens in alllines if len(tokens)>0)
            datastream = iter( filteredlines )
        elif format == b'binary_little_endian' \
                    or format == b'binary_big_endian':
            datastream = iter( datapart_of_file_bytes )
        else:
            raise InvalidPlyFormat( f"format '{format}' isnt supported" )

        try:
            for el in self.specs:
                el.finalize_properties()
                tmpdataloader = el.get_dataloader( format )
                for i in range( el.count ):
                    if format == b'ascii':
                        lineiterator = iter( datastream.__next__() )
                        tmpdataloader( lineiterator )
                    else:
                        tmpdataloader( datastream )
        except DataLoadError as err:
            raise InvalidPlyFormat( "header doesnt match with data" ) from err
        try:
            datastream.__next__()
            #if there is still data raise exception
            raise InvalidPlyFormat( "more data than in header specified" )
        except StopIteration:
            pass

    def __getitem__( self, key ):
        for el in self.specs:
            try:
                asciiname = str( el.name, encoding="ascii" )
            except Exception():
                asciiname = None
            if key == asciiname or key == el.name:
                return el
        raise KeyError( f"not found: {key}" )

    def keys( self, encoding=None ):
        if encoding:
            trans = lambda x: str( x, encoding=encoding )
        else:
            trans = lambda x: x
        return [ trans( el.name ) for el in self.specs ]


class ElementSpec:
    __slots__ = (
        "name",
        "count",
        "properties",
        "data",
        "finalized_properties", 
    )

    def __init__(self, name, count):
        self.name = name
        self.count = count
        self.properties = []
        self.data = []
        self.finalized_properties = False

    def finalize_properties( self ):
        self.finalized_properties = True

    def insert_element_with_data( self, *nextdata ):
        nextdata = list(( *nextdata, )) #?
        #produces error when nextdata is read twice. Maybe because of use
        # of iterators.
        if len( nextdata ) != len( self.properties ):
            raise Exception( ("inserted element must be same length %d"\
                            "as number of properties(%d)") \
                            %(len( nextdata),len(self.properties)))
        self.data.append( tuple((*nextdata,)) )

    def get_dataloader( self, format ):
        property_loader_array = [ prop.get_datagrabber( format )\
                                    for prop in self.properties ]
        def mydataloader( datastream ):
            nextdata = []
            for proploader in property_loader_array:
                nextdata.append( proploader( datastream ) )
            self.insert_element_with_data( *nextdata )
        return mydataloader

    def to_plyfileline(self):
        tostr = lambda x: x if type(x)==str \
                            else x.decode( "ascii" )
        return [" ".join(["element", tostr(self.name), \
                                    str( self.count )])\
                                    ,]

    def to_plydata( self, myformat ):
        #if myformat == "ascii":
        mytransarray = [ prop.get_toply_translator( myformat ) \
                        for prop in self.properties ]
        asd = bytearray()
        if myformat == "ascii":
            for data in self.data:
                line = list((mytransarray[i](single) \
                            for i, single in enumerate(data)))
                line = list( itertools.chain( *line ) )
                line = " ".join(line) + "\n"
                asd.extend( line.encode( myformat ) )
        else:
            raise Exception()
        return asd

    def get_datatranslator( self, format ):
        trans_array = [ prop.get_singletranslator( format ) \
                        for prop in self.properties ]
        num_properties = len( trans_array )
        if format == b'ascii':
            def mytrans( *args ):
                #return tuple( trans_array[i](args[i]) \
                return tuple( trans_array[i] \
                                for i in range( len(args)) )
        elif bytes(format) in (b'binary_little_endian',b'binary_big_endian'):
            slices = []
            current_index = 0
            for prop in self.properties:
                new_index = current_index \
                                + numtype_len[ bytes(prop.numeric_type) ]
                slices.append((current_index, new_index))
                current_index = new_index
            def mytrans( *inputbytes ):
                a = [ bytearray( inputbytes[ slices[i][0]:slices[i][1] ] )\
                                for i in range( num_properties ) ]
                return tuple( trans_array[i]( a[i] ) \
                                for i in range( num_properties) )
        else:
            raise InvalidPlyFormat()
        return mytrans

    def load(self, format, stream):
        if format == b'ascii':
            stream = stream.readline().split()
        return [x.load(format, stream) for x in self.properties]

    def get_filtered_data( self, *keys ):
        indices = [ self.index( key ) for key in keys ]
        datafilter = lambda singledata: tuple( singledata[i] for i in indices )
        return [ datafilter( singledata ) for singledata in self.data ]


    def index( self, key ):
        if type( key ) == str:
            key = key.encode( "ascii" )
        namelist = [ prop.name for prop in self.properties ]
        return namelist.index( key )

    def __getitem__( self, key ):
        for prop in self.properties:
            try:
                asciiname = str( prop.name, encoding="ascii" )
            except Exception():
                asciiname = None
            if key == asciiname or key == prop.name:
                return prop
        raise KeyError( f"{self.name} doesnt contain: {key}" )

    def keys( self, encoding=None ):
        if encoding:
            trans = lambda x: str( x, encoding=encoding )
        else:
            trans = lambda x: x
        return [ trans( prop.name ) for prop in self.properties ]



class PropertySpec:
    __slots__ = (
        "name",
        "datalength_type",
        "numeric_type",
        "propertytype", 
    )
    def __repr__( self ):
        return f"(asd{self.name}, {self.propertytype})"

    def __init__(self, name, propertytype, *args):
        interpret = { bytes: lambda x: x,\
                        str: lambda x: bytes( x, "ascii" ),\
                        bytearray: lambda x: bytes(x) }
        tobytes = lambda x: interpret[ type(x) ]( x )
        self.name = name
        if propertytype == b"list" or propertytype == "list":
            self.propertytype = propertytype
            self.numeric_type = tobytes( args[1] )
            self.datalength_type = tobytes( args[0] )
        else:
            self.propertytype = propertytype
            self.numeric_type = tobytes( propertytype )
            self.datalength_type = None

    def get_datagrabber( self, format ):
        if bytes(format) == b"ascii":
            get_data_from_iterator = lambda stream, l: \
                                        stream.__next__()
        elif bytes(format) in (b'binary_little_endian',\
                                b'binary_big_endian'):
            get_data_from_iterator \
                        = lambda stream, bytelength: \
                        bytearray( stream.__next__() \
                                    for i in range(bytelength))
        else:
            raise InvalidPlyFormat()
        if self.propertytype == b"list":
            lengthtranslator = self.get_singletranslator(format,\
                                        self.datalength_type )
            mytrans = self.get_singletranslator( format, \
                                        self.numeric_type )
            lengthbyteslength = numtype_len[self.datalength_type]
            datalength = numtype_len[ self.numeric_type ]
            def mygrabber( iterator_data ):
                lengthbytes = get_data_from_iterator( \
                                        iterator_data, \
                                        lengthbyteslength )
                length = lengthtranslator( lengthbytes )
                asd = []
                for i in range( length ):
                    data = get_data_from_iterator(iterator_data,\
                                        datalength )
                    asd.append( mytrans( data ))
                return tuple( asd )
            return mygrabber
        else:
            mytrans = self.get_singletranslator( format, \
                                            self.numeric_type )
            datalength = numtype_len[ self.numeric_type ]
            def mygrabber( iterator_data ):
                data = get_data_from_iterator( iterator_data, \
                                            datalength )
                return mytrans( data )
            return mygrabber

    def is_list( self ):
        return self.propertytype == b"list" \
                or self.propertytype == "list"
                    

    def to_plyfileline(self):
        tostr = lambda x: x if type(x)==str \
                            else x.decode( "ascii" )
        if self.is_list():
            description = ( "list", \
                                tostr( self.datalength_type ), \
                                tostr( self.numeric_type ), \
                                )
        else:
            description = [ tostr(self.numeric_type ), ]

        name = tostr( self.name )

        return [" ".join(["property", *description, name]),]

    def get_toply_translator( self, format ):
        if self.propertytype == b"list" or self.propertytype == "list":
            def mytranslator( inarray ):
                try:
                    (a,) = toascii_transfunction[self.datalength_type]\
                                                    ( len( inarray ))
                except TypeError as err:
                    raise KeyError("should translate ist but there is no list")\
                                    from err
                datatrans = toascii_transfunction[self.numeric_type]
                #this seems awful
                data_translated = ( datatrans(x) for x in inarray )
                return tuple( (a, *(x for (x,) in data_translated)) )
            return mytranslator
        else:
            return toascii_transfunction[ self.numeric_type ]
        return 

    def get_singletranslator( self, format, numeric_type ):
        alltrans = trans_for_format[ format ]
        return alltrans[ bytes( numeric_type ) ]

toascii_transfunction= {\
        b"char": lambda x: ("%d"%(x),), \
        b"uchar": lambda x: ("%d"%(x),), \
        b"short": lambda x: ("%d"%(x),), \
        b"ushort": lambda x: ("%d"%(x),), \
        b"int": lambda x: ("%d"%(x),), \
        b"uint": lambda x: ("%d"%(x),), \
        b"float": lambda x: ("%f"%(x),), \
        b"double": lambda x: ("%.14f"%(x),), \
        }

single_translator_ascii = {\
        b"char": int,\
        b"uchar": int,\
        b'short': int,\
        b'ushort': int,\
        b'int': int,\
        b'uint': int,\
        b'float': float,\
        b'double': float,\
        }
single_translator_binary_little = {\
        b"char": lambda x: int.from_bytes( x, "little", signed=True ),\
        b"uchar": lambda x: int.from_bytes( x, "little", signed=False ),\
        b'short': lambda x: int.from_bytes( x, "little", signed=True ),\
        b'ushort': lambda x: int.from_bytes( x, "little", signed=False ),\
        b'int': lambda x: int.from_bytes( x, "little", signed=True ),\
        b'uint': lambda x: int.from_bytes( x, "little", signed=False ),\
        b'float': lambda x: struct.unpack( "<f", x )[0], \
        b'double': lambda x: struct.unpack( "<d", x )[0], \
        }
single_translator_binary_big = {\
        b"char": lambda x: int.from_bytes( x, "big", signed=True ),\
        b"uchar": lambda x: int.from_bytes( x, "big", signed=False ),\
        b'short': lambda x: int.from_bytes( x, "big", signed=True ),\
        b'ushort': lambda x: int.from_bytes( x, "big", signed=False ),\
        b'int': lambda x: int.from_bytes( x, "big", signed=True ),\
        b'uint': lambda x: int.from_bytes( x, "big", signed=False ),\
        b'float': lambda x: struct.unpack( ">f", x )[0], \
        b'double': lambda x: struct.unpack( ">d", x )[0], \
        }
trans_for_format = { \
        b"ascii": single_translator_ascii, \
        b"binary_little_endian": single_translator_binary_little, \
        b"binary_big_endian": single_translator_binary_big, \
        }
numtype_len = { \
        b"char": 1, \
        b"uchar": 1, \
        b'short': 2, \
        b'ushort': 2, \
        b'int': 4, \
        b'uint': 4, \
        b'float': 4, \
        b'double': 8, \
        }
