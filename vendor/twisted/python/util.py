# -*- test-case-name: twisted.python.test.test_util -*-
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

import os, sys, errno, inspect, warnings
import types
try:
    import pwd, grp
except ImportError:
    pwd = grp = None
try:
    from os import setgroups, getgroups
except ImportError:
    setgroups = getgroups = None
from UserDict import UserDict


class InsensitiveDict:
    """Dictionary, that has case-insensitive keys.

    Normally keys are retained in their original form when queried with
    .keys() or .items().  If initialized with preserveCase=0, keys are both
    looked up in lowercase and returned in lowercase by .keys() and .items().
    """
    """
    Modified recipe at
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66315 originally
    contributed by Sami Hangaslammi.
    """

    def __init__(self, dict=None, preserve=1):
        """Create an empty dictionary, or update from 'dict'."""
        self.data = {}
        self.preserve=preserve
        if dict:
            self.update(dict)

    def __delitem__(self, key):
        k=self._lowerOrReturn(key)
        del self.data[k]

    def _lowerOrReturn(self, key):
        if isinstance(key, str) or isinstance(key, unicode):
            return key.lower()
        else:
            return key

    def __getitem__(self, key):
        """Retrieve the value associated with 'key' (in any case)."""
        k = self._lowerOrReturn(key)
        return self.data[k][1]

    def __setitem__(self, key, value):
        """Associate 'value' with 'key'. If 'key' already exists, but
        in different case, it will be replaced."""
        k = self._lowerOrReturn(key)
        self.data[k] = (key, value)

    def has_key(self, key):
        """Case insensitive test whether 'key' exists."""
        k = self._lowerOrReturn(key)
        return k in self.data

    __contains__=has_key

    def _doPreserve(self, key):
        if not self.preserve and (isinstance(key, str)
                                  or isinstance(key, unicode)):
            return key.lower()
        else:
            return key

    def keys(self):
        """List of keys in their original case."""
        return list(self.iterkeys())

    def values(self):
        """List of values."""
        return list(self.itervalues())

    def items(self):
        """List of (key,value) pairs."""
        return list(self.iteritems())

    def get(self, key, default=None):
        """Retrieve value associated with 'key' or return default value
        if 'key' doesn't exist."""
        try:
            return self[key]
        except KeyError:
            return default

    def setdefault(self, key, default):
        """If 'key' doesn't exists, associate it with the 'default' value.
        Return value associated with 'key'."""
        if not self.has_key(key):
            self[key] = default
        return self[key]

    def update(self, dict):
        """Copy (key,value) pairs from 'dict'."""
        for k,v in dict.items():
            self[k] = v

    def __repr__(self):
        """String representation of the dictionary."""
        items = ", ".join([("%r: %r" % (k,v)) for k,v in self.items()])
        return "InsensitiveDict({%s})" % items

    def iterkeys(self):
        for v in self.data.itervalues():
            yield self._doPreserve(v[0])

    def itervalues(self):
        for v in self.data.itervalues():
            yield v[1]

    def iteritems(self):
        for (k, v) in self.data.itervalues():
            yield self._doPreserve(k), v

    def popitem(self):
        i=self.items()[0]
        del self[i[0]]
        return i

    def clear(self):
        for k in self.keys():
            del self[k]

    def copy(self):
        return InsensitiveDict(self, self.preserve)

    def __len__(self):
        return len(self.data)

    def __eq__(self, other):
        for k,v in self.items():
            if not (k in other) or not (other[k]==v):
                return 0
        return len(self)==len(other)

class OrderedDict(UserDict):
    """A UserDict that preserves insert order whenever possible."""
    def __init__(self, dict=None, **kwargs):
        self._order = []
        self.data = {}
        if dict is not None:
            if hasattr(dict,'keys'):
                self.update(dict)
            else:
                for k,v in dict: # sequence
                    self[k] = v
        if len(kwargs):
            self.update(kwargs)
    def __repr__(self):
        return '{'+', '.join([('%r: %r' % item) for item in self.items()])+'}'

    def __setitem__(self, key, value):
        if not self.has_key(key):
            self._order.append(key)
        UserDict.__setitem__(self, key, value)

    def copy(self):
        return self.__class__(self)

    def __delitem__(self, key):
        UserDict.__delitem__(self, key)
        self._order.remove(key)

    def iteritems(self):
        for item in self._order:
            yield (item, self[item])

    def items(self):
        return list(self.iteritems())

    def itervalues(self):
        for item in self._order:
            yield self[item]

    def values(self):
        return list(self.itervalues())

    def iterkeys(self):
        return iter(self._order)

    def keys(self):
        return list(self._order)

    def popitem(self):
        key = self._order[-1]
        value = self[key]
        del self[key]
        return (key, value)

    def setdefault(self, item, default):
        if self.has_key(item):
            return self[item]
        self[item] = default
        return default

    def update(self, d):
        for k, v in d.items():
            self[k] = v

