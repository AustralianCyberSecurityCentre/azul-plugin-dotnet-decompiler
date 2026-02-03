"""Build an il data structure, expected input is individual lines of il code.

usage:
call parse() with a path to a file containing il code.
"""

import re
from typing import Any, Iterable

from . import util


class ILobject:
    """Base class for il objects that requires a line number representing the start of the object definition."""

    def __init__(self, i):
        self.i = i


class ILclass(ILobject):
    """Representation of an il class. links to contained methods and classes, as well as its parent class if any."""

    # 1: identifier
    # ([^\s<]+(?:<.+>\S+)?) : capture anything that doesn't have a <> in it, or
    # has <> with non whitespace afterward
    re_get = re.compile(r"([^\s<]+(?:<.+>\S+)?)(?:<.+>)?\s*$")
    re_is_start = re.compile(r"^\s*\.class(?! extern)")
    re_is_end = re.compile(r"// end of class")

    def __init__(self, i):
        super(ILclass, self).__init__(i)
        self.parent: ILclass = None
        self.children: list[ILclass] = []
        self.ilmethods: list[ILmethod] = []

        # data
        # the name of this class
        self.name: str = None

    @staticmethod
    def is_start(illine: str) -> re.Match | None:
        """Check if line is start of a class."""
        return ILclass.re_is_start.search(illine)

    @staticmethod
    def is_end(illine: str) -> re.Match | None:
        """Check if line is end of an IL class."""
        return ILclass.re_is_end.search(illine)

    def get_full_name(self) -> str:
        """Get full name of class."""
        full = self.name
        next_parent = self.parent
        while next_parent and next_parent.name:
            full = next_parent.name + "." + full
            next_parent = next_parent.parent
        return full

    def __repr__(self) -> str:
        """Get a string representation of a class."""
        return f"({self.name})"

    def to_dict(self) -> dict:
        """Convert the class into a dictionary."""
        res = {
            "name": self.name,
            "parent": self.parent.name if self.parent else None,
            "children": [child.name for child in self.children],
            "ilmethods": [],
        }
        for ilmethod in self.ilmethods:
            res["ilmethods"].append(ilmethod.to_dict())

        return res

    def read(self, line: str) -> None:
        """Read a class from it's start to end."""
        self.parent = None
        match_start = self.re_get.search(line)
        self.name = match_start.group(1)


