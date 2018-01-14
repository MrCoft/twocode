import ipykernel
import ipykernel.kernelbase
import ipykernel.kernelapp
import twocode.Twocode
from twocode import Utils
import sys
import contextlib

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
        self.context = twocode.Twocode.Twocode()
        self.streams  = Utils.wrap_streams(Utils.streams_object(sys),
                                          lambda stream: Utils.Object(
                                              write=lambda s:
                                                self.send_string(s),
                                              flush=lambda: None,
                                          ))
    def send_string(self, s):
        self.send_response(self.iopub_socket, "stream", {
            "name": "stdout",
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
        data = repr(base64.b64encode(data))[2:-1]

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
            ast = context.parse(code)
            obj = context.eval(ast)
            obj = self.code_magic(obj)
            if obj is not None:
                print(obj)

        return {
            "status": "ok",
            "execution_count": self.execution_count,
            "payload": [],
            "user_expressions": {},
        }
    def code_magic(self, obj):
        context = self.context
        if obj is None or obj.__type__ is context.basic_types.Null:
            return None
        if obj.__type__ in [context.objects.Func, context.objects.Class]:
            return context.unwrap(context.call_method(obj, "source"))
        if obj.__type__ is context.basic_types.String:
            return context.unwrap(obj)
        return context.unwrap(context.operators.repr.native(obj))
    def do_shutdown(self, restart):
        del self.context
        if restart:
            self.context = twocode.Twocode.Twocode()

if __name__ == "__main__":
    ipykernel.kernelapp.IPKernelApp.launch_instance(kernel_class=TwocodeKernel)