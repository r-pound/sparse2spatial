def add_longhurst_raster_array_and_LWI_core_NetCDFs():
    """ Driver to add Longhurst Provinces to files """
    Filenames = [
        'Oi_prj_predicted_iodide_0.125x0.125_No_Skagerrak',
        'Oi_prj_feature_variables_0.125x0.125',
        'Oi_prj_predicted_iodide_0.125x0.125',
    ]
    folder = '/work/home/ts551/data/iodide/'
    for name in Filenames:
        print(name)
        # Open dataset
        ds = xr.open_dataset(folder + name+'.nc')
        # Longhurst Province to dataset
        ds = add_Longhurst_Province_raster_to_array(ds)
        # Add LWI index too
        ds = add_LWI2array(ds, res='0.125x0.125')
        # Save dataset
        ds.to_netcdf(name+'_with_Provinces_II.nc')
        del ds


def add_Longhurst_Province_raster_to_array(ds):
    """ Add Longhurst Province to dataset as a raste"""
    import geopandas
    from rasterio import features
    from affine import Affine

    # - Get the shape files
    provinces = geopandas.read_file('/work/home/ts551/data/longhurst_v4_2010')
    shapes = [(shape, n) for n, shape in enumerate(provinces.geometry)]

    # - Now add the existing array
    ds_tmp = ds[list(ds.data_vars)[0]].copy().mean(dim='time')
    # Add raster the provinces onto this
    ds_tmp['LonghurstProvince'] = rasterize(shapes, ds_tmp.coords)
    # Then
    ds['LonghurstProvince'] = ds_tmp['LonghurstProvince']
    # Add Some attributes
    attrs = {
        'Long name': 'Longhurst Provinces',
        'data downloaded from': 'http://www.marineregions.org/downloads.php#longhurst',
        'version': 'Version 4 - March 2010',
        'Citations': "Longhurst, A.R et al. (1995). An estimate of global primary production in the ocean from satellite radiometer data. J. Plankton Res. 17, 1245-1271 ; Longhurst, A.R. (1995). Seasonal cycles of pelagic production and consumption. Prog. Oceanogr. 36, 77-167 ; Longhurst, A.R. (1998). Ecological Geography of the Sea. Academic Press, San Diego. 397p. (IMIS) ; Longhurst, A.R. (2006). Ecological Geography of the Sea. 2nd Edition. Academic Press, San Diego, 560p.",
    }
    ds['LonghurstProvince'].attrs = attrs
    return ds


def add_LonghurstProvince2NetCDF(ds=None, res='4x5', LatVar='lat', LonVar='lon',
                                 CoordVar='Province', ExStr=''):
    """ Add numbers for Longhurst Provinces to NetCDF """
    # Get xml data  for provinces
    provinces, tree = ParseLonghurstProvinceFile()
    # Just use 4x5 as an example
    if isinstance(ds, type(None)):
        filename = 'Oi_prj_feature_variables_{}.nc'.format(res)
        folder = get_Oi_file_locations('iodide_data')
        ds = xr.open_dataset(folder + filename)
    # get dictionary of province numbers
    Rnum2prov = RosieLonghurstProvinceFileNum2Province(
        None, invert=True, rtn_dict=True)
    # use an existing variables as a template
#	var2use = 'WOA_TEMP'
#	df = ds[var2use].mean(dim='time')
#	df = ds[var2use].mean(dim='time').to_pandas()
    # get lats
    DSlats = ds[LatVar].values
    # get lons
    DSlons = ds[LonVar].values
    # Get all lats and make a long form of the coords.
    lats = []
    lons = []
    coords = []
    for lat in DSlats:
        for lon in DSlons:
            lats += [lat]
            lons += [lon]
#			coords += [ (lon,lat) ]
    # make into a DataFrame
    df = pd.DataFrame()
    df[LatVar] = lats
    df[LonVar] = lons
