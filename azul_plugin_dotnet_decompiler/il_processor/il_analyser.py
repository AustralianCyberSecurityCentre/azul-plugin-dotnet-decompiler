"""This script takes in output from the il parser and returns several structures.

The structures represent information calculated from it as a jsonable dictionary.
"""

import time
import traceback

from azul_plugin_dotnet_decompiler.il_processor import il_parser

_call_tree_timeout = 300  # seconds
_call_tree_max_depth = 8


class AnalyseException(Exception):
    """Exception raised when the IL analyser and parser failed."""

    pass


def parse_il(il_file_path: str) -> dict:
    """Given the path to an dotnet il file extract a call tree and other metadata from the code."""
    results = dict()
    try:
        # il parser
        ilrepr = il_parser.parse(il_file_path)
        results["il_parsed"] = ilrepr.to_dict()

        # il analyser
        call_tree, call_tree_friendly = _do_call_tree(ilrepr)
        resana = {
            "opcode_count": _do_count_opcodes(ilrepr),
            "extracted_strings": _do_extract_strings(ilrepr),
            "call_wrappers": _do_call_wrappers(ilrepr),
            "string_manipulations": _do_string_change_methods(ilrepr),
            "call_tree": call_tree,
            "call_tree_friendly": call_tree_friendly,
        }
        results["il_analysis"] = resana
    except Exception as e:
        msg = "IL analysis failed:\n%s" % traceback.format_exc(limit=10)
        raise AnalyseException(msg) from e
    return results


def _do_count_opcodes(ilrepr: il_parser.ILrepr):
    """Count occurrences of opcodes such as ldstr, callvirt."""
    ops = {}
    for ilop in ilrepr.iter_ilops():
        ops[ilop.opcode] = ops.get(ilop.opcode, 0) + 1

    return ops


def _do_extract_strings(ilrepr: il_parser.ILrepr):
    """Stores the attrib string of ldstr operations."""
    strings = []

    for ilop in ilrepr.iter_ilops():
        if ilop.opcode == "ldstr":
            strings.append((ilop.attrib, ilop.get_loc()))

    return strings


def _do_call_wrappers(ilrepr: il_parser.ILrepr):
    """Gathers every call that only calls one other method, in the hopes that it may be a wrapper of an existing call.

    Such as to the .NET api, or other.
    """
    call_wrappers = []
    # a wrapper method calls one system operation, and has very few ilop
    # operations
    found = 0
    for ilmethod in ilrepr.iter_methods():
        if len(ilmethod.ilcalls) == 1 and ilmethod.name not in (".ctor", ".cctor"):
            found += 1
            callto = ilmethod.ilcalls[0]
            call_wrappers.append({"origin": ilmethod.get_loc_text(), "target": callto.get_target_name()})

    return call_wrappers


def _do_string_change_methods(ilrepr: il_parser.ILrepr) -> list:
    """Gathers all methods that take string as parameter and return a string."""
    string_changes: list[dict] = []
    count = 0
    for ilcall in ilrepr.iter_ilcalls():
        for texttype, ilparam in ilcall.iter_params():
            if texttype == "string" and ilparam and ilparam.ilcall:
                # could be a change method
                string_changes.append(ilparam.ilcall.get_loc_name())
                count += 1

    return string_changes


def _do_call_tree(ilrepr: il_parser.ILrepr) -> tuple[list, str]:
    """Non recursive start of the call tree extraction.

    The call tree starts by looking at all constructors, and then the entry point.
    """
    call_tree_print = f"\nGenerating call tree, max depth: {_call_tree_max_depth}\n"
    method_coll = set()
    for ilmethod in ilrepr.iter_methods():
        method_coll.add(ilmethod)

    timeout = time.time() + _call_tree_timeout
    tree = []
    for cctor in ilrepr.cctors:
        subtree, call_tree_print = __do_call_tree_recursive(ilrepr, call_tree_print, cctor, [], method_coll, timeout)
        tree.append(subtree)
    if ilrepr.entrypoint is not None:
        subtree, call_tree_print = __do_call_tree_recursive(
            ilrepr, call_tree_print, ilrepr.entrypoint, [], method_coll, timeout
        )
        tree.append(subtree)
    call_tree = tree

    return call_tree, call_tree_print


def __do_call_tree_recursive(
    ilrepr: il_parser.ILrepr,
    call_tree_print: str,
    root: il_parser.ILmethod,
    parents: list,
    method_coll: set[il_parser.ILmethod],
    timeout: float,
):
    """Recursive component of the call tree extraction."""
    if timeout is not None and timeout < time.time():
        return {"root": root, "local": False, "ilops": 0}, call_tree_print

    friendly = root
    local = False
    ilop_count = 0
    indent = "   " * len(parents)
    # get friendly text for this node if it isnt just a string
    if root in method_coll:
        friendly = root.get_loc_text()
        local = True
        ilop_count = len(root.ilops)
        call_tree_print += "\n" + indent + root.friendly_loc_text()
    else:
        try:
            call_tree_print += "\n" + indent + root[0] + "::" + root[1]
        except Exception:  # nosec B110
            pass

    # preorder print
    data = {"root": friendly, "local": local, "ilops": ilop_count}

    # branch for each call made from current method
    if local and root not in parents:
        # add to parents
        parents_new = list(parents)
        parents_new.append(root)
        data["children"] = []
        for ilcall in root.ilcalls:
            if not ilcall.intarget and not ilcall.extarget:
                # skipping unlinked local call
                continue
            if len(parents) > _call_tree_max_depth:
                # Recursion limit
                continue
            next_root = ilcall.intarget if ilcall.intarget else ilcall.extarget
            # build tree for each child
            subtree, call_tree_print = __do_call_tree_recursive(
                ilrepr, call_tree_print, next_root, parents_new, method_coll
            )
            data["children"].append(subtree)

    return data, call_tree_print
