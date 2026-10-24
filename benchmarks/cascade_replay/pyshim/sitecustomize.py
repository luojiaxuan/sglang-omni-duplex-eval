import setproctitle

_set = setproctitle.setproctitle
_set("/usr/bin/python")
setproctitle.setproctitle = lambda *args, **kwargs: _set("/usr/bin/python")
