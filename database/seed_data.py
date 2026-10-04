"""
database/seed_data.py
---------------------
Database seeding script for QuizMaster AI.

Populates a fresh or existing database with 110 accurate, standard technical and general knowledge questions:
    - 30 Python questions
    - 20 C++ questions
    - 20 Java questions
    - 20 DBMS questions
    - 10 Computer Networks questions
    - 10 General Knowledge questions

Features:
    - Distributed across Easy, Medium, and Hard difficulty levels.
    - Idempotent execution (skips questions that already exist in the database by question_text).
    - Includes option_a, option_b, option_c, option_d, correct_answer ('A','B','C','D'), explanation, category, topic, difficulty.
"""

import os
import sys
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.database import DatabaseManager
from database.schema import seed_default_admin

QUESTIONS_DATA: List[Dict[str, Any]] = [
    # =========================================================================
    # 1. PYTHON (30 Questions)
    # =========================================================================
    # --- Python Easy (10 Qs) ---
    {
        "category": "Python", "topic": "Basics", "difficulty": "easy",
        "question_text": "Which of the following is the correct file extension for Python files?",
        "option_a": ".pyt", "option_b": ".py", "option_c": ".pt", "option_d": ".python",
        "correct_answer": "B", "explanation": "Python source code files traditionally use the '.py' extension."
    },
    {
        "category": "Python", "topic": "Variables", "difficulty": "easy",
        "question_text": "Which built-in Python function returns the data type of an object?",
        "option_a": "type()", "option_b": "typeof()", "option_c": "datatype()", "option_d": "kind()",
        "correct_answer": "A", "explanation": "The type() function returns the class/type of the given object."
    },
    {
        "category": "Python", "topic": "Data Types", "difficulty": "easy",
        "question_text": "Which data type in Python is immutable?",
        "option_a": "List", "option_b": "Dictionary", "option_c": "Set", "option_d": "Tuple",
        "correct_answer": "D", "explanation": "Tuples are immutable sequences in Python; their elements cannot be changed after creation."
    },
    {
        "category": "Python", "topic": "Syntax", "difficulty": "easy",
        "question_text": "How do you insert a single-line comment in Python code?",
        "option_a": "// comment", "option_b": "/* comment */", "option_c": "# comment", "option_d": "<!-- comment -->",
        "correct_answer": "C", "explanation": "Python uses the '#' symbol to start single-line comments."
    },
    {
        "category": "Python", "topic": "Strings", "difficulty": "easy",
        "question_text": "What is the output of len('Hello World') in Python?",
        "option_a": "10", "option_b": "11", "option_c": "12", "option_d": "9",
        "correct_answer": "B", "explanation": "'Hello World' contains 11 characters, including 10 letters and 1 space."
    },
    {
        "category": "Python", "topic": "Lists", "difficulty": "easy",
        "question_text": "Which method is used to add an item to the end of a list in Python?",
        "option_a": "push()", "option_b": "add()", "option_c": "append()", "option_d": "insert()",
        "correct_answer": "C", "explanation": "list.append(item) adds a single element to the end of a list."
    },
    {
        "category": "Python", "topic": "Operators", "difficulty": "easy",
        "question_text": "Which operator is used for exponentiation (power) in Python?",
        "option_a": "^", "option_b": "**", "option_c": "^^", "option_d": "pow",
        "correct_answer": "B", "explanation": "The '**' operator calculates exponentiation, e.g., 2 ** 3 equals 8."
    },
    {
        "category": "Python", "topic": "Control Flow", "difficulty": "easy",
        "question_text": "Which keyword is used to create a loop in Python?",
        "option_a": "for", "option_b": "loop", "option_c": "repeat", "option_d": "iterate",
        "correct_answer": "A", "explanation": "Python provides 'for' and 'while' keywords for loop control."
    },
    {
        "category": "Python", "topic": "Functions", "difficulty": "easy",
        "question_text": "Which keyword is used to define a function in Python?",
        "option_a": "function", "option_b": "def", "option_c": "func", "option_d": "define",
        "correct_answer": "B", "explanation": "The 'def' keyword is used to declare user-defined functions in Python."
    },
    {
        "category": "Python", "topic": "Booleans", "difficulty": "easy",
        "question_text": "What is the boolean evaluation of bool([]) in Python?",
        "option_a": "True", "option_b": "False", "option_c": "None", "option_d": "Error",
        "correct_answer": "B", "explanation": "Empty collections such as empty lists [] evaluate to False in boolean context."
    },

    # --- Python Medium (10 Qs) ---
    {
        "category": "Python", "topic": "Lists", "difficulty": "medium",
        "question_text": "What is the output of print([1, 2, 3] * 2) in Python?",
        "option_a": "[2, 4, 6]", "option_b": "[1, 2, 3, 1, 2, 3]", "option_c": "[1, 2, 3, 2]", "option_d": "TypeError",
        "correct_answer": "B", "explanation": "Multiplying a sequence by an integer repeats the sequence contents."
    },
    {
        "category": "Python", "topic": "Dictionaries", "difficulty": "medium",
        "question_text": "Which dictionary method returns a default value if the specified key is not present?",
        "option_a": "fetch()", "option_b": "get()", "option_c": "find()", "option_d": "lookup()",
        "correct_answer": "B", "explanation": "dict.get(key, default) returns default if the key is missing rather than raising KeyError."
    },
    {
        "category": "Python", "topic": "OOP", "difficulty": "medium",
        "question_text": "What is the purpose of the '__init__' method in Python classes?",
        "option_a": "To initialize module imports", "option_b": "To initialize newly created instance attributes (constructor)", "option_c": "To destroy object instances", "option_d": "To make class abstract",
        "correct_answer": "B", "explanation": "__init__ serves as the instance initializer (constructor) when a class instance is created."
    },
    {
        "category": "Python", "topic": "List Comprehension", "difficulty": "medium",
        "question_text": "What is the result of [x for x in range(5) if x % 2 == 0]?",
        "option_a": "[0, 2, 4]", "option_b": "[1, 3]", "option_c": "[0, 1, 2, 3, 4]", "option_d": "[2, 4]",
        "correct_answer": "A", "explanation": "The list comprehension filters even numbers from range 0 to 4 inclusive."
    },
    {
        "category": "Python", "topic": "Scope", "difficulty": "medium",
        "question_text": "Which keyword allows modifying a variable outside the current scope in Python?",
        "option_a": "extern", "option_b": "global", "option_c": "outer", "option_d": "static",
        "correct_answer": "B", "explanation": "The 'global' (and 'nonlocal') keyword grants write access to outer scope variables."
    },
    {
        "category": "Python", "topic": "Exceptions", "difficulty": "medium",
        "question_text": "Which block in Python always executes after try-except regardless of whether an exception occurred?",
        "option_a": "else", "option_b": "catch", "option_c": "finally", "option_d": "complete",
        "correct_answer": "C", "explanation": "The 'finally' block executes cleanup operations regardless of try success or exception."
    },
    {
        "category": "Python", "topic": "Modules", "difficulty": "medium",
        "question_text": "What does __name__ evaluate to when a Python script is executed directly?",
        "option_a": "'__script__'", "option_b": "'__main__'", "option_c": "'__root__'", "option_d": "None",
        "correct_answer": "B", "explanation": "When executed directly, Python sets top-level script __name__ to '__main__'."
    },
    {
        "category": "Python", "topic": "Strings", "difficulty": "medium",
        "question_text": "What is the output of 'python'[::-1] in Python?",
        "option_a": "'python'", "option_b": "'nohtyp'", "option_c": "'p'", "option_d": "'n'",
        "correct_answer": "B", "explanation": "Slice step of -1 reverses the string sequence."
    },
    {
        "category": "Python", "topic": "Sets", "difficulty": "medium",
        "question_text": "Which set operation returns elements present in set A but not in set B?",
        "option_a": "union()", "option_b": "intersection()", "option_c": "difference()", "option_d": "symmetric_difference()",
        "correct_answer": "C", "explanation": "A.difference(B) or (A - B) produces set elements in A not present in B."
    },
    {
        "category": "Python", "topic": "Functions", "difficulty": "medium",
        "question_text": "What does *args allow in a Python function definition?",
        "option_a": "Keyword arguments only", "option_b": "Variable number of positional arguments", "option_c": "Required named parameters", "option_d": "Pointer reference",
        "correct_answer": "B", "explanation": "*args packs arbitrary positional arguments into a tuple."
    },

    # --- Python Hard (10 Qs) ---
    {
        "category": "Python", "topic": "Decorators", "difficulty": "hard",
        "question_text": "What is a Python decorator?",
        "option_a": "A GUI widget", "option_b": "A function that takes another function as argument and extends its behavior", "option_c": "A syntax validator", "option_d": "A class destructor",
        "correct_answer": "B", "explanation": "Decorators modify or extend function behavior dynamically via higher-order functions."
    },
    {
        "category": "Python", "topic": "Generators", "difficulty": "hard",
        "question_text": "Which keyword is used in generator functions to yield a sequence of values lazily?",
        "option_a": "return", "option_b": "yield", "option_c": "emit", "option_d": "produce",
        "correct_answer": "B", "explanation": "'yield' pauses generator function state and produces an iterated value lazily."
    },
    {
        "category": "Python", "topic": "GIL", "difficulty": "hard",
        "question_text": "What is the Global Interpreter Lock (GIL) in CPython?",
        "option_a": "A security encryption mechanism", "option_b": "A mutex that allows only one thread to execute Python bytecode at a time", "option_c": "A database lock", "option_d": "A garbage collection algorithm",
        "correct_answer": "B", "explanation": "GIL is CPython's execution mutex preventing concurrent multi-threaded bytecode execution."
    },
    {
        "category": "Python", "topic": "OOP", "difficulty": "hard",
        "question_text": "What is the Method Resolution Order (MRO) algorithm used in Python 3 for multiple inheritance?",
        "option_a": "Depth-First Search", "option_b": "Breadth-First Search", "option_c": "C3 Linearization", "option_d": "Dijkstra's Algorithm",
        "correct_answer": "C", "explanation": "Python 3 uses C3 Linearization to compute deterministic MRO across class inheritance hierarchies."
    },
    {
        "category": "Python", "topic": "Memory", "difficulty": "hard",
        "question_text": "Which module in Python provides low-level control over the reference-counting Garbage Collector?",
        "option_a": "sys", "option_b": "gc", "option_c": "mem", "option_d": "os",
        "correct_answer": "B", "explanation": "The 'gc' module enables programmatic configuration and invocation of Python's cyclic garbage collector."
    },
    {
        "category": "Python", "topic": "Dunder Methods", "difficulty": "hard",
        "question_text": "Which dunder method must a class implement to support context management with the 'with' statement?",
        "option_a": "__open__ and __close__", "option_b": "__enter__ and __exit__", "option_c": "__start__ and __stop__", "option_d": "__init__ and __del__",
        "correct_answer": "B", "explanation": "Context managers implement __enter__() and __exit__() for setup and teardown resource allocation."
    },
    {
        "category": "Python", "topic": "Metaclasses", "difficulty": "hard",
        "question_text": "What is the base class from which all Python metaclasses inherit?",
        "option_a": "object", "option_b": "type", "option_c": "meta", "option_d": "Class",
        "correct_answer": "B", "explanation": "Metaclasses inherit from 'type' in Python to control class creation behavior."
    },
    {
        "category": "Python", "topic": "Concurrency", "difficulty": "hard",
        "question_text": "Which standard library module provides coroutine-based cooperative multitasking in Python?",
        "option_a": "threading", "option_b": "multiprocessing", "option_c": "asyncio", "option_d": "concurrent",
        "correct_answer": "C", "explanation": "asyncio provides event loop infrastructure for async/await coroutine concurrency."
    },
    {
        "category": "Python", "topic": "Descriptors", "difficulty": "hard",
        "question_text": "Which trio of methods defines the Python Descriptor protocol?",
        "option_a": "__get__, __set__, __delete__", "option_b": "__read__, __write__, __erase__", "option_c": "__fetch__, __store__, __drop__", "option_d": "__load__, __save__, __destroy__",
        "correct_answer": "A", "explanation": "The descriptor protocol consists of __get__(), __set__(), and __delete__() method descriptors."
    },
    {
        "category": "Python", "topic": "Internals", "difficulty": "hard",
        "question_text": "What does sys.setrecursionlimit() control in Python?",
        "option_a": "Maximum size of lists", "option_b": "Maximum depth of the Python call stack", "option_c": "Number of threads", "option_d": "Garbage collection threshold",
        "correct_answer": "B", "explanation": "sys.setrecursionlimit() sets the maximum depth limit of the call stack to prevent stack overflow."
    },

    # =========================================================================
    # 2. C++ (20 Questions)
    # =========================================================================
    # --- C++ Easy (7 Qs) ---
    {
        "category": "C++", "topic": "Basics", "difficulty": "easy",
        "question_text": "Which header file must be included for standard input and output streams in C++?",
        "option_a": "<stdio.h>", "option_b": "<iostream>", "option_c": "<conio.h>", "option_d": "<stdlib.h>",
        "correct_answer": "B", "explanation": "<iostream> defines std::cin, std::cout, and stream I/O objects."
    },
    {
        "category": "C++", "topic": "Syntax", "difficulty": "easy",
        "question_text": "Which character is used to terminate statements in C++?",
        "option_a": ":", "option_b": ".", "option_c": ";", "option_d": ",",
        "correct_answer": "C", "explanation": "Semicolons (;) are required statement terminators in C++."
    },
    {
        "category": "C++", "topic": "Data Types", "difficulty": "easy",
        "question_text": "Which C++ data type is used to store boolean true/false values?",
        "option_a": "boolean", "option_b": "bool", "option_c": "bit", "option_d": "int",
        "correct_answer": "B", "explanation": "'bool' is the primitive boolean keyword in C++."
    },
    {
        "category": "C++", "topic": "Pointers", "difficulty": "easy",
        "question_text": "Which symbol is used to declare a pointer variable in C++?",
        "option_a": "&", "option_b": "*", "option_c": "#", "option_d": "@",
        "correct_answer": "B", "explanation": "The asterisk (*) denotes pointer declaration and dereferencing."
    },
    {
        "category": "C++", "topic": "Memory", "difficulty": "easy",
        "question_text": "Which operator is used to allocate memory dynamically in C++?",
        "option_a": "malloc", "option_b": "new", "option_c": "alloc", "option_d": "create",
        "correct_answer": "B", "explanation": "The 'new' operator allocates heap memory and calls class constructors in C++."
    },
    {
        "category": "C++", "topic": "OOP", "difficulty": "easy",
        "question_text": "What is the default access specifier for members of a C++ class?",
        "option_a": "public", "option_b": "protected", "option_c": "private", "option_d": "friend",
        "correct_answer": "C", "explanation": "Class members are 'private' by default in C++ (unlike structs which default to public)."
    },
    {
        "category": "C++", "topic": "Control Flow", "difficulty": "easy",
        "question_text": "Which operator is the scope resolution operator in C++?",
        "option_a": "->", "option_b": "::", "option_c": ".", "option_d": "=>",
        "correct_answer": "B", "explanation": ":: is the scope resolution operator used to qualify namespace or class scope."
    },

    # --- C++ Medium (7 Qs) ---
    {
        "category": "C++", "topic": "OOP", "difficulty": "medium",
        "question_text": "What is a virtual function in C++?",
        "option_a": "A function with no implementation", "option_b": "A member function expected to be overridden in derived classes for dynamic dispatch", "option_c": "A static global function", "option_d": "An inline function",
        "correct_answer": "B", "explanation": "Virtual functions enable runtime polymorphism / dynamic binding in derived class hierarchies."
    },
    {
        "category": "C++", "topic": "Destructors", "difficulty": "medium",
        "question_text": "How is a class destructor named in C++?",
        "option_a": "class_name()", "option_b": "~class_name()", "option_c": "delete_class()", "option_d": "!class_name()",
        "correct_answer": "B", "explanation": "Destructors use the class name prefixed with a tilde (~)."
    },
    {
        "category": "C++", "topic": "STL", "difficulty": "medium",
        "question_text": "Which STL container in C++ represents a dynamic sequence array with fast random access?",
        "option_a": "std::list", "option_b": "std::vector", "option_c": "std::map", "option_d": "std::set",
        "correct_answer": "B", "explanation": "std::vector manages dynamic contiguous array storage with O(1) random access."
    },
    {
        "category": "C++", "topic": "References", "difficulty": "medium",
        "question_text": "How does a reference variable differ from a pointer in C++?",
        "option_a": "References cannot be null and cannot be rebound to another variable", "option_b": "Pointers cannot hold memory addresses", "option_c": "References require pointer arithmetic", "option_d": "They are identical in all aspects",
        "correct_answer": "A", "explanation": "References act as alias names, cannot be null, and must be bound upon initialization."
    },
    {
        "category": "C++", "topic": "Templates", "difficulty": "medium",
        "question_text": "Which keyword is used to declare generic template functions or classes in C++?",
        "option_a": "generic", "option_b": "template", "option_c": "typename_all", "option_d": "type",
        "correct_answer": "B", "explanation": "The 'template' keyword introduces template parameters for compile-time generic code."
    },
    {
        "category": "C++", "topic": "Constness", "difficulty": "medium",
        "question_text": "What does declaring a C++ member function as 'const' guarantee?",
        "option_a": "It cannot accept arguments", "option_b": "It will not modify any non-mutable data members of the calling object", "option_c": "It can only be called once", "option_d": "It returns a constant pointer",
        "correct_answer": "B", "explanation": "Const member functions promise not to alter object member state."
    },
    {
        "category": "C++", "topic": "Exceptions", "difficulty": "medium",
        "question_text": "Which keyword is used to throw an exception in C++?",
        "option_a": "raise", "option_b": "throw", "option_c": "except", "option_d": "dispatch",
        "correct_answer": "B", "explanation": "'throw' signals an exceptional error condition to caller catch handlers."
    },

    # --- C++ Hard (6 Qs) ---
    {
        "category": "C++", "topic": "RAII", "difficulty": "hard",
        "question_text": "What does RAII stand for in modern C++ design?",
        "option_a": "Resource Allocation Is Instant", "option_b": "Resource Acquisition Is Initialization", "option_c": "Runtime Array Invalidation Interface", "option_d": "Reference Assignment In Inheritance",
        "correct_answer": "B", "explanation": "RAII ties resource lifecycle management (memory, file handles) to object scope lifetime."
    },
    {
        "category": "C++", "topic": "Smart Pointers", "difficulty": "hard",
        "question_text": "Which smart pointer type in C++11 enforces exclusive single ownership of a heap resource?",
        "option_a": "std::shared_ptr", "option_b": "std::weak_ptr", "option_c": "std::unique_ptr", "option_d": "std::auto_ptr",
        "correct_answer": "C", "explanation": "std::unique_ptr ensures single ownership without reference counting overhead."
    },
    {
        "category": "C++", "topic": "Move Semantics", "difficulty": "hard",
        "question_text": "Which utility function converts an lvalue to an rvalue reference to enable move semantics in C++11?",
        "option_a": "std::cast()", "option_b": "std::move()", "option_c": "std::forward()", "option_d": "std::transfer()",
        "correct_answer": "B", "explanation": "std::move() unconditionally casts its argument to an rvalue reference."
    },
    {
        "category": "C++", "topic": "Virtual Table", "difficulty": "hard",
        "question_text": "What is the function of the vtable (virtual table) in C++ compilers?",
        "option_a": "To store static global variables", "option_b": "To resolve dynamic dispatch function calls at runtime for virtual functions", "option_c": "To optimize template instantiation", "option_d": "To handle stack allocation",
        "correct_answer": "B", "explanation": "vtable is a runtime lookup array of pointers to virtual member functions for class instances."
    },
    {
        "category": "C++", "topic": "Pure Virtual", "difficulty": "hard",
        "question_text": "What makes a C++ class an abstract base class?",
        "option_a": "Declaring all members static", "option_b": "Containing at least one pure virtual function (= 0)", "option_c": "Having a private constructor", "option_d": "Inheriting from std::exception",
        "correct_answer": "B", "explanation": "Pure virtual functions (virtual ret func() = 0;) render a class abstract and non-instantiable."
    },
    {
        "category": "C++", "topic": "Constexpr", "difficulty": "hard",
        "question_text": "What does the 'constexpr' specifier enforce in C++11?",
        "option_a": "Evaluation of expression/function at compile-time", "option_b": "Execution on GPU hardware", "option_c": "Multithreaded thread safety", "option_d": "Inline assembly generation",
        "correct_answer": "A", "explanation": "constexpr mandates that expressions can be evaluated at compile-time when constant arguments are supplied."
    },

    # =========================================================================
    # 3. JAVA (20 Questions)
    # =========================================================================
    # --- Java Easy (7 Qs) ---
    {
        "category": "Java", "topic": "Basics", "difficulty": "easy",
        "question_text": "What is the extension of compiled Java bytecode files?",
        "option_a": ".java", "option_b": ".class", "option_c": ".exe", "option_d": ".jar",
        "correct_answer": "B", "explanation": "The Java compiler (javac) compiles source .java files into .class bytecode files."
    },
    {
        "category": "Java", "topic": "JVM", "difficulty": "easy",
        "question_text": "What does JVM stand for?",
        "option_a": "Java Virtual Machine", "option_b": "Java Variable Manager", "option_c": "Joint Visual Module", "option_d": "Java Vector Method",
        "correct_answer": "A", "explanation": "JVM is the Java Virtual Machine that executes bytecode on host platforms."
    },
    {
        "category": "Java", "topic": "Entry Point", "difficulty": "easy",
        "question_text": "Which method signature is the required main entry point of a standalone Java application?",
        "option_a": "public void main(String args[])", "option_b": "public static void main(String[] args)", "option_c": "static void main()", "option_d": "public int main(String[] args)",
        "correct_answer": "B", "explanation": "public static void main(String[] args) is the standard application launch method."
    },
    {
        "category": "Java", "topic": "Primitives", "difficulty": "easy",
        "question_text": "Which of the following is NOT a primitive data type in Java?",
        "option_a": "int", "option_b": "boolean", "option_c": "String", "option_d": "double",
        "correct_answer": "C", "explanation": "String is an object reference class in java.lang, not a primitive type."
    },
    {
        "category": "Java", "topic": "OOP", "difficulty": "easy",
        "question_text": "Which keyword is used to inherit a class in Java?",
        "option_a": "implements", "option_b": "extends", "option_c": "inherits", "option_d": "using",
        "correct_answer": "B", "explanation": "'extends' specifies single class inheritance in Java."
    },
    {
        "category": "Java", "topic": "Interfaces", "difficulty": "easy",
        "question_text": "Which keyword is used by a Java class to implement an interface?",
        "option_a": "extends", "option_b": "implements", "option_c": "interface", "option_d": "uses",
        "correct_answer": "B", "explanation": "'implements' binds contract interfaces to concrete class implementations."
    },
    {
        "category": "Java", "topic": "Memory", "difficulty": "easy",
        "question_text": "How is automatic memory deallocation performed in Java?",
        "option_a": "Manual free() calls", "option_b": "Garbage Collection (GC)", "option_c": "Destructors", "option_d": "Compiler inline deletes",
        "correct_answer": "B", "explanation": "Java's automatic Garbage Collector reclaims unreferenced heap memory."
    },

    # --- Java Medium (7 Qs) ---
    {
        "category": "Java", "topic": "Strings", "difficulty": "medium",
        "question_text": "Why are String objects immutable in Java?",
        "option_a": "To optimize String Pool caching, security, and thread safety", "option_b": "To save CPU register space", "option_c": "Java lacks pointers", "option_d": "Because strings use primitive arrays",
        "correct_answer": "A", "explanation": "String immutability enables String Intern Pool optimization, hash key stability, and thread safety."
    },
    {
        "category": "Java", "topic": "Collections", "difficulty": "medium",
        "question_text": "What is the key difference between ArrayList and LinkedList in Java?",
        "option_a": "ArrayList is indexed contiguous memory; LinkedList uses doubly-linked nodes", "option_b": "LinkedList does not allow duplicate items", "option_c": "ArrayList cannot hold objects", "option_d": "They are identical in memory storage",
        "correct_answer": "A", "explanation": "ArrayList uses continuous backing arrays (O(1) lookup); LinkedList uses doubly-linked nodes (O(1) insertion)."
    },
    {
        "category": "Java", "topic": "Keywords", "difficulty": "medium",
        "question_text": "What does the 'final' keyword signify when applied to a Java class?",
        "option_a": "The class cannot be instantiated", "option_b": "The class cannot be subclassed/inherited", "option_c": "The class has no methods", "option_d": "The class is private",
        "correct_answer": "B", "explanation": "'final' on a class prevents further sub-classing or extension."
    },
    {
        "category": "Java", "topic": "Exceptions", "difficulty": "medium",
        "question_text": "What is the parent superclass of all Exception and Error classes in Java?",
        "option_a": "java.lang.Object", "option_b": "java.lang.Throwable", "option_c": "java.lang.Exception", "option_d": "java.lang.Runtime",
        "correct_answer": "B", "explanation": "Throwable is the root class of Java's exception hierarchy."
    },
    {
        "category": "Java", "topic": "Multithreading", "difficulty": "medium",
        "question_text": "Which keyword is used to synchronize concurrent access to critical sections in Java?",
        "option_a": "lock", "option_b": "synchronized", "option_c": "atomic", "option_d": "threadsafe",
        "correct_answer": "B", "explanation": "'synchronized' acquires object intrinsic monitor locks for thread safety."
    },
    {
        "category": "Java", "topic": "Polymorphism", "difficulty": "medium",
        "question_text": "What is method overloading in Java?",
        "option_a": "Defining methods with same name but different parameter list signatures in same class", "option_b": "Overriding parent class method in child class", "option_c": "Calling a method recursively", "option_d": "Passing generic parameters",
        "correct_answer": "A", "explanation": "Overloading provides compile-time polymorphism via distinct method signatures."
    },
    {
        "category": "Java", "topic": "OOP", "difficulty": "medium",
        "question_text": "What does the 'super' keyword reference in Java?",
        "option_a": "The current class instance", "option_b": "The immediate parent (superclass) object", "option_c": "The outer class instance", "option_d": "The global namespace",
        "correct_answer": "B", "explanation": "'super' explicitly calls parent class constructors or overridden members."
    },

    # --- Java Hard (6 Qs) ---
    {
        "category": "Java", "topic": "JVM Internals", "difficulty": "hard",
        "question_text": "Which memory area in JVM stores loaded class structures, constant pools, and static variables in Java 8+?",
        "option_a": "PermGen", "option_b": "Metaspace", "option_c": "Young Generation", "option_d": "Thread Stack",
        "correct_answer": "B", "explanation": "Java 8 replaced PermGen with native-memory Metaspace for class metadata allocation."
    },
    {
        "category": "Java", "topic": "Generics", "difficulty": "hard",
        "question_text": "What is Type Erasure in Java Generics?",
        "option_a": "Removing duplicate array items at runtime", "option_b": "Compiler process that replaces generic type parameters with bounds/Object during compilation", "option_c": "Deleting unused class objects", "option_d": "Garbage collection of generic lists",
        "correct_answer": "B", "explanation": "Type erasure removes generic type checks at compile-time to maintain backwards compatibility."
    },
    {
        "category": "Java", "topic": "Concurrency", "difficulty": "hard",
        "question_text": "What does the 'volatile' keyword ensure in Java memory concurrency?",
        "option_a": "Mutual exclusion locking", "option_b": "Direct CPU cache flush / visibility guarantee across threads without locking", "option_c": "Atomic 64-bit operations", "option_d": "Preventing garbage collection",
        "correct_answer": "B", "explanation": "'volatile' guarantees variable read/write visibility directly from main memory."
    },
    {
        "category": "Java", "topic": "Streams API", "difficulty": "hard",
        "question_text": "In Java 8 Streams, what is the difference between intermediate and terminal operations?",
        "option_a": "Intermediate operations are lazy and return a new Stream; terminal operations produce a non-Stream result", "option_b": "Intermediate operations execute immediately", "option_c": "Terminal operations can be chained continuously", "option_d": "They have no performance difference",
        "correct_answer": "A", "explanation": "Intermediate operations (filter/map) build stream pipelines lazily until triggered by a terminal operation (collect/forEach)."
    },
    {
        "category": "Java", "topic": "ClassLoaders", "difficulty": "hard",
        "question_text": "What is the parent-delegation mechanism in Java ClassLoaders?",
        "option_a": "ClassLoaders always load classes locally first", "option_b": "A ClassLoader delegates loading to its parent before searching locally", "option_c": "ClassLoaders prevent package imports", "option_d": "Classes are loaded in alphabetical order",
        "correct_answer": "B", "explanation": "Delegation pattern ensures core runtime classes are safely loaded by Bootstrap ClassLoader first."
    },
    {
        "category": "Java", "topic": "Memory", "difficulty": "hard",
        "question_text": "What causes a PhantomReference to be enqueued in Java?",
        "option_a": "When an object becomes unreachable and after its finalize method has been called", "option_b": "When heap space exceeds 90%", "option_c": "When a thread terminates", "option_d": "On out of memory error",
        "correct_answer": "A", "explanation": "Phantom references allow post-mortem cleanup after objects are finalized."
    },

    # =========================================================================
    # 4. DBMS (20 Questions)
    # =========================================================================
    # --- DBMS Easy (7 Qs) ---
    {
        "category": "DBMS", "topic": "SQL", "difficulty": "easy",
        "question_text": "Which SQL command is used to retrieve data from a database table?",
        "option_a": "GET", "option_b": "FETCH", "option_c": "SELECT", "option_d": "EXTRACT",
        "correct_answer": "C", "explanation": "SELECT statements query and retrieve records from relational tables."
    },
    {
        "category": "DBMS", "topic": "Keys", "difficulty": "easy",
        "question_text": "What is a Primary Key in a database table?",
        "option_a": "A key containing duplicate values", "option_b": "A column or set of columns that uniquely identifies each row in a table", "option_c": "A foreign reference column", "option_d": "An optional index key",
        "correct_answer": "B", "explanation": "Primary keys enforce entity integrity by requiring unique, non-null row identifiers."
    },
    {
        "category": "DBMS", "topic": "SQL", "difficulty": "easy",
        "question_text": "Which clause is used to filter records returned by a SELECT query?",
        "option_a": "GROUP BY", "option_b": "WHERE", "option_c": "ORDER BY", "option_d": "HAVING",
        "correct_answer": "B", "explanation": "WHERE filters source rows matching search conditions before aggregation."
    },
    {
        "category": "DBMS", "topic": "DDL", "difficulty": "easy",
        "question_text": "Which SQL command is used to add a new record to a table?",
        "option_a": "ADD", "option_b": "INSERT INTO", "option_c": "CREATE", "option_d": "UPDATE",
        "correct_answer": "B", "explanation": "INSERT INTO creates new rows in target relational database tables."
    },
    {
        "category": "DBMS", "topic": "Database Types", "difficulty": "easy",
        "question_text": "What does RDBMS stand for?",
        "option_a": "Relational Database Management System", "option_b": "Rapid Database Method System", "option_c": "Remote Data Base Main System", "option_d": "Recursive Data Binary Storage",
        "correct_answer": "A", "explanation": "RDBMS manages relational tables based on relational algebra concepts."
    },
    {
        "category": "DBMS", "topic": "Keys", "difficulty": "easy",
        "question_text": "What is a Foreign Key?",
        "option_a": "A key imported from another vendor database", "option_b": "A field in one table referencing the Primary Key of another table", "option_c": "A secondary index", "option_d": "A composite key",
        "correct_answer": "B", "explanation": "Foreign keys establish referential integrity between related relational tables."
    },
    {
        "category": "DBMS", "topic": "SQL", "difficulty": "easy",
        "question_text": "Which SQL keyword is used to remove a table structure entirely from the database?",
        "option_a": "DELETE", "option_b": "TRUNCATE", "option_c": "DROP", "option_d": "REMOVE",
        "correct_answer": "C", "explanation": "DROP TABLE deletes both table schema metadata and all stored rows."
    },

    # --- DBMS Medium (7 Qs) ---
    {
        "category": "DBMS", "topic": "ACID", "difficulty": "medium",
        "question_text": "What does ACID stand for in database transaction management?",
        "option_a": "Atomicity, Consistency, Isolation, Durability", "option_b": "Accuracy, Control, Integration, Data", "option_c": "Access, Concurrency, Indexing, Delivery", "option_d": "Array, Column, Index, Directory",
        "correct_answer": "A", "explanation": "ACID properties ensure reliable database transaction execution guarantees."
    },
    {
        "category": "DBMS", "topic": "Normalization", "difficulty": "medium",
        "question_text": "What requirement must a table satisfy to be in First Normal Form (1NF)?",
        "option_a": "No partial functional dependencies", "option_b": "All column values must be atomic (indivisible) scalar values", "option_c": "No transitive dependencies", "option_d": "Must have composite keys",
        "correct_answer": "B", "explanation": "1NF requires atomic values and removal of repeating groups or arrays."
    },
    {
        "category": "DBMS", "topic": "Joins", "difficulty": "medium",
        "question_text": "What does an INNER JOIN return in SQL?",
        "option_a": "All rows from left table regardless of match", "option_b": "Only matching rows present in both join tables", "option_c": "Cartesian product of all rows", "option_d": "Non-matching rows",
        "correct_answer": "B", "explanation": "INNER JOIN filters records having matching values in both joining tables."
    },
    {
        "category": "DBMS", "topic": "Normalization", "difficulty": "medium",
        "question_text": "Which normal form deals with removing transitive dependencies?",
        "option_a": "1NF", "option_b": "2NF", "option_c": "3NF", "option_d": "BCNF",
        "correct_answer": "C", "explanation": "3NF requires that no non-prime attribute is transitively dependent on the primary key."
    },
    {
        "category": "DBMS", "topic": "Indexing", "difficulty": "medium",
        "question_text": "What is the primary benefit of creating an Index on a database column?",
        "option_a": "Reduces disk space usage", "option_b": "Speeds up data retrieval query performance", "option_c": "Ensures transaction rollback", "option_d": "Prevents table locks",
        "correct_answer": "B", "explanation": "Indexes provide fast search lookup access paths (B-Trees) to speed up SELECT queries."
    },
    {
        "category": "DBMS", "topic": "SQL", "difficulty": "medium",
        "question_text": "What is the difference between WHERE and HAVING clauses in SQL?",
        "option_a": "WHERE filters individual rows before grouping; HAVING filters group aggregations", "option_b": "HAVING is faster than WHERE", "option_c": "WHERE works only on numbers", "option_d": "They are identical in usage",
        "correct_answer": "A", "explanation": "WHERE filters rows before aggregation; HAVING filters aggregate results produced by GROUP BY."
    },
    {
        "category": "DBMS", "topic": "Transactions", "difficulty": "medium",
        "question_text": "Which SQL command permanently saves all changes made during the current transaction?",
        "option_a": "SAVEPOINT", "option_b": "ROLLBACK", "option_c": "COMMIT", "option_d": "CHECKPOINT",
        "correct_answer": "C", "explanation": "COMMIT persists pending transactional modifications permanently to database disk."
    },

    # --- DBMS Hard (6 Qs) ---
    {
        "category": "DBMS", "topic": "Concurrency Control", "difficulty": "hard",
        "question_text": "What is a Dirty Read phenomenon in database concurrency isolation levels?",
        "option_a": "Reading data that has been modified by an uncommitted transaction", "option_b": "Reading corrupt disk sectors", "option_c": "Re-reading data that changed between queries", "option_d": "Reading deleted tables",
        "correct_answer": "A", "explanation": "Dirty reads occur when a transaction reads uncommitted changes written by another concurrent transaction."
    },
    {
        "category": "DBMS", "topic": "Concurrency Control", "difficulty": "hard",
        "question_text": "Which isolation level prevents Dirty Reads, Non-repeatable Reads, and Phantom Reads?",
        "option_a": "Read Uncommitted", "option_b": "Read Committed", "option_c": "Repeatable Read", "option_d": "Serializable",
        "correct_answer": "D", "explanation": "Serializable isolation guarantees strict sequential execution semantics without concurrency anomalies."
    },
    {
        "category": "DBMS", "topic": "Indexing", "difficulty": "hard",
        "question_text": "Why are B+ Trees preferred over Binary Search Trees for disk-based database indexing?",
        "option_a": "High fan-out maximizes node storage per disk block, minimizing disk I/O reads", "option_b": "B+ Trees use less RAM", "option_c": "Binary trees cannot store strings", "option_d": "B+ Trees eliminate locking",
        "correct_answer": "A", "explanation": "High branching fan-out keeps tree depth small, matching physical block page I/O sizes."
    },
    {
        "category": "DBMS", "topic": "Transactions", "difficulty": "hard",
        "question_text": "What is the Two-Phase Locking (2PL) protocol used for?",
        "option_a": "To ensure serializability of concurrent transaction execution", "option_b": "To compress backup files", "option_c": "To convert 2NF to 3NF", "option_d": "To encrypt passwords",
        "correct_answer": "A", "explanation": "2PL (Growing phase & Shrinking phase) guarantees conflict serializability in transaction schedules."
    },
    {
        "category": "DBMS", "topic": "Recovery", "difficulty": "hard",
        "question_text": "What does the Write-Ahead Logging (WAL) protocol require?",
        "option_a": "Log records must be written to stable storage before corresponding data modifications are committed to database disk", "option_b": "Data must be backed up daily", "option_c": "Queries must be logged before execution", "option_d": "Tables must be locked before logging",
        "correct_answer": "A", "explanation": "WAL guarantees Durability by writing log changes to disk prior to modifying actual data pages."
    },
    {
        "category": "DBMS", "topic": "Normalization", "difficulty": "hard",
        "question_text": "How does Boyce-Codd Normal Form (BCNF) strictness compare to 3NF?",
        "option_a": "BCNF requires every determinant to be a superkey", "option_b": "BCNF permits transitive dependencies", "option_c": "BCNF applies only to NoSQL databases", "option_d": "3NF is stricter than BCNF",
        "correct_answer": "A", "explanation": "BCNF strictly requires that for every functional dependency X -> Y, X must be a superkey."
    },

    # =========================================================================
    # 5. COMPUTER NETWORKS (10 Questions)
    # =========================================================================
    # --- Networks Easy (4 Qs) ---
    {
        "category": "Computer Networks", "topic": "OSI Model", "difficulty": "easy",
        "question_text": "How many layers are defined in the standard OSI Reference Model?",
        "option_a": "4", "option_b": "5", "option_c": "7", "option_d": "6",
        "correct_answer": "C", "explanation": "The OSI model consists of 7 layers: Physical, Data Link, Network, Transport, Session, Presentation, Application."
    },
    {
        "category": "Computer Networks", "topic": "Protocols", "difficulty": "easy",
        "question_text": "Which protocol is used to resolve IP addresses to MAC physical addresses?",
        "option_a": "DHCP", "option_b": "ARP", "option_c": "DNS", "option_d": "ICMP",
        "correct_answer": "B", "explanation": "ARP (Address Resolution Protocol) resolves IPv4 addresses to physical MAC network interface addresses."
    },
    {
        "category": "Computer Networks", "topic": "Protocols", "difficulty": "easy",
        "question_text": "What is the primary function of the Domain Name System (DNS)?",
        "option_a": "To encrypt web traffic", "option_b": "To translate human-readable domain names to IP addresses", "option_c": "To assign IP addresses dynamically", "option_d": "To route packets across routers",
        "correct_answer": "B", "explanation": "DNS translates domain names (e.g. google.com) into numerical IP addresses."
    },
    {
        "category": "Computer Networks", "topic": "IP Addressing", "difficulty": "easy",
        "question_text": "What is the standard length of an IPv4 address in bits?",
        "option_a": "32 bits", "option_b": "64 bits", "option_c": "128 bits", "option_d": "16 bits",
        "correct_answer": "A", "explanation": "IPv4 uses 32-bit address identifiers (represented as four 8-bit octets)."
    },

    # --- Networks Medium (3 Qs) ---
    {
        "category": "Computer Networks", "topic": "Transport Layer", "difficulty": "medium",
        "question_text": "What are the core differences between TCP and UDP protocols?",
        "option_a": "TCP is connection-oriented and reliable; UDP is connectionless and lightweight", "option_b": "UDP guarantees packet delivery order", "option_c": "TCP operates at Network layer; UDP at Data Link layer", "option_d": "They are identical in transport behavior",
        "correct_answer": "A", "explanation": "TCP provides reliable, sequenced byte streams; UDP provides fast, unacknowledged datagram transport."
    },
    {
        "category": "Computer Networks", "topic": "Subnetting", "difficulty": "medium",
        "question_text": "How many usable host IP addresses are available in a /24 IPv4 subnet?",
        "option_a": "256", "option_b": "254", "option_c": "255", "option_d": "128",
        "correct_answer": "B", "explanation": "A /24 subnet has 256 addresses minus 2 reserved addresses (Network ID and Broadcast ID) = 254 hosts."
    },
    {
        "category": "Computer Networks", "topic": "HTTP", "difficulty": "medium",
        "question_text": "Which TCP port is used by default for secure HTTPS communication?",
        "option_a": "80", "option_b": "8080", "option_c": "443", "option_d": "22",
        "correct_answer": "C", "explanation": "Port 443 is the standard default port for HTTPS encrypted Web traffic."
    },

    # --- Networks Hard (3 Qs) ---
    {
        "category": "Computer Networks", "topic": "TCP Congestion Control", "difficulty": "hard",
        "question_text": "What is the purpose of the TCP Three-Way Handshake?",
        "option_a": "To negotiate encryption keys", "option_b": "To establish connection state and synchronize sequence numbers (SYN, SYN-ACK, ACK)", "option_c": "To measure bandwidth latency", "option_d": "To close sockets",
        "correct_answer": "B", "explanation": "The 3-way handshake synchronizes sequence numbers between client and server prior to data transfer."
    },
    {
        "category": "Computer Networks", "topic": "Routing", "difficulty": "hard",
        "question_text": "Which routing algorithm is used by the Border Gateway Protocol (BGP) for inter-domain routing?",
        "option_a": "Distance Vector", "option_b": "Link State", "option_c": "Path Vector", "option_d": "Flooding",
        "correct_answer": "C", "explanation": "BGP uses Path Vector routing to advertise autonomous system (AS) path attributes."
    },
    {
        "category": "Computer Networks", "topic": "Security", "difficulty": "hard",
        "question_text": "How does Diffie-Hellman Key Exchange operate securely over untrusted channels?",
        "option_a": "Using symmetric block ciphers", "option_b": "Allowing two parties to establish a shared secret key based on modular exponentiation discrete logarithms", "option_c": "Using preshared password lists", "option_d": "Relying on DNSSEC",
        "correct_answer": "B", "explanation": "Diffie-Hellman relies on the computational difficulty of discrete logarithms in finite fields."
    },

    # =========================================================================
    # 6. GENERAL KNOWLEDGE (10 Questions)
    # =========================================================================
    # --- General Knowledge Easy (4 Qs) ---
    {
        "category": "General Knowledge", "topic": "Geography", "difficulty": "easy",
        "question_text": "What is the capital city of France?",
        "option_a": "Berlin", "option_b": "Madrid", "option_c": "Paris", "option_d": "Rome",
        "correct_answer": "C", "explanation": "Paris is the capital and most populous city of France."
    },
    {
        "category": "General Knowledge", "topic": "Science", "difficulty": "easy",
        "question_text": "What is the chemical symbol for Gold?",
        "option_a": "Ag", "option_b": "Au", "option_c": "Fe", "option_d": "Pb",
        "correct_answer": "B", "explanation": "Au (from Latin 'aurum') is the chemical element symbol for Gold."
    },
    {
        "category": "General Knowledge", "topic": "Space", "difficulty": "easy",
        "question_text": "Which planet in our solar system is known as the Red Planet?",
        "option_a": "Venus", "option_b": "Mars", "option_c": "Jupiter", "option_d": "Saturn",
        "correct_answer": "B", "explanation": "Mars is called the Red Planet due to reddish iron oxide on its surface."
    },
    {
        "category": "General Knowledge", "topic": "History", "difficulty": "easy",
        "question_text": "Who is credited with inventing the telephone?",
        "option_a": "Thomas Edison", "option_b": "Alexander Graham Bell", "option_c": "Nikola Tesla", "option_d": "Guglielmo Marconi",
        "correct_answer": "B", "explanation": "Alexander Graham Bell was awarded the first US patent for the telephone in 1876."
    },

    # --- General Knowledge Medium (3 Qs) ---
    {
        "category": "General Knowledge", "topic": "Science", "difficulty": "medium",
        "question_text": "What is the hardest naturally occurring substance on Earth?",
        "option_a": "Quartz", "option_b": "Diamond", "option_c": "Titanium", "option_d": "Graphene",
        "correct_answer": "B", "explanation": "Diamond is the hardest natural mineral, scoring 10 on the Mohs hardness scale."
    },
    {
        "category": "General Knowledge", "topic": "Computer History", "difficulty": "medium",
        "question_text": "Who is widely recognized as the world's first computer programmer?",
        "option_a": "Alan Turing", "option_b": "Ada Lovelace", "option_c": "Grace Hopper", "option_d": "Charles Babbage",
        "correct_answer": "B", "explanation": "Ada Lovelace published the first algorithm intended for execution on Babbage's Analytical Engine."
    },
    {
        "category": "General Knowledge", "topic": "Geography", "difficulty": "medium",
        "question_text": "Which is the largest ocean on Earth by surface area?",
        "option_a": "Atlantic Ocean", "option_b": "Indian Ocean", "option_c": "Pacific Ocean", "option_d": "Arctic Ocean",
        "correct_answer": "C", "explanation": "The Pacific Ocean is the largest and deepest of Earth's oceanic divisions."
    },

    # --- General Knowledge Hard (3 Qs) ---
    {
        "category": "General Knowledge", "topic": "Physics", "difficulty": "hard",
        "question_text": "What fundamental constant of nature is denoted by the letter 'c' in physics equations?",
        "option_a": "Gravitational constant", "option_b": "Speed of light in vacuum", "option_c": "Planck's constant", "option_d": "Boltzmann constant",
        "correct_answer": "B", "explanation": "The constant 'c' represents the speed of light in vacuum (~299,792,458 m/s)."
    },
    {
        "category": "General Knowledge", "topic": "Computer Science History", "difficulty": "hard",
        "question_text": "In what year was the World Wide Web invented by Tim Berners-Lee at CERN?",
        "option_a": "1975", "option_b": "1989", "option_c": "1995", "option_d": "2000",
        "correct_answer": "B", "explanation": "Tim Berners-Lee proposed the information management system that became the World Wide Web in 1989."
    },
    {
        "category": "General Knowledge", "topic": "Biology", "difficulty": "hard",
        "question_text": "Which cell organelle is responsible for cellular respiration and ATP energy production?",
        "option_a": "Ribosome", "option_b": "Mitochondria", "option_c": "Golgi Apparatus", "option_d": "Endoplasmic Reticulum",
        "correct_answer": "B", "explanation": "Mitochondria generate most of the chemical energy needed to power cell biochemical reactions."
    }
]