class ILmethod(ILobject):
    """Representation of an il method, contains link to class it belongs too and ilosp and ilcalls found within.

    As well as where this method was called in the code.
    """

    re_is_start = re.compile(r"^\s*\.method")
    re_is_end = re.compile(r"// end of method")

    # 1: name
    # re_get_start = re.compile(r'(\'[^\']+\'|(?:<.+>|[^\'\s])*)\s?\((?!.+\()')
    # remove ending <gvtr>
    re_fix_start = re.compile(r"^((?:[^<>\$\n]+|<.+>(?!\s|$))*)")

    # 1: all words before last word, 2: last word, 3: if present, another
    # parameter below
    re_param_line = re.compile(r"\s*(.+(?=\s\S))\s([^\s,]+)(,)?\s*$")
    re_param_fix = re.compile(r"^([^<]+)")
    re_param_spot_mods = re.compile(r"\s\S+(?=\()\(.*\)\S*")

    # 1: all preceding method name, 2: method name, 3: if present, no
    # parameters
    re_initial_split = re.compile(r"\s*(.+(?=\s\S))\s(\S+)\s*\((\))?")

    def __init__(self, i: ILobject):
        super(ILmethod, self).__init__(i)
        self.ilclass: ILclass = None
        self.ilops: list[ILop] = []
        self.ilcalls: list[ILcall] = []
        self.calledby: list[ILcall] = []

        # data
        self.name: str = None
        self.params: list[str] = []
        self.rettype: list[str] = []

    @staticmethod
    def is_start(illine: str) -> re.Match | None:
        """Check if is start of an il method."""
        return ILmethod.re_is_start.search(illine)

    @staticmethod
    def is_end(illine: str) -> re.Match | None:
        """Check if is end of an il method."""
        return ILmethod.re_is_end.search(illine)

    def __repr__(self) -> str:
        """Get a string representation of a method."""
        return f"({self.get_loc_text()})"

    def to_dict(self) -> dict:
        """Convert the method into a dictionary."""
        res = {
            "name": self.name,
            "ilclass": self.ilclass.get_full_name() if self.ilclass else None,
            "called_by": [ilcall.get_loc_name() for ilcall in self.calledby],
            "ilcalls": [ilcall.to_dict() for ilcall in self.ilcalls],
            "ilops": [ilop.to_dict() for ilop in self.ilops] if True else None,
            "parameters": self.params,
        }

        return res

    def get_loc_text(self) -> dict:
        """Get a fully qualified method name as a dict."""
        return {"class": self.ilclass.get_full_name(), "method": self.name}

    def friendly_loc_text(self) -> str:
        """Get a fully qualified method name as a string."""
        return self.ilclass.get_full_name() + "::" + self.name

    def read(self, lines: list[str]):
        """Read through a number of lines looking for a complete method to parse."""
        # lines should be a 10 or so length of lines including initial method
        # definition
        line = lines[0]
        line2 = util.replace_space(line)
        match = self.re_initial_split.search(line2)
        raw_return, raw_name, hasnot_param = match.group(1, 2, 3)

        if not hasnot_param:
            # multi line params
            for line in lines[1:]:
                m = self.re_param_line.search(line)
                praw_type, _, phas_more = m.group(1, 2, 3)
                praw_type = self.re_param_fix.search(praw_type).group(1)
                # dunno what these out and in mean, but it makes matching not
                # work
                praw_type = praw_type.replace("[out] ", "")
                praw_type = praw_type.replace("[in] ", "")
                praw_type = praw_type.replace("[opt] ", "")

                # filter out marshal, etc
                matches = self.re_param_spot_mods.findall(praw_type)
                for match in matches:
                    praw_type = praw_type.replace(match, "")
                praw_type = praw_type.replace("!!T", "")
                self.params.append(praw_type)
                if not phas_more:
                    break

        almost_name = self.re_fix_start.search(raw_name).group(1)
        self.name = util.unreplace_space(almost_name)
        self.rettype = raw_return


class ILop(ILobject):
    """Representation of an il operation such as; ldstr 'dogmeat'."""

    # 1: global address, 2: code, 3: local address, 4: ilop code, 5: attributes
    re_get = re.compile(r"^\s*/\* (\S+) (\S+)\s*\*/ (\S+): (\S+)\s*(.*)?$")
    re_is = re.compile(r"\s*/\* 0x.+\*/ IL")

    def __init__(self, i):
        super(ILop, self).__init__(i)
        self.ilmethod: ILmethod = None
        self.ilcall: ILcall = None

        # data
        self.glob: str = None
        self.code: str = None
        self.loc: str = None
        self.opcode: str = None
        self.attrib: str = None

    @staticmethod
    def is_ilop(illine: str) -> re.Match | None:
        """Check to see if given line is an il OP."""
        return ILop.re_is.search(illine)

    def __repr__(self) -> str:
        """Get a string representation of the operation."""
        return "(%s, %s, %s)" % (self.get_loc(), self.opcode, self.attrib)

    def to_dict(self) -> dict:
        """Convert the Operation into a dictionary."""
        res = {
            "global_address": self.glob,
            "short_code": self.code,
            "local_address": self.loc,
            "opcode": self.opcode,
            "attributes": self.attrib,
        }
        return res

    def get_loc(self) -> dict:
        """Get the location of the operation within the il method."""
        loc = self.ilmethod.get_loc_text()
        return loc

    def read(self, line: str) -> None:
        """Read a il OP from a line of il code."""
        match = self.re_get.search(line)
        self.glob = match.group(1)
        self.code = match.group(2)
        self.loc = match.group(3)
        self.opcode = match.group(4)
        self.attrib = match.group(5)


