
import time

from language import (
    lex,
    parse,
    interpret,
    compile_ast,
    run_vm
)


def timed(function, *args):
    start = time.perf_counter()

    result = function(*args)

    elapsed = (time.perf_counter() - start) * 1000

    return result, elapsed


def compare_programs(source):

    # Lexical analysis
    tokens, lex_time = timed(lex, source)

    # Parsing
    ast, parse_time = timed(parse, tokens)

    # Interpreter execution
    (interpreter_output, interpreter_vars), interpreter_time = timed(
        interpret, ast
    )

    # Compiler translation
    bytecode, translation_time = timed(
        compile_ast, ast
    )

    # Virtual machine execution
    (
        compiler_output,
        compiler_vars,
        instruction_steps
    ), vm_time = timed(run_vm, bytecode)

    return {

        "interpreter": {

            "output": interpreter_output,

            "variables": interpreter_vars,

            "timings": {

                "Lexical analysis": round(lex_time, 6),

                "Parsing": round(parse_time, 6),

                "Translation": None,

                "Execution": round(interpreter_time, 6)

            },

            "total": round(
                lex_time + parse_time + interpreter_time,
                6
            )

        },

        "compiler": {

            "output": compiler_output,

            "variables": compiler_vars,

            "bytecode": bytecode,

            "instruction_count": len(bytecode),

            "executed_instructions": instruction_steps,

            "timings": {

                "Lexical analysis": round(lex_time, 6),

                "Parsing": round(parse_time, 6),

                "Translation": round(translation_time, 6),

                "Execution": round(vm_time, 6)

            },

            "total": round(
                lex_time + parse_time + translation_time + vm_time,
                6
            )

        },

        "correct": (
            interpreter_output == compiler_output
            and interpreter_vars == compiler_vars
        )

    }

