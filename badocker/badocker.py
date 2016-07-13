# -*- coding: utf-8 -*-


"""badocker.badocker: provides entry point main()."""

__version__ = "0.0.2"

from cmd import Cmd
from termcolor import colored
import pycurl
import sys
import os
import json
import cStringIO
import getopt
from urllib import urlencode

global KnownDomains
KnownDomains=['mlan', 'ulan', 'd3','d4']

def DoJob(command,args):
    try:
        output,domain,warning_messages,error_messages=reqStrConstructor(command,args)

        print colored(domain,"yellow")
        if len(error_messages) > 0:
            for msg in error_messages:
                for level, message in msg.iteritems():
                    print "{0}: {1}".format(colored(level,"red"),message)
        if len(warning_messages) > 0:
            for msg in warning_messages:
                for level, message in msg.iteritems():
                    print "{0}: {1}".format(colored(level,"red"),message)
        if len(error_messages) > 0:
            return
        print
        for i in output.keys():
            if output[i]['aliases'] is not None:
                print "{0} on {1}({2}) {3}".format(colored(i,"white"),output[i]['fqdn'],output[i]['aliases'],colored(output[i]['status'],"green"))
            else:
                print "{0} on {1} {2}".format(colored(i,"white"),output[i]['fqdn'],colored(output[i]['status'],"green"))

            if "messages" in output[i].keys():
                if len(output[i]['messages']) > 0:
                    for msg in output[i]['messages']:
                        for level, message in msg.iteritems():
                            print "{0}: {1}".format(colored(level,"red"),message)
            if command in ['start', 'stop', 'restart', 'deploy']:
                print colored("ssh {0} '{1}'".format(output[i]['fqdn'],output[i]['commands'][command]),"red")
                if command == 'deploy':
                    os.system("ssh {0} '{1}'".format(output[i]['fqdn'],output[i]['commands'][command]))
            # elif command in ['deploy']:
            #     print colored("'{0}'".format(output[i]),"red")
            elif command in ['update']:
                #for separate use
                # upd = output[i]['commands'][command].split(";")
                # for cmd in upd:
                #     print colored("ssh {0} '{1}'".format(output[i]['fqdn'],cmd),"red")
                # print output[i]['commands'][command].replace(";","\n")
                print colored("ssh {0} '{1}'".format(output[i]['fqdn'],output[i]['commands'][command].replace(';','; \\\n')),"red")

    except TypeError as e:
        pass
        # print "Unknown service \"{0}\", {1}".format(args.split(" ")[0], e)
def bdsm_sync():
        URL='http://badocker.mlan/services/bdsm_sync'
        buf = cStringIO.StringIO()
        c = pycurl.Curl()
        c.setopt(c.URL, URL)
        c.setopt(c.WRITEFUNCTION, buf.write)
        c.perform()
        output = json.loads(buf.getvalue())
        buf.close()
        if len(output['Added Types']) > 0:
            print "Added types from BDSM to badocker: \"{0}\"".format((", ".join(output['Added Types'])))
        if len(output['Deleted Types']) >0:
            print "Deleted types from badocker: \"{0}\"".format((", ".join(output['Deleted Types'])))
        if len(output['Deleted from bdsm']) >0:
            print "There are services in badocker, but not in BDSM: \"{0}\"".format((", ".join(output['Deleted from bdsm'])))
        if len(output['Not in badocker']) >0:
            print "There are services in in BDSM, but not in badocker: \"{0}\"".format((", ".join(output['Not in badocker'])))
        return

def GetServicesList():
    URL='http://docker2.mlan/services_run'
    buf = cStringIO.StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, URL)
    c.setopt(c.WRITEFUNCTION, buf.write)
    c.perform()
    output = json.loads(buf.getvalue())
    buf.close()
    # print output
    return output