def uniquify(lst):
    """Make the elements of a list unique by inserting them into a dictionary.
    This must not change the order of the input lst.
    """
    dct = {}
    result = []
    for k in lst:
        if k not in dct:
            result.append(k)
        dct[k] = 1
    return result

def padTo(n, seq, default=None):
    """
    Pads a sequence out to n elements,

    filling in with a default value if it is not long enough.

    If the input sequence is longer than n, raises ValueError.

    Details, details:
    This returns a new list; it does not extend the original sequence.
    The new list contains the values of the original sequence, not copies.
    """

    if len(seq) > n:
        raise ValueError, "%d elements is more than %d." % (len(seq), n)

    blank = [default] * n

    blank[:len(seq)] = list(seq)

    return blank


def getPluginDirs():
    warnings.warn(
        "twisted.python.util.getPluginDirs is deprecated since Twisted 12.2.",
        DeprecationWarning, stacklevel=2)
    import twisted
    systemPlugins = os.path.join(os.path.dirname(os.path.dirname(
                            os.path.abspath(twisted.__file__))), 'plugins')
    userPlugins = os.path.expanduser("~/TwistedPlugins")
    confPlugins = os.path.expanduser("~/.twisted")
    allPlugins = filter(os.path.isdir, [systemPlugins, userPlugins, confPlugins])
    return allPlugins


def addPluginDir():
    warnings.warn(
        "twisted.python.util.addPluginDir is deprecated since Twisted 12.2.",
        DeprecationWarning, stacklevel=2)
    sys.path.extend(getPluginDirs())


def sibpath(path, sibling):
    """
    Return the path to a sibling of a file in the filesystem.

    This is useful in conjunction with the special C{__file__} attribute
    that Python provides for modules, so modules can load associated
    resource files.
    """
    return os.path.join(os.path.dirname(os.path.abspath(path)), sibling)


def _getpass(prompt):
    """
    Helper to turn IOErrors into KeyboardInterrupts.
    """
    import getpass
    try:
        return getpass.getpass(prompt)
    except IOError, e:
        if e.errno == errno.EINTR:
            raise KeyboardInterrupt
        raise
    except EOFError:
        raise KeyboardInterrupt

def getPassword(prompt = 'Password: ', confirm = 0, forceTTY = 0,
                confirmPrompt = 'Confirm password: ',
                mismatchMessage = "Passwords don't match."):
    """Obtain a password by prompting or from stdin.

    If stdin is a terminal, prompt for a new password, and confirm (if
    C{confirm} is true) by asking again to make sure the user typed the same
    thing, as keystrokes will not be echoed.

    If stdin is not a terminal, and C{forceTTY} is not true, read in a line
    and use it as the password, less the trailing newline, if any.  If
    C{forceTTY} is true, attempt to open a tty and prompt for the password
    using it.  Raise a RuntimeError if this is not possible.

    @returns: C{str}
    """
    isaTTY = hasattr(sys.stdin, 'isatty') and sys.stdin.isatty()

    old = None
    try:
        if not isaTTY:
            if forceTTY:
                try:
                    old = sys.stdin, sys.stdout
                    sys.stdin = sys.stdout = open('/dev/tty', 'r+')
                except:
                    raise RuntimeError("Cannot obtain a TTY")
            else:
                password = sys.stdin.readline()
                if password[-1] == '\n':
                    password = password[:-1]
                return password

        while 1:
            try1 = _getpass(prompt)
            if not confirm:
                return try1
            try2 = _getpass(confirmPrompt)
            if try1 == try2:
                return try1
            else:
                sys.stderr.write(mismatchMessage + "\n")
    finally:
        if old:
            sys.stdin.close()
            sys.stdin, sys.stdout = old


def println(*a):
    sys.stdout.write(' '.join(map(str, a))+'\n')

# XXX
# This does not belong here
# But where does it belong?

def str_xor(s, b):
    return ''.join([chr(ord(c) ^ b) for c in s])


