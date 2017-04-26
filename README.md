# Twocode
A language designed for translation, featuring intertwined compile-time and runtime execution.

### Prerequisites
* Python 3

### Installation
```bash
pip install git+https://github.com/MrCoft/twocode
twocode
```
Starts the Twocode console.  
Right now it can do print("Hello, World!").

## Key ideas
* Taking "don't repeat yourself" to the extreme, Twocode is centered around code generation.
* The dream here is to write very readable code while having control over every last instruction for difficult problems.
* Most languages expect 1-to-1 correlation between the source code and the runtime. They offer features to change this(e.g. inline), but those features are limited, not "Turing complete". Some problems can be modelled better by setting up configuration objects, then building code from them.

# Features

### Parsed, not compiled
When you define a function, its parsed AST is located in its code attribute.  
None of its attributes are unreachable. AST objects print readable code.

```python
>>> func f(n): return if n == 1: 1 else: f(n - 1) * n
>>> f(7)
5040
>>> f.code
return if n == 1:
    1
else:
    f(n - 1) * n
>>> var block = f.code.lines[0].tuple.expr.if_chain.if_blocks[0]
>>> var lit = block.block.lines[0].tuple.expr.term.literal
>>> lit.value
"1"
>>> lit.value = "5"
>>> f(7)
25200
```

## Feedback
Everything is broken, don't bother yet.  
I will provide tutorials for confusing parts of the language.

## Roadmap
This is not a toy language. I plan for it to support polished, demanding game engines.
* The interpreter is still missing major features.
* The code will be written again in Twocode and compiled in C++/Rust.
    * The project is written in Python using readable but inefficient algorithms. I estimate its parsing speed to be ~100 lines/second. This should be up to ~10,000 to be useful for large projects.  
