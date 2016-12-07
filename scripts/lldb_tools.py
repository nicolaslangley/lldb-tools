import lldb
import commands
import pygments

file_location = "/Users/nico8506/.lldb/.breakpoints"

"""LLDB wrapper for 'ls' command"""
def ls(debugger, command, result, internal_dict):
    print >> result, (commands.getoutput('/bin/ls %s' % command))

"""Pretty printing of QStrings"""
def utf16string_summary(value, *rest):
    d = value.GetChildMemberWithName("d")
    length = d.GetChildMemberWithName("size").GetValueAsSigned()
    offset = d.GetChildMemberWithName("offset").GetValueAsSigned()
    address = d.GetValueAsUnsigned() + offset

    if length == 0:
        return '""'
    error = lldb.SBError()
    # UTF-16, so we multiply length by 2
    bytes = value.GetProcess().ReadMemory(address, length * 2, error)
    if bytes is None:
        return '""'
    return '"%s"' % (bytes.decode('utf-16').encode('utf-8'))

"""Save breakpoints for current target"""
def save_breakpoints(debugger, command, result, internal_dict):
    target = debugger.GetSelectedTarget()
    output = open(file_location + "_" + str(target) + "_" + str(command), "w+")
    for i in range(target.GetNumBreakpoints()):
        b = target.GetBreakpointAtIndex(i)
        bp_str = b.__str__()
        bp_list = [bp.strip() for bp in bp_str.split(',')]
        target_file = bp_list[1][8:-1]
        target_line = bp_list[2][7:]
        if target_line.isdigit():
            print >> output, "b " + target_file + ":" + target_line
        else:
            print >> output, "b " + target_file

"""Load breakpoints for current target if saved"""
def load_breakpoints(debugger, command, result, internal_dict):
    target = debugger.GetSelectedTarget()
    try:
        input = open(file_location + "_" + str(target) + "_" + str(command), "r")
        for line in input:
            debugger.HandleCommand(line)
    except:
        print "No Breakpoints Available"

"""Add syntax highlighting for C++ code"""
def frame_cpp(debugger, command, result, internal_dict):
    frame = debugger.GetSelectedTarget().GetProcess().GetThreadAtIndex(0).GetFrameAtIndex(0)
    line_entry = frame.GetLineEntry()
    file_spec = line_entry.GetFileSpec()
    line = line_entry.GetLine()
    source_manager = debugger.GetSourceManager()
    stream = lldb.SBStream()
    source_manager.DisplaySourceLinesWithLineNumbers(file_spec, line, 10, 10, '=>', stream)
    print pygments.highlight(stream.GetData(), pygments.lexers.CLexer(), pygments.formatters.TerminalFormatter())

def __lldb_init_module (debugger, dict):
    debugger.HandleCommand('command script add -f lldb_tools.ls ls')
    debugger.HandleCommand('command script add -f lldb_tools.save_breakpoints save_breakpoints')
    debugger.HandleCommand('command script add -f lldb_tools.load_breakpoints load_breakpoints')
    # debugger.HandleCommand('command script add -f lldb_tools.frame_cpp frame_cpp')

    summary = lldb.SBTypeSummary.CreateWithFunctionName("qstring.utf16string_summary")
    summary.SetOptions(lldb.eTypeOptionHideChildren)
    debugger.GetDefaultCategory().AddTypeSummary( lldb.SBTypeNameSpecifier("QString", False), summary )
