
def export_plyfile( filename, ply_info, myformat ):
    tostr = lambda x: x if type(x)==str \
                            else x.decode( "utf-8" )
    if tostr(myformat) not in ("ascii", "binary_little_endian", \
                                        "binary_big_endian"):
        raise Exception()
    header = generate_header( ply_info, myformat )
    data = generate_data( ply_info, myformat )
    tmptext = "\n".join( " ".join(lines) for lines in header )\
                + "\n"
    tmptext = tmptext.encode( "utf-8" )
    tobytes = lambda x: x.encode( "utf-8" ) if type(x)==str \
                        else bytes( x )
    tmptext += tobytes( data )
    #print( tmptext )
    asd = open( filename, "wb" )
    asd.write( tmptext )
    asd.close()

def generate_data( ply_info, myformat ):
    mybytes = bytearray()
    for el in ply_info.specs:
        mybytes.extend( el.to_plydata( myformat ) )

    return mybytes


def generate_header( ply_info, myformat ):
    header = [["ply",],]
    version = "1.0"
    header.append( ["format", myformat, version] )
    for el in ply_info.specs:
        header.append( el.to_plyfileline() )
        for prop in el.properties:
            header.append( prop.to_plyfileline() )
    header.append(["end_header"])
    return header


if __name__ == "__main__":
    from myimport_ply import *
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
    export_plyfile( "/home/hfechner/tester.ply", \
                    myobj, "ascii" )


