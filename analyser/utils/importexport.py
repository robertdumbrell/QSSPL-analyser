
import numpy as np
import os
import sys
from shutil import copyfile
import json


class Load_QSSPL_File_LabView():

    def __init__(self, Directory, RawDataFile):
        self.Directory = Directory
        self.RawDataFile = RawDataFile

    def Load_RawData_File(self):
        return np.genfromtxt(os.path.join(self.Directory, self.RawDataFile),
                             names=('Time', 'PC', 'Gen', 'PL'))

    def Load_InfData_File(self):
        InfFile = self.RawDataFile[:-13] + '.inf'

        '''info from inf file '''

        Cycles, dump, Frequency, LED_Voltage, dump, dump, dump, dump, DataPoints, dump = np.genfromtxt(
            self.Directory + InfFile, skip_header=20, skip_footer=22, delimiter=':', usecols=(1), autostrip=True, unpack=True)
        Waveform, LED_intensity = np.genfromtxt(
            self.Directory + InfFile, skip_header=31, skip_footer=20, delimiter=':', usecols=(1), dtype=None, autostrip=True, unpack=True)

        l = np.genfromtxt(
            self.Directory + InfFile, skip_header=36, delimiter=':', usecols=(1))

        Doping = l[9]
        Ai = l[6]
        Fs = l[7]
        Thickness = l[12]
        Quad = l[12]
        Lin = l[12]
        Const = 0

        Binning = int(l[2])
        Reflection = (1 - l[16]) * 100

        dic = locals()

        del dic['self']
        del dic['l']
        del dic['dump']

        return dic

    def Load_ProcessedData_File(self):
        DataFile = self.DataFile[:-13] + '.dat'
        return np.genfromtxt(self.Directory + DataFile, usecols=(0, 1, 8, 9), unpack=True, delimiter='\t', names=('Deltan_PC', 'Tau_PC', 'Deltan_PL', 'Tau_PL'))

    def WriteTo_Inf_File(self, Dictionary):

        InfFile = self.RawDataFile[:-13] + '.inf'

        if (os.path.isfile(self.Directory + InfFile + ".Backup") == False):
            copyfile(
                self.Directory + InfFile, self.Directory + InfFile + ".Backup")
            print 'Backuped original .inf  file as .inf.backup'

        ####
        # Creating the .inf file, this can be done more easily with list(f), but i'm not using it right now.
        ###
        f = open(self.Directory + InfFile, 'r')

        # print list(f)
        # print list(f).shape

        s = ''
        for i in range(38):
            s = s + f.readline()
        s = s + f.readline()[:26] + \
            '{0:.0f}'.format(Dictionary['Binning']) + '\n'
        for i in range(3):
            s = s + f.readline()
        s = s + f.readline()[:5] + '{0:.3e}'.format(Dictionary['Ai']) + '\n'
        s = s + f.readline()[:11] + '{0:.3e}'.format(Dictionary['Fs']) + '\n'
        s = s + f.readline()
        s = s + f.readline()[:23] + \
            '{0:.3e}'.format(Dictionary['Doping']) + '\n'
        s = s + f.readline()
        s = s + f.readline()
        s = s + f.readline()[:12] + \
            '{0:.4f}'.format(Dictionary['Thickness']) + '\n'
        s = s + f.readline()[:24] + '{0:.4e}'.format(Dictionary['Quad']) + '\n'
        s = s + f.readline()[:21] + '{0:.4e}'.format(Dictionary['Lin']) + '\n'
        s = s + f.readline()
        s = s + \
            f.readline()[
                :37] + '{0:.6f}'.format(1 - Dictionary['Reflection'] / 100) + '\n'

        for i in range(6):
            s = s + f.readline()

        f.close()
        f = open(self.Directory + InfFile, 'w')
        f.write(s)


class Load_QSSPL_File_Python():

    def __init__(self, Directory, RawDataFile):
        self.Directory = Directory
        self.RawDataFile = RawDataFile

    def Load_RawData_File(self):
        data = np.genfromtxt(
            self.Directory + self.RawDataFile,
            unpack=True,
            names=True,
            delimiter='\t')
        print data.dtype.names
        s = np.array([])
        dic = {'Time_s': 'Time', 'Generation_V': 'Gen',
               'PL_V': 'PL', 'PC_V': 'PC', 'Waveform_V': 'Gen_sent_voltage'}
        for i in np.array(data.dtype.names):

            s = np.append(s, dic[i])

        data.dtype.names = s

        return data

    def num(self, s):
        try:
            return float(s)
        except ValueError:
            return s

    def Load_InfData_File(self):
        # print 'Still under construction'

        InfFile = self.RawDataFile[:-13] + '.inf'

        # These are adjustment Values
        Doping = 1
        Thickness = 1
        Binning = 1
        Reflection = 0.0
        Fs = 1
        Ai = 1
        Quad = 0.0004338
        Lin = 0.03611
        Const = 0.001440789
        Temp = 300

        CropStart = 0
        CropEnd = 100

        List = locals()

        del List['InfFile']
        del List['self']

        with open(self.Directory + str(InfFile), 'r') as f:
            s = f.read()

        for i in s.split('\n')[2:-1]:
            # print i.split(':\t')[1]
            List[i.split(':\t')[0].strip()] = self.num(i.split(':\t')[1])
        # print List

        return List

    def Load_ProcessedData_File(self):
        print 'Still under construction'

        return zeros(4, 4)

    def WriteTo_Inf_File(self, Dictionary):

        InfFile = self.RawDataFile[:-13] + '.inf'

        if (os.path.isfile(self.Directory + InfFile + ".Backup") == False):
            copyfile(
                self.Directory + InfFile, self.Directory + InfFile + ".Backup")
            print 'Backuped original .inf  file as .inf.backup'

        s = 'MJ system\r\nList of vaiables:\r\n'
        for i in Dictionary:
            # if i != and i !='self':
            s += '{0}:\t{1}\r\n'.format(i, Dictionary[i])

        with open(self.Directory + InfFile, 'w') as text_file:
            text_file.write(s)


