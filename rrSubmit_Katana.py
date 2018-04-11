######################################################################
#
# Royal Render Plugin script for Katana
# Author:  Anno Schachner
# Last change: %rrVersion%
# #win:		rrInstall_Env: MAYA_PLUG_IN_PATH, Directory
# #linux:	rrInstall_Env: MAYA_PLUG_IN_PATH, Directory
# #mac:		rrInstall_Copy:			../MacOS/plug-ins/
#
######################################################################

import os
import sys
import time
import shutil
import random
import subprocess
import multiprocessing
from xml.etree.ElementTree import ElementTree, Element, SubElement

from Katana import FarmAPI, Callbacks, UI4, RenderingAPI, KatanaFile


def onStartup(**kwargs):
    # add Menu Option
    # FarmAPI.AddFarmMenuOption('rrSubmitter', initAssExport)
    FarmAPI.AddFarmPopupMenuOption('rrSubmitter (local)', localExport)
    FarmAPI.AddFarmPopupMenuOption('rrSubmitter (farm)', farmExport)

    FarmAPI.AddFarmSettingString('fileName')
    FarmAPI.AddFarmSettingString('outputFolder', hints={'widget': 'assetIdInput',
                                                        'dirsOnly': 'true',
                                                        'acceptDir': 'true'})
    # .setHintString("{'widget':'assetIdInput', 'dirsOnly':'true', 'acceptDir':'true'}")
    FarmAPI.AddFarmSettingNumber('stepSize', 1)
    FarmAPI.AddFarmSettingNumber('useThreads', 2)
    FarmAPI.AddFarmSettingNumber('packageSize', 10)
    FarmAPI.AddFarmSettingNumber('useRendermanDenoiserPostScript', hints={'widget': 'checkBox'})
    FarmAPI.AddFarmSettingNumber('useYetiLic', hints={'widget': 'checkBox'})
    FarmAPI.AddFarmSettingNumber('useComment', hints={'widget': 'checkBox'})
    FarmAPI.AddFarmSettingString('comment')

    # Denoise
    FarmAPI.AddFarmSettingNumber('useRendermanDenoiserPostScript', hints={'widget': 'checkBox'})
    FarmAPI.AddFarmSettingString('denoiseFilter', hints={'widget': 'popup',
                                                             'options': [
                                                                        'default.filter.json',
                                                                        'sigmaAlphaOnly.filter.json',
                                                                        'volume.filter.json',
                                                                        ]})
    FarmAPI.AddFarmSettingNumber('useFilterOverride', hints={'widget': 'checkBox'})

    FarmAPI.AddFarmSettingStringArray('denoiseFilterOverride', hints={'widget': 'dynamicArray',
                                                             'isDynamicArray': 'true',
                                                             #'panelWidget': 'popup',
                                                             # 'options': 'filterLayersIndependently.filteroverride.json|fireflyKiller.filteroverride.json|linearWarp.filteroverride.json|nearestWarp.filteroverride.json|noAlbedoDivide.filteroverride.json|noDepth.filteroverride.json|noFireflyKiller.filteroverride.json|nonsplitVariances.filteroverride.json|noUnpremultiplyColor.filteroverride.json|splitVariances.filteroverride.json|unpremultiplyColor.filteroverride.json|unpremultiplyFeatures.filteroverride.json',
                                                             # 'options': [
                                                             #            'filterLayersIndependently.filteroverride.json',
                                                             #            'fireflyKiller.filteroverride.json',
                                                             #            'linearWarp.filteroverride.json',
                                                             #            'nearestWarp.filteroverride.json',
                                                             #            'noAlbedoDivide.filteroverride.json',
                                                             #            'noDepth.filteroverride.json',
                                                             #            'noFireflyKiller.filteroverride.json',
                                                             #            'nonsplitVariances.filteroverride.json',
                                                             #            'noUnpremultiply:wColor.filteroverride.json',
                                                             #            'splitVariances.filteroverride.json',
                                                             #            'unpremultiplyColor.filteroverride.json',
                                                             #            'unpremultiplyFeatures.filteroverride.json'
                                                             #            ]
                                                             })