#	df[CoordVar] = coords
    # Add a single variable for the coordinate

    def f(x):
        return (x[LonVar], x[LatVar])
    df[CoordVar] = df.apply(f, axis=1)
    # map the calculation of provinces

    def GetProv(x):
        return Get_LonghurstProvince4coord(x[CoordVar], provinces=provinces,
                                           num2prov=Rnum2prov, tree=tree, verbose=False)
    df[CoordVar] = df.apply(GetProv, axis=1)
    # kludge test
    df.to_csv('Intial_test_{}_{}.csv'.format(res, ExStr))

    # construct DataFrame by unstacking
    lat = df[LatVar].values
    lon = df[LonVar].values
    vals = df[CoordVar].values
    df = pd.DataFrame(vals, index=[lat, lon]).unstack()
    df.to_csv('Intial_test_{}_processed_{}.csv'.format(res, ExStr))

    # convert to Dataset
#	ds[CoordVar] = df.values
#	ds[CoordVar]
    ds = xr.Dataset(data_vars={CoordVar: (['lat', 'lon', ], df.values)},
                    coords={'lat': DSlats, 'lon': DSlons, })

    # Just
#	ds = ds[ [CoordVar] ]
    ds.to_netcdf('Intial_test_{}_netCDF_{}.nc'.format(res, ExStr))
    # save without time dimension


def add_LonghurstProvince2table(df, LatVar='Latitude', LonVar='Longitude'):
    """ Add numbers for Longhurst provenience to DataFrame """
    # Get xml data  for provinces
    provinces, tree = ParseLonghurstProvinceFile()
    # Get the observational data
    if isinstance(df, type(None)):
        df = get_processed_df_obs_mod()  # NOTE this df contains values >400nM
#	num2prov = LonghurstProvinceFileNum2Province( None, invert=True, rtn_dict=True )
    Rnum2prov = RosieLonghurstProvinceFileNum2Province(
        None, invert=True, rtn_dict=True)

    # - Work with the provinces
    # Add a single variable for the coordinate
    CoordVar = 'Coord'

    def f(x):
        return (x[LonVar], x[LatVar])
    df[CoordVar] = df.apply(f, axis=1)
    # map the calculation of provinces

    def GetProv(x):
        return Get_LonghurstProvince4coord(x[CoordVar], provinces=provinces,
                                           num2prov=Rnum2prov, tree=tree, verbose=False)
    df['MIT Province'] = df.apply(GetProv, axis=1)

    # Provence name
    df['PName (R)'] = df['Province'].map(
        RosieLonghurstProvinceFileNum2Province)
    df['PName (MIT)'] = df['MIT Province'].map(
        RosieLonghurstProvinceFileNum2Province)

    # - Check the assignment
    # how many are just the same?
    bool = df['MIT Province'] == df['Province']
    PrtStr = '#={}  ({:.2f}%) are the calculated to be the same thing '
    Ns = float(df.loc[bool, :].shape[0])
    N = float(df.shape[0])
    print(PrtStr.format(N, Ns / N * 100))
    # Which of these are just missing assignments in the input files?
    Nnan = float(df['Province'].dropna().shape[0])
    PrtStr = 'The % non matching, observations without provinces #={} ({:.2f}%)'
    print(PrtStr.format(N-Nnan, (N-Nnan)/N*100))
    # the locations where both assignments have been made?
    dfT = df.loc[np.isfinite(df['Province']), :]
    # For certain points the new approach failed.
    tmp = dfT.loc[~np.isfinite(dfT['MIT Province']), :]
    print('The following provinces were not assigned (# of times) by MIT method:')
    PrtStr = 'This is a {} observations ({:.2f}%)'
    print(PrtStr.format(tmp.shape[0], tmp.shape[0]/N * 100))
    print(tmp['PName (R)'].value_counts())
    # What are the locations of these points?
    PrtStr = 'Full name of {} is {}'
    for prov in tmp.value_counts().index:
        print(PrtStr.format(prov, Get_LonghurstProvinceName4Num(prov)))
    # What data sets contribute to this
    PrtStr = 'Datasets contributing to these numbers: {}'
    print(PrtStr.format(', '.join(set(tmp['Data_Key']))))

    # for others, the assigned provinces differed
    bool = dfT['MIT Province'] != dfT['Province']
    vars2use = [u'Data_Key', 'MIT Province',
                'Province', 'PName (MIT)', 'PName (R)']
    tmp = dfT.loc[bool, :][vars2use].dropna()
    #
    print("When assignment differs - The MIT method gives:")
    PrtStr = "MIT:'{}' ({}), but R gives '{}' ({})"

    for prov in list(set(tmp['PName (R)'])):
        tmp_ = tmp.loc[tmp['PName (R)'] == prov, :]
        for idx in tmp_.index:
            MITp_ = tmp_.loc[tmp_.index == idx, :]['PName (MIT)'].values[0]
            print(PrtStr.format(MITp_, Get_LonghurstProvinceName4Num(MITp_),
                                prov, Get_LonghurstProvinceName4Num(prov)))

    # What data sets contribute to this
    PrtStr = 'Datasets contributing to these numbers: {}'
    print(PrtStr.format(', '.join(set(tmp['Data_Key']))))


