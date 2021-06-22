

SPECIAL_NONE = '_NONE_'             # used when looking for something where we want an explicit value of None for the parameter
SPECIAL_NOT_NONE = '_NOT_NONE_'     # used when looking for something where we want an explicit value of 'not None' for the parameter

def updateVariables(source_query_set, additional_query_set):
        """
        do a queryset union between source_query_set and additional_query_set, but when the same variable (same name) exists in both, this is the one from
        additional_query_set which is kept
        
        union() is not used as it prevents from doing further combinations
        """
        
        filtered_source_query_set = source_query_set.exclude(name__in=additional_query_set.values('name'))
        return filtered_source_query_set | additional_query_set