# FarmAPI.AddFarmSettingString('rrEnvFile', hints={'widget': 'assetIdInput'})
# FarmAPI.AddFarmSettingString('stepSize', hints={'widget': 'fileInput'})

Callbacks.addCallback(Callbacks.Type.onStartup, onStartup)


def initUi():
    global dialog
    if dialog is not None:
        dialog.close()


################################################################################
# initialize Export

def localExport():
    initExport('local')


def farmExport():
    initExport('farm')


def initExport(option):
    dependencyList = FarmAPI.GetSortedDependencyList()[0]
    filepath = FarmAPI.GetKatanaFileName()

    # TODO - validity check
    saved = FarmAPI.IsSceneValid(FarmAPI.NODES_ALL)
    if not saved:
        # errormsg = FarmAPI.GetErrorMessages()
        result = UI4.Widgets.MessageBox.Warning('Unsaved Changes', 'Save your file', acceptText='Save',
                                                cancelText='Cancel')
        if result == 0:  # Save
            KatanaFile.Save(filepath)
        else:  # cancel
            return

    # TODO - Get Katana version
    katanaVersion = "2.54"
    rendererVersion = "21.4"

    # get renderservice
    renderer = dependencyList['service']

    requ_lics = ''
    if renderer == 'arnold':
        rendererVersion = RenderingAPI.RendererInfo.GetPlugin('ArnoldRendererInfo').getRegisteredRendererVersion()
        extension = '.ass'
        requ_lics += 'Arnold;'
    elif renderer == 'prman':
        rendererVersion = RenderingAPI.RendererInfo.GetPlugin('PRManRendererInfo').getRegisteredRendererVersion()
        renderer = 'RenderMan'
        extension = '.rib'
        requ_lics += 'RenderMan;'
    else:
        UI4.Widgets.MessageBox.Warning('Unsupported Renderer', 'Unknown Renderer')
        return

    use_yeti = dependencyList['useYetiLic']
    if use_yeti:
        requ_lics += "Yeti"


    software = 'Katana'
    software = 'Katana'
    if option == 'local':
        software = renderer

    #  print 'dependency list ', dependencyList
    fileDir = dependencyList['outputFolder']
    #  print 'FILEDDIR ', fileDir
    fileName = dependencyList['fileName']
    if fileName == '':
        UI4.Widgets.MessageBox.Warning('Warning', 'Add a name parameter')
        return

    # tmp name for xml and katana farm file
    xmlFileName = getNewTempFileName(fileDir, fileName)
    tmpFile = open(xmlFileName, 'w')
    dst = tmpFile.name[:-4] + '.katana'
    comment_file = tmpFile.name[:-4] + '_comment.txt'

    comment = ''
    use_comment = dependencyList['useComment']
    if use_comment:
        comment = dependencyList['comment']
        with open(comment_file, 'w') as f:
            f.write(comment)

    if (option == 'local'):
        # check file/dir
        if not os.path.isdir(fileDir):
            if UI4.Widgets.MessageBox.Warning('Warning', 'Directory does not exist.\n' + fileDir + '\n\nCreate it?',
                                              acceptText='Yes', cancelText='No'):
                return
            else:
                os.mkdir(fileDir)
        sceneName = os.path.join(fileDir, fileName) + '_<FN4>' + extension
    else:
        sceneName = dst
        #  sceneName = FarmAPI.GetKatanaFileName()

    # check framerange
    framerange = dependencyList['range']
    if framerange is None:
        UI4.Widgets.MessageBox.Warning('Warning', 'Add a valid framerange')
        return
    startframe = int(framerange[0])
    endframe = int(framerange[1])
    if endframe <= startframe:
        UI4.Widgets.MessageBox.Warning('Warning', 'Add a valid framerange')
        return


    # distribution check
    threadCount = int(dependencyList['useThreads'])
    if threadCount <= 0:
        UI4.Widgets.MessageBox.Warning('Warning', 'You must use at least one thread')
        return
    availableThreads = multiprocessing.cpu_count()
    if (threadCount > availableThreads) and (option == 'local'):
        UI4.Widgets.MessageBox.Warning('Warning', 'Your machine is restricted to max.' + str(availableThreads))
        return
    packageSize = int(dependencyList['packageSize'])
    if packageSize <= 0:
        UI4.Widgets.MessageBox.Warning('Warning', 'Add a valid packageSize')
        return

    # denoiser post script flags
    if int(dependencyList['useRendermanDenoiserPostScript']) == 1:
        filter = dependencyList['denoiseFilter']
        filter_cmd = 'denoise -v variance -f {}'.format(filter)
        if dependencyList['useFilterOverride']:
            filter_override = dependencyList['denoiseFilterOverride']
            for override in filter_override:
                filter_cmd += '+{}'.format(override)

    # create job
    newJob = rrJob()

    if (option == 'local'):
        newJob.version = rendererVersion
    else:
        newJob.version = katanaVersion
    newJob.rendererVersionName = renderer
    newJob.rendererVersion = rendererVersion
    newJob.software = software
    newJob.renderer = renderer
    newJob.RequiredLicenses = requ_lics #"Yeti"  # TODO
    newJob.sceneName = sceneName
    newJob.sceneDatabaseDir = ""
    newJob.seqStart = startframe
    newJob.seqEnd = endframe
    newJob.seqStep = dependencyList['stepSize']  # TODO - get dynamic
    newJob.seqFileOffset = 0
    newJob.seqFrameSet = ""
    newJob.imageWidth = 99  # TODO - get dynamic
    newJob.imageHeight = 99
    newJob.imageDir = fileDir
    newJob.imageFileName = fileName + '_####_variance.exr'
    newJob.imageFramePadding = 4  # TODO - get dynamic
    newJob.imageExtension = "" # ".exr"  # TODO get dynamic
    newJob.imagePreNumberLetter = ""
    newJob.imageSingleOutput = False
    newJob.imageStereoR = ""
    newJob.imageStereoL = ""
    newJob.sceneOS = getOSString()  # TODO - get dynamic
    newJob.camera = ""
    newJob.layer = dependencyList['name']
    newJob.channel = ""
    newJob.maxChannels = 0
    newJob.channelFileName = []
    newJob.channelExtension = []
    newJob.isActive = False
    newJob.sendAppBit = ""
    newJob.preID = ""
    newJob.waitForPreID = ""
    if dependencyList['useRendermanDenoiserPostScript']:
        newJob.CustomA = filter_cmd
    else:
        newJob.CustomA = ""
    newJob.CustomB = "comment: {}".format(comment)
    newJob.CustomC = ""
    newJob.LocalTexturesFile = ""
    newJob.rrSubmitVersion = "%rrVersion%"
    newJob.packageSize = packageSize
    newJob.threadCount = threadCount
    newJob.renderNode = dependencyList['name']

    # write xml file
    root = newJob.writeToXMLstart(None)
    job = newJob.writeToXMLJob(root)
    newJob.writeToXMLEnd(tmpFile, root)

    # copy katanna recipie
    shutil.copy(filepath, dst)

    # submit job
    if option == 'local':
        # start control session for local conversion
        scriptDir = os.path.dirname(os.path.realpath(__file__))
        sessionScript = os.path.join(scriptDir, 'session/ControlSessions.py')
        subp = subprocess.Popen(['python', sessionScript, tmpFile.name, dst],
                                close_fds=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                                )

    elif option == 'farm':
        os.system(getRRSubmitterPath() + "  \"" + xmlFileName + "\"")


