from intbase import InterpreterBase
from intbase import ErrorType
from bparser import BParser


class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)   # call InterpreterBase’s constructor

    def run(self, program):
        result, parsed_program = BParser.parse(program)
        if result == False:
            return  # error
        for class_def in parsed_program:
            class_name = class_def[1]
            class_methods = []
            class_fields = []
            for item in class_def[2:]:
                if item[0] == 'field':
                    field_name, initial_value = item[1:]
                    class_fields.append(FieldDefinition(
                        field_name, initial_value))
                elif item[0] == 'method':
                    method_name = item[1]
                    params = item[2]
                    statements = item[3]
                    class_methods.append(MethodDefinition(
                        method_name, params, statements))
        new_class_def = ClassDefinition(
            class_name, class_methods, class_fields, self)
        obj_def = new_class_def.instantiate_object()
        obj_def.call_method("main", [])


class FieldDefinition:
    def __init__(self, field_name, initial_value):
        self.field_name = field_name
        self.initial_value = initial_value


class MethodDefinition:
    def __init__(self, method_name, params, statements):
        self.method_name = method_name
        self.params = params
        self.statements = statements

    def get_top_level_statement(self):
        return self.statements


class ClassDefinition:
    def __init__(self, name, methods, fields, interpreter):
        self.name = name
        self.methods = methods
        self.fields = fields
        self.interpreter = interpreter

    def add_method(self, method_def):
        self.methods.append(method_def)

    def add_field(self, field_def):
        self.fields = field_def

    def instantiate_object(self):
        obj = ObjectDefinition(self.interpreter)
        for method in self.methods:
            obj.add_method(method)
        for field in self.fields:
            obj.add_field(field.field_name, field.initial_value)
        return obj


class ObjectDefinition:
    def __init__(self, interpreter):
        self.methods = {}
        self.fields = {}
        self.interpreter = interpreter

    def add_field(self, field_name, initial_value):
        self.fields[field_name] = initial_value

    def add_method(self, method):
        self.methods[method.method_name] = method

    def call_method(self, method_name, parameters):
        method = self.methods[method_name]
        statement = method.get_top_level_statement()
        result = self.__run_statement(statement, parameters)
        return result

    def __run_statement(self, statement, parameters):
        result = None
        if statement[0] == InterpreterBase.PRINT_DEF:
            result = self.__execute_print_statement(statement, parameters)
        elif statement[0] == InterpreterBase.INPUT_INT_DEF or statement[0] == InterpreterBase.INPUT_STRING_DEF:
            result = self.__execute_input_statement(statement, parameters)
        elif statement[0] == InterpreterBase.CALL_DEF:
            result = self.__execute_call_statement(statement, parameters)
        elif statement[0] == InterpreterBase.WHILE_DEF:
            result = self.__execute_while_statement(statement, parameters)
        elif statement[0] == InterpreterBase.IF_DEF:
            result = self.__execute_if_statement(statement, parameters)
        elif statement[0] == InterpreterBase.RETURN_DEF:
            result = self.__execute_return_statement(statement, parameters)
        elif statement[0] == InterpreterBase.BEGIN_DEF:
            result = self.__execute_begin_statement(statement, parameters)
        return result

    def __execute_print_statement(self, statement, parameters=None):
        expression = Expression(statement[1], self.fields, self.interpreter)
        value = expression.evaluate_expression(parameters)
        print(value)
        return value

    def __execute_input_statement(self, statement, parameters=None):
        if statement[1] in self.fields:
            self.fields[statement[1]] = input()
        return

    def __execute_call_statement(self, statement, parameters=None):
        return

    def __execute_while_statement(self, statement, parameters=None):
        return

    def __execute_if_statement(self, statement, parameters=None):
        expression = Expression(statement[1], self.fields, self.interpreter)
        condition = expression.evaluate_expression(parameters)
        if type(condition) != bool: 
            self.interpreter.error(ErrorType.TYPE_ERROR)
        if condition:
            self.__run_statement(statement[2], parameters)
        else:
            if len(statement) > 3:
                self.__run_statement(statement[3], parameters)          
        return

    def __execute_return_statement(self, statement, parameters=None):
        return

    def __execute_begin_statement(self, statement, parameters=None):
        for i in statement:
            self.__run_statement(i, parameters)
        return


class Expression:
    def __init__(self, expression, fields, interpreter):
        self.expression = expression
        self.fields = fields
        self.interpreter = interpreter

    def evaluate_expression(self, parameters=None):
        result = None
        if isinstance(self.expression, list):
            op = self.expression[0]
            if op in {'+', '-', '*', '/', '%', '<', '>', '<=', '>=', '==', '!=', '&', '|'}:
                op_func = {
                    '+': lambda x, y: x + y,
                    '-': lambda x, y: x - y,
                    '*': lambda x, y: x * y,
                    '/': lambda x, y: x / y,
                    '%': lambda x, y: x % y,
                    '<': lambda x, y: x < y,
                    '>': lambda x, y: x > y,
                    '<=': lambda x, y: x <= y,
                    '>=': lambda x, y: x >= y,
                    '==': lambda x, y: x == y,
                    '!=': lambda x, y: x != y,
                    '&': lambda x, y: x and y,
                    '|': lambda x, y: x or y,
                }[op]
                arg1 = Expression(
                    self.expression[1], self.fields, self.interpreter).evaluate_expression(parameters)
                arg2 = Expression(
                    self.expression[2], self.fields, self.interpreter).evaluate_expression(parameters)
                if type(arg1) != type(arg2):
                    self.interpreter.error(ErrorType.TYPE_ERROR)
                if op in {'+', '-', '*', '/', '%', '<', '>', '<=', '>='} and (type(arg1) == bool or type(arg2) == bool):
                    return self.interpreter.error(ErrorType.TYPE_ERROR)
                elif op in {'-', '*', '/', '%', '&', '|'} and (type(arg1) == str or type(arg2) == str):
                    return self.interpreter.error(ErrorType.TYPE_ERROR)
                elif op in {'&', '|'} and (type(arg1) == int or type(arg2) == int):
                    return self.interpreter.error(ErrorType.TYPE_ERROR)
                result = op_func(arg1, arg2)
            elif op == '!':
                arg = Expression(self.expression[1], self.fields, self.interpreter).evaluate_expression(parameters)
                return not arg
        else:
            if self.expression.isdigit():
                result = int(self.expression)
            elif self.expression == 'True':
                result = True
            elif self.expression == 'False':
                result = False
            elif isinstance(self.expression, str):
                if self.expression in self.fields:
                    result = self.fields[self.expression]
                elif self.expression == 'null':
                    result = None
                else:
                    result = str(self.expression)
        return result
    '''
            elif op == 'if':
                condition = Expression(
                    self.expr_list[1]).evaluate_expression(parameters)
                if condition:
                    return Expression(self.expr_list[2]).evaluate_expression(parameters)
                else:
                    return Expression(self.expr_list[3]).evaluate_expression(parameters)
    


print_src = ['(class main',
             ' (method main ()',
             ' (print (+ (+ 2 5) 5 ))',
             ' ) # end of method',
             ') # end of class']

test = Interpreter()
test.run(print_src)
'''
print_src = ['(class main',
             '(field x 0)',
             '(field y "test")'
             ' (method main ()',
             '(begin ',
             '(inputi x)',
             ' (print x)',
             '(inputi y)',
             ' (print y)',
             ')',
             ')'
             ')']

test = Interpreter()
test.run(print_src)
