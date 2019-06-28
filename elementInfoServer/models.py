from django.db import models
import commonsServer

class Application(commonsServer.models.Application):
    class Meta:
        default_permissions = ('add', 'change', 'delete')
        proxy = True
                
class Version(commonsServer.models.Version):
    class Meta:
        proxy = True
        
class ElementInfo(models.Model): 
    
    application = models.ForeignKey(Application, null=True, on_delete=models.CASCADE) 
    version = models.ForeignKey(Version, null=True, on_delete=models.CASCADE)
       
    uuid = models.CharField(max_length=200);
    name = models.CharField(max_length=100);
    locator = models.CharField(max_length=200);
    tagName = models.CharField(max_length=50);
    text = models.CharField(max_length=500, default="");
    
    # rectangle of the object
    width = models.IntegerField(default=0)
    height = models.IntegerField(default=0)
    coordX = models.IntegerField(default=0)
    coordY = models.IntegerField(default=0)
    
    lastUpdate = models.DateTimeField(auto_now=True)
    
    b64Image = models.TextField(max_length=20000, null=True);
    attributes = models.CharField(max_length=1000, default="{}"); # json string containing attributes
    totalSearch = models.IntegerField(default=0);
    tagStability = models.IntegerField(default=0);
    textStability = models.IntegerField(default=0);
    rectangleStability = models.IntegerField(default=0);
    b64ImageStability = models.IntegerField(default=0);
    attributesStability = models.CharField(max_length=1000, default="{}"); # json string containing attributes stability