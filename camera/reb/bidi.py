
## -----------------------------------------------------------------------

class BidiMap(object):
    """
    Bidirectional channel map
    (very crude)
    """
    def __init__(self, channels, names):
        self.dictionary  = dict(zip(channels, names))
        self.reverse = {v: k for k, v in self.dictionary.iteritems()}
        self.dictionary.update(self.reverse)
    #
    def __getitem__(self, k):
        return self.dictionary[k]

    def has_key(self, k):
        return self.dictionary.has_key(k)

    def get(self, k, d=None):
        if self.has_key(k):
            return self[k]
        return d

    def __repr__(self):
        return repr(self.dictionary)


## -----------------------------------------------------------------------