def Get_LonghurstProvince4coord(coords, myLon=None, myLat=None,  provinces=None,
                                tree=None, num2prov=None, verbose=False):
    """
    Get the Longhurst Province

    coords (tuple), (LON, LAT) Easterly longitude ranging from -180 to 180,
    Northerly latitude ranging from -90 to 90

    Note orginal code is from X.
     -  code hosted as below
    https://github.com/thechisholmlab/Longhurst-Province-Finder
     - original documentation for COORDS2LONGHURST
    This script takes as input latitude and longitude coordinates and returns the
    Longhurst Province where the coordinate is found.  It works by parsing a file that
    contains lat/long coordinates that bound each province and performing the Crossings Test
    on each province.  The Crossings Test is used in computer graphics to quickly
    determine if a point is within or outside a polygon by "drawing" a line east from the
    input coordinate and seeing how many crossings the line makes with the polygon border.
    If there is an odd number of crossings, the point is within the polygon, otherwise the
    point is outside the polygon.

    """
    from xml.dom.minidom import parse, parseString

    # - Get lat and lon from coords tuple if not provided individual
    if isinstance(myLon, type(None)) or isinstance(myLat, type(None)):
        myLon, myLat = coords
    # Parse GML data from longhurst.xml - if not provided
    if isinstance(provinces, type(None)):
        provinces, tree = ParseLonghurstProvinceFile()
    # Find which candidate provinces our coordinates come from.
    inProvince = {}
    for p in provinces:
        inLat = 0
        inLon = 0
        if (myLat >= provinces[p]['y1'] and myLat <= provinces[p]['y2']):
            inLat = 1
        if (myLon >= provinces[p]['x1'] and myLon <= provinces[p]['x2']):
            inLon = 1
        if inLat and inLon:
            inProvince[p] = True

    # Perform Crossings Test on each candidate province.
    for node in tree.getElementsByTagName('MarineRegions:longhurst'):
        fid = node.getAttribute("fid")
        if inProvince.get(fid):
            crossings = 0
            # 1. Get all coordinate pairs for this province.
            geom = node.getElementsByTagName('MarineRegions:the_geom')
            for g in geom:
                c = g.getElementsByTagName('gml:coordinates')
                for i in c:
                    ii = i.childNodes
                    coordStr = ii[0].data  # <--- contains coordinate strings
                    P = coordStr.split(' ')
                    pairs = []
                    for p in P:
                        [lon, lat] = p.split(',')
                        pairs.append([float(lon), float(lat)])
                    # 2. Use pair p and p+1 to perform Crossings Test.
                    for i in range(len(pairs)-1):
                        # test latitude
                        passLat = (pairs[i][1] >= myLat and pairs[i+1][1] <= myLat) or (
                            pairs[i][1] <= myLat and pairs[i+1][1] >= myLat)
                        # test longitude
                        passLon = (myLon <= pairs[i+1][0])
                        if passLon and passLat:
                            crossings += 1
            if crossings % 2 == 1:
                inProvince[fid] = True
            else:
                inProvince[fid] = False

    # Confirm the solution
    solution = []
    for i in inProvince:
        if inProvince[i] == True:
            solution.append([provinces[i]['provCode'],
                             provinces[i]['provName']])
    # No solutions?
    if len(solution) == 0:
        if verbose:
            print()
            print('No province found matching ', myLat, 'N, ', myLon, 'E.  ')
            print('This coordinate is either on land or it could be in one of these... ')
            for i in inProvince:
                print(provinces[i]['provCode'], '\t', provinces[i]['provName'])
            print()
        return np.NaN
    # one solution
    elif len(solution) == 1:
        if verbose:
            print()
            print(myLat, 'N, ', myLon, 'E -->  ',
                  solution[0][0], '\t', solution[0][1])
            print()
