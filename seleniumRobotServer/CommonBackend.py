import logging
from django.contrib.auth.models import Group

class CommonBackend:
    
    # DEPRECATED
    def _add_user_to_groups(self, user):
        """
        Add permissions to user if user is allowed to have them (staff member or superuser)
        """
        variables_group = Group.objects.get(name='Variable Users')
        snapshot_group = Group.objects.get(name='Snapshot Users')
        
        # add Variable group and snapshot group to user
        if user.is_staff or user.is_superuser:
            try:
                variables_group.user_set.add(user)
                logging.info("User %s added to group 'Variable Users'" % user.username)
            except:
                logging.warn("Group 'Variable Users' should be created ")
                
            try:
                snapshot_group.user_set.add(user)
                logging.info("User %s added to group 'Snapshot Users'" % user.username)
            except:
                logging.warn("Group 'Snapshot Users' should be created ")
              
        # add Variable group and snapshot group from user if it's not staff or superuser  
        else:
            user.groups.remove(variables_group)
            user.groups.remove(snapshot_group)
            