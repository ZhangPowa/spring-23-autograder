from intbase import InterpreterBase
from intbase import ErrorType
from bparser import BParser


class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)   # call InterpreterBase’s constructor
        self.class_defs = {}

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
                    for i in class_fields:
                        if (i.field_name == field_name):
                            self.error(ErrorType.NAME_ERROR)
                    class_fields.append(FieldDefinition(
                        field_name, initial_value))
                elif item[0] == 'method':
                    method_name = item[1]
                    params = item[2]
                    statement = item[3]
                    for i in class_methods:
                        if (i.method_name == method_name):
                            self.error(ErrorType.NAME_ERROR)
                    class_methods.append(MethodDefinition(
                        method_name, params, statement))
            new_class_def = ClassDefinition(
                class_name, class_methods, class_fields, self)
            if (class_name in self.class_defs):
                self.error(ErrorType.TYPE_ERROR)
            else:
                self.class_defs[class_name] = new_class_def
        main_class = self.class_defs["main"]
        main_class.instantiate_object().call_method("main", [])

    def get_class_def(self):
        return self.class_defs


class FieldDefinition:
    def __init__(self, field_name, initial_value):
        self.field_name = field_name
        self.initial_value = initial_value


class MethodDefinition:
    def __init__(self, method_name, params, statement):
        self.method_name = method_name
        self.params = params
        self.statement = statement

    def get_top_level_statement(self):
        return self.statement


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
        self.parameters = {}
        self.interpreter = interpreter

    def add_field(self, field_name, initial_value):
        expression = Expression(
            initial_value, self, self.interpreter)
        value = expression.evaluate_expression()
        self.fields[field_name] = value

    def add_method(self, method):
        self.methods[method.method_name] = method

    def call_method(self, method_name, parameters):
        method = self.methods[method_name]
        statement = method.get_top_level_statement()
        if len(method.params) != len(parameters):
            self.interpreter.error(ErrorType.TYPE_ERROR)
        else:
            for i in range(0, len(method.params)):
                self.parameters[method.params[i]] = parameters[i]
        result = self.__run_statement(statement)
        return result

    def __run_statement(self, statement):
        result = None
        if statement[0] == InterpreterBase.PRINT_DEF:
            result = self.__execute_print_statement(statement)
        elif statement[0] == InterpreterBase.INPUT_INT_DEF or statement[0] == InterpreterBase.INPUT_STRING_DEF:
            result = self.__execute_input_statement(statement)
        elif statement[0] == InterpreterBase.CALL_DEF:
            result = self.__execute_call_statement(statement)
        elif statement[0] == InterpreterBase.WHILE_DEF:
            result = self.__execute_while_statement(statement)
        elif statement[0] == InterpreterBase.IF_DEF:
            result = self.__execute_if_statement(statement)
        elif statement[0] == InterpreterBase.RETURN_DEF:
            result = self.__execute_return_statement(statement)
        elif statement[0] == InterpreterBase.BEGIN_DEF:
            result = self.__execute_begin_statement(statement)
        elif statement[0] == InterpreterBase.SET_DEF:
            result = self.__execute_set_statement(statement)
        return result

    def __execute_print_statement(self, statement):
        output = ''
        for i in statement[1:]:
            expression = Expression(
                i, self, self.interpreter)
            value = expression.evaluate_expression()
            if value is True:
                value = 'true'
            elif value is False:
                value = 'false'
            elif isinstance(value, str):
                if value.startswith("\""):
                    value = value[1:len(value)-1]
            elif isinstance(value, int):
                value = str(value)
            output = output + value
        self.interpreter.output(output)
        return

    def __execute_input_statement(self, statement):
        expression = Expression(
            self.interpreter.get_input(), self, self.interpreter)
        value = expression.evaluate_expression()
        if statement[1] in self.fields:
            self.fields[statement[1]] = value
        return

    def __execute_call_statement(self, statement):
        value = None
        values = []
        for i in statement[3:]:
            param = Expression(
                i, self, self.interpreter)
            values.append(param.evaluate_expression())

        if statement[1] == 'me':
            if statement[2] in self.methods:
                if (self.call_method(statement[2], parameters=values)) is not None:
                    value = self.call_method(statement[2], parameters=values)
            else:
                self.interpreter.error(ErrorType.NAME_ERROR)
        else:
            expression = Expression(
                statement[1], self, self.interpreter)
            class_name = expression.evaluate_expression()
            if statement[2] in class_name.methods:
                if (class_name.call_method(statement[2], parameters=values)) is not None:
                    value = class_name.call_method(
                        statement[2], parameters=values)
            else:
                self.interpreter.error(ErrorType.NAME_ERROR)
        return value

    def __execute_while_statement(self, statement):
        result = None
        condition = (Expression(
            statement[1], self, self.interpreter).evaluate_expression())
        if type(condition) != bool:
            self.interpreter.error(ErrorType.TYPE_ERROR)
        if condition:
            result = self.__run_statement(statement[2])
            self.__execute_while_statement(statement)
        else:
            return result

    def __execute_if_statement(self, statement):
        result = None
        expression = Expression(
            statement[1], self, self.interpreter)
        condition = expression.evaluate_expression()
        if type(condition) != bool:
            self.interpreter.error(ErrorType.TYPE_ERROR)
        if condition:
            result = self.__run_statement(statement[2])
        else:
            if len(statement) > 3:
                result = self.__run_statement(statement[3])
        return result

    def __execute_return_statement(self, statement):
        if (len(statement)) > 1:
            expression = Expression(
                statement[1], self, self.interpreter)
            value = expression.evaluate_expression()
            return value
        else:
            return

    def __execute_begin_statement(self, statement):
        for i in statement[1:]:
            self.__run_statement(i)
        return

    def __execute_set_statement(self, statement):
        expression = Expression(
            statement[2], self, self.interpreter)
        value = expression.evaluate_expression()
        if statement[1] in self.fields:
            self.fields[statement[1]] = value
        else:
            self.interpreter.error(ErrorType.NAME_ERROR)
        return


