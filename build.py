import os
import shutil
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo
from seleniumRobotServer.settings import STATIC_ROOT

root = os.path.abspath(os.path.dirname(__file__))
distDir = root + os.sep + 'dist'

"""
deployment process:
- python install
- apache install
    - apache from apachelounge, same bitness as python
    - C++ redistributable microsoft, same version as the one used for apache compilation
    - mod_wsgi, same bitness as python
- deploy files: unzip seleniumRobotServer.zip
- install python requirements: pip install -r requirements.txt
- database migration: python manage.py migrate
- database fix: python manage.py fix_permissions
- create super user on first deploy ONLY: python manage.py createsuperuser
"""

def getFileList():
    distFileList = []
    for dirName, subdirList, fileList in os.walk(root):
        
        # skip media files
        if os.path.normpath(dirName).endswith("media/documents"):
            distFileList.append(dirName)
            continue
        
        subdirList[:] = [d for d in subdirList if not (d.startswith(".") 
                                                    or d.startswith("__") 
                                                    or (d == 'documents' and os.path.basename(dirName) == 'media')
                                                    )]
        
        for fileName in fileList:
            if os.path.splitext(fileName)[1].lower() in [".py", ".md", ".txt", ".yaml", ".css", ".js", ".png", ".jpg", ".html"]:
                distFileList.append(dirName + os.sep + fileName)
                
    return distFileList

def collectStatic():
    shutil.rmtree(STATIC_ROOT, ignore_errors=True)
    
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "seleniumRobotServer.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line([root + "/manage.py", "collectstatic"])
                
def makeDist(fileList):
    
    os.makedirs(distDir, exist_ok=True)
    for f in fileList:
        copyTo = f.replace(root, distDir)
        os.makedirs(os.path.dirname(copyTo), exist_ok=True)
        shutil.copy(f, copyTo)
        
    # add media dir
    os.makedirs(os.path.join(distDir, 'media', 'documents'))
    
def createDistFile(fileList): 
    with ZipFile('seleniumrobot-server.zip', 'w') as srsZip:
        for f in fileList:
            srsZip.write(f, f.replace(root, '', ZIP_DEFLATED))
        zfi = ZipInfo('log/')
        srsZip.writestr(zfi, '')
        zfi = ZipInfo('media/documents/')
        srsZip.writestr(zfi, '')
     
        
if __name__ == '__main__':
    
    shutil.rmtree(distDir, ignore_errors=True)
    
    collectStatic()
    fileList = getFileList()
    makeDist(fileList)
    createDistFile(fileList)
    