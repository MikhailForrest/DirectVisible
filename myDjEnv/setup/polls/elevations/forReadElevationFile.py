import pandas as pd

def readElevationFile (file_name):
    try:
        excel_data = pd.read_excel(file_name)
        data = pd.DataFrame(excel_data, columns=['A','E'])
        lst_azimuts = data['A'].to_list()
        lst_elevations = data['E'].to_list()
        if (len(lst_azimuts) == len (lst_elevations)) and (len(lst_azimuts)!=0):
            return {'azimuts': lst_azimuts, 'elevations': lst_elevations}
    except NameError:
        raise('NameError')