class Expression():
    def __init__(self, expression, object, interpreter):
        self.expression = expression
        self.object = object
        self.interpreter = interpreter

    def evaluate_expression(self):
        result = None
        if isinstance(self.expression, list):
            op = self.expression[0]
            if op in {'+', '-', '*', '/', '%', '<', '>', '<=', '>=', '==', '!=', '&', '|'}:
                op_func = {
                    '+': lambda x, y: x + y,
                    '-': lambda x, y: x - y,
                    '*': lambda x, y: x * y,
                    '/': lambda x, y: round(x / y),
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
                    self.expression[1], self.object, self.interpreter).evaluate_expression()
                arg2 = Expression(
                    self.expression[2],  self.object, self.interpreter).evaluate_expression()
                if (arg1 == 'null' or arg2 == 'null'):
                    if arg1 == 'null' and arg2 == 'null':
                        if op == '==':
                            return True
                        else:
                            return False
                    elif self.expression[1] not in self.object.fields and self.expression[2] not in self.object.fields:
                        self.interpreter.error(ErrorType.TYPE_ERROR)
                elif type(arg1) != type(arg2):
                    self.interpreter.error(ErrorType.TYPE_ERROR)
                elif op in {'+', '-', '*', '/', '%', '<', '>', '<=', '>='} and (type(arg1) == bool or type(arg2) == bool):
                    return self.interpreter.error(ErrorType.TYPE_ERROR)
                elif op in {'-', '*', '/', '%', '&', '|'} and (type(arg1) == str or type(arg2) == str):
                    return self.interpreter.error(ErrorType.TYPE_ERROR)
                elif op in {'&', '|'} and (type(arg1) == int or type(arg2) == int):
                    return self.interpreter.error(ErrorType.TYPE_ERROR)
                elif op in {'+', '-', '*', '/', '%', '<', '>', '<=', '>=', '&', '|'} and (arg1 == 'null' or arg2 == 'null'):
                    return self.interpreter.error(ErrorType.TYPE_ERROR)
                result = op_func(arg1, arg2)
            elif op == '!':
                arg = Expression(
                    self.expression[1],  self.object, self.interpreter).evaluate_expression()
                return not arg
            elif op == 'new':
                class_defs = self.interpreter.get_class_def()
                if self.expression[1] in class_defs:
                    new_obj = class_defs[self.expression[1]
                                         ].instantiate_object()
                else:
                    self.interpreter.error(ErrorType.TYPE_ERROR)
                result = new_obj
            elif op == 'call':
                value = self.object._ObjectDefinition__execute_call_statement(
                    self.expression)
                result = value
        else:
            if self.expression.isdigit() or self.expression[1:].isdigit():
                result = int(self.expression)
            elif self.expression == 'true':
                result = True
            elif self.expression == 'false':
                result = False
            elif isinstance(self.expression, str):
                if self.expression in self.object.fields:
                    result = self.object.fields[self.expression]
                    if isinstance(result, str):
                        if self.expression.isdigit() or self.expression[1:].isdigit():
                            result = int(self.expression)
                elif self.expression in self.object.parameters:
                    result = self.object.parameters[self.expression]
                else:
                    result = self.expression.replace('"', '')
        return result
    '''
          

print_src = ['(class main',
             ' (method main ()',
             ' (print (+ (+ 2 5) 5 ))',
             ' ) # end of method',
             ') # end of class']

test = Interpreter()
test.run(print_src)

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

print_src = ['(class main',
             '(field x 5)',
             '(field y "test")',
             '(method main ()',
             '(begin',
             '(set x "def")',
             '(print x)',
             '(set x true)',
             '(print x)',
             ')',
             ')',
             ')']
print_src = ['(class main',
             '(field x 0)',
             '(field y "test")'
             ' (method main ()',
             '(print "here\'s a result " (* 3 5) " and here\'s a boolean" true)',
             ')'
             ')']



print_src = ['(class main',
             '(field other null)',
             '(method main ()',
             '(begin',
             '(set other (new other_class))',
             '(call other foo 5 6)))',
             ')',
             '(class other_class',
             '(field a 10)',
             '(method foo (q r) (print (+ a (+ q r))))',
             ')']
['(class main',
             '(method fact (n)',
             '(if (== n 1)',
             '(return 1)',
             '(return (* n (call me fact (- n 1))))',
             ')',
             ')',
             '(method main () (print (call me fact 5)))',
             ')']
['(class main',
             '(field x 0)',
             '(method main ()',
             '(begin',
             '(inputi x)',
             '(while (> x 0)',
             '(begin',
             '(print "x is " x)',
             '(set x (- x 1))',
             '))))'
             ')']

(class main
  (method fact (n)
   (if (== n 1)
     (return 1)
     (return (* n (call me fact (- n 1))))
   )
  )
  (method main () (print (call me fact 5)))
)
(class main',
             '(field other null)',
             '(field result 0)',
             '(method main ()',
             '(begin',
             '(call me foo 10 20) ',
             '(set other (new other_class))',
             '(call other foo 5 6)',
             '(print "square: " (call other square 10))))',
             '(method foo (a b)',
             '(print a b)))'
             '(class other_class',
             '(method foo (q r) (print q r))',
             '(method square (q) (return (* q q))))'

             ['(class main',
             '(method fact (n)',
             '(if (== n 1)',
             '(return 1)',
             '(return (* n (call me fact (- n 1))))',
             ')) ',
             '(method main () (print (call me fact 2))))',
             ]





print_src = ['(class main',
             '(field x -45)',
             '(method main()',
             '(print (/ 40 x)',
             ')))']
test = Interpreter()
test.run(print_src)
'''
