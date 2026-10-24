# note (luojiaxuan): keeps every process title at the interpreter path on shared
# hosts; the scoring venv has no setproctitle, and its processes set no title.
import importlib.util

if importlib.util.find_spec("setproctitle") is not None:
    import setproctitle

    _set_title = setproctitle.setproctitle
    setproctitle.setproctitle = lambda title: _set_title("/usr/bin/python")
    _set_title("/usr/bin/python")
else:
    pass
