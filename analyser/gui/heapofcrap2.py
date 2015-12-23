####################
# Written By Mattias Juhl
# Things to improve:
#  Need toadd a save name file on the export button.
# remove button inline, this really shouldn't be too hard. To be placed underneath the load button
# Can change plots
#######################


# Bugs fixed in this version
############
#       Saving bug, only saving one file
#       Reflection not working
#       Saving adding a tab at the end of the save file

# Changes from 2.4:
# 3
#       Added new input and output, based on a dictionary. This is in a file called ImportQSSFiles.
#       Labels, if can'tfind them will list number
##########


# Changes from 2.3:
# 3
#       B is now correct, updated using email from TT (2014)
#       Output now includes scalled data
#       Generation is no calculated differently for both PC and PL, previously it used Delta n from PC in both cases.
#       Graphs now auto scale after loggling
#       Legend button added for easier workings
##########


import sys
import os

from numpy import *

import collections
from string import find
from models.ConstantsClass import *
from CanvasClass import *


from models.MobilityV2 import Mobility_Klassen as Mobility
from analysis.analysisV2 import Data
from models.NumericalDifferentiation_windows import Finite_Difference, Regularisation
from models.Recombination_v2_01 import Radiative

from utils.importexport import LoadData


def SplitName(FileName,  separator, suffix, block):

    if len(FileName.strip().split(separator)) > block:
        return FileName.strip().split(separator)[block] + str(suffix)
    else:
        return ''