class ILcall(ILobject):
    """Represents an IL call opcode with the parameters separated and linked where possible.

    To internally defined methods, or externally defined methods.
    """

    re_remove_modopts = re.compile(r"(?:modopt|modreq)\([^\)]*\)")
    # 1; class::method, 2; params
    # use findall to get each param
    re_params = re.compile(r"(.+?)(?:,\s|$)")
    # 1: library, 2; class, 3; method
    re_library_class_method = re.compile(r"(?:\[([^\]]+)\])?(.*)::(.+)")

    # capture anything after the System.class/ stuff
    re_fix_class = re.compile(r"^((?:<[^>]+>(?=\S)|\'[^\']+\'|[^\'\[<>]+)*)")
    # trim $FEP7893279 and <btehteh> that is at the end
    re_fix_class_slashes = re.compile(r"([^/]+)$")
    re_fix_method = re.compile(r"^((?:<[^<>]+>(?=\S)|[^<$>]+)*)")

    # new
    # split return type, lib&class&method, parameters
    re_initial_split = re.compile(r"(?:(.+)\s)?([^\s\)\(]+)\s*\((.*)\)\s*$")
    # To handle cases where IL calls are generated without params '()'
    re_initial_noparam = re.compile(r"(?:(.+)\s)?([^\s\)\(]+)\s*$")

    def __init__(self, i):
        super(ILcall, self).__init__(i)
        self.ilop: ILop = None
        self.intarget: ILmethod = None
        self.extarget: tuple[str, str] = None

        # data
        self.texttarget: tuple[str, str, str] = None
        self.textparams: list[str] = []
        self.params: list = []
        self.rettype: list[str] = None

    @staticmethod
    def is_ilcall(opcode: str) -> bool:
        """Check if the given opcode is an ilcall type."""
        return opcode in ["call", "callvirt", "newobj", "ldftn"]

    def to_dict(self) -> dict:
        """Convert the Call into a dictionary."""
        res = {
            "internal_target": self.intarget.get_loc_text() if self.intarget else None,
            "external_target": {"class": self.extarget[0], "method": self.extarget[1]} if self.extarget else None,
            "parameters": self.textparams,
        }
        return res

    def get_target_name(self) -> dict:
        """Get the fully qualified target of the function call as a dict."""
        return {"library": self.texttarget[0], "class": self.texttarget[1], "method": self.texttarget[2]}

    def get_loc_name(self) -> dict:
        """Returns the location of the Call."""
        return self.ilop.get_loc()

    def iter_params(self) -> Iterable[tuple[str, Any]]:
        """Iterate through the call parameters."""
        for i in range(len(self.params)):
            yield self.textparams[i], self.params[i]

    def read(self, line: str) -> None:
        """Parses the il call line and prevents various edge cases from breaking everything."""
        line2 = util.replace_space(line)
        matches = self.re_remove_modopts.findall(line2)
        for match in matches:
            line2 = line2.replace(match, "")
        split_res = self.re_initial_split.search(line2)
        if split_res is not None:
            raw_return, raw_names, raw_params = split_res.group(1, 2, 3)
        else:
            raw_return, raw_names = self.re_initial_noparam.search(line2).group(1, 2)
            raw_params = ""
        raw_lib, raw_class, raw_method = self.re_library_class_method.search(raw_names).group(1, 2, 3)

        call_class = self.re_fix_class.search(raw_class).group(1)
        call_method = self.re_fix_method.search(raw_method).group(1)

        # get rid of preceding '/'es
        if call_class:
            call_class = self.re_fix_class_slashes.search(call_class).group(1)

        raw_params = util.redo_space(raw_params)
        call_params = self.re_params.findall(raw_params)

        # other cleanup of strange edge cases
        call_class = util.unreplace_space(call_class)
        call_params = [ILmethod.re_param_fix.search(x).group(1) for x in call_params]
        # handle methods with undefined types by ignoring it
        call_params = [x.replace("!!0", "") for x in call_params]
        # replace amgic string with space again
        call_params = [util.unreplace_space(x) for x in call_params]

        call_method = util.unreplace_space(call_method)
        raw_lib = util.unreplace_space(raw_lib)
        raw_return = util.unreplace_space(raw_return)

        self.texttarget = raw_lib, call_class, call_method
        self.textparams = call_params
        self.rettype = raw_return


class EXassembly:
    """Represents an external assembly used by the current il code.

    Keeps track of what is called and where it is called from.
    """

    def __init__(self, name):
        # self.exmethods = []

        # data
        self.name: str = name
        # dictionary of (class, method): ilcall
        self.extarget_classes: dict[str, dict[str, list]] = {}

    def __repr__(self) -> str:
        """String representation of an external assemblyline."""
        return "(%s, %s)" % (self.name, self.extarget_classes)

    def to_dict(self):
        """Convert the current External assembly into a dictionary."""
        targets = {}
        for idclass, idmethods in self.extarget_classes.items():
            targets[idclass] = {}
            for idmethod, ilcalls in idmethods.items():
                targets[idclass][idmethod] = []
                for ilcall in ilcalls:
                    targets[idclass][idmethod].append(ilcall.get_loc_name())

        res = {self.name: targets}

        return res


