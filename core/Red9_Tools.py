'''
..
    Red9 Pro Pack: Maya Pipeline Solutions
    ======================================
     
    Author: Mark Jackson
    email: info@red9consultancy.com
     
    Red9 : http://red9consultancy.com
    Red9 Vimeo : https://vimeo.com/user9491246
    Twitter : @red9_anim
    Facebook : https://www.facebook.com/Red9Anim

'''

from __future__ import print_function

import maya.cmds as cmds

from functools import partial
import time
import getpass
import os

import Red9.startup.setup as r9Setup
import Red9_Meta as r9Meta
# import Red9_CoreUtils as r9Core
import Red9_AnimationUtils as r9Anim

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# Language map is used for all UI's as a text mapping for languages
LANGUAGE_MAP = r9Setup.LANGUAGE_MAP


class SceneReviewerUI(object):
    '''
    this is the reporter Dialogue that the scriptNode calls to display and edit the
    sceneReview data, held on the time node
    '''
    def __init__(self):
        self.win = LANGUAGE_MAP._SceneReviewerUI_.title
        self.SceneReviewer = SceneReviewer()  # main reporter object

    @classmethod
    def show(cls):
        if r9Setup.mayaVersion() < 2010:
            raise StandardError('This tool is not supported in versions of Maya running Python2.5')
        cls()._showUI()

    def close(self):
        if cmds.window(self.win, exists=True):
            cmds.deleteUI(self.win, window=True)

    def _showUI(self):

        self.close()
        window = cmds.window(self.win, title=self.win, s=True, widthHeight=(450, 700))

        cmds.menuBarLayout()
        cmds.menu(l=LANGUAGE_MAP._Generic_.tools)
        cmds.menuItem(l=LANGUAGE_MAP._Generic_.vimeo_help,
                      c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('https://vimeo.com/459389038')")
        cmds.menuItem(divider=True)
        cmds.menuItem(l='Delete SceneNode Data', c=self.delete)

        cmds.scrollLayout('reviewScrollLayout', rc=lambda *args: self._resizeTextScrollers(), cr=True)
        cmds.columnLayout(adjustableColumn=True, columnAttach=('both', 5))
        cmds.textFieldGrp('author', l=LANGUAGE_MAP._SceneReviewerUI_.author, ed=False, text='')
        cmds.textFieldGrp('date', l=LANGUAGE_MAP._SceneReviewerUI_.date, ed=False, text='')
        cmds.textFieldGrp('sceneName', l=LANGUAGE_MAP._SceneReviewerUI_.scene_name, ed=False, text='')
#         cmds.checkBox('wordwrap', l='word wrap', v=False)
        cmds.separator(h=15, style='none')
        cmds.text(l=LANGUAGE_MAP._SceneReviewerUI_.comment)
        cmds.scrollField('comment', text='', ed=True, h=200, wordWrap=True,
                         kpc=partial(self.updateInternalDict),
                         cc=partial(self.updateInternalDict))
        cmds.button(l=LANGUAGE_MAP._SceneReviewerUI_.new_comment, bgc=r9Setup.red9ButtonBGC(1), c=partial(self.addNewComment))
        cmds.separator(h=15, style='none')
        cmds.text(l=LANGUAGE_MAP._SceneReviewerUI_.history)
        cmds.scrollField('history', editable=False, en=True, wordWrap=True, h=200, text='')
        cmds.separator(h=15, style='none')
        cmds.rowColumnLayout('SceneNodeActivatorRC', numberOfColumns=3, columnWidth=[(1, 200), (2, 200)])
        cmds.button('setReviewActive', l=LANGUAGE_MAP._SceneReviewerUI_.activate_live_review,
                                        bgc=r9Setup.red9ButtonBGC(1),
                                        c=lambda x: self._setReviewStatus('active'))
        cmds.button('setReviewInActive', l=LANGUAGE_MAP._SceneReviewerUI_.disable_live_review,
                                        bgc=r9Setup.red9ButtonBGC(1),
                                        c=lambda x: self._setReviewStatus('inactive'))
        cmds.setParent('..')
        cmds.separator(h=15, style='none')
        cmds.iconTextButton(style='iconAndTextHorizontal', bgc=(0.7, 0, 0),
                            image1='Rocket9_buttonStrap.png',
                            align='left',
                            c=lambda *args: (r9Setup.red9ContactInfo()), h=24, w=200)
        cmds.showWindow(window)
        self._refresh()

        if self.SceneReviewer.exists():
            self._setReviewStatus('active')
        else:
            self._setReviewStatus('inactive')

    def _refresh(self):
        '''
        sync the data to the ui
        '''
        reportData = self.SceneReviewer.getReportData()
        allowEdit = False
        sceneName = None
        date = ''
        if 'sceneName' in reportData:
            sceneName = reportData['sceneName']
        author = None

        if not reportData['author']:
            # new sceneReport
            author = getpass.getuser()
            allowEdit = True
        elif reportData['author'] == getpass.getuser():
            # current author of comment == you
            author = getpass.getuser()
            allowEdit = True
            date = time.ctime()
        else:
            # current author != you
            author = reportData['author']
        if not date:
            date = time.ctime()
        if not sceneName:
            sceneName = self.getSceneName()

        cmds.textFieldGrp('author', e=True, text=author)
        cmds.textFieldGrp('date', e=True, text=date)
        cmds.textFieldGrp('sceneName', e=True, text=sceneName)
        cmds.scrollField('comment', e=True, ed=allowEdit, text=reportData['comment'])
        cmds.scrollField('history', e=True, text=reportData['history'])

    def getSceneName(self):
        return os.path.basename(cmds.file(q=True, sn=True))

    def updateInternalDict(self, *args):
        if cmds.scrollField('comment', q=True, ed=True):
            self.SceneReviewer.storedDataDict['author'] = cmds.textFieldGrp('author', q=True, text=True)
        self.SceneReviewer.storedDataDict['date'] = cmds.textFieldGrp('date', q=True, text=True)
        self.SceneReviewer.storedDataDict['sceneName'] = cmds.textFieldGrp('sceneName', q=True, text=True)
        self.SceneReviewer.storedDataDict['comment'] = cmds.scrollField('comment', q=True, text=True)
        print(self.SceneReviewer.storedDataDict)
        self.SceneReviewer.storeReportData()

    def addNewComment(self, *args):
        self.SceneReviewer.pushCommentToHistory()
        cmds.textFieldGrp('author', e=True, text=getpass.getuser())
        cmds.textFieldGrp('date', e=True, text=time.ctime())
        cmds.textFieldGrp('sceneName', e=True, text=self.getSceneName())
        cmds.scrollField('comment', e=True, ed=True, text='')
        cmds.scrollField('history', e=True, text=self.SceneReviewer.storedDataDict['history'])
        self.updateInternalDict()

    def _setReviewStatus(self, status='active', *args):
        if status == 'active':
            if not self.SceneReviewer.exists():
                self.SceneReviewer.addScriptNode()
            cmds.button('setReviewActive', e=True, bgc=r9Setup.red9ButtonBGC(2))
            cmds.button('setReviewInActive', e=True, bgc=r9Setup.red9ButtonBGC(1))
        else:
            if self.SceneReviewer.exists():
                self.SceneReviewer.deleteScriptNode()
            cmds.button('setReviewActive', e=True, bgc=r9Setup.red9ButtonBGC(1))
            cmds.button('setReviewInActive', e=True, bgc=r9Setup.red9ButtonBGC(2))

    def _resizeTextScrollers(self):
        height = (cmds.scrollLayout('reviewScrollLayout', q=True, h=True) / r9Setup.maya_dpi_scaling_factor())
        width = (cmds.scrollLayout('reviewScrollLayout', q=True, w=True) / r9Setup.maya_dpi_scaling_factor()) - 18  # column attach space = 5 on both
#         cmds.scrollField('comment', e=True, wordWrap=cmds.checkBox('wordwrap', q=True, v=True))
#         cmds.scrollField('history', e=True, wordWrap=cmds.checkBox('wordwrap', q=True, v=True))
        cmds.scrollField('comment', e=True, h=(height / 2) - 120)
        cmds.scrollField('history', e=True, h=(height / 2) - 120)
        cmds.rowColumnLayout('SceneNodeActivatorRC', e=True, columnWidth=[(1, (width / 2) - 1), (2, (width / 2) - 1)])

    def delete(self, *args):
        self.SceneReviewer.deleteData()
        self._refresh()

class SceneReviewer(object):

    def __init__(self):
        '''
        This is a really simple proc that will stamp data onto the time node and retrieve it so that
        leads can review and enter info into the scene itself. Why the time1 node??? this saves any
        issues with merging scenes as the time node is one of the only nodes in Maya that can only
        exist once, and is managed in that way internally
        '''
        self.dataRepository = r9Meta.MetaClass('time1')
        self.dataRepository.addAttr('sceneReport', attrType="string")
        self.sceneScriptNode = "sceneReviewData"
        self.storedDataDict = {'author': "", 'date': "", 'sceneName': "", 'comment': "", 'history': ""}
        self.getReportData()
        self.__deleteImportedScriptNodes()

    def addScriptNode(self, *args):
        if not self.exists():
            cmds.scriptNode(sourceType="python", scriptType=1,
                            name=self.sceneScriptNode,
                            bs="try:\r\timport Red9.core.Red9_Tools as r9Tools;\r\tr9Tools.SceneReviewerUI.show();\rexcept:\r\tpass")
        else:
            log.warning('sceneReview ScriptNode already exists')

    def getReportData(self):
        if issubclass(type(self.dataRepository.sceneReport), dict):
            self.storedDataDict = self.dataRepository.sceneReport
            if 'sceneName' not in self.storedDataDict:
                self.storedDataDict['sceneName'] = ""
            return self.dataRepository.sceneReport
        else:
            return self.storedDataDict

    def storeReportData(self):
        self.dataRepository.sceneReport = self.storedDataDict

    def pushCommentToHistory(self):
        self.storedDataDict['history'] += 'author:\t%s\rdate:\t%s\rsceneName:\t%s\rcomment:\r%s\r------------------------------------------------\r' \
                    % (self.storedDataDict['author'],
                       self.storedDataDict['date'],
                       self.storedDataDict['sceneName'],
                       self.storedDataDict['comment'])
        self.storeReportData()

    def exists(self):
        return cmds.objExists(self.sceneScriptNode)

    def deleteData(self):
        '''
        clear the custom attr and remove all comments from the setups
        '''
        if self.exists():
            self.deleteScriptNode()
        self.dataRepository.sceneReport = ''
        self.storedDataDict = {'author': "", 'date': "", 'sceneName': "", 'comment': "", 'history': ""}
        self.storeReportData()

    def selectScriptNode(self):
        cmds.select(self.sceneScriptNode)

    def deleteScriptNode(self, *args):
        if self.exists():
            try:
                cmds.delete(self.sceneScriptNode)
            except:
                log.info('script node failed to delete')
        else:
            log.info('Script Node not found')

    def __deleteImportedScriptNodes(self):
        '''
        Important function to clean any imported scriptReviewNodes that might have
        come in from over imported Maya files. Only a single instance of this scriptNode
        should ever exists
        '''
        scriptNodes = cmds.ls('*%s*' % self.sceneScriptNode, r=True)
        if type(scriptNodes) == list:
            if cmds.objExists(self.sceneScriptNode):
                scriptNodes.remove(self.sceneScriptNode)
        if scriptNodes:
            [cmds.delete(node) for node in scriptNodes]

    def scriptNodeFunc(self):
        self.getReportData()


class RecordAttrs(object):
    '''
    Simple class to use the Mouse as a MoCap input device
    #BUG : Maya can't now record fucking rotate channels as it pushes a unitConvert Node
    between the rotate and the record plugs and nothing gets captured. Trying to figure a way
    round this
    '''
    def __init__(self):
        self.currAngularUnits = cmds.currentUnit(q=True, angle=True)
        self.rotateInRads = True

    @classmethod
    def show(cls):
        cls()._showUI()

    def close(self):
        if cmds.window('MouseMoCap', exists=True):
            cmds.deleteUI('MouseMoCap', window=True)

    def addAttrsToRecord(self, attrs=None, *args):
        node = cmds.ls(sl=True, l=True)[0]
        if not attrs:
            attrs = r9Anim.getChannelBoxSelection()
        if attrs:
            try:
                if self.rotateInRads and self.currAngularUnits == 'deg':
                    log.info('setting AngularUnits to Radians')
                    cmds.currentUnit(angle='rad')
                cmds.recordAttr(node, at=attrs)
            except:
                pass
            finally:
                cmds.currentUnit(angle=self.currAngularUnits)
                log.info('setting AngularUnits back to Degrees')
        else:
            raise StandardError('No Channels selected in the ChannelBox to Set')

    def removeAttrsToRecord(self, attrs=None, *args):
        node = cmds.ls(sl=True, l=True)[0]
        if not attrs:
            attrs = r9Anim.getChannelBoxSelection()
        if attrs:
            cmds.recordAttr(node, at=attrs, delete=True)
        else:
            raise StandardError('No Channels selected in the ChannelBox to Set')

    def recordStart(self):
        cmds.play(record=True)

    def recordStop(self):
        cmds.play(state=False)
        self.removeAttrsToRecord([attr.split('.')[-1]
                                  for attr in cmds.listAnimatable(cmds.ls(sl=True))])

    def _runRecord(self, *args):
        if cmds.button('MouseMoCapRecord', q=True, label=True) == 'RECORD':
            cmds.button('MouseMoCapRecord', e=True, label='STOP', bgc=[0.8, 0.1, 0.1])
            self.recordStart()
        else:
            cmds.button('MouseMoCapRecord', e=True, label='RECORD', bgc=[0.1, 0.8, 0.1])
            self.recordStop()

    def _showUI(self):
        self.close()
        cmds.window('MouseMoCap', title="MouseMoCap")  # , widthHeight=(260, 180))

        cmds.columnLayout(adjustableColumn=True, cw=200,columnAttach=('both', 5))
        cmds.separator(h=15, style='none')
        cmds.text('     Use the Mouse as a MoCap input device     ')
        cmds.separator(h=15, style='none')
        cmds.button(label='Set Attributes to Record (chBox)',
                    ann='Prime Selected Attributes in the channelBox for Recording',
                     command=partial(self.addAttrsToRecord))
        cmds.separator(h=5, style='none')
        cmds.button(label='Remove Record Attributes (chBox)',
                    ann='Remove Attrs from Record selected in the channelBox',
                     command=partial(self.removeAttrsToRecord))
        cmds.separator(h=15, style='none')
        cmds.button('MouseMoCapRecord', label='RECORD', bgc=[0.1, 0.8, 0.1],
                     command=partial(self._runRecord), h=35)
        cmds.separator(h=25, style='none')
        cmds.iconTextButton(style='iconOnly', bgc=(0.7, 0, 0),
                            image1='Rocket9_buttonStrap.png',
                            align='left',
                            c=lambda *args: (r9Setup.red9ContactInfo()), h=24, w=200)
        cmds.separator(h=15, style='none')
        cmds.showWindow('MouseMoCap')
#         cmds.window('MouseMoCap', e=True, widthHeight=(260, 180))
