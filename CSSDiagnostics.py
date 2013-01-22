'''
Created on Oct 24, 2012 for Vernier Software and Technology

@author: mbergman at x-consulting dot net


Copyright (C) 2012 Matthew Bergman

Permission is hereby granted, free of charge, to any person obtaining a copy of this software 
and associated documentation files (the "Software"), to deal in the Software without restriction, 
including without limitation the rights to use, copy, modify, merge, publish, distribute, 
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is 
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or 
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING 
BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, 
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

'''

import socket
import re
from ipcalc import Network,IP
import select
import pybonjour
import struct
import subprocess
import gtk, gobject
import sys
import ipconfig
from datetime import datetime
import os

class NetworkedDevice:
    ip = ""
    netmask = ""
    route = ""
    ssid = ""
    datashare_port = 0
    
    def __init__(self):
        pass
    
def get_local_ip():
    return socket.gethostbyname(socket.gethostname())

class CSSDiagnostics:

    def die_nicely(self, arg):
        try:
            self.logfile.close()
        except:
            pass
        gtk.main_quit()

    def log(self, message):
        if self.logfile:
            self.logfile.write(message)
            self.logfile.write("\n")
    
    def __init__(self):
        self.datashare = NetworkedDevice()
        self.local = NetworkedDevice()
    
        self.regtype  = "_vernier-data._tcp"
        self.timeout  = 5
        self.resolved = []
        self.found_bonjour_hosts = []
        
        self.message = ""
        
        self.local.ip = get_local_ip()
        self.local.netmask = ipconfig.get_netmask_for_adaptor(self.local.ip)
        
        try:
            self.logfile = open("CSSDiagnosticsLog.txt","a+")
            self.log("\n\n")
            self.log("Starting Connected Science System Diagnostic Tool")
        except:
            pass
        
        self.win = gtk.Window()
        self.win.connect("destroy", self.die_nicely)
        self.win.set_title("Connected Science System Diagnostic Tool from Vernier Software & Technology")
        self.vbox = gtk.VBox()
        self.win.add(self.vbox)
        
        self.top_hbox = gtk.HBox()
        self.vbox.pack_start(self.top_hbox)
        
        self.diag_lbl = gtk.Label("Network Diagnostics")
        self.top_hbox.pack_start(self.diag_lbl,False,False,5)
        self.run_btn = gtk.Button("Start")
        self.run_btn.connect("clicked", self.run_tests)
        self.top_hbox.pack_start(self.run_btn,False,False,5)
        
        self.information_hbox = gtk.HBox()
        self.datashare_frame = gtk.Frame("Data Sharing Source (LabQuest 2 or Logger Pro)")
        self.local_frame = gtk.Frame("Local Information")
        self.vbox.pack_start(self.information_hbox)
        self.information_hbox.pack_start(self.datashare_frame)
        self.information_hbox.pack_start(self.local_frame)
        self.datashare_hbox = gtk.HBox()
        self.local_hbox = gtk.HBox()
        self.datashare_lbl_vbox = gtk.VBox()
        self.datashare_val_vbox = gtk.VBox()
        self.local_lbl_vbox = gtk.VBox()
        self.local_val_vbox = gtk.VBox()
        
        self.datashare_hbox.pack_start(self.datashare_lbl_vbox,False,False,5)
        self.datashare_hbox.pack_start(self.datashare_val_vbox,False,False,5)
        self.local_hbox.pack_start(self.local_lbl_vbox,False,False,5)
        self.local_hbox.pack_start(self.local_val_vbox,False,False,5)
        self.datashare_frame.add(self.datashare_hbox)
        self.local_frame.add(self.local_hbox)
        
        self.datashare_lbl_vbox.pack_start(gtk.Label("IP Address"))
        self.datashare_lbl_vbox.pack_start(gtk.Label("Netmask"))
        self.datashare_lbl_vbox.pack_start(gtk.Label("Hostname"))
        self.datashare_lbl_vbox.pack_start(gtk.Label("Port"))
        #self.datashare_lbl_vbox.pack_start(gtk.Label("SSID"))
        
        self.datashare_ip = gtk.Entry()
        self.datashare_ip.set_tooltip_text("e.g. 192.168.123.23")
        self.datashare_netmask = gtk.Entry()
        self.datashare_netmask.set_tooltip_text("e.g. 255.255.255.0")
        self.datashare_port = gtk.Entry()
        self.datashare_port.set_tooltip_text("For LabQuest this is usually 80, and for Logger Pro please refer to the Data Sharing dialog")
        self.datashare_hostname = gtk.Entry()
        #self.datashare_ssid = gtk.Entry()
        self.datashare_val_vbox.pack_start(self.datashare_ip)
        self.datashare_val_vbox.pack_start(self.datashare_netmask)
        self.datashare_val_vbox.pack_start(self.datashare_hostname)
        self.datashare_val_vbox.pack_start(self.datashare_port)
        #self.datashare_val_vbox.pack_start(self.datashare_ssid)
        
        self.local_lbl_vbox.pack_start(gtk.Label("IP Address"))
        self.local_lbl_vbox.pack_start(gtk.Label("Netmask"))
        self.local_lbl_vbox.pack_start(gtk.Label(""))
        self.local_lbl_vbox.pack_start(gtk.Label(""))
        
        self.local_ip = gtk.Label()
        self.local_netmask = gtk.Label()
        
        self.local_val_vbox.pack_start(self.local_ip)
        self.local_val_vbox.pack_start(self.local_netmask)
        self.local_val_vbox.pack_start(gtk.Label())
        self.local_val_vbox.pack_start(gtk.Label())
        
        self.local_ip.set_text(str(self.local.ip))
        self.local_netmask.set_text(str(self.local.netmask))
        
        self.test_frame = gtk.Frame("Tests")
        self.vbox.pack_start(self.test_frame)
        self.tests_vbox = gtk.VBox()
        self.test_frame.add(self.tests_vbox)
        
        self.check_datashare_info_icon = gtk.Image()
        self.check_datashare_info_icon.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_MENU)
        check_datashare_info_hbox = gtk.HBox()
        check_datashare_info_hbox.pack_start(self.check_datashare_info_icon,False,False,5)
        check_datashare_info_hbox.pack_start(gtk.Label("Verify CSS Data Sharing Network Information"),False,False,5)
        self.tests_vbox.add(check_datashare_info_hbox)
        
        self.check_valid_ip_local_icon = gtk.Image()
        self.check_valid_ip_local_icon.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_MENU)
        check_valid_ip_local_hbox = gtk.HBox()
        check_valid_ip_local_hbox.pack_start(self.check_valid_ip_local_icon,False,False,5)
        check_valid_ip_local_hbox.pack_start(gtk.Label("Verify Local IP Address"),False,False,5)
        self.tests_vbox.add(check_valid_ip_local_hbox)
        
        self.check_valid_ip_datashare_icon = gtk.Image()
        self.check_valid_ip_datashare_icon.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_MENU)
        check_valid_ip_datashare_hbox = gtk.HBox()
        check_valid_ip_datashare_hbox.pack_start(self.check_valid_ip_datashare_icon,False,False,5)
        check_valid_ip_datashare_hbox.pack_start(gtk.Label("Verify  Data Sharing Source IP Address"),False,False,5)
        self.tests_vbox.add(check_valid_ip_datashare_hbox)        
        
        self.check_different_subnets_icon = gtk.Image()
        self.check_different_subnets_icon.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_MENU)
        check_different_subnets_hbox = gtk.HBox()
        check_different_subnets_hbox.pack_start(self.check_different_subnets_icon,False,False,5)
        check_different_subnets_hbox.pack_start(gtk.Label("Check that the Data Sharing Source and this computer are on the same subnet"),False,False,5)
        self.tests_vbox.add(check_different_subnets_hbox) 
        
        self.check_for_isolation_mode_icon = gtk.Image()
        self.check_for_isolation_mode_icon.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_MENU)
        check_for_isolation_mode_hbox = gtk.HBox()
        check_for_isolation_mode_hbox.pack_start(self.check_for_isolation_mode_icon,False,False,5)
        check_for_isolation_mode_hbox.pack_start(gtk.Label("Test for AP Isolation Mode on the WiFi Access Point"),False,False,5)
        self.tests_vbox.add(check_for_isolation_mode_hbox) 
        
        self.check_connect_by_ip_icon = gtk.Image()
        self.check_connect_by_ip_icon.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_MENU)
        check_connect_by_ip_hbox = gtk.HBox()
        check_connect_by_ip_hbox.pack_start(self.check_connect_by_ip_icon,False,False,5)
        check_connect_by_ip_hbox.pack_start(gtk.Label("Connect to the Data Sharing Source by IP Address"),False,False,5)
        self.tests_vbox.add(check_connect_by_ip_hbox)
        
        self.check_multicast_icon = gtk.Image()
        self.check_multicast_icon.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_MENU)
        check_multicast_hbox = gtk.HBox()
        check_multicast_hbox.pack_start(self.check_multicast_icon,False,False,5)
        check_multicast_hbox.pack_start(gtk.Label("Test IP Multicast Protocol"),False,False,5)
        self.tests_vbox.add(check_multicast_hbox)
        
        self.check_bonjour_list_icon = gtk.Image()
        self.check_bonjour_list_icon.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_MENU)
        check_bonjour_list_hbox = gtk.HBox()
        check_bonjour_list_hbox.pack_start(self.check_bonjour_list_icon,False,False,5)
        check_bonjour_list_hbox.pack_start(gtk.Label("Find Data Sharing Source using Bonjour"),False,False,5)
        self.tests_vbox.add(check_bonjour_list_hbox)
        
        self.check_hostname_lookup_icon = gtk.Image()
        self.check_hostname_lookup_icon.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_MENU)
        check_hostname_lookup_hbox = gtk.HBox()
        check_hostname_lookup_hbox.pack_start(self.check_hostname_lookup_icon,False,False,5)
        check_hostname_lookup_hbox.pack_start(gtk.Label("Resolve the Data Sharing Source Hostname via DNS or mDNS"),False,False,5)
        self.tests_vbox.add(check_hostname_lookup_hbox)
        
        self.check_connect_by_host_icon = gtk.Image()
        self.check_connect_by_host_icon.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_MENU)
        check_connect_by_host_hbox = gtk.HBox()
        check_connect_by_host_hbox.pack_start(self.check_connect_by_host_icon,False,False,5)
        check_connect_by_host_hbox.pack_start(gtk.Label("Connect to Data Sharing Source by Hostname"),False,False,5)
        self.tests_vbox.add(check_connect_by_host_hbox)

        self.check_reliability_icon = gtk.Image()
        self.check_reliability_icon.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_MENU)
        check_reliability_hbox = gtk.HBox()
        check_reliability_hbox.pack_start(self.check_reliability_icon,False,False,5)
        check_reliability_hbox.pack_start(gtk.Label("Test Network for Reliability (may take several minutes)"),False,False,5)
        self.tests_vbox.add(check_reliability_hbox)

        self.error_frame = gtk.Frame("Details")
        self.error_lbl = gtk.Label("")
        self.error_frame.add(self.error_lbl)
        self.vbox.pack_start(self.error_frame)
        
        self.log_frame = gtk.Frame("Log File")
        try:
            pathname = os.path.dirname(sys.argv[0])
            path = os.path.abspath(pathname) + os.sep + self.logfile.name
        except:
            path = self.logfile.name
        self.log_lbl = gtk.Label(path)
        self.log_frame.add(self.log_lbl)
        self.vbox.pack_start(self.log_frame)
        
        self.win.show_all()
        
    def check_valid_ip(self,ip):
        '''
        Not 127.0.0.1 or 169.254.x.x
        '''
        self.log("Checking ip: "+str(ip))
        self.ip_message = ""
        regex = "(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
        m = re.match(regex, ip)
        if m == None:
            self.ip_message += "The IP address '"+str(ip)+"' is not valid.\n"
            return False
            
        oct1 = m.group(1)
        oct2 = m.group(2)
        oct3 = m.group(3)
        oct4 = m.group(4)
        self.log(oct1+" "+oct2+" "+oct3+" "+oct4)
        
        if str(oct1) == "127" and str(oct2) == "0" and str(oct3) == "0" and str(oct4) == "1":
            self.ip_message = "127.0.0.1 is a loopback IP address. Contact Vernier for more information."
            return False
            
        return (oct1,oct2,oct3,oct4)
        
    def check_datashare_info(self):
        has_errors = False
        
        ip = self.datashare_ip.get_text()
        self.datashare.ip = ip
        if self.check_valid_ip(ip) == False:
            self.message += "You must enter the IP address for DataShare, e.g. 192.168.23.125.\n"
            self.message += self.ip_message
            has_errors = True
        
        netmask = self.datashare_netmask.get_text()
        self.datashare.netmask = netmask
        if not self.check_valid_ip(self.datashare.netmask):
            self.message += "You must enter the network mask for DataShare, e.g. 255.255.255.0.\n"
            has_errors = True
            
        if str(self.datashare.netmask) != str(self.local.netmask):
            self.message += "The local and DataShare netmasks are not the same. Please make sure you entered the subnet mask correctly.\n"
            has_errors = True 
        
        port = self.datashare_port.get_text()
        try:
            self.datashare.datashare_port = int(port)
            if self.datashare.datashare_port < 1 or self.datashare.datashare_port > 65535:
                self.message += "You must enter the valid port for DataShare, e.g. 80 or 8080.\n"
                has_errors = True    
        except:
            self.message += "You must enter the valid port for DataShare, e.g. 80 or 8080.\n"
            has_errors = True   
            
        hostname = self.datashare_hostname.get_text()
        self.datashare.hostname = hostname
        if hostname == "" or not hostname.endswith(".local"):
            self.message += "You must enter the hostname for DataShare, e.g. mylabquest2.local.\n"
            has_errors = True
        
        '''    
        ssid = self.datashare_ssid.get_text()
        self.datashare.ssid = ssid
        if ssid == "":
            self.message += "You must enter the SSID (Wifi network name) which the LabQuest2 is connected to, e.g. classroom128.\n"
            has_errors = True
       '''
        
        if has_errors == True:
            self.message += "\nYou can obtain the required information from the LabQuest2 under System->System Information on the Network Tab."
            return False
        return True

    def check_different_subnets(self):
        '''
        Take both IPs and the subnets and run algorithm
        '''
        self.log("Checking subnets")
        (mask1,mask2,mask3,mask4) = self.check_valid_ip(self.datashare.netmask)
        mask = str(bin(int(mask1)))+str(bin(int(mask2)))+str(bin(int(mask3)))+str(bin(int(mask4)))
        mask = mask.count("1")
        self.log("Converting subnetmask from "+str(self.datashare.netmask)+" to "+str(mask))
        datashare_ip = IP(self.datashare.ip,mask=mask)
        for ip in Network(datashare_ip):
            if self.local.ip == str(ip):
                return True
        self.message = str(self.local.ip)+" is not in the same subnet as "+str(self.datashare.ip)+".\n"
        self.message += "The devices you wish to use with DataShare must be on the same network as DataShare."
        self.message += "Contact your network administrator for more details."
        return False
    
    def check_multicast(self):
        '''
        Currently we send a multicast and see if we get it back. This doesn't really work though.
        We need an echo service on another host to really tell if multicast is blocked.
        TODO: need to test this one in a proper environment where multicast is off.
        '''
        self.log("Starting Multicast check")
        try:
            s_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            s_send.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            s_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            s_recv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except socket.error, msg:
            self.message = "Could not create socket: "+str(msg)
            self.message += "Contact Vernier for assistance."
            return False
        
        message = ""
        try:
            mcast_ip = '224.0.0.251'
            s_recv.bind(("", 5353))
            s_recv.settimeout(1)
            mreq = struct.pack("4sl", socket.inet_aton(mcast_ip), socket.INADDR_ANY)
            s_recv.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            s_send.sendto('Hello, world',(mcast_ip, 5353))
        except:
            self.log("Something died during multicast sendto.")
            pass
        
        messages = 0
        for count in range(1,10):
            try:
                message = s_recv.recv(4096)
                if message != "":
                    messages += 1
                    self.log("Got multicast message: "+str(message))
            except socket.error, msg:
                self.log("Error occurred during multicast receive")
                pass
        
        if messages == 0:
            self.message = "Failed to get multicast messages: "+str(msg)+"\n\n"
            self.message += "Your network most likely does not support the IP Multicast protocol."
            self.message += "Without this support you will not be able to browse the network for DataShare using Bonjour."
            self.message += "Contact your network administrator for assistance."
        
        try:
            s_send.close()
            s_recv.close()
        except:
            pass
        if message == "":
            return False
        return True

    def connect_to_port(self, port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((self.datashare.ip, port))
            s.close()
            return True
        except socket.error, msg:
            self.log("Error occured during connect to DataShare via IP on port "+str(self.datashare.datashare_port)+".")
        return False
    
    
    def check_for_isolation_mode(self):
        '''
        Check if we can can connect via IP and get an arp entry.
        TODO: Can't tell if the IP is correct or some other catastrophic issue...
        We should be checking multiple ports and maybe ICMP (22,80,111,5900,6000) for LQ2.
        What should we try to connect to for LoggerPro?
        '''    
        self.log("Checking for AP isolation mode")
        
        if self.connect_to_port(self.datashare.datashare_port):
            return True
        if self.connect_to_port(22):
            return True
        if self.connect_to_port(111):
            return True        
        if self.connect_to_port(6000):
            return True
        if self.connect_to_port(5900):
            return True
        
        childStderrPath = 'stderr'
        childstderr = file(childStderrPath, 'a')
        childStdinPath = 'stdin'
        childstdin = file(childStdinPath, 'a')
        
        output = subprocess.check_output(["arp", "-a"],stderr=childstderr,stdin=childstdin)
        lines = output.split("\n")
        for line in lines:
            self.log(str(line))
            if " "+str(self.datashare.ip)+" " in line:
                self.log("We found DataShare in the ARP table, we can't be entirely isolated. Must be blocking ports...")
                return True
        
        resolved = self.check_hostname_lookup()
        if resolved:
            self.message = "Unable to get an ARP resolution for the DataShare IP, but DNS resolves the hostname correctly. "
            self.message += "Make sure you entered the IP address correctly for DataShare."
            return False
        
        self.message = "Your network appears to be in AP Isolation mode since no connection could be made to DataShare and ARP does not resolve the DataShare IP.\n"
        self.message += "Make sure you entered the DataShare IP address correctly and contact your network administrator for assistance."
        
        return False
    
    
    def resolve_callback(self, sdRef, flags, interfaceIndex, errorCode, fullname,
                         hosttarget, port, txtRecord):
        if errorCode == pybonjour.kDNSServiceErr_NoError:
            self.log('Resolved service:')
            self.log('  fullname   ='+str(fullname))
            self.log('  hosttarget ='+str(hosttarget))
            self.log('  port       ='+str(port))
            self.resolved.append(True)
            self.found_bonjour_hosts.append(hosttarget.lower())
    
    
    def browse_callback(self, sdRef, flags, interfaceIndex, errorCode, serviceName,
                        regtype, replyDomain):
        if errorCode != pybonjour.kDNSServiceErr_NoError:
            return
    
        if not (flags & pybonjour.kDNSServiceFlagsAdd):
            self.log('Service removed')
            return
    
        self.log('Service added '+serviceName+'; resolving')
    
        resolve_sdRef = pybonjour.DNSServiceResolve(0,
                                                    interfaceIndex,
                                                    serviceName,
                                                    regtype,
                                                    replyDomain,
                                                    self.resolve_callback)
    
        try:
            while not self.resolved:
                ready = select.select([resolve_sdRef], [], [], self.timeout)
                if resolve_sdRef not in ready[0]:
                    self.log('Resolve timed out')
                    break
                pybonjour.DNSServiceProcessResult(resolve_sdRef)
            else:
                self.resolved.pop()
        finally:
            resolve_sdRef.close()
    
    def check_bonjour_list(self):
        '''
        Do we see the DataShare hostname?
        http://code.google.com/p/pybonjour/
        '''
        self.log("Checking bonjour list for DataShare services")
        browse_sdRef = pybonjour.DNSServiceBrowse(regtype = self.regtype, callBack = self.browse_callback)
        try:
            try:
                while True:
                    self.log("Searching for Bonjour service...")
                    ready = select.select([browse_sdRef], [], [], self.timeout)
                    while gtk.events_pending():
                        gtk.main_iteration(False)  
                    if ready[0] == []:
                        self.log("Nothing.")
                        break
                    if browse_sdRef in ready[0]:
                        pybonjour.DNSServiceProcessResult(browse_sdRef)
            except KeyboardInterrupt:
                pass
        finally:
            browse_sdRef.close()
        datashare_hostname = self.datashare.hostname+"."
        self.log("Found "+str(len(self.found_bonjour_hosts))+" DataShare services via Bonjour.")
        if len(self.found_bonjour_hosts) == 0:
            self.message = "Bonjour found 0 DataShare services on the network. Contact your network administrator for assistance."
            return False
        if datashare_hostname.lower() not in self.found_bonjour_hosts:
            self.message = "Bonjour found "+str(len(self.found_bonjour_hosts))+" DataShare services, but not "+str(self.datashare.hostname)+"."
            self.message += " Verify that you provided the correct hostname for DataShare.\n"
            self.message += "This can be the result of a saturated or weak WiFi network. Contact your network administrator for assistance."
            return False
        return True
    
    def check_hostname_lookup(self):
        '''
        Can we resolve the hostname with some form of DNS?
        '''
        self.log("Starting hostname lookup")
        try:
            ip = socket.gethostbyname(self.datashare.hostname)
            self.log("Resolved "+str(self.datashare.hostname)+" to "+str(ip))
            return True
        except:
            self.message = "Could not resolve the hostname: "+str(self.datashare.hostname)+"\nMake sure you entered the hostname correctly.\n"
            self.message += "Your network might be blocking Multicast DNS service. Contact your network administrator for assistance."
        return False
    
    def check_connect_by_host(self):
        '''
        Try to get info page via hostname
        '''
        self.log("Starting connect by hostname")
        return self.connect_to_datashare(self.datashare.hostname)
    
    def check_connect_by_ip(self):
        '''
        Try to get info page via IP
        '''
        self.log("Starting connect by IP")
        return self.connect_to_datashare(self.datashare.ip)
    
    def connect_to_datashare(self, host):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error, msg:
            self.message = "Could not create socket: "+str(msg)+"\n\n"
            self.message += "Contact Vernier for assistance."
            return False
            
        try:
            s.connect((host, self.datashare.datashare_port))
            s.settimeout(15)
        except socket.error, msg:
            self.message = "Could not connect to DataShare: "+str(msg)+"\n\n"
            self.message += "Ensure that the Vernier DataShare service is enabled.\n"
            self.message += "Your network might be blocking TCP port "+str(self.datashare.datashare_port)+" which"
            self.message += " is required for Vernier DataShare, please contact your network administrator for assistance."
            return False
        
        self.log("Connected to DataShare, trying to get the info page.")
        
        info = ""
        try:
            s.sendall("GET /info HTTP/1.1\n\n")
            info = s.recv(4096)
        except socket.error, msg:
            self.log("Error while trying to get /info.")
            pass
            
        if info == "":
            self.message = "A connection was successfully established to DataShare, but we did not receive any data.\n"
            self.message += "This can be the result of a saturated or weak WiFi network. Please contact your network administrator for assistance."
            return False
        
        self.log('Received: '+str(info))
        
        try:
            s.close()
        except:
            return False
        return True
    
    def check_reliability(self):
        '''
        Keep checking the page....
        '''
        self.log("Checking reliability")
        successes = 0
        runs = 10
        dt1 = datetime.now()
        for run in range(1,runs):
            info = ""
            try:
                while gtk.events_pending():
                    gtk.main_iteration(False)  
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((self.datashare.hostname, self.datashare.datashare_port))
                s.settimeout(1)
                s.sendall("GET /status HTTP/1.1\n\n")
                info = s.recv(4096)
                info += s.recv(4096)
                self.log(str(info))
                s.close()                
                successes += 1
            except socket.error, msg:
                self.log("Error getting status.")
                pass
        dt2 = datetime.now()
        delta = dt2 - dt1
        secs = delta.total_seconds()
        
        self.message = "Completed "+str(successes)+" out of "+str(runs)+" trials in "+str(secs)+" seconds.\n\n"
        self.log(self.message)
        if successes > (runs*0.8):
            return True
        self.message += "Your network might be saturated or the WiFi signal too weak for good performance."
        return False

    def set_error(self):
        self.error_lbl.set_text(self.message)
        self.log(self.message)
        return False

    def run_tests(self, args):
        self.check_datashare_info_icon.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_MENU)
        self.check_valid_ip_local_icon.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_MENU)
        self.check_valid_ip_datashare_icon.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_MENU)
        self.check_different_subnets_icon.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_MENU)
        self.check_for_isolation_mode_icon.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_MENU)
        self.check_connect_by_ip_icon.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_MENU)
        self.check_multicast_icon.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_MENU)
        self.check_bonjour_list_icon.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_MENU)
        self.check_hostname_lookup_icon.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_MENU)
        self.check_connect_by_host_icon.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_MENU)
        self.check_reliability_icon.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_MENU)
        self.message = ""
        self.error_lbl.set_text(self.message)

        while gtk.events_pending():
            gtk.main_iteration(False)
        
        if not self.check_datashare_info():
            self.check_datashare_info_icon.set_from_stock(gtk.STOCK_NO, gtk.ICON_SIZE_MENU)
            return self.set_error()
        else:
            self.check_datashare_info_icon.set_from_stock(gtk.STOCK_YES, gtk.ICON_SIZE_MENU)
        
        while gtk.events_pending():
            gtk.main_iteration(False)
        
        if not self.check_valid_ip(self.local.ip):
            self.check_valid_ip_local_icon.set_from_stock(gtk.STOCK_NO, gtk.ICON_SIZE_MENU)
            return self.set_error()
        else:
            self.check_valid_ip_local_icon.set_from_stock(gtk.STOCK_YES, gtk.ICON_SIZE_MENU)
        
        while gtk.events_pending():
            gtk.main_iteration(False)
        
        if not self.check_valid_ip(self.datashare.ip):
            self.check_valid_ip_datashare_icon.set_from_stock(gtk.STOCK_NO, gtk.ICON_SIZE_MENU)
            return self.set_error()
        else:
            self.check_valid_ip_datashare_icon.set_from_stock(gtk.STOCK_YES, gtk.ICON_SIZE_MENU)
        
        while gtk.events_pending():
            gtk.main_iteration(False)
        
        if not self.check_different_subnets():
            self.check_different_subnets_icon.set_from_stock(gtk.STOCK_NO, gtk.ICON_SIZE_MENU)
            return self.set_error()
        else:
            self.check_different_subnets_icon.set_from_stock(gtk.STOCK_YES, gtk.ICON_SIZE_MENU)
        
        while gtk.events_pending():
            gtk.main_iteration(False)
        
        if not self.check_for_isolation_mode():
            self.check_for_isolation_mode_icon.set_from_stock(gtk.STOCK_NO, gtk.ICON_SIZE_MENU)
            return self.set_error()
        else:
            self.check_for_isolation_mode_icon.set_from_stock(gtk.STOCK_YES, gtk.ICON_SIZE_MENU)
        
        while gtk.events_pending():
            gtk.main_iteration(False)
        
        if not self.check_connect_by_ip():
            self.check_connect_by_ip_icon.set_from_stock(gtk.STOCK_NO, gtk.ICON_SIZE_MENU)
            return self.set_error()
        else:
            self.check_connect_by_ip_icon.set_from_stock(gtk.STOCK_YES, gtk.ICON_SIZE_MENU)
        
        while gtk.events_pending():
            gtk.main_iteration(False)
        
        if not self.check_multicast():
            self.check_multicast_icon.set_from_stock(gtk.STOCK_NO, gtk.ICON_SIZE_MENU)
            return self.set_error()
        else:
            self.check_multicast_icon.set_from_stock(gtk.STOCK_YES, gtk.ICON_SIZE_MENU)
        
        while gtk.events_pending():
            gtk.main_iteration(False)
        
        if not self.check_bonjour_list():
            self.check_bonjour_list_icon.set_from_stock(gtk.STOCK_NO, gtk.ICON_SIZE_MENU)
            return self.set_error()
        else:
            self.check_bonjour_list_icon.set_from_stock(gtk.STOCK_YES, gtk.ICON_SIZE_MENU)
        
        while gtk.events_pending():
            gtk.main_iteration(False)
        
        if not self.check_hostname_lookup():
            self.check_hostname_lookup_icon.set_from_stock(gtk.STOCK_NO, gtk.ICON_SIZE_MENU)
            return self.set_error()
        else:
            self.check_hostname_lookup_icon.set_from_stock(gtk.STOCK_YES, gtk.ICON_SIZE_MENU)
            
        while gtk.events_pending():
            gtk.main_iteration(False)    
            
        if not self.check_connect_by_host():
            self.check_connect_by_host_icon.set_from_stock(gtk.STOCK_NO, gtk.ICON_SIZE_MENU)
            return self.set_error()
        else:
            self.check_connect_by_host_icon.set_from_stock(gtk.STOCK_YES, gtk.ICON_SIZE_MENU)

        while gtk.events_pending():
            gtk.main_iteration(False)  
        
        if not self.check_reliability():
            self.check_reliability_icon.set_from_stock(gtk.STOCK_NO, gtk.ICON_SIZE_MENU)
            return self.set_error()
        else:
            self.check_reliability_icon.set_from_stock(gtk.STOCK_YES, gtk.ICON_SIZE_MENU)
        

if __name__ == '__main__':
    CSSDiagnostics()    
    gtk.main()