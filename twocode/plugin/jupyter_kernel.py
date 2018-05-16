import ipykernel
import ipykernel.kernelbase
import ipykernel.kernelapp
import twocode
from twocode import utils
import sys
import contextlib
import traceback

class TwocodeKernel(ipykernel.kernelbase.Kernel):
    implementation = "Twocode Kernel"
    implementation_version = "1.0"
    language = "twocode"
    language_version = twocode.__version__
    language_info = {
        "name": "twocode",
        "mimetype": "text/x-twocode",
        "file_extension": ".2c",
    }
    banner = "Twocode kernel"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context = twocode.Twocode()
        redirect = lambda stream: utils.Object(
            write=lambda s: self.send_string(s, stream),
            flush=lambda: None,
        )
        self.streams = utils.Streams(stdout=redirect("stdout"), stderr=redirect("stderr"))
    def send_string(self, s, stream):
        self.send_response(self.iopub_socket, "stream", {
            "name": stream,
            "text": s,
        })
    def send_image(self, img):
        from PIL import Image
        img = Image.open(img)

        import io
        buf = io.BytesIO()
        img.save(buf, "png")
        data = buf.getvalue()
        import base64
        data = str(base64.b64encode(data))[2:-1]

        size = img.size

        self.send_response(self.iopub_socket, "display_data", {
            "data": {
                "image/png": data,
            },
            "metadata": {
                "image/png": {
                    "width": size[0],
                    "height": size[1],
                }
            }
        })
    def do_execute(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=False):
        with contextlib.ExitStack() as stack:
            if not silent:
                stack.enter_context(self.streams)
            context = self.context
            out = None
            try:
                ast = context.parse(code)
                obj = context.eval(ast, type="stmt")
            except context.exc.RuntimeError as exc:
                msg = context.traceback(exc)
                print(msg, file=sys.stderr)
                status = "error"
            except:
                exc_type, exc, tb = sys.exc_info()
                msg = traceback.format_exception(exc_type, exc, tb)
                print("".join(msg), file=sys.stderr, end="")
                status = "error"
            else:
                out = code_magic(context, obj)
                status = "ok"

        content = {
            "status": status,
            "execution_count": self.execution_count,
        }
        if status == "ok":
            content.update({
                "payload": [],
                "user_expressions": {},
            })
            if not silent and out is not None:
                self.send_response(self.iopub_socket, "execute_result", {
                    "data": {
                        "text/plain": out,
                    },
                    "metadata": {},
                    "execution_count": self.execution_count,
                })
        elif status == "error":
            """
                {
                    'ename' : 'NameError',
                    'evalue' : 'foo',
                    'traceback' : ...
                }
            """
            pass
        return content
        # complete, inspect, history, is_complete
    def do_shutdown(self, restart):
        del self.context
        if restart:
            self.context = twocode.Twocode()

def code_magic(context, obj):
    if obj is None or obj.__type__ is context.basic_types.Null:
        return None
    if obj.__type__ in [context.objects.Func, context.objects.Class] or obj.__type__ in context.node_types.values():
        return context.unwrap(context.call_method(obj, "source"))
    if obj.__type__ is context.basic_types.String:
        return context.unwrap(obj)
    return context.unwrap(context.operators.repr.native(obj))

def register_context_magic(context):
    from IPython.core.magic import register_line_cell_magic
    @register_line_cell_magic
    def tc(line, cell=None):
        code = line if cell is None else cell
        try:
            ast = context.parse(code)
            obj = context.eval(ast, type="stmt")
        except context.exc.RuntimeError as exc:
            msg = context.traceback(exc)
            print(msg, file=sys.stderr)
        except:
            exc_type, exc, tb = sys.exc_info()
            msg = traceback.format_exception(exc_type, exc, tb)
            print("".join(msg), file=sys.stderr, end="")
        else:
            out = code_magic(context, obj)
            if out is not None:
                return repr_obj(out)
    class repr_obj:
        def __init__(self, msg):
            self.msg = msg
        def __repr__(self):
            return self.msg

if __name__ == "__main__":
    ipykernel.kernelapp.IPKernelApp.launch_instance(kernel_class=TwocodeKernel)
