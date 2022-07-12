import re

def parse_number(code, i):
  """
    Parse a number given as a sequence of tabs and spaces
  """

  if code[i] == '\n':
    raise Exception('Invalid number: starts with a line feed.')
  elif (code[i] == ' ' or code[i] == '\t') and code[i + 1] == '\n':
    return [0, i + 2]
  else:
    if code[i] == '\t':
      sign = -1
    elif code[i] == ' ':
      sign = 1
    else:
      raise Exception('Invalid number: unknown sign.')

    j = i + 1
    n = ''
    while code[j] != '\n':
      if code[j] == ' ':
        n += '0'
      elif code[j] == '\t':
        n += '1'
      else:
        raise Exception('Invalid number: unknown digit.')
      j += 1

    return [sign * int(n, 2), j + 1]

def parse_label(code, i):
  """
    Parse a label given as a sequence of tabs and spaces
  """

  label = ''
  while code[i] != '\n':
    if code[i] == '\t':
      label += 't'
    elif code[i] == ' ':
      label += 's'
    else:
      raise Exception('Invalid label: unknown character.')
    i += 1

  return [label, i + 1]

def code_to_instructions(code):
  """
    First pass:
      - break the code given as a sequence of tabs, spaces and line feeds into instructions
      - keep track of the labels that mark positions in the code so that both forward and backward
      references are possible
  """

  res = []
  labels = {}
  i = 0
  k = 0
  while i < len(code):
    # IMP - stack manipulation
    if code[i] == ' ':
      if code[i + 1] == ' ':
        _, end_ind = parse_number(code, i + 2)
        res.append(code[i:end_ind])
        i = end_ind
      elif code[i + 1:i + 3] in ['\t ', '\t\n']:
        _, end_ind = parse_number(code, i + 3)
        res.append(code[i:end_ind])
        i = end_ind
      elif code[i + 1:i + 3] in ['\n ', '\n\t', '\n\n']:
        res.append(code[i:i + 3])
        i += 3
      else:
        raise Exception('Invalid operation: stack manipulation.')

    # IMP - arithmetic
    elif code[i:i + 2] == '\t ':
      if code[i + 2:i + 4] in ['  ', ' \t', ' \n', '\t ', '\t\t']:
        res.append(code[i:i + 4])
      else:
        raise Exception('Invalid operation: arithmetic.')
      i += 4

    # IMP - heap access
    elif code[i:i + 2] == '\t\t':
      if code[i + 2] in [' ', '\t']:
        res.append(code[i:i + 3])
      else:
        raise Exception('Invalid operation: heap access.')
      i += 3

    # IMP - I/O
    elif code[i:i + 2] == '\t\n':
      if code[i + 2:i + 4] in ['  ', ' \t', '\t ', '\t\t']:
        res.append(code[i:i + 4])
      else:
        raise Exception('Invalid operation: I/O.')
      i += 4

    # IMP - flow control
    elif code[i] == '\n':
      if code[i + 1:i + 3] in ['  ', ' \t', ' \n', '\t ', '\t\t']:
        label, end_ind = parse_label(code, i + 3)
        res.append(code[i:end_ind])
        if code[i + 1:i + 3] == '  ':
          if label in labels:
            raise Exception('Error: repeated label.')
          else:
            labels[label] = k;
        i = end_ind
      elif code[i + 1:i + 3] in ['\t\n', '\n\n']:
        res.append(code[i:i + 3])
        i += 3
      else:
        raise Exception('Invalid operation: flow control.')
    k = k + 1

  return [res, labels]

def read_number(inp, inp_pos):
  """
    Read & parse a number from the input stream
  """
  if inp[inp_pos:].startswith('0x'):
    base = 16
    pl = 1
  elif inp[inp_pos:].startswith('0b'):
    base = 2
    pl = 2
  elif inp[inp_pos:].startswith('0'):
    base = 8
    pl = 1
  else:
    base = 10
    pl = 0

  i = inp_pos
  k = 0
  while inp[i] != '\n':
    i += 1
    k += 1

  try:
    num = int(inp[inp_pos + pl:inp_pos + k])
    return [num, inp_pos + k + 1]
  except ValueError:
    raise Exception('Error: invalid number on input stream.')

