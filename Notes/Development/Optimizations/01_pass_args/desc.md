Testing setup and basic JS generation, finished in 68.5s.
Twocode spends 68% of time in `Object.pass_args`.

Func code in `context/Objects.py`:
```
@create
def Func(this, args=None, return_type=None, code=None, native=None, sign=None):
    if args is None: args = []
    this.scope = None
    this.pass_args("this sign".split())
    if sign:
        context.setup.sign(this, sign)
```
This is because of its use of `inspect` which accesses the filesystem. 46% of time is spent in `nt.stat`.

New Func:
```
@create
def Func(this, args=None, return_type=None, code=None, native=None, sign=None):
    if args is None: args = []
    this.scope = None
    this.args = args
    this.return_type = return_type
    this.code = code
    this.native = native
    if sign:
        context.setup.sign(this, sign)
```
Finished in 20.6s, a speedup factor of 3.33.