class Analyser(wx.Frame, Constants):

    def __init__(self, *args, **kw):
        wx.Frame.__init__(
            self, None, -1, "EQE", size=(wx.DisplaySize()[0] * .9, wx.DisplaySize()[1] * .9))
        self.dirname = '/media/User Files/BackUp/30042013/PHD/Measurements/PHD/QSSPL'

        self.Files = array([])
        self.DataSet = -1

        self.MyMenu()
        self.InitUI()

        self.Centre()  # centering program in screen
        self.Show(True)

    # Read more at
    # http://www.devshed.com/c/a/Python/Dialogs-in-wxPython/5/#MTHpCyrzjo4gshMW.99

    def MyMenu(self):

        menubar = wx.MenuBar()
        OutputOptions = wx.Menu()
        self.Ouput_Lifetime = OutputOptions.Append(
            101, 'Lifetime', 'Outputs Deltan tau Data', wx.ITEM_CHECK)
        self.Ouput_SunsVoc = OutputOptions.Append(
            102, 'Suns-iVoc', 'Outputs Generation iVoc', wx.ITEM_CHECK)
        self.Ouput_LocalIdealityFactor = OutputOptions.Append(
            103, 'Local Ideality Factor', 'Outputs  Generation iVoc', wx.ITEM_CHECK)
        OutputOptions.AppendSeparator()
        menubar.Append(OutputOptions, '&Output Options')
        self.SetMenuBar(menubar)
        self.CreateStatusBar()
        self.Ouput_Lifetime.Check(True)

    def InitUI(self):
        global Fig1, Fig2

        sizer = wx.GridBagSizer(vgap=30)
        sizer1 = wx.GridBagSizer(vgap=30)
        sizer2 = wx.GridBagSizer(vgap=30)
        #sizers = wx.GridBagSizer()
        self.scrolling = wx.ScrolledWindow(self, wx.ID_ANY)

        self.waferdetails()

        Fig1 = CanvasPanel(self.scrolling)
        Fig1.Axes(1e9, 1e17, 1e-6, 1e-2)
        Fig1.labels('Lifetime Curve', '$\Delta$ n ($cm^{-3}$)', '$\\tau$ (s)')
        Fig1.loglog()

        Fig2 = CanvasPanel(self.scrolling)
        Fig2.labels('Raw Data', 'Time (a.u.)', 'Voltage (V)')

        # Opts.Hide()
        self.SetTitle('Offline QSSPL - Multiple Files')

        sizer2.Add(Fig1, (0, 0))
        sizer2.Add(Fig2, (1, 0))
        sizer1.Add(self.waferdetails, (0, 0))

        sizer.Add(sizer1, (0, 1))
        sizer.Add(sizer2, (0, 0))

        self.scrolling.SetSizer(sizer)
        self.scrolling.SetScrollRate(10, 10)

    def onWidgetSetup(self, widget,   sizer, row, column):
        #widget.Bind(event, handler)
        sizer.Add(widget, (row, column), flag=wx.ALL, border=10)
        return widget

    def waferdetails(self):

        self.waferdetails = wx.Panel(self.scrolling, style=0)
        self.sizar = wx.GridBagSizer()
        #self.StaticBoxsizar =wx.GridBagSizer()

        '''PC Coefficients'''
        # creating items
        SintonCoilConstants = wx.StaticBox(
            self.waferdetails, label='Sinton Coil Calibration Constants')
        SintonCalibration_box = wx.StaticBoxSizer(
            SintonCoilConstants, wx.VERTICAL)
        SintonCalibration_Box_contence = wx.GridBagSizer()

        self.TextPCa = self.onWidgetSetup(wx.StaticText(
            self.waferdetails, label="Quadratic"), SintonCalibration_Box_contence, 0, 1)
        self.TextPCb = self.onWidgetSetup(wx.StaticText(
            self.waferdetails, label="Linear"), SintonCalibration_Box_contence, 0, 2)
        self.TextPCc = self.onWidgetSetup(wx.StaticText(
            self.waferdetails, label="Offset"), SintonCalibration_Box_contence, 0, 3)
        self.InputPCa = self.onWidgetSetup(wx.TextCtrl(
            self.waferdetails, value=str(self.Quad)), SintonCalibration_Box_contence, 1, 1)
        self.InputPCb = self.onWidgetSetup(wx.TextCtrl(
            self.waferdetails, value=str(self.Lin)), SintonCalibration_Box_contence, 1, 2)
        self.InputPCc = self.onWidgetSetup(wx.TextCtrl(
            self.waferdetails, value=str(self.Const)), SintonCalibration_Box_contence, 1, 3)

        # Arranging items
        self.sizar.Add(SintonCalibration_box,           (0, 0), (2, 2),
                       flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL, border=20)
        # Adding them to a sizer
        SintonCalibration_box.Add(SintonCalibration_Box_contence)

        '''Anaylsis Settings '''
        # Creating Items
        self.AnaylsisBox = wx.StaticBox(
            self.waferdetails, label='Analysis Settings')
        Anaylsis_Box_contence = wx.GridBagSizer()

        self.AnaylsisType_label = self.onWidgetSetup(wx.StaticText(
            self.waferdetails, label="Analysis Method"), Anaylsis_Box_contence, 0, 0)
        self.AnaylsisType = self.onWidgetSetup(wx.ComboBox(self.waferdetails, value='Generalised', choices=[
                                               'Steady State', 'Generalised', 'Transient'], style=wx.CB_READONLY), Anaylsis_Box_contence, 1, 0)
        self.DifferentialType_label = self.onWidgetSetup(wx.StaticText(
            self.waferdetails, label="Derivative Method"), Anaylsis_Box_contence, 0, 1)
        self.DifferentialType = self.onWidgetSetup(wx.ComboBox(self.waferdetails, value='Finite Difference', choices=[
                                                   'Regularised', 'Finite Difference'], style=wx.CB_READONLY), Anaylsis_Box_contence, 1, 1)

        # Adding box
        AnaylsisBox_box = wx.StaticBoxSizer(self.AnaylsisBox, wx.VERTICAL)
        self.sizar.Add(AnaylsisBox_box,           (0, 2), (1, 2),
                       flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL, border=20)
        AnaylsisBox_box.Add(Anaylsis_Box_contence)

        '''Figure Settings '''
        # Creating Items

        tau_string = u"\u03C4_eff"
        deltan_string = u"\u0394n"
        Delta_conductance = u"\u0394\u03C3"
        Conductance_string = u"\u03C3"

        self.Plotting_Choice = wx.StaticBox(
            self.waferdetails, label='Plotting')
        Plotting_Choice_Box_contence = wx.GridBagSizer()

        self.y_axis_label = self.onWidgetSetup(wx.StaticText(
            self.waferdetails, label="y-axis"), Plotting_Choice_Box_contence, 0, 0)
        self.y_axis = self.onWidgetSetup(wx.ComboBox(self.waferdetails, value=tau_string, choices=[
                                         u"\u0394n", tau_string, 'Generation', 'Generation (Suns)', 'Time', 'iVoc', u"\u0394\u03C3", u"\u03C3", 'Ideality Factor'], style=wx.CB_READONLY), Plotting_Choice_Box_contence, 1, 0)
        self.x_axis_label = self.onWidgetSetup(wx.StaticText(
            self.waferdetails, label="x-axis"), Plotting_Choice_Box_contence, 0, 1)
        self.x_axis = self.onWidgetSetup(wx.ComboBox(self.waferdetails, value=deltan_string, choices=[
                                         deltan_string, deltan_string + '-PL', tau_string, 'Generation', 'Time', 'Time - Normalised', 'iVoc', u"\u0394\u03C3"], style=wx.CB_READONLY), Plotting_Choice_Box_contence, 1, 1)

        # Adding box
        self.Plotting_Choice_Box = wx.StaticBoxSizer(
            self.Plotting_Choice, wx.VERTICAL)
        self.sizar.Add(self.Plotting_Choice_Box,           (2, 2), (1, 2),
                       flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL, border=20)

        self.Plotting_Choice_Box.Add(Plotting_Choice_Box_contence)

        ' '' Global Wafer Things'''
        # Global Wafer Things
        self.GlobalWaferProperties_Box = wx.StaticBox(
            self.waferdetails, label='Global Wafer Properties')

        GlobalWafer_Box_contence = wx.GridBagSizer()
        self.TextWaferDoping = self.onWidgetSetup(wx.StaticText(
            self.waferdetails, label="Doping (cm^-3)"), GlobalWafer_Box_contence, 0, 1)
        self.TextWaferThickness = self.onWidgetSetup(wx.StaticText(
            self.waferdetails, label="Thickness (cm)"), GlobalWafer_Box_contence, 0, 2)
        self.TextDopingType = self.onWidgetSetup(wx.StaticText(
            self.waferdetails, label="Doping (p or n)"), GlobalWafer_Box_contence, 0, 3)

        self.InputWaferDoping = self.onWidgetSetup(
            wx.TextCtrl(self.waferdetails, value=str(8e15)), GlobalWafer_Box_contence, 1, 1)
        self.InputWaferThickness = self.onWidgetSetup(
            wx.TextCtrl(self.waferdetails, value=str(0.0180)), GlobalWafer_Box_contence, 1, 2)
        self.InputDopingType = self.onWidgetSetup(
            wx.TextCtrl(self.waferdetails, value='p'), GlobalWafer_Box_contence, 1, 3)

        # Placing Wafer Coefficients box
        self.GloablWafer_sizer = wx.StaticBoxSizer(
            self.GlobalWaferProperties_Box, wx.VERTICAL)
        self.sizar.Add(self.GloablWafer_sizer,           (2, 0), (2, 2),
                       flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL, border=20)

        self.GloablWafer_sizer.Add(GlobalWafer_Box_contence)

        ' ''The Other Stuff '''

        self.AddButton = wx.Button(self.waferdetails, label="Add File")
        self.RemoveButton = wx.Button(self.waferdetails, label="Remove File")
        self.ExportButton = wx.Button(self.waferdetails, label="Export")

        '''Analysis Tab'''
        # Define box and some items to go in the box
        self.AnalyseFiles_Box = wx.StaticBox(
            self.waferdetails, label="Analyse Files")
        self.AnalyseFiles_Box_contence = wx.GridBagSizer()

        self.Fs_Heading = self.onWidgetSetup(wx.StaticText(
            self.waferdetails, label="Fs", style=wx.ALIGN_CENTRE), self.AnalyseFiles_Box_contence, 0, 2)
        self.Ai_Heading = self.onWidgetSetup(wx.StaticText(
            self.waferdetails, label="Ai ", style=wx.ALIGN_CENTRE), self.AnalyseFiles_Box_contence, 0, 3)
        self.Reflection_Heading = self.onWidgetSetup(wx.StaticText(
            self.waferdetails, label="Ref (%)", style=wx.ALIGN_CENTRE), self.AnalyseFiles_Box_contence, 0, 4)
        self.Wavelength_Heading = self.onWidgetSetup(wx.StaticText(
            self.waferdetails, label="Temp (K)", style=wx.ALIGN_CENTRE), self.AnalyseFiles_Box_contence, 0, 5)
        self.Crop_Heading = self.onWidgetSetup(wx.StaticText(
            self.waferdetails, label="Crop (%)", style=wx.ALIGN_CENTRE), self.AnalyseFiles_Box_contence, 0, 6)
        self.Binning_Heading = self.onWidgetSetup(wx.StaticText(
            self.waferdetails, label="Points binned", style=wx.ALIGN_CENTRE), self.AnalyseFiles_Box_contence, 0, 7)

        # Place box and create sizers
        self.AnalyseFiles_Box_sizer = wx.StaticBoxSizer(
            self.AnalyseFiles_Box, wx.VERTICAL)
        self.sizar.Add(self.AnalyseFiles_Box_sizer,           (7, 0), (1, 4),
                       flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL, border=20)

        self.AnalyseFiles_Box_sizer.Add(self.AnalyseFiles_Box_contence)

        ''' Headings Format'''
        heading = wx.Font(18, wx.ROMAN, wx.ITALIC, wx.NORMAL)

        # Processes Things

        #self.sizar.Add(self.waferdetails.TextLoadFiles,                (5,0)    ,flag=wx.ALL|wx.GROW|wx.ALIGN_CENTER,border=10)
        self.sizar.Add(self.AddButton,
                       (5, 0), (1, 1), flag=wx.ALL | wx.GROW | wx.ALIGN_CENTER, border=10)
        self.sizar.Add(self.RemoveButton,
                       (5, 1), (1, 1), flag=wx.ALL | wx.GROW | wx.ALIGN_CENTER, border=10)
        self.sizar.Add(self.ExportButton,
                       (5, 2), (1, 1), flag=wx.ALL | wx.GROW | wx.ALIGN_CENTER, border=10)

        self.InputPCGraph = wx.CheckBox(self.waferdetails, -1, 'Show PC Data')
        self.InputPLGraph = wx.CheckBox(self.waferdetails, -1, 'Show PL Data')
        self.InputSystemGraph = wx.CheckBox(
            self.waferdetails, -1, 'Show System Data')
        self.InputCommonScale = wx.CheckBox(
            self.waferdetails, -1, 'Common Scale')
        self.Legend = wx.CheckBox(self.waferdetails, -1, 'Legend')

        self.InputPLGraph.SetValue(True)
        self.InputPCGraph.SetValue(True)
        self.InputSystemGraph.SetValue(False)
        self.InputCommonScale.SetValue(True)
        self.Legend.SetValue(False)

        self.sizar.Add(self.InputPCGraph,                 (8, 0),
                       flag=wx.ALL | wx.GROW | wx.ALIGN_CENTER, border=10)
        self.sizar.Add(self.InputPLGraph,                 (8, 1),
                       flag=wx.ALL | wx.GROW | wx.ALIGN_CENTER, border=10)
        self.sizar.Add(self.InputSystemGraph,             (9, 0),
                       flag=wx.ALL | wx.GROW | wx.ALIGN_CENTER, border=10)
        self.sizar.Add(self.InputCommonScale,             (9, 1),
                       flag=wx.ALL | wx.GROW | wx.ALIGN_CENTER, border=10)
        self.sizar.Add(self.Legend,                       (10, 0),
                       flag=wx.ALL | wx.GROW | wx.ALIGN_CENTER, border=10)

        # Binds

        """making binds for load buttongs"""
        self.AddButton.Bind(wx.EVT_BUTTON, self.onAddData)
        self.RemoveButton.Bind(wx.EVT_BUTTON, self.onRemoveData)
        self.ExportButton.Bind(wx.EVT_BUTTON, self.onExportData)

        '''load buttons'''
        """
        labels = [self.LoadFileButton0,self.LoadFileButton1,self.LoadFileButton2]

        for label in labels:
            label.Bind(wx.EVT_BUTTON, self.LoadRawDataFile)
        """
        """making binds for  changeing processed data"""

        '''Binding for things '''

        # ,self.InputGenerationCeofficient0,self.InputGenerationCeofficient1,self.InputGenerationCeofficient2,self.InputWaferAi0,self.InputWaferAi1,self.InputWaferAi2,]
        labels = [self.InputPCa, self.InputPCb, self.InputPCc,
                  self.InputWaferDoping, self.InputWaferThickness, self.InputDopingType]

        # labels= self.InputWaferThickness,self.InputWaferDoping,self.InputDopingType

        for label in labels:
            label.Bind(wx.EVT_KEY_DOWN, self.OnKeyDownChangedProcessed)

        # Checkboxes as applies to figures has to be done after figures are
        # real
        labels = [self.InputPCGraph, self.InputPLGraph, self.InputSystemGraph]
        for label in labels:
            self.CheckboxBinderChangeProcessed(label)

        """making binds for  changing raw data"""
        # labels= [self.InputPercentageStart0, self.InputPercentageEnd0, self.InputBinning0,self.InputPercentageStart1, self.InputPercentageEnd1, self.InputBinning1, self.InputPercentageStart2,self.InputPercentageEnd2,self.InputBinning2]

        # for label in labels:
            # label.Bind(wx.EVT_KEY_DOWN, self.OnKeyDownChangedRaw)

        """Binder for fitting buttons"""
        # self.CalcEQEButton.Bind(wx.EVT_BUTTON, self.CalcEQE)

        self.waferdetails.SetSizer(self.sizar)
        # self.waferdetails.SetSizer(self.StaticBoxsizar)
        self.onAddData(0)

    def onExportData(self, event):

        # setting the file name
        a = self.Files[0]
        num = find(a.RawDataFile[:-13], '_')

        # Making the header
        header = 'Time (s)\t'

        if self.Ouput_Lifetime.IsChecked() == True:
            header += 'Deltan PC (cm^-3) \t Deltan PL (cm^-3) \t  Tau PC (s) \t Tau PL(s) \t'

        if self.Ouput_SunsVoc.IsChecked() == True:
            header += 'iVoc PC (V) \t iVoc PL (V) \tGeneration PC (Suns) \t Generation PL (Suns) \t'

        if self.Ouput_LocalIdealityFactor.IsChecked() == True:
            header += 'iVoc PC (V) \t iVoc PL (V) \tm PC \t m PL \ '

        header = header.strip('\t')
        # writing the header
        with open(a.Directory + a.RawDataFile[:num] + '.txt', 'wb') as f:
            f.write(header)

        # getting the data from each file
        s = ''

        for i in reversed(range(self.Files.shape[-1])):

            if self.Files[i].Used:
                b = self.Files[i]
                s = self.GrabData(b, 'Time')[0]

                if self.Ouput_Lifetime.IsChecked() == True:
                    s = vstack((s.T, array(self.GrabData(b, u"\u0394n")), array(
                        self.GrabData(b, u"\u03C4_eff")))).T

                if self.Ouput_SunsVoc.IsChecked() == True:
                    s = vstack((s.T, array(self.GrabData(b, 'iVoc')), array(
                        self.GrabData(b, 'Generation (Suns)')))).T

                if self.Ouput_LocalIdealityFactor.IsChecked() == True:
                    s = vstack((s.T, array(self.GrabData(b, 'iVoc')), array(
                        self.GrabData(b, 'Ideality Factor')))).T
            # print
            # self.Ouput_Lifetime.IsChecked(),self.Ouput_SunsVoc.IsChecked(),self.Ouput_LocalIdealityFactor.IsChecked()

            # One got data from a file, write it and leave a space.

            # print s.shape,a.OutputData().shape
            # do no need to close file as with a with block
            with open(a.Directory + a.RawDataFile[:num] + '.txt', 'a') as f:
                f.write('\n')
                savetxt(f, s, delimiter='\t')

    def onAddData(self, event):
        # Need to add one more reference to the Files array

        self.Files = append(self.Files, array([Data()]))
        # print self.Files

        Suffix = str(self.Files.shape[0] - 1)
        Id = float(str(self.Files.shape[0] - 1))
        # print Suffix

        offset = 0
        row = (offset + self.Files.shape[0]) * 2
        row2 = row + 1

        # Then need to add extra buttons
        LoadFileButton = self.onWidgetSetup(wx.Button(
            self.waferdetails, label="Load Data", name="LoadFileButton" + Suffix, id=Id), self.AnalyseFiles_Box_contence, row, 0)
        LoadFileText = wx.TextCtrl(
            self.waferdetails, value="Loaded Dummy Name", name="LoadFileText" + Suffix)
        Fs = self.onWidgetSetup(wx.TextCtrl(self.waferdetails, value=str(
            1.24e16), name="Fs" + Suffix), self.AnalyseFiles_Box_contence, row2, 2)
        Ai = self.onWidgetSetup(wx.TextCtrl(self.waferdetails, value=str(
            1e15), name="Ai" + Suffix), self.AnalyseFiles_Box_contence, row2, 3)
        Reflection = self.onWidgetSetup(wx.TextCtrl(self.waferdetails, value=str(
            10), name="Reflection" + Suffix), self.AnalyseFiles_Box_contence, row2, 4)
        Temp = self.onWidgetSetup(wx.TextCtrl(self.waferdetails, value=str(
            300), name="Temp" + Suffix), self.AnalyseFiles_Box_contence, row2, 5)
        CropStart = self.onWidgetSetup(wx.TextCtrl(self.waferdetails, value=str(
            0), name="CropStart" + Suffix), self.AnalyseFiles_Box_contence, row, 6)
        CropEnd = self.onWidgetSetup(wx.TextCtrl(self.waferdetails, value=str(
            100), name="CropEnd" + Suffix), self.AnalyseFiles_Box_contence, row2, 6)
        Binning = self.onWidgetSetup(wx.TextCtrl(self.waferdetails, value=str(
            100), name="Binning" + Suffix), self.AnalyseFiles_Box_contence, row2, 7)

        # LoadFileText.Size.SetSize(10000,-1)
        # print "LoadFileButton" + Suffix

        # Need to make them do something
        # self.AnalyseFiles_Box_contence.Add(LoadFileButton,                  ( row ,0)     ,flag=wx.ALL|wx.GROW|wx.ALIGN_CENTER,border=3)
        self.AnalyseFiles_Box_contence.Add(
            LoadFileText,                    (row, 1), (1, 4), flag=wx.ALL | wx.GROW | wx.ALIGN_CENTER, border=10)

        "Bindings"

        labels = [Fs, Ai, CropStart, Reflection, Temp, CropStart, CropEnd, Binning]

        LoadFileButton.Bind(wx.EVT_BUTTON, self.LoadRawDataFile)

        for label in labels:
            label.Bind(wx.EVT_CHAR_HOOK, self.OnKeyDownChangedRaw)

        self.waferdetails.Fit()

    def onRemoveData(self, event):

        self.Files[-1] = ''
        self.Files = self.Files[:-1]
        num = int(self.Files.shape[0])

        # Makeing the name of the Text screen that is being updated
        names = ['LoadFileButton', 'LoadFileText', 'Fs', 'Ai',
                 'Reflection', 'Temp', 'CropStart', 'CropEnd', 'Binning']

        for name in names:
            ControlName = name + str(num)

        # updating that value
            self.waferdetails.FindWindowByName(ControlName).Destroy()

        self.waferdetails.Fit()


    def CheckboxBinderChangeProcessed(self, name):
        name.Bind(wx.EVT_CHECKBOX, self.CheckBoxChanged)

    def GrabData(self, handel, String):

        if(String == u"\u03C4_eff"):
            return handel.Tau_PC, handel.Tau_PL

        elif(String == u"\u0394n"):
            return handel.DeltaN_PC, handel.DeltaN_PL

        elif(String == u"\u0394n-PL"):
            return handel.DeltaN_PL, handel.DeltaN_PL

        elif(String == 'Generation'):
            return handel.Generation('PC'), handel.Generation('PL')

        elif(String == 'Generation (Suns)'):
            return handel.Generation('PC', suns=True), handel.Generation('PL', suns=True)

        elif(String in ['Time', 'PL', 'RaW PC']):
            return handel.Data[String], handel.Data[String]

        elif(String == 'Time - Normalised'):
            return handel.Data['Time'] / handel.Data['Time'][-1], handel.Data['Time'] / handel.Data['Time'][-1]

        elif(String == 'iVoc'):
            return handel.iVoc()

        elif(String == u"\u0394\u03C3"):
            return handel.Data['PC'], handel.DeltaN_PL * self.q * Mobility().mobility_sum(handel.DeltaN_PL, handel.n0, handel.p0, handel.Wafer['Temp']) * handel.Wafer['Thickness']

        elif(String == u"\u03C3"):
            return handel.Raw_PCEdited + handel.DarkConductance, handel.DeltaN_PL * self.q * Mobility().mobility_sum(handel.DeltaN_PL, handel.n0, handel.p0, handel.Wafer['Temp']) * handel.Thickness + handel.DarkConductance

        elif(String == 'Ideality Factor'):
            return handel.Local_IdealityFactor()

        elif(String == 'EQE:beta'):
            return handel.EQE()

        elif(String == 'Wavelength'):
            return handel.Wavelength, handel.Wavelength

        elif(String == 'IQE at G=0.1sun'):
            return handel.IQE_SingleIntensity()

        elif(String == 'The Number 1'):
            return 1, 1

        else:
            print 'negitivie', String

            return ones(handel.Tau_PC.shape[0]), ones(handel.Tau_PC.shape[0])

    def DrawProcessedData(self):

        a = Normalize(0, self.Files.shape[0] - 1)
        b = ScalarMappable(norm=a, cmap=get_cmap('rainbow'))

        Fig1.clear()

        for i in range(self.Files.shape[0]):

            if (self.Files[i].Used == True):
                self.Files[i].UpdateInfData()
                Fig1.labels("", self.x_axis.GetValue(), self.y_axis.GetValue())

                a = self.Files[i]

                if self.Legend.IsChecked() == True:
                    try:
                        Label = SplitName(a.DataFile, '_', '', 1)
                    except:
                        Label = str(i)
                else:
                    Label = ""

                if (self.InputPCGraph.IsChecked() == True):

                    Fig1.draw_points(self.GrabData(a, self.x_axis.GetValue())[0], self.GrabData(
                        a, self.y_axis.GetValue())[0], '^', Color=b.to_rgba(i))
                    if (self.InputSystemGraph.IsChecked() == True):
                        Fig1.draw_points(
                            a.SystemDeltan_PC, a.SystemTau_PC, ',', Color='k')

                if (self.InputPLGraph.IsChecked() == True):

                    Fig1.draw_points(self.GrabData(a, self.x_axis.GetValue())[1], self.GrabData(
                        a, self.y_axis.GetValue())[1], '8', Color=b.to_rgba(i), Label='')
                    if (self.InputSystemGraph.IsChecked() == True):
                        Fig1.draw_points(
                            a.SystemDeltan_PL, a.SystemTau_PL, ',', Color='k')

                Fig1.draw_points(
                    inf, inf, 's', Color=b.to_rgba(i), Label=Label)

        if (self.Files[i].Used == True and self.Files[i].Used == True):
            Fig1.legend()
        if self.InputCommonScale.IsChecked() == True:
            Fig1.Axes(1e9, 1e17, 1e-6, 1e-2)
        Fig1.update()

        a = ''
        self.DrawRawDataFig()

    def DrawRawDataFig(self):

        a = Normalize(0, self.Files.shape[0] - 1)
        b = ScalarMappable(norm=a, cmap=get_cmap('rainbow'))

        Fig2.clear()
        for i in range(self.Files.shape[0]):

            if (self.Files[i].Used == True):

                a = self.Files[i]

                Filler = linspace(0, 1, a.RawData['PC'].shape[0])
                Filler_croped = a.Data['Time'] / a.RawData['Time'][-1]

                if a.RawData['PC'].shape[0] > 1000:
                        # print int(1000/a.RawData['PC'].shape[0]),
                    num_raw = int(a.RawData['PC'].shape[0] / 1000)
                else:
                    num_raw = 1
                if a.Data['PC'].shape[0] > 1000:
                    # print int(1000/a.RawData['PC'].shape[0]),
                    num_proc = int(a.RawData['PC'].shape[0] / 1000)
                else:
                    num_proc = 1

                if (self.InputPCGraph.IsChecked() == True):
                    Fig2.draw_points(
                        Filler[::num_raw], a.RawData['PC'][::num_raw], '.', Color='k')
                    Fig2.draw_points(
                        Filler_croped[::num_proc], a.Data['PC'][::num_proc], '^', Color=b.to_rgba(i))

                if (self.InputPLGraph.IsChecked() == True):
                    # b=1

                    Fig2.draw_points(
                        Filler[::num_raw], a.RawData['PL'][::num_raw], '.', Color='k')
                    Fig2.draw_points(
                        Filler_croped[::num_proc], a.Data['PL'][::num_proc], 'o', Color=b.to_rgba(i))

        Fig2.draw_points(inf, inf, '.', Color='b', Label='Raw Data')

        a = ''
        Fig2.legend()
        Fig2.update()

    def LoadRawDataFile(self, e):
        """ Open a file"""

        self.DataSet = int(e.GetId())
        input_dic = collections.OrderedDict()
        # add what should appear as wild cards, in order
        input_dic['All Raw data Files'] = '*Data.dat;*.tsv'
        input_dic['Old QSSPL'] = '*_Raw Data.dat'
        input_dic['New QSSPL'] = '*.Raw Data.dat'
        input_dic['Temp Dep'] = '*.tsv'

        # make into format or wild cards
        ext_options = '|'.join(
            [key + "|" + val for key, val in input_dic.items()])

        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "",
                            ext_options, wx.OPEN)

        if dlg.ShowModal() == wx.ID_OK:  # Only continues when file is selected

            # Get the info about the file
            filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()

            # Makeing the name of the Text screen that is being updated
            ControlName = "LoadFileText" + str(self.DataSet)

            # updating that value
            self.waferdetails.FindWindowByName(
                ControlName).SetValue(filename[:-13])

            # Pulling the info from the data files.
            self.Files[self.DataSet].ProvideRawDataFile(self.dirname, filename)
            # Makein the cropping based on the Wavefunction
            self.Files[self.DataSet].ChoosingDefultCropValues()
            # placing the data that has been pulled from the files.
            self.Inital_Get_Inf_Info()

            dlg.Destroy()

            self.UpdateInputtedValues()

        else:

            dlg.Destroy()

    ##
    # Should return Ai,Btlow,fs, Doping, Thickness,"""Reflection"""
    ##
    def Inital_Get_Inf_Info(self):

        # only updates doping and thickness when the first file is loaded.
        if self.DataSet == 0:
            self.InputWaferDoping.SetValue(
                str(self.Files[self.DataSet].Wafer['Doping']))
            self.InputWaferThickness.SetValue(
                str(self.Files[self.DataSet].Wafer['Thickness']))

        # Grabs the values from the Data Dictionary
        for i in ['Fs', 'Ai']:
            self.waferdetails.FindWindowByName(
                i + str(self.DataSet)).SetValue('{0:.2e}'.format(self.Files[self.DataSet].Wafer[i]))

        for i in ['Reflection', 'CropStart', 'CropEnd', 'Binning']:
            self.waferdetails.FindWindowByName(
                i + str(self.DataSet)).SetValue(str(self.Files[self.DataSet].Wafer[i]))

    def OnKeyDownChangedProcessed(self, e):
        # print e.GetKeyCode()
        if (e.GetKeyCode() == 13):
            # This is for indicating which colum of data to use.
            if (e.GetId() > 0):
                self.DataSet = e.GetId() % 10

            self.UpdateInputtedValues()
            self.CalLifetieme()
            self.DrawProcessedData()

        e.Skip()

    def OnKeyDownChangedRaw(self, e):
        # print e.GetKeyCode()
        # print e.GetKeyCode()
        # print 'This is pressed when'
        if (e.GetKeyCode() == 13):
            # This is for indicating which colum of data to use.
            if (e.GetId() > 0):
                self.DataSet = e.GetId() % 10
            self.UpdateInputtedValues()
            self.CalLifetieme()
            self.DrawProcessedData()
        e.Skip()

    def CalLifetieme(self):

        for j in range(self.Files.shape[0]):
            a = self.Files[j]
            if a.Used:
                a.CalculateLifetime()

    def UpdateInputtedValues(self):
        # This should change later to check if values have changed, and then if
        # they have onlyprocess the files that have changed. Should make for
        # quicker plot refreshing

        for j in range(self.Files.shape[0]):

            a = self.Files[j]
            if (a.Used == True):

                for i in ['Fs', 'Ai', 'Reflection', 'Temp', 'CropStart', 'CropEnd']:
                    # print i
                    a.Wafer[i] = float(
                        self.waferdetails.FindWindowByName(i + str(j)).GetValue())

                for i in ['Binning']:
                    # print float(self.waferdetails.FindWindowByName(i + str(j)).GetValue()),i
                    # print a.Wafer[i]
                    a.Wafer[i] = int(
                        float(self.waferdetails.FindWindowByName(i + str(j)).GetValue()))

                a.Wafer['Quad'], a.Wafer['Lin'], a.Wafer['Const'] = float(self.InputPCa.GetValue(
                )), float(self.InputPCb.GetValue()), float(self.InputPCc.GetValue())

                a.Wafer['Thickness'] = float(
                    self.InputWaferThickness.GetValue())
                a.Wafer['Doping'] = float(self.InputWaferDoping.GetValue())
                a.Wafer['Type'] = self.InputDopingType.GetValue()

                a.Analysis = self.AnaylsisType.GetValue()
                a.Derivitive = self.DifferentialType.GetValue()

                # a.CalculateLifetime()

        a = None

    def CheckBoxChanged(self, e):
        self.DrawRawDataFig()
        self.DrawProcessedData()
        e.Skip()