class ILrepr:
    """A representation of the il code in a variety of data structures."""

    def __init__(self):
        self.entrypoint: ILmethod = None
        self.cctors: list[ILmethod] = []
        self.ilclasses: list[ILclass] = []
        self.exassemblies: dict[str, EXassembly] = {}
        self.method_sigs: dict[tuple[str, str], list[ILmethod]] = {}
        self.il: list[str] = None

        # map of index to ilop
        self.ilopmap: dict[int, ILop] = {}

    def to_dict(self) -> dict:
        """Return dictionary representation for the il code."""
        res = {
            "entry_point": self.entrypoint.get_loc_text() if self.entrypoint else None,
            "cctors": [cctor.get_loc_text() for cctor in self.cctors],
            "ilclasses": [],
            "external_assemblies": [ass.to_dict() for _, ass in self.exassemblies.items()],
            "list_ilmethod": [],
            "list_ilclass": [],
            "list_external_method": [],
        }
        for ilclass in self.iter_classes():
            res["ilclasses"].append(ilclass.to_dict())
            res["list_ilclass"].append(ilclass.get_full_name())

        for ilmethod in self.iter_methods():
            res["list_ilmethod"].append(ilmethod.friendly_loc_text())

        for exmethod in self.iter_ex_methods():
            res["list_external_method"].append("[%s]%s::%s" % (exmethod[0], exmethod[1], exmethod[2]))

        return res

    def iter_ilcalls(self) -> Iterable[ILcall]:
        """Iterate over all the calls to an il method."""
        for ilclass in self.ilclasses:
            for ilmethod in ilclass.ilmethods:
                for ilcall in ilmethod.ilcalls:
                    yield ilcall

    def iter_ilops(self) -> Iterable[ILop]:
        """Iterate through all the il ops."""
        for ilclass in self.ilclasses:
            for ilmethod in ilclass.ilmethods:
                for ilop in ilmethod.ilops:
                    yield ilop

    def iter_classes(self) -> Iterable[ILclass]:
        """Iterate through all of the classes."""
        for ilclass in self.ilclasses:
            yield ilclass

    def iter_methods(self) -> Iterable[ILmethod]:
        """Iterate through all the methods."""
        for ilclass in self.ilclasses:
            for ilmethod in ilclass.ilmethods:
                yield ilmethod

    def iter_ex_methods(self) -> Iterable[tuple[str, str, str]]:
        """Iterate through a tuple of the external method calls.

        return tuple is in the form (External Assembly, External Class, External Method)
        """
        for exassembly, exclasses in self.exassemblies.items():
            for exclass, exmethods in exclasses.extarget_classes.items():
                for exmethod in exmethods:
                    yield (exassembly, exclass, exmethod)


class Stack:
    """Tracks nested Classes."""

    def __init__(self):
        self.classes: list[ILclass] = []

    def current(self) -> ILclass:
        """Get the current class in the stack."""
        return self.classes[len(self.classes) - 1]

    def finish(self) -> ILclass:
        """Pops the last class from the stack."""
        self.classes.pop()

    def start(self, ilclass: ILclass) -> None:
        """Append a new class to the stack."""
        self.classes.append(ilclass)

    def parent(self) -> ILclass | None:
        """Get the parent of the current class or None if there is none."""
        if len(self.classes) >= 2:
            return self.classes[len(self.classes) - 2]
        else:
            return None


def parse(il_file_path: str) -> ILrepr:
    """Main function to parse an il string into classes, methods, and operations.

    :return: ilrepr object containing details of classes, methods, etc
    """
    raw_il = ""
    with open(il_file_path, "r") as f:
        raw_il = f.read()

    ilrepr = ILrepr()
    ilrepr.il = raw_il.splitlines()
    try:
        _parse_structure(ilrepr)
        _parse_lines(ilrepr)
        _link_ilcalls(ilrepr)
        _link_entry_point(ilrepr)
        _link_ilcall_params(ilrepr)
    except Exception:  # noqa: S110
        pass
        # Can sometimes fail to parse EP on obfuscated binaries
        # Don't raise as this will abort the entire plugin
        # raise

    return ilrepr