# generate a tempfile
def getNewTempFileName(filedir, filename):
    random.seed(time.time())
    num = str(random.randrange(1000, 10000, 1))
    name = 'rrSubmit_%s_%s.xml' % (filename, num)
    name = os.path.join(filedir, name)
    print name
    return name


def writeInfo(msg):
    print(msg)


def writeError(msg):
    print(msg)


class rrJob(object):
    def __init__(self):
        self.version = ""
        self.software = ""
        self.renderer = ""
        self.RequiredLicenses = ""
        self.sceneName = ""
        self.sceneDatabaseDir = ""
        self.seqStart = 0
        self.seqEnd = 100
        self.seqStep = 1
        self.seqFileOffset = 0
        self.seqFrameSet = ""
        self.imageWidth = 99
        self.imageHeight = 99
        self.imageDir = ""
        self.imageFileName = ""
        self.imageFramePadding = 4
        self.imageExtension = ""
        self.imagePreNumberLetter = ""
        self.imageSingleOutput = False
        self.imageStereoR = ""
        self.imageStereoL = ""
        self.sceneOS = ""
        self.camera = ""
        self.layer = ""
        self.channel = ""
        self.maxChannels = 0
        self.channelFileName = []
        self.channelExtension = []
        self.isActive = False
        self.sendAppBit = ""
        self.preID = ""
        self.waitForPreID = ""
        self.CustomA = ""
        self.CustomB = ""
        self.CustomC = ""
        self.LocalTexturesFile = ""
        self.rrSubmitVersion = "%rrVersion%"
        self.packageSize = ""
        self.threadCount = ""
        self.renderNode = ""
        self.rendererVersionName = ""
        self.rendererVersion = ""

    # from infix.se (Filip Solomonsson)
    def indent(self, elem, level=0):
        i = "\n" + level * ' '
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + " "
            for e in elem:
                self.indent(e, level + 1)
                if not e.tail or not e.tail.strip():
                    e.tail = i + " "
            if not e.tail or not e.tail.strip():
                e.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
        return True

    def subE(self, parent, tag, text):
        sub = SubElement(parent, tag)
        if (type(text) == unicode):
            sub.text = text.encode('utf8')
        else:
            sub.text = str(text).decode("utf8")
        return sub

    def writeToXMLstart(self, submitOptions):
        rootElement = Element("rrJob_submitFile")
        rootElement.attrib["syntax_version"] = "6.0"
        self.subE(rootElement, "DeleteXML", "0")
        self.subE(rootElement, "SubmitterParameter", submitOptions)
        # YOU CAN ADD OTHER NOT SCENE-INFORMATION PARAMETERS USING THIS FORMAT:
        # self.subE(jobElement,"SubmitterParameter","PARAMETERNAME=" + PARAMETERVALUE_AS_STRING)
        return rootElement

    def writeToXMLJob(self, rootElement):

        jobElement = self.subE(rootElement, "Job", "")
        self.subE(jobElement, "Software", self.software)
        self.subE(jobElement, "Renderer", self.renderer)
        self.subE(jobElement, "RequiredLicenses", self.RequiredLicenses)
        self.subE(jobElement, "Version", self.version)
        if (len(self.rendererVersionName) > 0):
            self.subE(jobElement, "customRenVer_" + self.rendererVersionName, self.rendererVersion)
        self.subE(jobElement, "SceneName", self.sceneName)
        self.subE(jobElement, "SceneDatabaseDir", self.sceneDatabaseDir)
        self.subE(jobElement, "IsActive", self.isActive)
        self.subE(jobElement, "SeqStart", self.seqStart)
        self.subE(jobElement, "SeqEnd", self.seqEnd)
        self.subE(jobElement, "SeqStep", self.seqStep)
        self.subE(jobElement, "SeqFileOffset", self.seqFileOffset)
        self.subE(jobElement, "SeqFrameSet", self.seqFrameSet)
        self.subE(jobElement, "ImageWidth", int(self.imageWidth))
        self.subE(jobElement, "ImageHeight", int(self.imageHeight))
        self.subE(jobElement, "ImageDir", self.imageDir)
        self.subE(jobElement, "ImageFilename", self.imageFileName)
        self.subE(jobElement, "ImageFramePadding", self.imageFramePadding)
        self.subE(jobElement, "ImageExtension", self.imageExtension)
        self.subE(jobElement, "ImageSingleOutput", self.imageSingleOutput)
        self.subE(jobElement, "ImagePreNumberLetter", self.imagePreNumberLetter)
        self.subE(jobElement, "ImageStereoR", self.imageStereoR)
        self.subE(jobElement, "ImageStereoL", self.imageStereoL)
        self.subE(jobElement, "SceneOS", self.sceneOS)
        self.subE(jobElement, "Camera", self.camera)
        self.subE(jobElement, "Layer", self.layer)
        self.subE(jobElement, "Channel", self.channel)
        self.subE(jobElement, "SendAppBit", self.sendAppBit)
        self.subE(jobElement, "PreID", self.preID)
        self.subE(jobElement, "WaitForPreID", self.waitForPreID)
        self.subE(jobElement, "CustomDenoiseFlags", self.CustomA)
        self.subE(jobElement, "CustomB", self.CustomB)
        self.subE(jobElement, "CustomC", self.CustomC)
        self.subE(jobElement, "rrSubmitVersion", self.rrSubmitVersion)
        self.subE(jobElement, "LocalTexturesFile", self.LocalTexturesFile)

        self.subE(jobElement, "PackageSize", self.packageSize)
        self.subE(jobElement, "ThreadCount", self.threadCount)
        self.subE(jobElement, "Rendernode", self.renderNode)

        for c in range(0, self.maxChannels):
            self.subE(jobElement, "ChannelFilename", self.channelFileName[c])
            self.subE(jobElement, "ChannelExtension", self.channelExtension[c])
        return True

    def writeToXMLEnd(self, f, rootElement):
        xml = ElementTree(rootElement)
        self.indent(xml.getroot())

        if not f == None:
            xml.write(f)
            f.close()
        else:
            print("No valid file has been passed to the function")
            try:
                f.close()
            except:
                pass
            return False
        return True


