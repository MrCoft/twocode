import io

def lsp_msg(header, content):
    buf = io.StringIO()
    for key, value in header:
        buf.write(key)
        buf.write(": ")
        buf.write(value)
        buf.write("\r\n")
    buf.write("\r\n")
    header_data = buf.getvalue().encode("ascii")
    header_lines = []
    content_data = buf.getvalue().encode("utf-8")
def lsp_send(cmd):
    content = {}
    header = {}
    header["Content-Length"] = str(len(content))
    header["Content-Type"] = "application/vscode-jsonrpc; charset=utf-8"

    content = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "textDocument/didOpen",
        "params": {
            ...
        }
    }

#  IN: textDocument/didOpen; Params: document
    # now the truth about the document is in your memory
#  IN: textDocument/didChange; Params: {documentURI, changes}
    # IDE made an edit
# OUT: textDocument/publishDiagnostics; Params: Diagnostic[]
    # return ANY changes: errors, warnings
# didClose - up to date, stop

'''
This is the request:
{
    "jsonrpc": "2.0",
    "id" : 1,
    "method": "textDocument/definition",
    "params": {
        "textDocument": {
            "uri": "file:///p%3A/mseng/VSCode/Playgrounds/cpp/use.cpp"
        },
        "position": {
            "line": 3,
            "character": 12
        }
    }
}
This is the response:

{
    "jsonrpc": "2.0",
    "id": "1",
    "result": {
        "uri": "file:///p%3A/mseng/VSCode/Playgrounds/cpp/provide.cpp",
        "range": {
            "start": {
                "line": 0,
                "character": 4
            },
            "end": {
                "line": 0,
                "character": 11
            }
        }
    }
}
'''
# capabilities:
# about to save -> format

# syntax highlighting
# syntax errors!

# Node.js language server npm module








'''
interface ShowMessageParams {
	/**
	 * The message type. See {@link MessageType}.
	 */
	type: number;

	/**
	 * The actual message.
	 */
	message: string;
}
Where the type is defined as follows:

export namespace MessageType {
	/**
	 * An error message.
	 */
	export const Error = 1;
	/**
	 * A warning message.
	 */
	export const Warning = 2;
	/**
	 * An information message.
	 */
	export const Info = 3;
	/**
	 * A log message.
	 */
	export const Log = 4;
}

'''

# Request
@decor("window/showMessageRequest")
def window_show_msg_req():
    # show, allow action

'''
params: ShowMessageRequestParams defined as follows:
Response:

result: the selected MessageActionItem | null if none got selected.
error: code and message set in case an exception happens during showing a message.
interface ShowMessageRequestParams {
	/**
	 * The message type. See {@link MessageType}
	 */
	type: number;

	/**
	 * The actual message
	 */
	message: string;

	/**
	 * The message action items to present.
	 */
	actions?: MessageActionItem[];
}
Where the MessageActionItem is defined as follows:

interface MessageActionItem {
	/**
	 * A short title like 'Retry', 'Open Log' etc.
	 */
	title: string;
}
'''
# log message


import json

class LangServer:
    def __init__(self):
        self.id = 1
    def send(self):
        self.id += 1
        # "method": "subtract"
        # "params":
        # [42, 24]
        # # "params": {"subtrahend": 23, "minuend": 42}

        # "result": 19
        # (same id)
    def handle_errors(self, msg):
        try:
            msg = json.loads(msg, encoding="utf-8")
        except ValueError:
            # {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": null}
            # same id, id: null if no id

            # if method not str, if params not list or dict
            # if batch that is empty
            # or an element is eg 1 and not a proper msg - in that case, return []
            # if proper parse, have an answer for each thing - that needs it. ignore notifies
            # return nothing for notifies only
            # {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": null}

        # {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": "1"}

        # batch:
        # [ ] stuff for each
        # if fails, id null

# TESTS! a dummy method? a dummy server?