class TempDep_loads():

    def __init__(self, Directory, RawDataFile):
        self.Directory = Directory
        self.RawDataFile = RawDataFile

    def Load_RawData_File(self):
        '''
        Loads the measured data from the data file.
        This has the file extension tsv (tab seperated values)

        from a provided file name,
        takes data and outputs data with specific column headers
        '''

        # get data, something stange was happening with os.path.join
        file_location = os.path.normpath(
            os.path.join(self.Directory, self.RawDataFile))

        data = np.genfromtxt(
            os.path.join(file_location),
            unpack=True, names=True, delimiter='\t')

        # string to convert file names to program names
        dic = {'Time_s': 'Time', 'Generation_V': 'Gen',
               'PL_V': 'PL', 'PC_V': 'PC'}

        # create empty array
        s = np.array([])

        # build array of names, in correct order
        for i in np.array(data.dtype.names):
            s = np.append(s, dic[i])

        # assign names
        data.dtype.names = s

        return data

    def num(self, s):
        '''
        converts s to a number, or returns s
        '''
        try:
            return float(s)
        except ValueError:
            return s

    def Load_InfData_File(self):
        # print 'Still under construction'

        # replace the ending with a new ending
        InfFile = self.get_inf_name()

        # These are adjustment Values, requried by the following
        temp_list = {'Doping': 1,
                     'Thickness': 1,
                     'Binning': 1,
                     'Reflection': 0.0,
                     'Fs': 1,
                     'Ai': 1,
                     'Quad': 0.0004338,
                     'Lin': 0.03611,
                     'CropStart': 0,
                     'CropEnd': 100,
                     }

        with open(os.path.join(self.Directory, InfFile), 'r') as f:
            file_contents = f.read()
            List = json.loads(file_contents)

        List.update(temp_list)

        return List

    def Load_ProcessedData_File(self):
        print 'Still under construction'

        return zeros(4, 4)

    def WriteTo_Inf_File(self, metadata_dict):
        '''
        write to inf file, with "correct format" format as 
        '''

        # get inf file location
        InfFile = os.path.join(self.Directory, self.get_inf_name())

        # check if there is backup, and make
        backup_file = os.path.join(self.Directory, InfFile + ".Backup")
        if os.path.isfile(backup_file) is False:

            copyfile(InfFile, backup_file)
            print 'Backuped original .inf  file as .inf.backup'

        # specify how to output

        serialised_json = json.dumps(
            metadata_dict,
            sort_keys=True,
            indent=4,
            separators=(',', ': ')
        )

        # writes to file
        with open(InfFile, 'w') as text_file:
            text_file.write(serialised_json)

    def get_inf_name(self):

        if self.RawDataFile.count('.tsv') == 1:
            InfFile = self.RawDataFile.replace('.tsv', '.json')
        else:
            print 'stop fucking around with the name!!'

        return InfFile


class LoadData():

    Directory = ''
    RawDataFile = ''
    File_Type = ''

    file_ext_dic = {
        '.Raw Data.dat': 'Python',
        '_Raw Data.dat': 'Labview',
        '.tsv': 'TempDep'
    }
    file_ext_2_class = {
        r'.Raw Data.dat': r'Load_QSSPL_File_Python',
        r'_Raw Data.dat': r'Load_QSSPL_File_LabView',
        r'.tsv': r'TempDep_loads'
    }

    def obtain_operatorclass(self, Directory=None, RawDataFile=None):
        if Directory is None:
            Directory = self.Directory
            RawDataFile = self.RawDataFile
        LoadClass = None

        for ext, _class in self.file_ext_2_class.iteritems():
            # print ext, _class

            if ext in RawDataFile:

                LoadClass = getattr(sys.modules[__name__],
                                    _class)(
                    Directory, RawDataFile)

        return LoadClass

    def Load_RawData_File(self):
        LoadClass = self.obtain_operatorclass()
        return LoadClass.Load_RawData_File()

    def Load_InfData_File(self):
        LoadClass = self.obtain_operatorclass()
        return LoadClass.Load_InfData_File()

    def Load_ProcessedData_File(self):
        LoadClass = self.obtain_operatorclass()
        return LoadClass.Load_ProcessedData_File()

    def WriteTo_Inf_File(self, Dict):
        LoadClass = self.obtain_operatorclass()
        return LoadClass.WriteTo_Inf_File(Dict)

if __name__ == "__main__":
    Folder = r'C:\git\ui\pvapp\test\data'
    File = r'raw_test_data.tsv'
    LoadData()
    B = LoadData().obtain_operatorclass(Folder, File)

    dictr = B.Load_InfData_File()
    B.WriteTo_Inf_File(dictr)