def reqStrConstructor(command,args):

    buf = cStringIO.StringIO()
    URL='http://docker2.mlan/cmd/'+str(command)
    Domain='mlan'
    ReqVersion = None
    nodes = None

    rInfo = args.split()
    if len(rInfo) > 0:
        Service = rInfo[0]
        if Service not in KnownServices:
                sys.stdout.write('Unknown Service {0}. Use "services" command to view the list of known services\n'.format(Service))
                return
        else:
            URL+='/{0}'.format(Service)
            del rInfo[0]

        Types = GetServicesList()[Service]['known_types']

        optlist, args = getopt.getopt(rInfo, 't:d:v:n:')
        for o, a in optlist:
            if o == '-t':
                ServiceType = a
                if a in Types:
                    URL+='/{0}'.format(ServiceType)
                else:
                    if command not in ['deploy']:
                        sys.stdout.write('Unknown type "{0}" for service "{1}".\n'.format(ServiceType, Service))
                        return
                    #     URL+='/{0}'.format(ServiceType)
                    # else:

                    # return
            if o == '-d':
                if a in KnownDomains:
                    Domain = a
            if o == '-v':
                ReqVersion = a
            if o == '-n':
                nodes = a

        c = pycurl.Curl()
        c.setopt(c.URL, URL)
        c.setopt(c.WRITEFUNCTION, buf.write)
        if command in ['update', 'deploy']:
            post_data = {}
            if not ReqVersion is None:
                post_data.update({'version': ReqVersion})
                # postfields = urlencode(post_data)
                # c.setopt(c.POSTFIELDS, postfields)
            if not nodes is None:
                post_data.update({'nodes': nodes})
            try: ServiceType
            except: ServiceType = None

            if not ServiceType is None:
                post_data.update({'type': ServiceType})
            if not Domain is None:
                post_data.update({'platform': Domain})

            if len(post_data) > 0:
                postfields = urlencode(post_data)
                c.setopt(c.POSTFIELDS, postfields)

        c.perform()
        # print buf.getvalue()
        output = json.loads(buf.getvalue())
        buf.close()
        try:
            return output[Domain]["Service"],Domain,output[Domain]['_WARNINGS'],output[Domain]['_ERRORS']
        except KeyError:
            try:
                sys.stdout.write('Can\'t find type "{0}" for domain "{1}"\n'.format(ServiceType, Domain))
            except UnboundLocalError:
                sys.stdout.write('Can\'t find running "{0}" on domain "{1}"\n'.format(Service, Domain))
            return

    else:
        sys.stdout.write('\n')
        return

class BadockerPrompt(Cmd):

    def do_shell(self, args):
        """Pass command to a system shell(local) when line begins with '!'"""
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
        """Get List of services here in BaDocker
           'services' with no arguments prints a list of services for which badocker is available
           'services <service>' gives a list of types for <service>
        """
        if len(args)> 0:
            service = args.split()[0]
            if service in KnownServices:
                print "Known types for service \"{0}\": {1}".format(service,", ".join(GetServicesList()[service]['known_types']))
            else:
                print "Unknown service \"{0}\"".format(service)
        else:
            for service in KnownServices:
                print service

    def do_stop(self, args):
        """Stop service
           Usage: stop SERVICE [OPTION]
           Options
           -d   set domain (default: mlan)
           -t   service type
        """

        DoJob('stop',args)

    def do_status(self, args):
        """Show status of service
           Usage: status SERVICE [OPTION]
           Options
           -d   set domain (default: mlan)
           -t   service type
        """

        DoJob('status',args)

    def do_start(self, args):
        """Start service
           Usage: start SERVICE [OPTION]
           Options
           -d   set domain (default: mlan)
           -t   service type
        """

        DoJob('start',args)

    def do_deploy(self, args):
        """Deploy service
           Usage: deploy SERVICE -t TYPE [-d domain] [-v VERSION] [-n NODES]
           Options
           -t   service type
           -d   set domain (default: mlan)
           -v   service version. If not available – version from BDSM will be in use
           -n   service nodes to deploy. If not present it will find node from BDSM
        """

        DoJob('deploy',args)

    def do_restart(self, args):
        """Restart service
           Usage: restart SERVICE [OPTION]
           Options
           -d   set domain (default: mlan)
           -t   service type
        """
        DoJob('restart',args)

    def do_update(self, args):
        """Update service
           Usage: update SERVICE [OPTION]
           Options
           -d   set domain (default: mlan)
           -t   service type
           -v   version (default: version from BDSM will be in use)
        """

        DoJob('update',args)

    def do_bdsm_sync(self,args):
        """Sync services and types from BDSM
           Usage: bdsm_sync
        """
        bdsm_sync()
        # print output


    def do_quit(self, args):
        """Quits the program."""
        print "Quitting."
        raise SystemExit


# if __name__ == '__main__':
def main():
        global KnownServices
        KnownServices = sorted(GetServicesList().keys())
        prompt = BadockerPrompt()
        # prompt.intro = colored("Welcome to BaDocker","red")
        print colored("Welcome to BaDocker","red")
        print colored("I'm going to sync services and types from BDSM. There are results:\n","white")
        bdsm_sync()
        prompt.prompt = colored("\nbadocker >> ","cyan")
        prompt.cmdloop_with_keyboard_interrupt()