

SPECIAL_NONE = '_NONE_'             # used when looking for something where we want an explicit value of None for the parameter
SPECIAL_NOT_NONE = '_NOT_NONE_'     # used when looking for something where we want an explicit value of 'not None' for the parameter

def updateVariables(sourceQuerySet, additionalQuerySet):
        """
        do a queryset union between sourceQuerySet and additionalQuerySet, but when the same variable (same name) exists in both, this is the one from
        additionalQuerySet which is kept
        
        union() is not used as it prevents from doing further combinations
        """
        
        filteredSourceQuerySet = sourceQuerySet.exclude(name__in=additionalQuerySet.values('name'))
        return filteredSourceQuerySet | additionalQuerySet