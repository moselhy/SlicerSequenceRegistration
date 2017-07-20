import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

#
# Elastix4D
#

class Elastix4D(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Elastix4D" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Registration"]
    self.parent.dependencies = []
    self.parent.contributors = ["Mohamed Moselhy (Western University)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
It performs a simple thresholding on the input volume and optionally captures a screenshot.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# Elastix4DWidget
#

class Elastix4DWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    self.registrationInProgress = False
    self.logic = ElastixLogic()
    self.tempNodes = []

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # input volume selector
    #
    self.inputSelector = slicer.qMRMLNodeComboBox()
    self.inputSelector.nodeTypes = ["vtkMRMLSequenceNode"]
    self.inputSelector.selectNodeUponCreation = True
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = False
    self.inputSelector.noneEnabled = False
    self.inputSelector.showHidden = False
    self.inputSelector.showChildNodeTypes = False
    self.inputSelector.setMRMLScene( slicer.mrmlScene )
    self.inputSelector.setToolTip( "Pick the input to the algorithm." )
    parametersFormLayout.addRow("Input Sequence: ", self.inputSelector)

    browserNodes = slicer.util.getNodesByClass("vtkMRMLSequenceBrowserNode")
    self.inputVolumeBrowser = None
    self.movingBrowserNode = None
    for browserNode in browserNodes:
      if browserNode.IsSynchronizedSequenceNode(self.inputSelector.currentNode(), True):
        self.inputVolumeBrowser = browserNode

    self.fixedIndex = -1
    self.movingIndex = -1

    #
    # output volume selector
    #
    self.outputVolumesSelector = slicer.qMRMLNodeComboBox()
    self.outputVolumesSelector.nodeTypes = ["vtkMRMLSequenceNode"]
    self.outputVolumesSelector.selectNodeUponCreation = True
    self.outputVolumesSelector.addEnabled = True
    self.outputVolumesSelector.removeEnabled = True
    self.outputVolumesSelector.noneEnabled = True
    self.outputVolumesSelector.showHidden = False
    self.outputVolumesSelector.showChildNodeTypes = False
    self.outputVolumesSelector.setMRMLScene( slicer.mrmlScene )
    self.outputVolumesSelector.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Output Sequence: ", self.outputVolumesSelector)
    self.outputVolumeBrowser = None

    self.outputSeqIndex = -1


    
    # output transform selector
    
    self.outputTransformSelector = slicer.qMRMLNodeComboBox()
    self.outputTransformSelector.nodeTypes = ["vtkMRMLSequenceNode"]
    self.outputTransformSelector.selectNodeUponCreation = True
    self.outputTransformSelector.addEnabled = True
    self.outputTransformSelector.removeEnabled = True
    self.outputTransformSelector.noneEnabled = True
    self.outputTransformSelector.showHidden = False
    self.outputTransformSelector.showChildNodeTypes = False
    self.outputTransformSelector.setMRMLScene( slicer.mrmlScene )
    self.outputTransformSelector.setToolTip( "(optional) Computed displacement field that transform nodes from moving volume space to fixed volume space. NOTE: You must set at least one output object (transform and/or output volume)." )
    parametersFormLayout.addRow("Output transform: ", self.outputTransformSelector)


    # 
    # Preset selector
    # 
    self.elastixLogic = ElastixLogic()
    self.registrationPresetSelector = qt.QComboBox()
    for preset in self.elastixLogic.getRegistrationPresets():
      self.registrationPresetSelector.addItem("{0} ({1})".format(preset[RegistrationPresets_Modality], preset[RegistrationPresets_Content]))
    parametersFormLayout.addRow("Preset: ", self.registrationPresetSelector)


    #
    # Advanced Area
    #
    advancedCollapsibleButton = ctk.ctkCollapsibleButton()
    advancedCollapsibleButton.text = "Advanced"
    advancedCollapsibleButton.collapsed = 1
    self.layout.addWidget(advancedCollapsibleButton)

    # Layout within the dummy collapsible button
    advancedFormLayout = qt.QFormLayout(advancedCollapsibleButton)


    #
    # Step size of input (i.e. register with fixed volume at frame X)
    #

    label = qt.QLabel('Input Step:')
    self.inputStepSize = qt.QDoubleSpinBox()
    self.inputStepSize.value = 0
    self.inputStepSize.setMinimum(0)
    advancedFormLayout.addRow(label, self.inputStepSize)

    #
    # fixed frame number value
    #
    self.initialFixedFrame = ctk.ctkSliderWidget()
    self.initialFixedFrame.singleStep = 1
    self.initialFixedFrame.minimum = 1
    self.initialFixedFrame.value = 1
    self.initialFixedFrame.setToolTip("Set the frame of the input sequence that you would like to use as the fixed volume.")
    advancedFormLayout.addRow("Start at fixed frame number", self.initialFixedFrame)

    #
    # Option to select custom Elastix directory
    #

    customElastixBinDir = self.elastixLogic.getCustomElastixBinDir()
    self.customElastixBinDirSelector = ctk.ctkPathLineEdit()
    self.customElastixBinDirSelector.filters = ctk.ctkPathLineEdit.Dirs
    self.customElastixBinDirSelector.setCurrentPath(customElastixBinDir)
    self.customElastixBinDirSelector.setSizePolicy(qt.QSizePolicy.MinimumExpanding, qt.QSizePolicy.Preferred)
    self.customElastixBinDirSelector.setToolTip("Set bin directory of an Elastix installation (where elastix executable is located). "
      "If value is empty then default elastix (bundled with SlicerElastix extension) will be used.")
    advancedFormLayout.addRow("Custom Elastix toolbox location:", self.customElastixBinDirSelector)

    #
    # Option to show detailed log
    #

    self.showDetailedLogDuringExecutionCheckBox = qt.QCheckBox(" ")
    self.showDetailedLogDuringExecutionCheckBox.checked = False
    self.showDetailedLogDuringExecutionCheckBox.setToolTip("Show detailed log during registration.")
    advancedFormLayout.addRow("Show detailed log during registration:", self.showDetailedLogDuringExecutionCheckBox)

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Register")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    self.layout.addWidget(self.applyButton)


    self.statusLabel = qt.QPlainTextEdit()
    self.statusLabel.setTextInteractionFlags(qt.Qt.TextSelectableByMouse)
    self.statusLabel.setCenterOnScroll(True)
    self.layout.addWidget(self.statusLabel)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.outputVolumesSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    if not self.inputSelector.currentNode():
      self.numberOfDataNodes = 0
    else:
      self.numberOfDataNodes = self.inputSelector.currentNode().GetNumberOfDataNodes()

    self.initialFixedFrame.maximum = self.numberOfDataNodes
    self.inputStepSize.setMaximum(self.numberOfDataNodes)
    self.applyButton.enabled = self.inputSelector.currentNode() and self.outputVolumesSelector.currentNode()
    self.fixedIndex = self.initialFixedFrame.value - 1

    if not self.registrationInProgress:
      self.applyButton.text = "Register"
      return
    # self.updateBrowsers()

  def onApplyButton(self):
    # Refresh variables
    self.onSelect()

    if self.registrationInProgress:
      self.registrationInProgress = False
      self.logic.abortRequested = True
      self.applyButton.text = "Cancelling..."
      self.applyButton.enabled = False
      return

    self.registrationInProgress = True
    self.applyButton.text = "Cancel"
    self.statusLabel.plainText = ''
    slicer.app.setOverrideCursor(qt.Qt.WaitCursor)
    try:
      if self.customElastixBinDirSelector.currentPath:
        self.logic.setCustomElastixBinDir(self.customElastixBinDirSelector.currentPath)

      self.logic.logStandardOutput = self.showDetailedLogDuringExecutionCheckBox.checked

      parameterFilenames = self.logic.getRegistrationPresets()[self.registrationPresetSelector.currentIndex][RegistrationPresets_ParameterFilenames]

      # Copy the volumes that will not be registered as is
      if self.initialFixedFrame.value != 1:
        self.copySequences(inputSequence, outputSequence, self.initialFixedFrame.value - 1)

      # self.inputVolumeBrowser.SetSelectedItemNumber(int(self.initialFixedFrame.value))

      while True:
        (fixedFrame, movingFrame) = self.getNextMove()
        if not (fixedFrame and movingFrame):
          break


        inputSeq = self.inputSelector.currentNode()
        outputVolSeq = self.outputVolumesSelector.currentNode()
        outputTransformSeq = self.outputTransformSelector.currentNode()

        tmpVol = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        self.tempNodes.append(tmpVol)
        outputVol = outputVolSeq.SetDataNodeAtValue(tmpVol, str(self.outputSeqIndex))


        tmpTransform = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode")
        # self.tempNodes.append(tmpTransform)

        # v1 = slicer.util.loadVolume(r'C:\Users\Moselhy\Downloads\v1.nrrd', returnNode=True)[1]
        # v2 = slicer.util.loadVolume(r'C:\Users\Moselhy\Downloads\v2.nrrd', returnNode=True)[1]

        self.logic.registerVolumes(
          fixedFrame, movingFrame,
          # v1, v2,
          outputVolumeNode = outputVol,
          parameterFilenames = parameterFilenames,
          outputTransformNode = tmpTransform
          # fixedVolumeMaskNode = self.fixedVolumeMaskSelector.currentNode(),
          # movingVolumeMaskNode = self.movingVolumeMaskSelector.currentNode()
          )

        outputTransform = outputTransformSeq.SetDataNodeAtValue(tmpTransform, str(self.outputSeqIndex))
        slicer.mrmlScene.AddNode(outputTransform)


        for i in range(len(self.tempNodes)):
          n = self.tempNodes.pop()
          slicer.mrmlScene.RemoveNode(n)

    except Exception as e:
      print e
      self.addLog("Error: {0}".format(e.message))
      import traceback
      traceback.print_exc()
    finally:
      slicer.app.restoreOverrideCursor()
      self.registrationInProgress = False
      self.onSelect() # restores default Apply button state


  def addLog(self, text):
    """Append text to log window
    """
    self.statusLabel.appendPlainText(text)
    slicer.app.processEvents()  # force update

  def getNextMove(self):
    self.fixedIndex += self.inputStepSize.value
    self.movingIndex += 1
    self.outputSeqIndex += 1

    # nextFixedFrameIndex = self.inputVolumeBrowser.SelectNextItem(int(self.inputStepSize.value))
    # nextMovingFrameIndex = self.movingBrowserNode.SelectNextItem()

    nextFixedFrame = self.inputSelector.currentNode().GetNthDataNode(int(self.fixedIndex))
    nextMovingFrame = self.inputSelector.currentNode().GetNthDataNode(int(self.movingIndex))

    self.tempNodes.append(nextFixedFrame)
    self.tempNodes.append(nextMovingFrame)

    nextFixedFrame.SetName("fixedFrame"+str(self.fixedIndex))
    nextMovingFrame.SetName("movingFrame"+str(self.movingIndex))

    slicer.mrmlScene.AddNode(nextFixedFrame)
    slicer.mrmlScene.AddNode(nextMovingFrame)

    # If there are no more frames available, return None
    if self.fixedIndex >= self.numberOfDataNodes:
      return None, None

    return nextFixedFrame, nextMovingFrame

  def copySequences(self, srcSeq, trgSeq, numberOfVols):
    for i in range(numberOfVols):
      self.movingIndex += 1
      self.outputSeqIndex += 1
      srcVol = srcSeq.GetDataNodeAtValue(str(i))
      outputSequence.SetDataNodeAtValue(srcVol, str(i))

  # def updateBrowsers(self):
  #   if self.outputVolumesSelector.currentNode() and not self.outputVolumeBrowser:
  #     self.outputVolumeBrowser = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSequenceBrowserNode")
  #     self.outputVolumeBrowser.SetAndObserveMasterSequenceNodeID(self.outputVolumesSelector.currentNode().GetID())
  #     self.outputVolumeBrowser.SetSelectedItemNumber(0)

  #   if self.inputSelector.currentNode() and not self.inputVolumeBrowser:
  #     self.inputVolumeBrowser = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSequenceBrowserNode")
  #     self.inputVolumeBrowser.SetAndObserveMasterSequenceNodeID(self.inputSelector.currentNode().GetID())
  #     self.inputVolumeBrowser.SetSelectedItemNumber(0)

  #   if self.inputSelector.currentNode() and not self.movingBrowserNode:
  #     self.movingBrowserNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSequenceBrowserNode")
  #     self.movingBrowserNode.SetAndObserveMasterSequenceNodeID(self.inputSelector.currentNode().GetID())
  #     self.movingBrowserNode.SetSelectedItemNumber(0)

#
# Elastix4DLogic
#

class Elastix4DLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def hasImageData(self,volumeNode):
    """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      logging.debug('hasImageData failed: no volume node')
      return False
    if volumeNode.GetImageData() is None:
      logging.debug('hasImageData failed: no image data in volume node')
      return False
    return True

  def isValidInputOutputData(self, inputVolumeNode, outputVolumeNode):
    """Validates if the output is not the same as input
    """
    if not inputVolumeNode:
      logging.debug('isValidInputOutputData failed: no input volume node defined')
      return False
    if not outputVolumeNode:
      logging.debug('isValidInputOutputData failed: no output volume node defined')
      return False
    if inputVolumeNode.GetID()==outputVolumeNode.GetID():
      logging.debug('isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
      return False
    return True

  def takeScreenshot(self,name,description,type=-1):
    # show the message even if not taking a screen shot
    slicer.util.delayDisplay('Take screenshot: '+description+'.\nResult is available in the Annotations module.', 3000)

    lm = slicer.app.layoutManager()
    # switch on the type to get the requested window
    widget = 0
    if type == slicer.qMRMLScreenShotDialog.FullLayout:
      # full layout
      widget = lm.viewport()
    elif type == slicer.qMRMLScreenShotDialog.ThreeD:
      # just the 3D window
      widget = lm.threeDWidget(0).threeDView()
    elif type == slicer.qMRMLScreenShotDialog.Red:
      # red slice window
      widget = lm.sliceWidget("Red")
    elif type == slicer.qMRMLScreenShotDialog.Yellow:
      # yellow slice window
      widget = lm.sliceWidget("Yellow")
    elif type == slicer.qMRMLScreenShotDialog.Green:
      # green slice window
      widget = lm.sliceWidget("Green")
    else:
      # default to using the full window
      widget = slicer.util.mainWindow()
      # reset the type so that the node is set correctly
      type = slicer.qMRMLScreenShotDialog.FullLayout

    # grab and convert to vtk image data
    qpixMap = qt.QPixmap().grabWidget(widget)
    qimage = qpixMap.toImage()
    imageData = vtk.vtkImageData()
    slicer.qMRMLUtils().qImageToVtkImageData(qimage,imageData)

    annotationLogic = slicer.modules.annotations.logic()
    annotationLogic.CreateSnapShot(name, description, type, 1, imageData)

  def run(self, inputVolume, outputVolume, imageThreshold, enableScreenshots=0):
    """
    Run the actual algorithm
    """

    if not self.isValidInputOutputData(inputVolume, outputVolume):
      slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
      return False

    logging.info('Processing started')

    # Compute the thresholded output volume using the Threshold Scalar Volume CLI module
    cliParams = {'InputVolume': inputVolume.GetID(), 'OutputVolume': outputVolume.GetID(), 'ThresholdValue' : imageThreshold, 'ThresholdType' : 'Above'}
    cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True)

    # Capture screenshot
    if enableScreenshots:
      self.takeScreenshot('Elastix4DTest-Start','MyScreenshot',-1)

    logging.info('Processing completed')

    return True


class Elastix4DTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_Elastix4D1()

  def test_Elastix4D1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = Elastix4DLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')

class ElastixLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self):
    ScriptedLoadableModuleLogic.__init__(self)
    self.logCallback = None
    self.abortRequested = False
    self.deleteTemporaryFiles = True
    self.logStandardOutput = False
    self.registrationPresets = None
    self.customElastixBinDirSettingsKey = 'Elastix/CustomElastixPath'
    import os
    self.scriptPath = os.path.dirname(os.path.abspath(__file__))
    self.registrationParameterFilesDir = os.path.abspath(os.path.join(self.scriptPath, 'Resources', 'RegistrationParameters'))
    self.elastixBinDir = None # this will be determined dynamically

    import platform
    executableExt = '.exe' if platform.system() == 'Windows' else ''
    self.elastixFilename = 'elastix' + executableExt
    self.transformixFilename = 'transformix' + executableExt

  def addLog(self, text):
    logging.info(text)
    if self.logCallback:
      self.logCallback(text)

  def getElastixBinDir(self):
    if self.elastixBinDir:
      return self.elastixBinDir

    self.elastixBinDir = self.getCustomElastixBinDir()
    if self.elastixBinDir:
      return self.elastixBinDir

    elastixBinDirCandidates = [
      # install tree
      os.path.join(self.scriptPath, '../../../bin'),
      # build tree
      os.path.join(self.scriptPath, '../../../../bin'),
      os.path.join(self.scriptPath, '../../../../bin/Release'),
      os.path.join(self.scriptPath, '../../../../bin/Debug'),
      os.path.join(self.scriptPath, '../../../../bin/RelWithDebInfo'),
      os.path.join(self.scriptPath, '../../../../bin/MinSizeRel') ]

    for elastixBinDirCandidate in elastixBinDirCandidates:
      if os.path.isfile(os.path.join(elastixBinDirCandidate, self.elastixFilename)):
        # elastix found
        self.elastixBinDir = os.path.abspath(elastixBinDirCandidate)
        return self.elastixBinDir

    raise ValueError('Elastix not found')

  def getCustomElastixBinDir(self):
    settings = qt.QSettings()
    if settings.contains(self.customElastixBinDirSettingsKey):
      return slicer.util.toVTKString(settings.value(self.customElastixBinDirSettingsKey))
    return ''

  def setCustomElastixBinDir(self, customPath):
    # don't save it if already saved
    settings = qt.QSettings()
    if settings.contains(self.customElastixBinDirSettingsKey):
      if customPath == settings.value(self.customElastixBinDirSettingsKey):
        return
    settings.setValue(self.customElastixBinDirSettingsKey, customPath)
    # Update elastix bin dir
    self.elastixBinDir = None
    self.getElastixBinDir()

  def getElastixEnv(self):
    """Create an environment for elastix where executables are added to the path"""
    elastixBinDir = self.getElastixBinDir()
    elastixEnv = os.environ.copy()
    elastixEnv["PATH"] = elastixBinDir + os.pathsep + elastixEnv["PATH"] if elastixEnv.get("PATH") else elastixBinDir

    import platform
    if platform.system() != 'Windows':
      elastixLibDir = os.path.abspath(os.path.join(elastixBinDir, '../lib'))
      elastixEnv["LD_LIBRARY_PATH"] = elastixLibDir + os.pathsep + elastixEnv["LD_LIBRARY_PATH"] if elastixEnv.get("LD_LIBRARY_PATH") else elastixLibDir

    return elastixEnv

  def getRegistrationPresets(self):
    if self.registrationPresets:
      return self.registrationPresets

    # Read database from XML file
    elastixParameterSetDatabasePath = os.path.join(self.scriptPath, 'Resources', 'RegistrationParameters', 'ElastixParameterSetDatabase.xml')
    if not os.path.isfile(elastixParameterSetDatabasePath):
      raise ValueError("Failed to open parameter set database: "+elastixParameterSetDatabasePath)
    elastixParameterSetDatabaseXml = vtk.vtkXMLUtilities.ReadElementFromFile(elastixParameterSetDatabasePath)
    elastixParameterSetDatabaseXml.UnRegister(None)

    # Create python list from XML for convenience
    self.registrationPresets = []
    for parameterSetIndex in range(elastixParameterSetDatabaseXml.GetNumberOfNestedElements()):
      parameterSetXml = elastixParameterSetDatabaseXml.GetNestedElement(parameterSetIndex)
      parameterFilesXml = parameterSetXml.FindNestedElementWithName('ParameterFiles')
      parameterFiles = []
      for parameterFileIndex in range(parameterFilesXml.GetNumberOfNestedElements()):
        parameterFiles.append(parameterFilesXml.GetNestedElement(parameterFileIndex).GetAttribute('Name'))
      self.registrationPresets.append([parameterSetXml.GetAttribute('id'), parameterSetXml.GetAttribute('modality'),
        parameterSetXml.GetAttribute('content'), parameterSetXml.GetAttribute('description'), parameterSetXml.GetAttribute('publications'), parameterFiles])

    return self.registrationPresets

  def startElastix(self, cmdLineArguments):
    self.addLog("Register volumes...")
    import subprocess
    executableFilePath = os.path.join(self.getElastixBinDir(),self.elastixFilename)
    logging.info("Register volumes using: "+executableFilePath+": "+repr(cmdLineArguments))
    return subprocess.Popen([executableFilePath] + cmdLineArguments, env=self.getElastixEnv(),
                            stdout=subprocess.PIPE, universal_newlines=True)

  def startTransformix(self, cmdLineArguments):
    self.addLog("Generate output...")
    import subprocess
    executableFilePath = os.path.join(self.getElastixBinDir(), self.transformixFilename)
    logging.info("Generate output using: " + executableFilePath + ": " + repr(cmdLineArguments))
    return subprocess.Popen([os.path.join(self.getElastixBinDir(),self.transformixFilename)] + cmdLineArguments, env=self.getElastixEnv(),
                            stdout=subprocess.PIPE, universal_newlines = True)

  def logProcessOutput(self, process):
    # save process output (if not logged) so that it can be displayed in case of an error
    processOutput = ''
    import subprocess
    for stdout_line in iter(process.stdout.readline, ""):
      if self.logStandardOutput:
        self.addLog(stdout_line.rstrip())
      else:
        processOutput += stdout_line.rstrip() + '\n'
      slicer.app.processEvents()  # give a chance to click Cancel button
      if self.abortRequested:
        process.kill()
    process.stdout.close()
    return_code = process.wait()
    if return_code:
      if self.abortRequested:
        raise ValueError("User requested cancel.")
      else:
        if processOutput:
          self.addLog(processOutput)
        raise subprocess.CalledProcessError(return_code, "elastix")

  def getTempDirectoryBase(self):
    tempDir = qt.QDir(slicer.app.temporaryPath)
    fileInfo = qt.QFileInfo(qt.QDir(tempDir), "Elastix")
    dirPath = fileInfo.absoluteFilePath()
    qt.QDir().mkpath(dirPath)
    return dirPath

  def createTempDirectory(self):
    import qt, slicer
    tempDir = qt.QDir(self.getTempDirectoryBase())
    tempDirName = qt.QDateTime().currentDateTime().toString("yyyyMMdd_hhmmss_zzz")
    fileInfo = qt.QFileInfo(qt.QDir(tempDir), tempDirName)
    dirPath = fileInfo.absoluteFilePath()
    qt.QDir().mkpath(dirPath)
    return dirPath

  def registerVolumes(self, fixedVolumeNode, movingVolumeNode, parameterFilenames = None, outputVolumeNode = None, outputTransformNode = None,
    fixedVolumeMaskNode = None, movingVolumeMaskNode = None):

    self.abortRequested = False
    tempDir = self.createTempDirectory()
    self.addLog('Volume registration is started in working directory: '+tempDir)

    # Write inputs
    inputDir = os.path.join(tempDir, 'input')
    qt.QDir().mkpath(inputDir)

    inputParamsElastix = []

    # Add input volumes
    inputVolumes = []
    inputVolumes.append([fixedVolumeNode, 'fixed.mha', '-f'])
    inputVolumes.append([movingVolumeNode, 'moving.mha', '-m'])
    inputVolumes.append([fixedVolumeMaskNode, 'fixedMask.mha', '-fMask'])
    inputVolumes.append([movingVolumeMaskNode, 'movingMask.mha', '-mMask'])
    for [volumeNode, filename, paramName] in inputVolumes:
      if not volumeNode:
        continue
      filePath = os.path.join(inputDir, filename)
      slicer.util.saveNode(volumeNode, filePath, {"useCompression": False})
      inputParamsElastix.append(paramName)
      inputParamsElastix.append(filePath)

    # Specify output location
    resultTransformDir = os.path.join(tempDir, 'result-transform')
    qt.QDir().mkpath(resultTransformDir)
    inputParamsElastix += ['-out', resultTransformDir]

    # Specify parameter files
    if parameterFilenames == None:
      parameterFilenames = self.getRegistrationPresets()[0][RegistrationPresets_ParameterFilenames]
    for parameterFilename in parameterFilenames:
      inputParamsElastix.append('-p')
      parameterFilePath = os.path.abspath(os.path.join(self.registrationParameterFilesDir, parameterFilename))
      inputParamsElastix.append(parameterFilePath)

    # Run registration
    ep = self.startElastix(inputParamsElastix)
    self.logProcessOutput(ep)

    # Resample
    if not self.abortRequested:
      resultResampleDir = os.path.join(tempDir, 'result-resample')
      qt.QDir().mkpath(resultResampleDir)
      inputParamsTransformix = ['-in', os.path.join(inputDir, 'moving.mha'), '-out', resultResampleDir]
      if outputTransformNode:
        inputParamsTransformix += ['-def', 'all']
      if outputVolumeNode:
        inputParamsTransformix += ['-tp', resultTransformDir+'/TransformParameters.'+str(len(parameterFilenames)-1)+'.txt']
      tp = self.startTransformix(inputParamsTransformix)
      self.logProcessOutput(tp)

    # Write results
    if not self.abortRequested:

      if outputVolumeNode:
        outputVolumePath = os.path.join(resultResampleDir, "result.mhd")
        [success, loadedOutputVolumeNode] = slicer.util.loadVolume(outputVolumePath, returnNode = True)
        if success:
          outputVolumeNode.SetAndObserveImageData(loadedOutputVolumeNode.GetImageData())
          ijkToRas = vtk.vtkMatrix4x4()
          loadedOutputVolumeNode.GetIJKToRASMatrix(ijkToRas)
          outputVolumeNode.SetIJKToRASMatrix(ijkToRas)
          slicer.mrmlScene.RemoveNode(loadedOutputVolumeNode)

      if outputTransformNode:
        outputTransformPath = os.path.join(resultResampleDir, "deformationField.mhd")
        [success, loadedOutputTransformNode] = slicer.util.loadTransform(outputTransformPath, returnNode = True)
        if success:
          if loadedOutputTransformNode.GetReadAsTransformToParent():
            outputTransformNode.SetAndObserveTransformToParent(loadedOutputTransformNode.GetTransformToParent())
          else:
            outputTransformNode.SetAndObserveTransformFromParent(loadedOutputTransformNode.GetTransformFromParent())
          slicer.mrmlScene.RemoveNode(loadedOutputTransformNode)

    # Clean up
    if self.deleteTemporaryFiles:
      import shutil
      shutil.rmtree(tempDir)

    self.addLog("Registration is completed")

class ElastixTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_Elastix1()

  def test_Elastix1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #

    import SampleData
    sampleDataLogic = SampleData.SampleDataLogic()
    tumor1 = sampleDataLogic.downloadMRBrainTumor1()
    tumor2 = sampleDataLogic.downloadMRBrainTumor2()

    outputVolume = slicer.vtkMRMLScalarVolumeNode()
    slicer.mrmlScene.AddNode(outputVolume)
    outputVolume.CreateDefaultDisplayNodes()

    logic = ElastixLogic()
    parameterFilenames = logic.getRegistrationPresets()[0][RegistrationPresets_ParameterFilenames]
    logic.registerVolumes(tumor1, tumor2, parameterFilenames = parameterFilenames, outputVolumeNode = outputVolume)

    self.delayDisplay('Test passed!')


RegistrationPresets_Id = 0
RegistrationPresets_Modality = 1
RegistrationPresets_Content = 2
RegistrationPresets_Description = 3
RegistrationPresets_Publications = 4
RegistrationPresets_ParameterFilenames = 5