def _parse_structure(ilrepr: ILrepr) -> None:
    """Create objects for each class, method and ilop, linking them to each other."""
    cclass, cmethod, cilop = 0, 0, 0
    stack = Stack()
    current_method = None
    for i in range(len(ilrepr.il)):
        line = ilrepr.il[i]
        if ILop.is_ilop(line):
            ilop = ILop(i)
            ilrepr.ilopmap[i] = ilop
            _link_ilop_method(ilop, current_method)
            cilop += 1
        elif ILmethod.is_start(line):
            if current_method:
                raise ValueError("method within method unhandled", i)
            current_method = ILmethod(i)
            _link_method_class(current_method, stack.current())
            cmethod += 1
        elif ILclass.is_start(line):
            stack.start(ILclass(i))
            if stack.parent():
                _link_class_class(stack.current(), stack.parent())
            ilrepr.ilclasses.append(stack.current())
            cclass += 1
        elif ILmethod.is_end(line):
            current_method = None
        elif ILclass.is_end(line):
            stack.finish()


def _parse_lines(ilrepr: ILrepr) -> None:
    """Goes through created il classes, methods and operations to fill in the data that each has about itself.

    Links them together depending on where they are in the file, methods linked to containing classes, etc.
    """
    # parse ids and other information from classes, methods, ilops
    count_calls = 0
    # fill in ilclass details from il code
    for ilclass in ilrepr.ilclasses:
        _do_ilclass(ilrepr.il, ilclass)

        # fill in ilmethod details from il code
        for ilmethod in ilclass.ilmethods:
            _do_ilmethod(ilrepr.il, ilmethod)
            key = (ilclass.get_full_name(), ilmethod.name)
            if key not in ilrepr.method_sigs:
                ilrepr.method_sigs[key] = []
            ilrepr.method_sigs[key].append(ilmethod)
            if ilmethod.name == ".cctor":
                ilrepr.cctors.append(ilmethod)

            # fill in ilop details from il code
            for ilop in ilmethod.ilops:
                _do_ilop(ilrepr.il, ilop)

                # sometimes calls have no attributes.
                # these ~shouldnt~ do anything.
                if ILcall.is_ilcall(ilop.opcode) and ilop.attrib != "":
                    # fill in ilcall details from il code
                    _do_ilcall(ilop)
                    _link_call_method(ilop.ilcall, ilop.ilmethod)
                    count_calls += 1


def _link_ilcalls(ilrepr: ILrepr) -> None:
    # link ilcalls to the methods that they call
    csystem, clocal, cfailed, cassumed = 0, 0, 0, 0
    for ilcall in ilrepr.iter_ilcalls():
        try:
            exlibrary, ilclass, ilmethod = ilcall.texttarget
        except Exception:
            print("failed to link call %s %s" % (ilcall.ilop.to_dict(), ilcall.texttarget))
            raise
        if not exlibrary:
            # try to match it to a local method
            try:
                str1, str2 = "", ""
                ilmethods = ilrepr.method_sigs[(ilclass, ilmethod)]
                if len(ilmethods) == 1:
                    ilcall.intarget = ilmethods[0]
                    ilmethods[0].calledby.append(ilcall)
                else:
                    for ilmethod in ilmethods:
                        str1 = "".join(ilmethod.params)
                        str2 = "".join(ilcall.textparams)
                        if str1 == str2:
                            ilcall.intarget = ilmethod
                            ilmethod.calledby.append(ilcall)
                            clocal += 1
                            break
                    else:
                        # local method call paramater mismatch
                        # assume first method is correct
                        ilcall.intarget = ilmethods[0]
                        ilmethods[0].calledby.append(ilcall)
                        cassumed += 1

            except KeyError:
                if ilclass.startswith("Enum"):
                    print("failed to link enum %s\n%s" % (ilcall.i, ilcall.texttarget))
                else:
                    print("failed to link local method %d\n%s" % (ilcall.i, ilcall.texttarget))
                    cfailed += 1
            except TypeError:
                print(
                    "failed something with the param string types\nm: %s c: %s" % (ilmethod.params, ilcall.textparams)
                )
                raise
        else:
            # link the external method
            if exlibrary not in ilrepr.exassemblies:
                ilrepr.exassemblies[exlibrary] = EXassembly(exlibrary)
            ea = ilrepr.exassemblies[exlibrary]
            key = (ilclass, ilmethod)
            if ilclass not in ea.extarget_classes:
                ea.extarget_classes[ilclass] = {}
            if ilmethod not in ea.extarget_classes[ilclass]:
                ea.extarget_classes[ilclass][ilmethod] = []

            ea.extarget_classes[ilclass][ilmethod].append(ilcall)
            ilcall.extarget = key
            csystem += 1
    if cassumed > 0:
        print("there were calls that could have parameters matched: %d" % cassumed)


