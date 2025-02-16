'''

  myTerm.py

'''

import os


# Posix (Linux, OS X)
import sys
import termios
import atexit
from select import select
import time

class myTerm:

  def __init__(self):
    '''Creates a myTerm object that you can call to do various keyboard things.
    '''
    
    # Line Data
    self.line_queue = []
    self.line_queueing = True
    self.cur_line = ""
    self.line_count = 0
    self.input_row = 0

    # Cursor
    self.cursor_char = '_'
    self.cursor_blink_rate = .3
    self.cursor_toggle_time = 0
    self.cursor_visible = True 

    # Save the terminal settings
    self.prefix = ">: "
    self.exit_req = False
    self.fd = sys.stdin.fileno()
    self.new_term = termios.tcgetattr(self.fd)
    self.old_term = termios.tcgetattr(self.fd)
    self.rows = os.get_terminal_size().lines
    self.cols = os.get_terminal_size().columns
    
    # Output Printing
    self.output_prefix  = "[myTerm] "
    self.output_line    = ""
    self.output_row     = 2
    
    # New terminal setting unbuffered
    self.new_term[3] = (self.new_term[3] & ~termios.ICANON & ~termios.ECHO)
     
    # Support normal-terminal reset at exit
    atexit.register(self.end_term)
    
  
  def _screen_roll(self):
    '''
    '''
    self.move(0, 0)
    self._print_title()
    self.move(self.input_row + 2, 0)
    self.clear_full_line()
    print(self.prefix + self.cur_line, end="")
    self.move(self.output_row, 0)

  def _print_title(self):
    ''' Print header title
    '''
    title = " MyTerm "
    self._term_size_update()
    
    for i in range( int(self.cols/2) - int(len(title)/2) ): print("=",end="") 
    print(title, end="")
    for i in range( self.cols - int(self.cols/2) - int(len(title)/2) ): print("=",end="")


  def _term_size_update(self):
    ''' Update size of terminal
    '''
    self.rows = os.get_terminal_size().lines
    self.cols = os.get_terminal_size().columns

  def _term_size_change(self):
    ''' Returns tuple of screen row, col
    '''
    return( self.cols != os.get_terminal_size().lines or self.rows != os.get_terminal_size().columns ) 

  def _line_queue_pop(self):
    ''' Pop line queue
    '''
    ret_line = ""
    if( self.line_count != 0 ):
      ret_line = self.line_queue[0]
      self.line_queue = self.line_queue[1:]
      self.line_count -= 1
    return ret_line

  def _line_queue_push(self):
    ''' Push line to queue
    '''
    if( self.cur_line != "" ):
      self.line_count += 1
      self.line_queue.append(self.cur_line)

  def start_term(self):
    '''Start the terminal
    '''
    os.system('clear')
    self._print_title()
    print()
    termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.new_term)
    print("\x1b[?25l", end="")
    
    print(self.prefix, end="\r")
    

  def end_term(self):
    ''' Resets to normal terminal.  On Windows this is a no-op.
    '''
    print("\x1b[?25h", end="")
    termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.old_term)
    os.system('clear')


  def getch(self):
    ''' Returns a keyboard character after kbhit() has been called.
    Should not be called in the same program as getarrow().
    '''
    return sys.stdin.read(1)


  def getarrow(self):
    ''' Returns an arrow-key code after kbhit() has been called. Codes are
    0 : up
    1 : right
    2 : down
    3 : left
    Should not be called in the same program as getch().
    '''
    c = sys.stdin.read(3)[2]
    vals = [65, 67, 66, 68]

    return vals.index(ord(c.decode('utf-8')))


  def kbhit(self):
    ''' Returns True if keyboard character was hit, False otherwise.
    '''
    dr,dw,de = select([sys.stdin], [], [], 0)
    return dr != []


  def cursor_show(self):
    ''' Show cursor char
    '''
    print(self.prefix + self.cur_line, end=self.cursor_char+"\r")
    self.cursor_visible = True

  def cursor_hide(self):
    ''' Hide my terminal cursor char
    '''
    print(self.prefix + self.cur_line, end=" \r")
    self.cursor_visible = False

  def cursor_blink(self):
    ''' Evaluate blink
    '''
    if((time.time() - self.cursor_toggle_time) > self.cursor_blink_rate):
      self.move(self.input_row, 0)
      if( self.cursor_visible ): 
        self.cursor_hide()
      else:
        self.cursor_show()
        
      self.cursor_toggle_time = time.time()

  def backspace(self):
    ''' Erase char
    '''
    self.cur_line = self.cur_line[0:-1]
    print(self.prefix + self.cur_line + "   ", end="\r")

  def clear_full_line(self):
    ''' Prints blank over entire width of current terminal
    '''
    self._term_size_update()
    for i in range(self.cols):
      print(" ",end="")
    print("\r", end="")

  def clear_line(self):
    ''' Print blank spaces over current line
    '''
    print(self.prefix, end="")
    for i in range(len(self.cur_line)):
      print(" ", end="")
    print("\r", end="")

  def newline(self):
    ''' Print new line, record line to queue
    '''
    if( self.line_queueing ):
      self._line_queue_push()
    self.cursor_hide()
    
    if( False ):
      print()
    else:
      self.clear_line()
    
    self.cur_line = ""
    print(self.prefix, end="\r")

  def get_line(self):
    ''' Pop a line from the queue
    '''
    return( self._line_queue_pop() )
  
  def output(self, outstr: str):
    ''' print text to screen
    '''
    self.move(self.output_row, 0)
    #self.cursor_hide()
    #self.clear_line()
    for c in outstr:
      if( ord(c) == 10 ):
        self.output_newline()
      else:
        self.output_line += c
        print(self.output_prefix + self.output_line, end = "\r")
    
    #self.move(0, 0)
    #print("duur")
    #self.move(self.input_row, 0)

  def output_newline(self):
    ''' Handles a NL char in output string
    '''
    self._term_size_update()
    if(self.output_row < self.rows-1):
      self.output_row += 1
    else:
      self._screen_roll()
    self.output_line = ""        
    print()

  def eval(self):
    ''' Evaluate terminal
    '''
    self.move(self.input_row, 0)
    if self.kbhit():  
      c = self.getch() 
              
      if ord(c) == 27: # ESC
        self.exit_req = True
        self.cursor_hide()

      elif( ord(c) == 8 or ord(c) == 127): # ASCII Backspace or Delete
        self.backspace()

      elif ord(c) == 10: # New Line
        self.newline()

      else:
        self.cur_line += c
        print(self.prefix + self.cur_line, end="\r")

    self.cursor_blink()

    

  def move (self, y, x):
    print("\033[%d;%dH" % (y, x))

  

# Test    
"""
if __name__ == "__main__":
  i = 0
  term = myTerm()
  term.start_term()
  
  t = time.time()

  while(not term.exit_req):
    term.eval()
    if( (time.time() - t) > 1 ):
      #term.output("{}\n".format(term.output_row))
      term.output("{}\n".format(i))
      t = time.time()
      i+=1

  term.end_term()
"""


