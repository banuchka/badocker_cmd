# -*- coding: utf-8 -*-


"""badocker.badocker: provides entry point main()."""

__version__ = "0.0.1"

from cmd import Cmd
from termcolor import colored
import pycurl
import sys
import os
import json
import cStringIO
import getopt


def DoJob(command,args):
    try:
        output,domain=reqStrConstructor(command,args)

        print colored(domain,"yellow")
        for i in output.keys():
            print "{0} on {1}({2}) {3}".format(colored(i,"white"),output[i]['fqdn'],output[i]['aliases'],colored(output[i]['status'],"green"))

            if "messages" in output[i].keys():
                for level, message in output[i]['messages'].iteritems():
                    print "{0}: {1}".format(colored(level,"red"),message)
            if command in ['start', 'stop', 'restart']:
                print colored("ssh {0} '{1}'".format(output[i]['fqdn'],output[i]['commands'][command]),"red")

    except TypeError:
        print "Unknown service \"{0}\"".format(args.split(" ")[0])

def GetServicesList():
    URL='http://docker2.mlan/services_run'
    buf = cStringIO.StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, URL)
    c.setopt(c.WRITEFUNCTION, buf.write)
    c.perform()
    output = json.loads(buf.getvalue())
    buf.close()
    return sorted(output.keys())

def reqStrConstructor(command,args):

    buf = cStringIO.StringIO()
    URL='http://docker2.mlan/cmd/'+str(command)
    Domain='mlan'

    rInfo = args.split()
    if len(rInfo) > 0:
        Service = rInfo[0]
        if Service not in KnownServices:
                sys.stdout.write('\n')
                return
        else:
            URL+='/{0}'.format(Service)
            del rInfo[0]

        optlist, args = getopt.getopt(rInfo, 't:d:')
        for o, a in optlist:
            if o == '-t':
                ServiceType = a
                URL+='/{0}'.format(ServiceType)
            if o == '-d':
                Domain = a

        c = pycurl.Curl()
        c.setopt(c.URL, URL)
        c.setopt(c.WRITEFUNCTION, buf.write)
        c.perform()
        output = json.loads(buf.getvalue())
        buf.close()
        return output[Domain],Domain
    else:
        sys.stdout.write('\n')
        return

class MyPrompt(Cmd):

    def do_shell(self, args):
        """Pass command to a system shell when line begins with '!'"""
        os.system(args)

    def preloop(self):
        """Initialization before prompting user for commands.
           Despite the claims in the Cmd documentaion, Cmd.preloop() is not a stub.
        """
        Cmd.preloop(self)   ## sets up command completion
        self._hist    = []      ## No history yet
        self._locals  = {}      ## Initialize execution namespace for user
        self._globals = {}

    def do_history(self, args):
        """Print a list of commands that have been entered"""
        print self._hist

    def postcmd(self, stop, line):
        """If you want to stop the console, return something that evaluates to true.
           If you want to do some post command processing, do it here.
        """
        return stop

    def precmd(self, line):
        """ This method is called after the line has been input but before
            it has been interpreted. If you want to modifdy the input line
            before execution (for example, variable substitution) do it here.
        """
        self._hist += [ line.strip() ]
        return line

    def do_help(self, args):
        """Get help on commands
           'help' or '?' with no arguments prints a list of commands for which help is available
           'help <command>' or '? <command>' gives help on <command>
        """
        ## The only reason to define this method is for the help text in the doc string
        Cmd.do_help(self, args)

    def do_EOF(self,args):
        """Exit"""
        return self.do_quit(args)

    def emptyline(self):
        """Do nothing on empty input line"""
        pass

    def cmdloop_with_keyboard_interrupt(self):
        doQuit = False
        while doQuit != True:
            try:
                self.cmdloop()
                doQuit = True
            except KeyboardInterrupt:
                sys.stdout.write('\n')

    def do_services(self, args):
        """Show list of known services"""
        for service in KnownServices:
            print service

    def do_stop(self, args):
        """Stop service"""

        DoJob('stop',args)

    def do_status(self, args):
        """Show service status.\nstatus [service] [type]"""

        DoJob('status',args)

    def do_start(self, args):
        """Start service"""

        DoJob('start',args)

    def do_restart(self, args):
        """Start service"""

        DoJob('restart',args)

    def do_quit(self, args):
        """Quits the program."""
        print "Quitting."
        raise SystemExit


# if __name__ == '__main__':
def main():
        global KnownServices
        KnownServices = GetServicesList()
        prompt = MyPrompt()
        prompt.intro = colored("Welcome to BaDocker","red")
        prompt.prompt = colored("\nbadocker >> ","cyan")
        prompt.cmdloop_with_keyboard_interrupt()