def execute_instructions(instructions, labels, inp):
  """
    Second pass: execute the instructions created in the first pass
  """

  stack = []
  heap = {}

  i = 0
  inp_pos = 0
  subroutine_from = None
  output = ''
  clean_term = False

  while i < len(instructions):
    line = instructions[i]

    # IMP - stack manipulation
    if line[0] == ' ':
      if line[1] == ' ':
        num, _ = parse_number(line, 2)
        stack.append(num)
      elif line[1:3] == '\t ':
        num, _ = parse_number(line, 3)
        if len(stack) < num + 1:
          raise Exception('Error: not enough values on the stack.')
        elif num < 0:
            raise Exception('Error: out of bounds index.')
        else:
          stack.append(stack[-num - 1])
      elif line[1:3] == '\t\n':
        num, _ = parse_number(line, 3)
        if num < 0:
            limit = len(stack) + 1
        else:
            limit = num + 2
        if len(stack) < num + 1:
          raise Exception('Error: not enough values on the stack.')
        else:
          for j in range(2, limit):
            stack[-j] = None
          stack = [el for el in stack if el]
      elif line[1:3] == '\n ':
        stack.append(stack[-1])
      elif line[1:3] == '\n\t':
        if len(stack) < 2:
          raise Exception('Error: not enough values on the stack.')
        else:
          stack[-1], stack[-2] = stack[-2], stack[-1]
      elif line[1:3] == '\n\n':
        if len(stack) == 0:
          raise Exception('Error: not enough values on the stack.')
        else:
          stack.pop()

    # IMP - arithmetic
    elif line[0:2] == '\t ':
      if len(stack) < 2:
        raise Exception('Error: not enough values on the stack.')
      else:
        a = stack.pop()
        b = stack.pop()
      if line[2:4] == '  ':
        stack.append(b + a)
      elif line[2:4] == ' \t':
        stack.append(b - a)
      elif line[2:4] == ' \n':
        stack.append(b * a)
      elif line[2:4] == '\t ':
        if a == 0:
          raise Exception('Error: division by 0.')
        else:
          stack.append(b // a)
      elif line[2:4] == '\t\t':
        if a == 0:
          raise Exception('Error: division by 0.')
        else:
          stack.append(b % a)

    # IMP - heap access
    elif line[0:2] == '\t\t':
      if line[2] == ' ':
        if len(stack) < 2:
          raise Exception('Error: not enough values on the stack.')
        else:
          a = stack.pop()
          b = stack.pop()
          heap[b] = a
      if line[2] == '\t':
        if len(stack) == 0:
          raise Exception('Error: not enough values on the stack.')
        else:
          a = stack.pop()
          if a not in heap:
            raise Exception('Error: address \'a\' does not exist in heap.')
          stack.append(heap[a])

    # IMP - I/O
    elif line[0:2] == '\t\n':
      if line[2:4] == '  ':
        if len(stack) == 0:
          raise Exception('Error: not enough values on the stack.')
        else:
          char = stack.pop()
          output += chr(char)
      elif line[2:4] == ' \t':
        if len(stack) == 0:
          raise Exception('Error: not enough values on the stack.')
        else:
          num = stack.pop()
          output += str(num)
      elif line[2:4] == '\t ':
        if len(stack) == 0:
          raise Exception('Error: not enough values on the stack.')
        else:
          a = inp[inp_pos]
          b = stack.pop()
          heap[b] = ord(a)
          inp_pos += 1
      elif line[2:4] == '\t\t':
        if len(stack) == 0:
          raise Exception('Error: not enough values on the stack.')
        else:
          a, inp_pos = read_number(inp, inp_pos)
          b = stack.pop()
          heap[b] = a

    # IMP - flow control
    elif line[0] == '\n':
      if line[1:3] in [' \t', ' \n', '\t ', '\t\t']:
        label, _ = parse_label(line, 3)
        if label not in labels:
          raise Exception('Error: label not found.')
      if line[1:3] == ' \t':
        subroutine_from = i
        i = labels[label]
      elif line[1:3] == ' \n':
        i = labels[label]
      elif line[1:3] == '\t ':
        if len(stack) == 0:
          raise Exception('Error: not enough values on the stack.')
        else:
          a = stack.pop()
          if a == 0:
            i = labels[label]
      elif line[1:3] == '\t\t':
        if len(stack) == 0:
          raise Exception('Error: not enough values on the stack.')
        else:
          a = stack.pop()
          if a < 0:
            i = labels[label]
      elif line[1:3] == '\t\n':
        i = subroutine_from
      elif line[1:3] == '\n\n':
        clean_term = True
        break

    i += 1
  
  if not clean_term:
    raise Exception('Error: unclean termination.')

  return output

def whitespace(code, inp = ''):
  code = re.sub('[^\t \n]*', '', code)

  # First pass: break code into instructions and mark label positions
  [instr, labels] = code_to_instructions(code)

  # Second pass: execute program
  return execute_instructions(instr, labels, inp)