def makeStatBar(width, maxPosition, doneChar = '=', undoneChar = '-', currentChar = '>'):
    """
    Creates a function that will return a string representing a progress bar.
    """
    aValue = width / float(maxPosition)
    def statBar(position, force = 0, last = ['']):
        assert len(last) == 1, "Don't mess with the last parameter."
        done = int(aValue * position)
        toDo = width - done - 2
        result = "[%s%s%s]" % (doneChar * done, currentChar, undoneChar * toDo)
        if force:
            last[0] = result
            return result
        if result == last[0]:
            return ''
        last[0] = result
        return result

    statBar.__doc__ = """statBar(position, force = 0) -> '[%s%s%s]'-style progress bar

    returned string is %d characters long, and the range goes from 0..%d.
    The 'position' argument is where the '%s' will be drawn.  If force is false,
    '' will be returned instead if the resulting progress bar is identical to the
    previously returned progress bar.
""" % (doneChar * 3, currentChar, undoneChar * 3, width, maxPosition, currentChar)
    return statBar


def spewer(frame, s, ignored):
    """
    A trace function for sys.settrace that prints every function or method call.
    """
    from twisted.python import reflect
    if frame.f_locals.has_key('self'):
        se = frame.f_locals['self']
        if hasattr(se, '__class__'):
            k = reflect.qual(se.__class__)
        else:
            k = reflect.qual(type(se))
        print 'method %s of %s at %s' % (
            frame.f_code.co_name, k, id(se)
        )
    else:
        print 'function %s in %s, line %s' % (
            frame.f_code.co_name,
            frame.f_code.co_filename,
            frame.f_lineno)


def searchupwards(start, files=[], dirs=[]):
    """
    Walk upwards from start, looking for a directory containing
    all files and directories given as arguments::
    >>> searchupwards('.', ['foo.txt'], ['bar', 'bam'])

    If not found, return None
    """
    start=os.path.abspath(start)
    parents=start.split(os.sep)
    exists=os.path.exists; join=os.sep.join; isdir=os.path.isdir
    while len(parents):
        candidate=join(parents)+os.sep
        allpresent=1
        for f in files:
            if not exists("%s%s" % (candidate, f)):
                allpresent=0
                break
        if allpresent:
            for d in dirs:
                if not isdir("%s%s" % (candidate, d)):
                    allpresent=0
                    break
        if allpresent: return candidate
        parents.pop(-1)
    return None


class LineLog:
    """
    A limited-size line-based log, useful for logging line-based
    protocols such as SMTP.

    When the log fills up, old entries drop off the end.
    """
    def __init__(self, size=10):
        """
        Create a new log, with size lines of storage (default 10).
        A log size of 0 (or less) means an infinite log.
        """
        if size < 0:
            size = 0
        self.log = [None]*size
        self.size = size

    def append(self,line):
        if self.size:
            self.log[:-1] = self.log[1:]
            self.log[-1] = line
        else:
            self.log.append(line)

    def str(self):
        return '\n'.join(filter(None,self.log))

    def __getitem__(self, item):
        return filter(None,self.log)[item]

    def clear(self):
        """Empty the log"""
        self.log = [None]*self.size


def raises(exception, f, *args, **kwargs):
    """
    Determine whether the given call raises the given exception.
    """
    try:
        f(*args, **kwargs)
    except exception:
        return 1
    return 0


class IntervalDifferential:
    """
    Given a list of intervals, generate the amount of time to sleep between
    "instants".

    For example, given 7, 11 and 13, the three (infinite) sequences::

        7 14 21 28 35 ...
        11 22 33 44 ...
        13 26 39 52 ...

    will be generated, merged, and used to produce::

        (7, 0) (4, 1) (2, 2) (1, 0) (7, 0) (1, 1) (4, 2) (2, 0) (5, 1) (2, 0)

    New intervals may be added or removed as iteration proceeds using the
    proper methods.
    """

    def __init__(self, intervals, default=60):
        """
        @type intervals: C{list} of C{int}, C{long}, or C{float} param
        @param intervals: The intervals between instants.

        @type default: C{int}, C{long}, or C{float}
        @param default: The duration to generate if the intervals list
        becomes empty.
        """
        self.intervals = intervals[:]
        self.default = default

    def __iter__(self):
        return _IntervalDifferentialIterator(self.intervals, self.default)