#		return solution[0][0]
        return num2prov[solution[0][0]]
    # mutiple solutions
    elif len(solution) > 1:
        if verbose:
            print()
            print('Conflict between these provinces... ')
            for i in solution:
                print(solution[0][0], '\t', solution[0][1])
            print()
        return np.NaN


def ParseLonghurstProvinceFile():
    """ Parse the .xml file into a dictionary object """
#	from xml.dom.minidom
    from xml.dom.minidom import parse, parseString

    provinces = {}
    tree = parse('longhurst.xml')

    for node in tree.getElementsByTagName('MarineRegions:longhurst'):

        # 1. Get province code, name and bounding box from file
        provCode = node.getElementsByTagName('MarineRegions:provcode')[
            0].firstChild.data
        provName = node.getElementsByTagName('MarineRegions:provdescr')[
            0].firstChild.data
        fid = node.getAttribute("fid")
        b = node.getElementsByTagName('gml:coordinates')[0].firstChild.data

        # 2. Parse bounding box coordinates
        b = b.split(' ')
        x1, y1 = b[0].split(',')
        x2, y2 = b[1].split(',')
        x1 = float(x1)
        y1 = float(y1)
        x2 = float(x2)
        y2 = float(y2)

        provinces[fid] = {'provName': provName, 'provCode': provCode,
                          'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2}

    return provinces, tree


def LonghurstProvinceFileNum2Province(input, invert=False, rtn_dict=False):
    """
    Get the longhurst province
    NOTE: these are not the longhurst numbers (just number within MIT list)
    """
    num2prov = {
    1: u'FKLD', 2: u'CHIL', 3: u'TASM', 4: u'BRAZ', 5: u'SATL', 6: u'EAFR', 7: u'AUSW',
    8: u'AUSE', 9: u'ISSG', 10: u'BENG', 11: u'ARCH', 12: u'SUND', 13: u'GUIN',
    14: u'PEQD', 15: u'MONS', 16: u'ETRA', 17: u'CNRY', 18: u'GUIA', 19: u'ARAB',
    20: u'WTRA', 21: u'KURO', 22: u'NECS', 23: u'NASE', 24: u'PSAE', 25: u'CHIN',
    26: u'INDE', 27: u'CAMR', 28: u'PNEC', 29: u'REDS', 30: u'INDW', 31: u'CARB',
    32: u'NPTG', 33: u'NATR', 34: u'MEDI', 35: u'CCAL', 36: u'NWCS', 37: u'NASW',
    38: u'GFST', 39: u'NADR', 40: u'ALSK', 41: u'ARCT', 42: u'SARC', 43: u'NEWZ',
    44: u'SSTC', 45: u'SPSG', 46: u'PSAW', 47: u'BERS', 48: u'NPPF', 49: u'NPSW',
    50: u'ANTA', 51: u'SANT', 52: u'WARM', 53: u'APLR', 54: u'BPLR'
    }
    # Invert?
    if invert:
        num2prov = {v: k for k, v in list(num2prov.items())}
    # Return the dictionary
    if rtn_dict:
        return num2prov
    else:
        return num2prov[input]


def MarineRegionsOrg_LonghurstProvinceFileNum2Province(input, invert=False,
                                                       rtn_dict=False):
    """
    Get the longhurst province
    NOTE: this is listing order of the shape file from http://www.marineregions.org/sources.php#longhurst
    """
    num2prov = {
    0: u'BPLR', 1: u'ARCT', 2: u'SARC', 3: u'NADR', 4: u'GFST', 5: u'NASW', 6: u'NATR',
    7: u'WTRA', 8: u'ETRA', 9: u'SATL', 10: u'NECS', 11: u'CNRY', 12: u'GUIN',
    13: u'GUIA', 14: u'NWCS', 15: u'MEDI', 16: u'CARB', 17: u'NASE', 18: u'BRAZ',
    19: u'FKLD', 20: u'BENG', 21: u'MONS', 22: u'ISSG', 23: u'EAFR', 24: u'REDS',
    25: u'ARAB', 26: u'INDE',27: u'INDW', 28: u'AUSW', 29: u'BERS', 30: u'PSAE',
    31: u'PSAW', 32: u'KURO', 33: u'NPPF', 34: u'NPSW', 35: u'TASM', 36: u'SPSG',
    37: u'NPTG', 38: u'PNEC', 39: u'PEQD', 40: u'WARM', 41: u'ARCH', 42: u'ALSK',
    43: u'CCAL', 44: u'CAMR', 45: u'CHIL', 46: u'CHIN', 47: u'SUND', 48: u'AUSE',
    49: u'NEWZ', 50: u'SSTC', 51: u'SANT', 52: u'ANTA', 53: u'APLR'
    }
    # Invert?
    if invert:
        num2prov = {v: k for k, v in list(num2prov.items())}
    # Return the dictionary
    if rtn_dict:
        return num2prov
    else:
        return num2prov[input]


def RosieLonghurstProvinceFileNum2Province(input, invert=False, rtn_dict=False):
    """
    Get the longhurst province
    NOTE: these **are** the longhurst numbers
    """
    Rnum2prov = {
    1: 'BPLR', 2: 'ARCT', 3: 'SARC', 4: 'NADR', 5: 'GFST', 6: 'NASW', 7: 'NATR',
    8: 'WTRA', 9: 'ETRA', 10: 'SATL', 11: 'NECS', 12: 'CNRY', 13: 'GUIN', 14: 'GUIA',
    15: 'NWCS', 16: 'MEDI', 17: 'CARB', 18: 'NASE', 19: 'CHSB', 20: 'BRAZ', 21: 'FKLD',
    22: 'BENG', 30: 'MONS', 31: 'ISSG', 32: 'EAFR', 33: 'REDS', 34: 'ARAB', 35: 'INDE',
    36: 'INDW', 37: 'AUSW', 50: 'BERS', 51: 'PSAE', 52: 'PSAW', 53: 'KURO', 54: 'NPPF',
    55: 'NPSE', 56: 'NPSW', 57: 'OCAL', 58: 'TASM', 59: 'SPSG', 60: 'NPTG', 61: 'PNEC',
    62: 'PEQD', 63: 'WARM', 64: 'ARCH', 65: 'ALSK', 66: 'CCAL', 67: 'CAMR', 68: 'CHIL',
    69: 'CHIN', 70: 'SUND', 71: 'AUSE', 72: 'NEWZ', 80: 'SSTC', 81: 'SANT', 82: 'ANTA',
    83: 'APLR', 99: 'LAKE'
    }
    # Invert?
    if invert:
        Rnum2prov = {v: k for k, v in list(Rnum2prov.items())}
    # Return the dictionary
    if rtn_dict:
        return Rnum2prov
    else:
        try:
            return Rnum2prov[input]
        except KeyError:
            if not np.isfinite(input):
                return np.NaN
            else:
                print(input, type(input), np.isfinite(input))
                vstr = "'KeyError for dictionary not for NaN '{}' (type:{})"
                raise ValueError(vstr.format(input, type(input)))


def Get_LonghurstProvinceName4Num(input):
    """ Get full Longhurst Province for given number """
    LonghurstProvinceDict = {
        'ALSK': 'AlaskaDownwellingCoastalProvince',
        'ANTA': 'AntarcticProvince',
        'APLR': 'AustralPolarProvince',
        'ARAB': 'NWArabianUpwellingProvince',
        'ARCH': 'ArchipelagicDeepBasinsProvince',
        'ARCT': 'AtlanticArcticProvince',
        'AUSE': 'EastAustralianCoastalProvince',
        'AUSW': 'AustraliaIndonesiaCoastalProvince',
        'BENG': 'BenguelaCurrentCoastalProvince',
        'BERS': 'N.PacificEpicontinentalProvince',
        'BPLR': 'BorealPolarProvince(POLR)',
        'BRAZ': 'BrazilCurrentCoastalProvince',
        'CAMR': 'CentralAmericanCoastalProvince',
        'CARB': 'CaribbeanProvince',
        'CCAL': 'CaliforniaUpwellingCoastalProvince',
        'CHIL': 'ChilePeruCurrentCoastalProvince',
        'CHIN': 'ChinaSeaCoastalProvince',
        'CHSB': 'CheasapeakeBayProvince',
        'CNRY': 'CanaryCoastalProvince(EACB)',
        'EAFR': 'E.AfricaCoastalProvince',
        'ETRA': 'EasternTropicalAtlanticProvince',
        'FKLD': 'SWAtlanticShelvesProvince',
        'GFST': 'GulfStreamProvince',
        'GUIA': 'GuianasCoastalProvince',
        'GUIN': 'GuineaCurrentCoastalProvince',
        'INDE': 'E.IndiaCoastalProvince',
        'INDW': 'W.IndiaCoastalProvince',
        'ISSG': 'IndianS.SubtropicalGyreProvince',
        'KURO': 'KuroshioCurrentProvince',
        'LAKE': 'CaspianSea,AralSea',
        'MEDI': 'MediterraneanSea,BlackSeaProvince',
        'MONS': 'IndianMonsoonGyresProvince',
        'NADR': 'N.AtlanticDriftProvince(WWDR)',
        'NASE': 'N.AtlanticSubtropicalGyralProvince(East)(STGE)',
        'NASW': 'N.AtlanticSubtropicalGyralProvince(West)(STGW)',
        'NATR': 'N.AtlanticTropicalGyralProvince(TRPG)',
        'NECS': 'NEAtlanticShelvesProvince',
        'NEWZ': 'NewZealandCoastalProvince',
        'NPPF': 'N.PacificPolarFrontProvince',
        'NPSE': 'N.PacificSubtropicalGyreProvince(East)',
        'NPSW': 'N.PacificSubtropicalGyreProvince(West)',
        'NPTG': 'N.PacificTropicalGyreProvince',
        'NWCS': 'NWAtlanticShelvesProvince',
        'OCAL': 'OffshoreCaliforniaCurrentProvince',
        'PEQD': 'PacificEquatorialDivergenceProvince',
        'PNEC': 'N.PacificEquatorialCountercurrentProvince',
        'PSAE': 'PacificSubarcticGyresProvince(East)',
        'PSAW': 'PacificSubarcticGyresProvince(West)',
        'REDS': 'RedSea,PersianGulfProvince',
        'SANT': 'SubantarcticProvince',
        'SARC': 'AtlanticSubarcticProvince',
        'SATL': 'SouthAtlanticGyralProvince(SATG)',
        'SPSG': 'S.PacificSubtropicalGyreProvince',
        'SSTC': 'S.SubtropicalConvergenceProvince',
        'SUND': 'SundaArafuraShelvesProvince',
        'TASM': 'TasmanSeaProvince',
        'WARM': 'W.PacificWarmPoolProvince',
        'WTRA': 'WesternTropicalAtlanticProvince'
    }
    return LonghurstProvinceDict[input]
