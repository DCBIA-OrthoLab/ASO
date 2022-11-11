import os
import logging
import glob
import time
import vtk, qt, slicer
from qt import QWidget, QVBoxLayout, QScrollArea, QTabWidget, QCheckBox
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import webbrowser
from abc import ABC, abstractmethod
import json

# import csv


#region ========== FUNCTIONS ==========








# "Dental" :  ['LL7','LL6','LL5','LL4','LL3','LL2','LL1','LR1','LR2','LR3','LR4','LR5','LR6','LR7','UL7','UL6','UL5','UL4','UL3','UL2','UL1','UR1','UR2','UR3','UR4','UR5','UR6','UR7'] ,

# "Landmarks type" : ['CL','CB','O','DB','MB','R','RIP','OIP']






class ASO(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "ASO"  # TODO: make this more human readable by adding spaces
        self.parent.categories = ["Automated Dental Tools"]  # set categories (folders where the module shows up in the module selector)
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["Maxime Gillot (UoM), Baptiste Baquero (UoM)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        self.parent.helpText = """
        This is an example of scripted loadable module bundled in an extension.
        See more information in <a href="https://github.com/organization/projectname#ASO">module documentation</a>.
        """
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = """
        This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
        and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
        """

        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", self.registerSampleData)

        #
        # Register sample data sets in Sample Data module
        #

    def registerSampleData(self):
        """
        Add data sets to Sample Data module.
        """
        # It is always recommended to provide sample data for users to make it easy to try the module,
        # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

        import SampleData
        iconsPath = os.path.join(os.path.dirname(__file__), 'Resources/Icons')

        # To ensure that the source code repository remains small (can be downloaded and installed quickly)
        # it is recommended to store data sets that are larger than a few MB in a Github release.

        # ALI1
        SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category='ASO',
        sampleName='ASO1',
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, 'ASO1.png'),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        fileNames='ASO1.nrrd',
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums = 'SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95',
        # This node name will be used when the data set is loaded
        nodeNames='ASO1'
        )

        # ASO2
        SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category='ASO',
        sampleName='ASO2',
        thumbnailFileName=os.path.join(iconsPath, 'ASO2.png'),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        fileNames='ASO2.nrrd',
        checksums = 'SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97',
        # This node name will be used when the data set is loaded
        nodeNames='ASO2'
        )

#
# ASOWidget
#

class ASOWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None):
        """
        Called when the user opens the module the first time and the widget is initiASOzed.
        """
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._updatingGUIFromParameterNode = False



        self.nb_patient = 0 # number of scans in the input folder






    def setup(self):
        """
        Called when the user opens the module the first time and the widget is initiASOzed.
        """
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath('UI/ASO.ui'))
        self.layout.addWidget(uiWidget)

        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = ASOLogic()

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
        # (in the selected parameter node).


      

        #region ===== INPUTS =====



        self.MethodeDic={'IOS':IOS(self),'CBCT':CBCT(self)}
        self.ActualMeth= Methode
        self.nb_scan = 0
        self.startprocess =0
        self.patient_process = 0
        self.dicchckbox={}  
        self.dicchckbox2={}
        """
        exemple dic = {'teeth'=['A,....],'Type'=['O',...]}
        """

        self.initCheckbox(self.MethodeDic['IOS'],self.ui.LayoutLandmarkIOS,self.ui.tohideIOS)
        # self.initCheckbox(self.MethodeDic['CBCT'],self.ui.LayoutLandmarkCBCT,self.ui.tohideCBCT) a decommmente

        self.ui.ButtonSearchScanLmFolder.connect('clicked(bool)',self.SearchScanLm)
        self.ui.ButtonSearchReference.connect('clicked(bool)',self.SearchReference)
        self.ui.ButtonDowloadRefLm.connect('clicked(bool)',self.DownloadRef)
        self.ui.ButtonOriented.connect('clicked(bool)',self.onPredictButton)
        self.ui.ButtonOutput.connect('clicked(bool)',self.ChosePathOutput)
        self.ui.ButtonCancel.connect('clicked(bool)',self.onCancel)
        self.ui.ButtonSugestLmIOS.clicked.connect(self.SelectSugestLandmark)
        self.ui.ButtonSugestLmCBCT.clicked.connect(self.SelectSugestLandmark)

        self.ui.CbInputType.currentIndexChanged.connect(self.SwitchType)




    def SwitchType(self,index):
        if index == 0 :
            self.ActualMeth = self.MethodeDic['CBCT']
            self.ui.stackedWidget.setCurrentIndex(0)

        elif index == 1 :
            self.ActualMeth = self.MethodeDic['IOS']
            self.ui.stackedWidget.setCurrentIndex(1)

        self.dicchckbox=self.ActualMeth.getcheckbox()
        self.dicchckbox2=self.ActualMeth.getcheckbox2()

        self.updateCheckbox()


    def SearchScanLm(self):
        scan_folder = qt.QFileDialog.getExistingDirectory(self.parent, "Select a scan folder")
        if not scan_folder == '':
            nb_scans = self.ActualMeth.SearchScanLm(scan_folder)

        if nb_scans == 0 :
            qt.QMessageBox.warning(self.parent, 'Warning', 'No scans or landmark found in the selected folder')
        else :
            self.nb_patient = nb_scans
            self.ui.lineEditScanLmPath.setText(scan_folder)
            self.ui.LabelInfoPreProc.setText("Number of scans to process : " + str(nb_scans))
            self.ui.LabelProgress.setText('Patient process : 0 /'+str(nb_scans))
            self.updateCheckbox()

    def SearchReference(self):
        ref_folder = qt.QFileDialog.getExistingDirectory(self.parent, "Select a scan folder")
        if not ref_folder == '':
            error = self.ActualMeth.SearchReference(ref_folder)

        if isinstance(error,str):
            qt.QMessageBox.warning(self.parent, 'Warning', error)

        else:
            self.ui.lineEditRefFolder.setText(ref_folder)

    def ChosePathOutput(self):
        out_folder = qt.QFileDialog.getExistingDirectory(self.parent, "Select a scan folder")
        if not out_folder =='':
            self.ui.lineEditOutputPath.setText(out_folder)

    def DownloadRef(self):
        self.ActualMeth.DownloadRef()


    def SelectSugestLandmark(self):
        best = self.ActualMeth.SugestLandmark()
        for listcheckbox in self.dicchckbox.values():
            for checkbox in listcheckbox:
                if checkbox.text in best and checkbox.isEnabled():
                    checkbox.setCheckState(True)
                else :
                    checkbox.setCheckState(False)




    def onPredictButton(self):





        self.process = self.ActualMeth.Process(self.ui.lineEditScanLmPath.text,self.ui.lineEditRefFolder.text,self.ui.lineEditOutputPath.text,self.ui.lineEditAddName.text,self.dicchckbox)

        if isinstance(self.process,str):
            qt.QMessageBox.warning(self.parent, 'Warning', self.process.replace(',','\n'))

        else :

            self.processObserver = self.process.AddObserver('ModifiedEvent',self.onProcessUpdate)
            self.onProcessStarted()



    def onProcessStarted(self):
        self.startTime = time.time()

        self.ui.progressBar.setMaximum(self.nb_patient)
        self.ui.progressBar.setValue(0)


        self.ui.LabelProgress.setText(f"Patient : 0 / {self.nb_patient}")

        self.nb_patient_treat = 0
        self.progress = 0

        self.RunningUI(True)



    def onProcessUpdate(self,caller,event):

        timer = f"Time : {time.time()-self.startTime:.2f}s"
        self.ui.LabelTimer.setText(timer)
        progress = caller.GetProgress()

        if progress == 0:
            self.updateProgessBar = False

        if progress != 0 and self.updateProgessBar == False:
            self.updateProgessBar = True
            self.nb_patient_treat+=1
            self.ui.progressBar.setValue(self.nb_patient_treat)
            self.ui.LabelProgress.setText(f"patient : {self.nb_patient_treat} / {self.nb_patient}")

        if self.process.GetStatus() & self.process.Completed:
            # process complete


            if self.process.GetStatus() & self.process.ErrorsMask:
                # error
                print("\n\n ========= PROCESSED ========= \n")

                print(self.process.GetOutputText())
                print("\n\n ========= ERROR ========= \n")
                errorText = self.process.GetErrorText()
                print("CLI execution failed: \n \n" + errorText)


            else:


                self.OnEndProcess()


    def OnEndProcess(self):

        
        print('PROCESS DONE.')
        self.RunningUI(False)

        stopTime = time.time()

        logging.info(f'Processing completed in {stopTime-self.startTime:.2f} seconds')


    def onCancel(self):


        self.logic.cliNode.Cancel()


        self.RunningUI(False)




    def RunningUI(self, run = False):

        self.ui.ButtonOriented.setVisible(not run)

      
        self.ui.progressBar.setVisible(run)
        self.ui.LabelTimer.setVisible(run)




    def initCheckbox(self,methode,layout,tohide : qt.QLabel):
        tohide.setHidden(True)
        dic  = methode.DicLandmark()
        status = methode.existsLandmark('')
        dicchebox={}
        dicchebox2={}
        for type , tab in dic.items():
            
            Tab = QTabWidget()
            layout.addWidget(Tab)
            listcheckboxlandmark =[]
            listcheckboxlandmark2 = []

            all_checkboxtab = self.CreateMiniTab(Tab,'All',0)
            for i, (name , listlandmark) in enumerate(tab.items()):
                widget = self.CreateMiniTab(Tab,name,i+1)
                for landmark in listlandmark:
                    checkbox  = QCheckBox()
                    checkbox2 = QCheckBox()
                    checkbox.setText(landmark)
                    checkbox2.setText(landmark)
                    checkbox.setEnabled(status[landmark])
                    checkbox2.setEnabled(status[landmark])
                    checkbox2.toggled.connect(checkbox.setChecked)
                    checkbox.toggled.connect(checkbox2.setChecked)
                    widget.addWidget(checkbox)
                    all_checkboxtab.addWidget(checkbox2)
                    
                    listcheckboxlandmark.append(checkbox)
                    listcheckboxlandmark2.append(checkbox2)
                    

            dicchebox[type] = listcheckboxlandmark
            dicchebox2[type]=listcheckboxlandmark2

        methode.setcheckbox(dicchebox)
        methode.setcheckbox2(dicchebox2)



    def CreateMiniTab(self,tabWidget : QTabWidget, name : str, index : int):
    

        new_widget = QWidget()
        new_widget.setMinimumHeight(250)

        layout = QVBoxLayout(new_widget)

        scr_box = QScrollArea(new_widget)
        scr_box.setMinimumHeight(200)

        layout.addWidget(scr_box)

        new_widget2 = QWidget(scr_box)
        layout2 = QVBoxLayout(new_widget2)

        
        layout.addStretch()
        scr_box.setWidgetResizable(True)
        scr_box.setWidget(new_widget2)

        
        tabWidget.insertTab(index,new_widget,name)

        return layout2

    

    def updateCheckbox(self):
        status = self.ActualMeth.existsLandmark(self.ui.lineEditScanLmPath.text)
        for checkboxs,checkboxs2 in zip(self.dicchckbox.values(),self.dicchckbox2.values()):
            for checkbox, checkbox2 in zip(checkboxs,checkboxs2):
                checkbox.setEnabled(status[checkbox.text])
                checkbox2.setEnabled(status[checkbox2.text])


    def cleanup(self):
        """
        Called when the application closes and the module widget is destroyed.
        """
        if self.logic.cliNode is not None:
            # if self.logic.cliNode.GetStatus() & self.logic.cliNode.Running:
            self.logic.cliNode.Cancel() 

        self.removeObservers()

    def enter(self):
        """
        Called each time the user opens this module.
        """
        # Make sure parameter node exists and observed
        self.initializeParameterNode()

    def exit(self):
        """
        Called each time the user opens a different module.
        """
        # Do not react to parameter node changes (GUI wlil be updated when the user enters into the module)
        self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

    def onSceneStartClose(self, caller, event):
        """
        Called just before the scene is closed.
        """
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event):
        """
        Called just after the scene is closed.
        """
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self):
        """
        Ensure parameter node exists and observed.
        """
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.


    def setParameterNode(self, inputParameterNode):
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        # if inputParameterNode:
        self.setParameterNode(self.logic.getParameterNode())

        # Unobserve previously selected parameter node and add an observer to the newly selected.
        # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
        # those are reflected immediately in the GUI.
        if self._parameterNode is not None:
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
        self._parameterNode = inputParameterNode
        if self._parameterNode is not None:
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

        # Initial GUI update
        self.updateGUIFromParameterNode()

    def updateGUIFromParameterNode(self, caller=None, event=None):
        """
        This method is called whenever parameter node is changed.
        The module GUI is updated to show the current state of the parameter node.
        """

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
        self._updatingGUIFromParameterNode = True

        # Update node selectors and sliders
        self.ui.inputSelector.setCurrentNode(self._parameterNode.GetNodeReference("InputVolume"))
        self.ui.outputSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputVolume"))
        self.ui.invertedOutputSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputVolumeInverse"))
        # self.ui.imageThresholdSliderWidget.value = float(self._parameterNode.GetParameter("Threshold"))
        self.ui.invertOutputCheckBox.checked = (self._parameterNode.GetParameter("Invert") == "true")

        # Update buttons states and tooltips
        # if self._parameterNode.GetNodeReference("InputVolume") and self._parameterNode.GetNodeReference("OutputVolume"):
        #   self.ui.applyButton.toolTip = "Compute output volume"
        #   self.ui.applyButton.enabled = True
        # else:
        #   self.ui.applyButton.toolTip = "Select input and output volume nodes"
        #   self.ui.applyButton.enabled = False

        # All the GUI updates are done
        self._updatingGUIFromParameterNode = False

    def updateParameterNodeFromGUI(self, caller=None, event=None):
        """
        This method is called when the user makes any change in the GUI.
        The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
        """

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

        self._parameterNode.SetNodeReferenceID("InputVolume", self.ui.inputSelector.currentNodeID)
        self._parameterNode.SetNodeReferenceID("OutputVolume", self.ui.outputSelector.currentNodeID)
        # self._parameterNode.SetParameter("Threshold", str(self.ui.imageThresholdSliderWidget.value))
        self._parameterNode.SetParameter("Invert", "true" if self.ui.invertOutputCheckBox.checked else "false")
        self._parameterNode.SetNodeReferenceID("OutputVolumeInverse", self.ui.invertedOutputSelector.currentNodeID)

        self._parameterNode.EndModify(wasModified)











#
# ASOLogic
#

class ASOLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self):
        """
        Called when the logic class is instantiated. Can be used for initializing member variables.
        """
        ScriptedLoadableModuleLogic.__init__(self)

        self.cliNode = None


    def process(self, parameters):
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param inputVolume: volume to be thresholded

        """

        # import time
        # startTime = time.time()

        logging.info('Processing started')

        PredictProcess = slicer.modules.aso_ios


        self.cliNode = slicer.cli.run(PredictProcess, None, parameters)


        return PredictProcess




class Methode(ABC):
    def __init__(self,widget):
        self.widget = widget
        self.diccheckbox = {}
        self.diccheckbox2={}

    @abstractmethod
    def SearchScanLm(self,scan_folder : str ):
        """
            count the number of patient in folder
            if the number of patient is 0, Slicer display an error for user to chose a file with landmark and IOS/CBCT
        Args:
            scan_folder (str): folder path with landmark and IOS/CBCT to oriented


        Return:
            int : return the number of patient. If number is 0, slicer display a warning for user
        """
        pass

    @abstractmethod
    def SearchReference(self,ref_folder :str):
        """Look in folder if there are gold landmark, if Ture return None and if False return str with error message to user

        Args:
            ref_folder (str): folder path with gold landmark 

        Return :
            str or None : display str to user like warning
        """


        pass 

    @abstractmethod
    def DownloadRef(self):
        """Download Landmark ref in our gitbub
        """
        pass

    @abstractmethod
    def Process(self,folder_ScanLm,folder_gold,folder_output,add_in_namefile,list_landmark):
        """Launch orient's code

        Args:
            folder_ScanLm (str): _description_
            folder_gold (str): _description_
            folder_output (str): _description_
            add_in_namefile (str): _description_
        """

        pass
    @abstractmethod
    def DicLandmark(self):
        """
        return dic landmark like this:
        dic = {'teeth':{
                        'Lower':['LR6','LR5',...],
                        'Upper':['UR6',...]
                        },
                'Landmark':{
                        'Occlusual':['O',...],
                        'Cervical':['R',...]
                        }
                }
        """

        pass


    @abstractmethod
    def ListLandmark(self):

        pass

    @abstractmethod
    def existsLandmark(self,pathfile):
        pass

    @abstractmethod
    def SugestLandmark(self):

        pass

    def getcheckbox(self):
        return self.diccheckbox

    def setcheckbox(self,dicccheckbox):
        self.diccheckbox = dicccheckbox

    def getcheckbox2(self):
        return self.diccheckbox2

    def setcheckbox2(self,dicccheckbox):
        self.diccheckbox2 = dicccheckbox


    def search(self,path,type):
        out=[]
        a = glob.glob(path+'/*'+type)
        for p in a: 
            if os.path.isfile(p):
                out.append(p)
            else:
                out+= self.search(path=p,type=type)
        return out


class IOS(Methode):
    def __init__(self, widget):
        super().__init__(widget)


    def SearchScanLm(self, scan_folder: str):
            
        return len(super().search(scan_folder,'vtk'))


    def SearchReference(self, ref_folder: str):
        list = glob.glob(ref_folder+'/*json')
        out = None
        if len(list) == 0:
            out = 'Please choose a folder with json file'
        elif len(list)>2:
            out = 'Too many json file '
        return out

    def DownloadRef(self):
        webbrowser.open('https://github.com/HUTIN1/SlicerAutomatedDentalTools/releases/download/untagged-a16b2657fd8938d33138/GOLD_file.zip')
        


    def Process(self, folder_ScanLm, folder_gold, folder_output, add_in_namefile,dic_landmark):

        out  = ''
        list_landmark = self.LandmarkisChecked(dic_landmark)

        if len(super().search(folder_ScanLm,'vtk'))==0:
            out = out + "Give folder with vkt file,"
        if len(super().search(folder_ScanLm,'json')) == 0:
            out = out + "Give folder with json file,"
        if len(super().search(folder_gold,'json')) == 0 :
            out = out + "Give folder with minimum one json file like gold landmark,"
        if folder_output == '':
            out = out + "Give output folder,"

        if len(list_landmark.split(','))< 3:
            out = out + "Give minimum 3 landmark,"
        if add_in_namefile== '':
            out = out + "Give somethinf to add in name of file,"
        


        if out == '':

            parameter= {'input':folder_ScanLm,'folder_gold':folder_gold,'output_folder':folder_output,'add_infile':add_in_namefile,'list_landmark':list_landmark }
            OrientProcess = slicer.modules.aso_ios
            process = slicer.cli.run(OrientProcess,None,parameter)

            out = process

        else :
            out = out[:-1]

        return out

    def DicLandmark(self):
       
        dic = {'Teeth':
                    {'Upper':['UL7','UL6','UL5','UL4','UL3','UL2','UL1','UR1','UR2','UR3','UR4','UR5','UR6','UR7'],
                    'Lower':['LL7','LL6','LL5','LL4','LL3','LL2','LL1','LR1','LR2','LR3','LR4','LR5','LR6','LR7']
                    },
                'Landmark':
                    {'Cervical':['CL','CB','R','RIP','OIP'],
                    'Occlusal' : ['O','DB','MB']
                    }
                }
        return dic

    def ListLandmark(self):
        list = ['UL7','UL6','UL5','UL4','UL3','UL2','UL1','UR1','UR2','UR3','UR4','UR5','UR6','UR7','LL7','LL6','LL5','LL4','LL3','LL2','LL1','LR1','LR2','LR3','LR4','LR5','LR6','LR7','CL','CB','R','RIP','OIP','O','DB','MB']
        return list



    def existsLandmark(self,folderpath):
        teeth = ['UL7','UL6','UL5','UL4','UL3','UL2','UL1','UR1','UR2','UR3','UR4','UR5','UR6','UR7','LL7','LL6','LL5','LL4','LL3','LL2','LL1','LR1','LR2','LR3','LR4','LR5','LR6','LR7']
        landmarks = ['CL','CB','R','RIP','OIP','O','DB','MB']
        dicLandmarkexists={}
        path  = glob.glob(folderpath+'/*json')
        if folderpath == '':
            for tooth in teeth:
                dicLandmarkexists[tooth] = False
            for landmark in landmarks:
                dicLandmarkexists[landmark] = False
        else :

            paths = glob.glob(folderpath+'/*json')
            listlandmark = []
            for path in paths:
                with open(path) as f:
                    data = json.load(f)
                
                markups = data["markups"][0]["controlPoints"]
            
                
                for markup in markups:
                    listlandmark.append(markup['label'])

            listlandmark = set(listlandmark)


            dicLandmarkexists={}
            
            for tooth in teeth :
                if True in [tooth in lm[:3] for lm in listlandmark]:
                    dicLandmarkexists[tooth] = True

                else :
                    dicLandmarkexists[tooth] = False

            for landmark in landmarks :
                if True in [landmark in lm[3:] for lm in listlandmark]:
                    dicLandmarkexists[landmark] = True

                else :
                    dicLandmarkexists[landmark] = False 

        return dicLandmarkexists

    def SugestLandmark(self):
        return ['UR6','UR1','UL6','UL1','LR1','LR6','LL1','LL6','O']



    def LandmarkisChecked(self,diccheckbox : dict):

        out=''
        if not len(diccheckbox) == 0:

            listcheckbox=[]


            for i, checkboxs in enumerate(diccheckbox.values()):
                listcheckbox.append([])
                for checkbox in checkboxs:
                    if checkbox.isChecked():
                        listcheckbox[i].append(checkbox.text)
            
            for a in listcheckbox[0]:
                for b in listcheckbox[1]:
                    landmark = a+b+','
                    out=out +landmark
            out = out[:-1]
        return out






class CBCT(Methode):
    def __init__(self, widget):
        super().__init__(widget)

    def SearchReference(self, ref_folder: str):
        return super().SearchReference(ref_folder)

    def SearchScanLm(self, scan_folder: str):
        return super().SearchScanLm(scan_folder)

    def DownloadRef(self):
        return super().DownloadRef()

    def Process(self, folder_ScanLm, folder_gold, folder_output, add_in_namefile,list_landmark):
        return super().Process(folder_ScanLm, folder_gold, folder_output, add_in_namefile,list_landmark)

    def DicLandmark(self):
        return super().DicLandmark()

    def ListLandmark(self):
        return super().ListLandmark()
        
    def existsLandmark(self,pathfile):
        return super().existsLandmark()

    def SugestLandmark(self):
        return super().SugestLandmark()