class _IntervalDifferentialIterator:
    def __init__(self, i, d):

        self.intervals = [[e, e, n] for (e, n) in zip(i, range(len(i)))]
        self.default = d
        self.last = 0

    def next(self):
        if not self.intervals:
            return (self.default, None)
        last, index = self.intervals[0][0], self.intervals[0][2]
        self.intervals[0][0] += self.intervals[0][1]
        self.intervals.sort()
        result = last - self.last
        self.last = last
        return result, index

    def addInterval(self, i):
        if self.intervals:
            delay = self.intervals[0][0] - self.intervals[0][1]
            self.intervals.append([delay + i, i, len(self.intervals)])
            self.intervals.sort()
        else:
            self.intervals.append([i, i, 0])

    def removeInterval(self, interval):
        for i in range(len(self.intervals)):
            if self.intervals[i][1] == interval:
                index = self.intervals[i][2]
                del self.intervals[i]
                for i in self.intervals:
                    if i[2] > index:
                        i[2] -= 1
                return
        raise ValueError, "Specified interval not in IntervalDifferential"


class FancyStrMixin:
    """
    Set showAttributes to a sequence of strings naming attributes, OR
    sequences of C{(attributeName, displayName, formatCharacter)}.
    """
    showAttributes = ()
    def __str__(self):
        r = ['<', hasattr(self, 'fancybasename') and self.fancybasename or self.__class__.__name__]
        for attr in self.showAttributes:
            if isinstance(attr, str):
                r.append(' %s=%r' % (attr, getattr(self, attr)))
            else:
                r.append((' %s=' + attr[2]) % (attr[1], getattr(self, attr[0])))
        r.append('>')
        return ''.join(r)
    __repr__ = __str__



class FancyEqMixin:
    compareAttributes = ()
    def __eq__(self, other):
        if not self.compareAttributes:
            return self is other
        if isinstance(self, other.__class__):
            return (
                [getattr(self, name) for name in self.compareAttributes] ==
                [getattr(other, name) for name in self.compareAttributes])
        return NotImplemented


    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result



try:
    from twisted.python._initgroups import initgroups as _c_initgroups
except ImportError:
    _c_initgroups = None



if pwd is None or grp is None or setgroups is None or getgroups is None:
    def initgroups(uid, primaryGid):
        """
        Do nothing.

        Underlying platform support require to manipulate groups is missing.
        """
else:
    # Fallback to the inefficient Python version
    def _setgroups_until_success(l):
        while(1):
            # NASTY NASTY HACK (but glibc does it so it must be okay):
            # In case sysconfig didn't give the right answer, find the limit
            # on max groups by just looping, trying to set fewer and fewer
            # groups each time until it succeeds.
            try:
                setgroups(l)
            except ValueError:
                # This exception comes from python itself restricting
                # number of groups allowed.
                if len(l) > 1:
                    del l[-1]
                else:
                    raise
            except OSError, e:
                if e.errno == errno.EINVAL and len(l) > 1:
                    # This comes from the OS saying too many groups
                    del l[-1]
                else:
                    raise
            else:
                # Success, yay!
                return

    def initgroups(uid, primaryGid):
        """
        Initializes the group access list.

        If the C extension is present, we're calling it, which in turn calls
        initgroups(3).

        If not, this is done by reading the group database /etc/group and using
        all groups of which C{uid} is a member.  The additional group
        C{primaryGid} is also added to the list.

        If the given user is a member of more than C{NGROUPS}, arbitrary
        groups will be silently discarded to bring the number below that
        limit.

        @type uid: C{int}
        @param uid: The UID for which to look up group information.

        @type primaryGid: C{int} or C{NoneType}
        @param primaryGid: If provided, an additional GID to include when
            setting the groups.
        """
        if _c_initgroups is not None:
            return _c_initgroups(pwd.getpwuid(uid)[0], primaryGid)
        try:
            # Try to get the maximum number of groups
            max_groups = os.sysconf("SC_NGROUPS_MAX")
        except:
            # No predefined limit
            max_groups = 0

        username = pwd.getpwuid(uid)[0]
        l = []
        if primaryGid is not None:
            l.append(primaryGid)
        for groupname, password, gid, userlist in grp.getgrall():
            if username in userlist:
                l.append(gid)
                if len(l) == max_groups:
                    break # No more groups, ignore any more
        try:
            _setgroups_until_success(l)
        except OSError, e:
            # We might be able to remove this code now that we
            # don't try to setgid/setuid even when not asked to.
            if e.errno == errno.EPERM:
                for g in getgroups():
                    if g not in l:
                        raise
            else:
                raise