def _link_ilcall_params(ilrepr: ILrepr) -> None:
    """Links ilcall with ilops that give parameters to the call."""
    fail_count = 0
    for ilcall in ilrepr.iter_ilcalls():
        for i in range(len(ilcall.textparams)):
            origin_ilop = None
            offset = i - len(ilcall.textparams)
            index = ilcall.ilop.i

            try:
                origin_ilop = ilrepr.ilopmap[index + offset]
            except KeyError:
                if not ilcall.textparams[i] == "class [mscorlib]System.Exception":
                    print("failed to map ilop %s %s" % (offset, ilcall.ilop.get_loc()))
                    fail_count += 1
                else:
                    origin_ilop = None
                    print("param ilop is exception handler, set as None %s %s" % (ilcall.ilop.get_loc(), offset))
            ilcall.params.append(origin_ilop)


def _link_entry_point(ilrepr: ILrepr) -> None:
    # link entry point with method it calls
    ep_line = ilrepr.il[1]
    ep_match = re.search(r"// Entry point: ([^\s]+)\.([^\.\s]+)", ep_line)
    if not ep_match:
        print("assembly has no entry point")
        return
    ep_text = ep_match.group(1), ep_match.group(2)
    try:
        # has to be the only method in list, since entry point has special
        # parameter reqs
        ilrepr.entrypoint = ilrepr.method_sigs[ep_text][0]
    except KeyError:
        try:
            ep_text_alt = "'" + ep_text[0] + "'", ep_text[1]
            ilrepr.entrypoint = ilrepr.method_sigs[ep_text_alt][0]
        except Exception as e:
            raise Exception("failed to link entry point", ep_text) from e


def _do_ilclass(il: str, ilclass: ILclass) -> None:
    # parses various class data
    ilclass.read(il[ilclass.i])


def _do_ilmethod(il: str, ilmethod: ILmethod) -> None:
    # parses method data from the second line (first line does not contain much
    # useful atm)
    ilmethod.read(il[ilmethod.i + 1 : ilmethod.i + 1 + 20])


def _do_ilop(il: str, ilop: ILop) -> None:
    # parses data from il line
    ilop.read(il[ilop.i])


def _do_ilcall(ilop: ILop) -> None:
    # double links an ilcall with its ilop
    ilop.ilcall = ILcall(ilop.i)
    ilop.ilcall.ilop = ilop
    try:
        ilop.ilcall.read(ilop.attrib)
    except AttributeError:
        print("failed to parse call: %s" % ilop.attrib)


def _link_call_method(ilcall: ILcall, ilmethod: ILmethod) -> None:
    # links the method with what it calls
    ilmethod.ilcalls.append(ilcall)


def _link_class_class(child: ILclass, parent: ILclass) -> None:
    # double links a parent with its child class
    child.parent = parent
    parent.children.append(child)


def _link_method_class(ilmethod: ILmethod, ilclass: ILclass) -> None:
    # double link method with ints containing class
    ilmethod.ilclass = ilclass
    ilclass.ilmethods.append(ilmethod)


def _link_ilop_method(ilop: ILop, ilmethod: ILmethod) -> None:
    # double link ilop with its containing method
    ilop.ilmethod = ilmethod
    ilmethod.ilops.append(ilop)


def _line_str(ilrepr: ILrepr, i: int) -> str:
    imax = len(str(len(ilrepr.il)))

    return str(i).zfill(imax) + ")"