def getOSString():
    if ((sys.platform.lower() == "win32") or (sys.platform.lower() == "win64")):
        return "win"
    elif (sys.platform.lower() == "darwin"):
        return "osx"
    else:
        return "lx"


################################################################################
# global functions
# from rrSubmit_Nuke_5.py (Copyright (c) Holger Schoenberger - Binary Alchemy)


def getRR_Root():
    if os.environ.has_key('RR_ROOT'):
        return os.environ['RR_ROOT']
    HCPath = "%"
    if ((sys.platform.lower() == "win32") or (sys.platform.lower() == "win64")):
        HCPath = "%RRLocationWin%"
    elif (sys.platform.lower() == "darwin"):
        HCPath = "%RRLocationMac%"
    else:
        HCPath = "%RRLocationLx%"
    if HCPath[0] != "%":
        return HCPath
    writeError("This plugin was not installed via rrWorkstationInstaller!")


def getRRSubmitterPath():
    ''' returns the rrSubmitter filename '''
    rrRoot = getRR_Root()
    if ((sys.platform.lower() == "win32") or (sys.platform.lower() == "win64")):
        rrSubmitter = rrRoot + "\\win__rrSubmitter.bat"
    elif (sys.platform.lower() == "darwin"):
        rrSubmitter = rrRoot + "/bin/mac64/rrSubmitter.app/Contents/MacOS/rrSubmitter"
    else:
        rrSubmitter = rrRoot + "/lx__rrSubmitter.sh"
    return rrSubmitter