def switchUID(uid, gid, euid=False):
    """
    Attempts to switch the uid/euid and gid/egid for the current process.

    If C{uid} is the same value as L{os.getuid} (or L{os.geteuid}),
    this function will issue a L{UserWarning} and not raise an exception.

    @type uid: C{int} or C{NoneType}
    @param uid: the UID (or EUID) to switch the current process to. This
                parameter will be ignored if the value is C{None}.

    @type gid: C{int} or C{NoneType}
    @param gid: the GID (or EGID) to switch the current process to. This
                parameter will be ignored if the value is C{None}.

    @type euid: C{bool}
    @param euid: if True, set only effective user-id rather than real user-id.
                 (This option has no effect unless the process is running
                 as root, in which case it means not to shed all
                 privileges, retaining the option to regain privileges
                 in cases such as spawning processes. Use with caution.)
    """
    if euid:
        setuid = os.seteuid
        setgid = os.setegid
        getuid = os.geteuid
    else:
        setuid = os.setuid
        setgid = os.setgid
        getuid = os.getuid
    if gid is not None:
        setgid(gid)
    if uid is not None:
        if uid == getuid():
            uidText = (euid and "euid" or "uid")
            actionText = "tried to drop privileges and set%s %s" % (uidText, uid)
            problemText = "%s is already %s" % (uidText, getuid())
            warnings.warn("%s but %s; should we be root? Continuing."
                          % (actionText, problemText))
        else:
            initgroups(uid, gid)
            setuid(uid)


class SubclassableCStringIO(object):
    """
    A wrapper around cStringIO to allow for subclassing.
    """
    __csio = None

    def __init__(self, *a, **kw):
        from cStringIO import StringIO
        self.__csio = StringIO(*a, **kw)

    def __iter__(self):
        return self.__csio.__iter__()

    def next(self):
        return self.__csio.next()

    def close(self):
        return self.__csio.close()

    def isatty(self):
        return self.__csio.isatty()

    def seek(self, pos, mode=0):
        return self.__csio.seek(pos, mode)

    def tell(self):
        return self.__csio.tell()

    def read(self, n=-1):
        return self.__csio.read(n)

    def readline(self, length=None):
        return self.__csio.readline(length)

    def readlines(self, sizehint=0):
        return self.__csio.readlines(sizehint)

    def truncate(self, size=None):
        return self.__csio.truncate(size)

    def write(self, s):
        return self.__csio.write(s)

    def writelines(self, list):
        return self.__csio.writelines(list)

    def flush(self):
        return self.__csio.flush()

    def getvalue(self):
        return self.__csio.getvalue()



def untilConcludes(f, *a, **kw):
    while True:
        try:
            return f(*a, **kw)
        except (IOError, OSError), e:
            if e.args[0] == errno.EINTR:
                continue
            raise

_idFunction = id

def setIDFunction(idFunction):
    """
    Change the function used by L{unsignedID} to determine the integer id value
    of an object.  This is largely useful for testing to give L{unsignedID}
    deterministic, easily-controlled behavior.

    @param idFunction: A function with the signature of L{id}.
    @return: The previous function being used by L{unsignedID}.
    """
    global _idFunction
    oldIDFunction = _idFunction
    _idFunction = idFunction
    return oldIDFunction


# A value about twice as large as any Python int, to which negative values
# from id() will be added, moving them into a range which should begin just
# above where positive values from id() leave off.
_HUGEINT = (sys.maxint + 1L) * 2L
def unsignedID(obj):
    """
    Return the id of an object as an unsigned number so that its hex
    representation makes sense.

    This is mostly necessary in Python 2.4 which implements L{id} to sometimes
    return a negative value.  Python 2.3 shares this behavior, but also
    implements hex and the %x format specifier to represent negative values as
    though they were positive ones, obscuring the behavior of L{id}.  Python
    2.5's implementation of L{id} always returns positive values.
    """
    rval = _idFunction(obj)
    if rval < 0:
        rval += _HUGEINT
    return rval


def mergeFunctionMetadata(f, g):
    """
    Overwrite C{g}'s name and docstring with values from C{f}.  Update
    C{g}'s instance dictionary with C{f}'s.

    To use this function safely you must use the return value. In Python 2.3,
    L{mergeFunctionMetadata} will create a new function. In later versions of
    Python, C{g} will be mutated and returned.

    @return: A function that has C{g}'s behavior and metadata merged from
        C{f}.
    """
    try:
        g.__name__ = f.__name__
    except TypeError:
        try:
            merged = types.FunctionType(
                g.func_code, g.func_globals,
                f.__name__, inspect.getargspec(g)[-1],
                g.func_closure)
        except TypeError:
            pass
    else:
        merged = g
    try:
        merged.__doc__ = f.__doc__
    except (TypeError, AttributeError):
        pass
    try:
        merged.__dict__.update(g.__dict__)
        merged.__dict__.update(f.__dict__)
    except (TypeError, AttributeError):
        pass
    merged.__module__ = f.__module__
    return merged