def seed_database(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Idempotently seeds the database schema, default admin user, and 110 standard questions.
    Returns summary stats dict of total, added, and skipped questions.
    """
    db_mgr = DatabaseManager(db_path) if db_path else DatabaseManager()
    db_mgr.initialize_database()

    # 1. Seed Default Admin User
    seed_default_admin(db_mgr)

    added_count = 0
    skipped_count = 0

    print("\n============================================================")
    print("🌱 QuizMaster AI — Database Seeding Script")
    print("============================================================")

    # 2. Seed Questions Idempotently
    for q in QUESTIONS_DATA:
        # Check if question text already exists in database
        existing = db_mgr.fetch_one(
            "SELECT id FROM questions WHERE question_text = ?;",
            (q["question_text"],)
        )
        if existing:
            skipped_count += 1
            continue

        # Insert question
        db_mgr.execute_query(
            """
            INSERT INTO questions (category, topic, difficulty, question_text, option_a, option_b, option_c, option_d, correct_answer, explanation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                q["category"],
                q["topic"],
                q["difficulty"],
                q["question_text"],
                q["option_a"],
                q["option_b"],
                q["option_c"],
                q["option_d"],
                q["correct_answer"],
                q["explanation"]
            )
        )
        added_count += 1

    summary = {
        "total_seed_items": len(QUESTIONS_DATA),
        "added": added_count,
        "skipped": skipped_count
    }

    print(f"[DB Seed Result] Added: {added_count} | Skipped (Already Existed): {skipped_count} | Total Items: {len(QUESTIONS_DATA)}")
    print("============================================================\n")

    return summary


if __name__ == "__main__":
    seed_database()