def nameToLabel(mname):
    """
    Convert a string like a variable name into a slightly more human-friendly
    string with spaces and capitalized letters.

    @type mname: C{str}
    @param mname: The name to convert to a label.  This must be a string
    which could be used as a Python identifier.  Strings which do not take
    this form will result in unpredictable behavior.

    @rtype: C{str}
    """
    labelList = []
    word = ''
    lastWasUpper = False
    for letter in mname:
        if letter.isupper() == lastWasUpper:
            # Continuing a word.
            word += letter
        else:
            # breaking a word OR beginning a word
            if lastWasUpper:
                # could be either
                if len(word) == 1:
                    # keep going
                    word += letter
                else:
                    # acronym
                    # we're processing the lowercase letter after the acronym-then-capital
                    lastWord = word[:-1]
                    firstLetter = word[-1]
                    labelList.append(lastWord)
                    word = firstLetter + letter
            else:
                # definitely breaking: lower to upper
                labelList.append(word)
                word = letter
        lastWasUpper = letter.isupper()
    if labelList:
        labelList[0] = labelList[0].capitalize()
    else:
        return mname.capitalize()
    labelList.append(word)
    return ' '.join(labelList)



def uidFromString(uidString):
    """
    Convert a user identifier, as a string, into an integer UID.

    @type uid: C{str}
    @param uid: A string giving the base-ten representation of a UID or the
        name of a user which can be converted to a UID via L{pwd.getpwnam}.

    @rtype: C{int}
    @return: The integer UID corresponding to the given string.

    @raise ValueError: If the user name is supplied and L{pwd} is not
        available.
    """
    try:
        return int(uidString)
    except ValueError:
        if pwd is None:
            raise
        return pwd.getpwnam(uidString)[2]



def gidFromString(gidString):
    """
    Convert a group identifier, as a string, into an integer GID.

    @type uid: C{str}
    @param uid: A string giving the base-ten representation of a GID or the
        name of a group which can be converted to a GID via L{grp.getgrnam}.

    @rtype: C{int}
    @return: The integer GID corresponding to the given string.

    @raise ValueError: If the group name is supplied and L{grp} is not
        available.
    """
    try:
        return int(gidString)
    except ValueError:
        if grp is None:
            raise
        return grp.getgrnam(gidString)[2]



def runAsEffectiveUser(euid, egid, function, *args, **kwargs):
    """
    Run the given function wrapped with seteuid/setegid calls.

    This will try to minimize the number of seteuid/setegid calls, comparing
    current and wanted permissions

    @param euid: effective UID used to call the function.
    @type euid: C{int}

    @type egid: effective GID used to call the function.
    @param egid: C{int}

    @param function: the function run with the specific permission.
    @type function: any callable

    @param *args: arguments passed to C{function}
    @param **kwargs: keyword arguments passed to C{function}
    """
    uid, gid = os.geteuid(), os.getegid()
    if uid == euid and gid == egid:
        return function(*args, **kwargs)
    else:
        if uid != 0 and (uid != euid or gid != egid):
            os.seteuid(0)
        if gid != egid:
            os.setegid(egid)
        if euid != 0 and (euid != uid or gid != egid):
            os.seteuid(euid)
        try:
            return function(*args, **kwargs)
        finally:
            if euid != 0 and (uid != euid or gid != egid):
                os.seteuid(0)
            if gid != egid:
                os.setegid(gid)
            if uid != 0 and (uid != euid or gid != egid):
                os.seteuid(uid)



__all__ = [
    "uniquify", "padTo", "getPluginDirs", "addPluginDir", "sibpath",
    "getPassword", "println", "makeStatBar", "OrderedDict",
    "InsensitiveDict", "spewer", "searchupwards", "LineLog",
    "raises", "IntervalDifferential", "FancyStrMixin", "FancyEqMixin",
    "switchUID", "SubclassableCStringIO", "unsignedID", "mergeFunctionMetadata",
    "nameToLabel", "uidFromString", "gidFromString", "runAsEffectiveUser",
]
