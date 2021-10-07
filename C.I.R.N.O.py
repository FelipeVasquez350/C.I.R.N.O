import pafy
import vlc
from enum import Enum

class SubNet:

    NET_ADD = ""
    def __init__(self, no, n_hosts, network_address):
        self.subnet_n = no 
        self.n_hosts = n_hosts
        self.NET_ADD = network_address

    def getSubnetAddress(self):
        return self.NET_ADD

    def getSubnetMask(self):
        i=0
        while(pow(2,i)-2<self.n_hosts): i+=1
        return getFullNetworkMask(str(32-i))
    
    def getGateway(self):
        return f"{self.NET_ADD[:-1]}{int(self.NET_ADD[-1])+1}"

    def getBroadcast(self):
        return getSumNetworkMask(self.NET_ADD, pow(2,32-int(getShortNetworkMask(self.getSubnetMask())))-1)

    def getRange(self):
        IPRanges = []
        for i in range (pow(2,32-int(getShortNetworkMask(self.getSubnetMask())))-2):
            if i==0:
                IPRanges.append(f"{self.NET_ADD[:-1]}{int(self.NET_ADD[-1])+1+i}")
            else:
                IPRanges.append(getNextNetworkAddress(IPRanges[-1]))
        return IPRanges

    def toString(self):
        return f"\nSubnet n: {self.subnet_n}\n-Subnet Address: {self.getSubnetAddress()}\n-Subnet Mask: {self.getSubnetMask()}\n-Gateway: {self.getGateway()}\n-Broadcast: {self.getBroadcast()}\n-Subnet Range: {self.getRange()[0]} - {self.getRange()[-1]}\n"
class Router:
    
    def __init__(self, hostname):
        self.hostname = hostname
        self.Interfaces = []
    def addInterface(self, int_name, port, endpoint, source_ip, source_mask, end_ip, end_mask):
        newInterface = {
            "Interface Name": int_name,
            "Port": port,
            "EndPoint": endpoint,
            "Source IP": source_ip,
            "Source Mask": source_mask,
            "Destination IP": end_ip,
            "Destination Mask": end_mask
        }    
        self.Interfaces.append(newInterface)
    
    def showInterfaces(self):
        Output = f"{self.hostname}:\n"
        for interface in self.Interfaces:
            Output+=f"\n{self.interfaceToString(interface)}\n"
        return Output

    def interfaceToString(self, interface):
        return f"""-Interface Name: {interface["Interface Name"]}
-Port: {interface["Port"]}
-EndPoint: {interface["EndPoint"]}
-Source IP: {interface["Source IP"]}
-Source Mask: {interface["Source Mask"]}
-Destination IP: {interface["Destination IP"]}
-Destination Mask: {interface["Destination Mask"]}"""


class Network_Address_Class(Enum):
    Invalid = 0
    A = 1
    B = 2
    C = 3
    Non_Local = 4

def checkNetworkAddressClass(NETWORK_ADDRESS):
    S0, S1, S2, S3 = map(int, NETWORK_ADDRESS.split("."))
    
    if S0 == 10:
        if S1 > 255 or S2 > 255 or S3 > 255:
            return Network_Address_Class.Invalid
        return Network_Address_Class.A

    elif S0 == 172:
        if S1 >= 16 and S1 <= 31:
            if S2 > 255 or S3 > 255:
                return Network_Address_Class.Invalid
            return Network_Address_Class.B
        return Network_Address_Class.Invalid
    
    elif S0 == 192 and S1 == 168:
        if S2 > 255 or S3 > 255:
            return Network_Address_Class.Invalid
        return Network_Address_Class.C

    elif S0 <= 255 and S1 <= 255 or S2 <= 255 or S3 <= 255: 
        return Network_Address_Class.Non_Local
    
    return Network_Address_Class.Invalid
def getNextNetworkAddress(NETWORK_ADDRESS):
    S0, S1, S2, S3 = map(int, NETWORK_ADDRESS.split("."))
    if S3 >= 255:
        S3 = 0
        if S2 >= 255:
            S2 = 0
            if S1 >= 255:
                S1 = 0
                if S0 >= 255: 
                    S0 = 0
                else: S0+=1    
            else: S1+=1
        else: S2+=1
    else: S3+=1
    return f"{S0}.{S1}.{S2}.{S3}"
def getSumNetworkMask(NETWORK_ADDRESS, VALUE):
    if VALUE > 255:
        print("ERROR: VALUE OVER 255")
        return
    REST=0
    S0, S1, S2, S3 = map(int, NETWORK_ADDRESS.split("."))
    if S3+VALUE > 255 or S3 >= 255:
        S3 = 0
        REST=S3+VALUE-255
        if S2+REST > 255 or S2 >= 255:
            S2 = 0
            REST=S2+VALUE-255
            if S1+REST > 255 or S1 >= 255:
                S1 = 0
                REST=S1+VALUE-255
                if S0+REST > 255 or S0 >= 255: 
                    S0 = 0
                else: S0+=REST    
            else: S1+=REST
        else: S2+=REST
    else: S3+=VALUE
    return f"{S0}.{S1}.{S2}.{S3}"

#Ancora da determinare se è una cazzata o meno
class MaskStatus(Enum):
    Invalid = 0
    Short = 1
    Long = 2

def checkNetworkMaskFormat(NETWORK_MASK):
    #Controlla se può essere nel formato /xx
    if len(NETWORK_MASK) < 3:
        try:
            if int(NETWORK_MASK) <= 32: return MaskStatus.Short
            else: return MaskStatus.Invalid
        except Exception: return MaskStatus.Invalid

    #Altrimenti controlla se può essere nel formato xxx.xxx.xxx.xxx
    elif len(NETWORK_MASK) == 15:
        i=0
        MASK_END=False
        while(i<=12):
            #Prende parte per parte a 3
            INT_VALUE=int(NETWORK_MASK[i:i+3])

            #Controlla se il valore massimo viene superato
            if INT_VALUE > 255: return MaskStatus.Invalid

            j=0
            while(INT_VALUE>0):           
                INT_VALUE-=pow(2,7-j)
                j+=1

            #Controlla se il valore appartiene alle potenze inverse di 2
            if INT_VALUE < 0 or (MASK_END and j>0): return MaskStatus.Invalid
            
            #Controlla se i valori successivi debbano essere maggiori di 0
            elif j!=8:
                MASK_END=True
            i+=4
        return MaskStatus.Long
    return MaskStatus.Invalid
def getFullNetworkMask(NETWORK_MASK):
    #Defines the variable
    CORRECT_MASK=""

    #Checks if the Mask is in the /xx format
    if len(NETWORK_MASK) < 3:
        NETWORK_MASK_INT = int(NETWORK_MASK)
        NETWORK_MASK_CLASS = 3

        while(NETWORK_MASK_INT >= 8):
            NETWORK_MASK_INT-=8
            NETWORK_MASK_CLASS-=1
            CORRECT_MASK+="255."

        LASTVALUE=0
        i=0

        while(NETWORK_MASK_INT>0):
            NETWORK_MASK_INT-=1
            LASTVALUE+=pow(2,7-i)
            i+=1

        ZERO_FLAG=(LASTVALUE==0 and i==0)
        if LASTVALUE!=0 or ZERO_FLAG and NETWORK_MASK_CLASS!=-1: 
            if NETWORK_MASK_CLASS==3 and ZERO_FLAG:
                CORRECT_MASK="000"
            elif LASTVALUE==0:
                CORRECT_MASK+="000"
            else:
                CORRECT_MASK+=f"{LASTVALUE}"

            while(NETWORK_MASK_CLASS>0):
                NETWORK_MASK_CLASS-=1
                CORRECT_MASK+=".000"

        elif (len(CORRECT_MASK) > 15): 
            CORRECT_MASK = CORRECT_MASK[:-1]

    #Checks if the mask is of the correct size
    elif(len(NETWORK_MASK) > 15):
        print("Error: Invalid Subnet Mask")

    #TODO Create a final check to determine if the mask is valid or not(a new method)
    return CORRECT_MASK
def getShortNetworkMask(NETWORK_MASK):
    #Checks if the given mask is in the correct format
    if(len(NETWORK_MASK) != 15): return
    
    i=0
    SHORT_NETWORK_MASK=0
    while(i<=12):
        INT_VALUE=int(NETWORK_MASK[i:i+3])
        j=0
    
        while(INT_VALUE>0):           
            INT_VALUE-=pow(2,7-j)
            j+=1
    
        SHORT_NETWORK_MASK+=j
        i+=4
    return SHORT_NETWORK_MASK
def belongsNetworkMasktoClass(NETWORK_ADDRESS, NETWORK_MASK):
    NETWORK_CLASS = checkNetworkAddressClass(NETWORK_ADDRESS)
    MASK_VALUE = getShortNetworkMask(NETWORK_MASK)
    if NETWORK_CLASS == Network_Address_Class.A and MASK_VALUE<8:
        return False
    elif NETWORK_CLASS == Network_Address_Class.B and MASK_VALUE<16:
        return False
    elif  NETWORK_CLASS == Network_Address_Class.C and MASK_VALUE<24:
        return False
    return True
def getReverseNetworkMask(NETWORK_MASK):
    S0, S1, S2, S3 = map(int, NETWORK_MASK.split("."))
    return f"{255-S0}.{255-S1}.{255-S2}.{255-S3}"
def getMaxSubnets(NETWORK_MASK):
    return pow(2, 30 - getShortNetworkMask(NETWORK_MASK))
def getMaxHosts(NETWORK_MASK):
    return pow(2, 32 - getShortNetworkMask(NETWORK_MASK))-2

def Classless():
    return
def Classfull():
    return
def Subnetting_Statico_Dinamico():
    return
def RIP_RIPv2():
    return
def VLSM():
    
    NETWORK_ADDRESS, NETWORK_MASK = input("Inserisci l'indirizzo della rete: ").split("/")

    #region Check IP ADDRESS 
    if checkNetworkAddressClass(NETWORK_ADDRESS) == Network_Address_Class.Invalid:
        print("ERROR: INVALID NETWORK ADDRESS")
        return

    elif checkNetworkAddressClass(NETWORK_ADDRESS) == Network_Address_Class.Non_Local:
        print("ERROR: ONLY LOCAL NETWORK ADDRESSES")
        return
    #endregion

    print(NETWORK_ADDRESS +", "+NETWORK_MASK)

    #region Check MASK 
    NETWORK_MASK_STATUS = checkNetworkMaskFormat(NETWORK_MASK)  
    if NETWORK_MASK_STATUS == MaskStatus.Invalid: 
        print("ERROR: INVALID NETWORK MASK")
        return

    elif NETWORK_MASK_STATUS == MaskStatus.Short:
        NETWORK_MASK = getFullNetworkMask(NETWORK_MASK)

    if not belongsNetworkMasktoClass(NETWORK_ADDRESS, NETWORK_MASK):
        print("ERROR: INVALID MASK") 
        return   
    #endregion
   
    print(NETWORK_MASK)

    N_HOSTS = int(input("Inserire il numero di host totali: "))
    if N_HOSTS>getMaxHosts(NETWORK_MASK):
        print("FAILED: Not enought subnets available")
        return

    N_SUBNETS = int(input("Inserire il numero di sottoreti: "))
    if N_SUBNETS>getMaxSubnets(NETWORK_MASK):
        print("FAILED: Not enought subnets available")
        return
    
    print(getMaxSubnets(NETWORK_MASK))
    print(getMaxHosts(NETWORK_MASK))

    TOTAL_SUBNETS = []
    CURRENT_SUBNET_ADDRESS = NETWORK_ADDRESS
    for i in range(N_SUBNETS):
        subnet_hosts =  int(input("Inserire il numero di host della subnet: "))
        N_HOSTS -= subnet_hosts
        if N_HOSTS < 0:
            print("TOO MANY HOSTS!")
            return
        Test = SubNet(i, subnet_hosts, CURRENT_SUBNET_ADDRESS)
        TOTAL_SUBNETS.append(Test)
        CURRENT_SUBNET_ADDRESS = getNextNetworkAddress(Test.getBroadcast())
        print(Test.toString())
    
    Option=input("Do you want to save this subnet? [yes/no]")
    if Option.lower() == "yes":
        Filename=input("Filename [SubnetConfig by default]: ")
        if Filename == "":
            Filename="SubnetConfig"
        TextFile = open(f"{Filename}.txt", "a")
        for Subnet in TOTAL_SUBNETS:
            TextFile.write(Subnet.toString())
    return
def OSPFv2():
    N_NETWORKS = int(input("Quante reti sono presenti [min 2]? "))
    if N_NETWORKS < 2: 
        N_NETWORKS = 2
    # ROUTERS = [Router(f"R{i+1}") for i in range(N_NETWORKS)]
    ROUTERS=[]
    for i in range(N_NETWORKS):
        router = Router(f"R{i+1}")
        ROUTERS.append(router)
    for i in range(N_NETWORKS):
        CONNECTED_NETWORKS = int(input("\nQuanti collegamenti ci sono con la rete [min 2]? "))
        if CONNECTED_NETWORKS < 2: 
            CONNECTED_NETWORKS = 2
        
        for j in range(CONNECTED_NETWORKS):
            int_name = input("\nInserisci il nome dell'interfaccia a cui il router è collegato: ")
            port = input("Indica il tipo di porta: ")
            endpoint = input("Indica il tipo di porta d6el destinatario: ")
            source_ip, source_mask = input("Inserisci l'indirizzo della rete: ").split("/")
            end_ip, end_mask = input("Inserisci l'indirizzo della rete del destinatario: ").split("/")
            ROUTERS[i].addInterface(int_name, port, endpoint, source_ip, source_mask, end_ip, end_mask)
            #ROUTERS[i].addInterface("a", "port", "endpoint", source_ip, source_mask, "end_ip", "end_mask")
            print(ROUTERS[i])
    for router in ROUTERS:
        for interface in router.Interfaces:
            print(f"\n{router.hostname}(config)#router ospf 1")
            print(f"{router.hostname}(config-router)#network " + interface["Source IP"] + " " +getReverseNetworkMask(getFullNetworkMask(interface["Source Mask"])) + " area 0")
    print("\n\n\n\n\n\n")
    for router in ROUTERS:
        for interface in router.Interfaces:
            print(f"\n{router.hostname}(config)#interface loopback 0")
            print(f"{router.hostname}(config-if)#ip address 1.1.1.1 255.255.255.255")
            print(f"{router.hostname}(config-if)#end")
    print("\n\n\n\n\n\n")

    for router in ROUTERS:
        for interface in router.Interfaces:      
            print(f"\n{router.hostname}(config)#router ospf 1")  
            print(f"\n{router.hostname}(config-router)#router-id 11.11.11.11")
            print(f"{router.hostname}#clear ip ospf process")
            print(f"{router.hostname}#show ip ospf neighbor")
    print("\n\n\n\n\n\n")

    for router in ROUTERS:
        for interface in router.Interfaces:
            print(f"\n{router.hostname}#show ip ospf interface "+ interface["Port"])
            print(f"\n{router.hostname}(config)#router ospf 1")
            print(f"{router.hostname}(config-router)#passive-interface "+ interface["Port"])
            print(f"\n{router.hostname}#show ip ospf interface "+ interface["Port"])
            print(f"\n{router.hostname}#show ip route")
    print("\n\n\n\n\n\n")

    for router in ROUTERS:
        for interface in router.Interfaces:
            print(f"\n{router.hostname}(config)#router ospf 1")
            print(f"{router.hostname}(config-router)#auto-cost reference-bandwidth 10000")
    print("\n\n\n\n\n\n")

    for router in ROUTERS:
        for interface in router.Interfaces:
            print(f"\n{router.hostname}(config)#interface" + interface["Port"])
            print(f"{router.hostname}(config-if)#bandwidth?")
            print(f"{router.hostname}(config-if)#bandwidth 64")
            print(f"\n{router.hostname}#show ip route")

    return
def Load_Config():
    return
def Edit_Config():
    return
def About_Me(): 
    print("C.I.R.N.O. aka Calcolatore Informatico di Reti Note Online, è uno strumento per velocizzare la pianificazione di reti locali.\n")   
    url = "https://www.youtube.com/watch?v=AND4V18up7A"
    print(f"Baka mitai: {url}")
    video = pafy.new(url)
    best = video.getbest()
    playurl = best.url
    Instance = vlc.Instance()
    player = Instance.media_player_new()
    Media = Instance.media_new(playurl)
    Media.get_mrl()
    player.set_media(Media)
    player.play()   
def Exit():
    return

options = {0 : Exit,
           1 : Classless,
           2 : Classfull,
           3 : Subnetting_Statico_Dinamico,
           4 : RIP_RIPv2,
           5 : VLSM,
           6 : OSPFv2,
           7 : Load_Config,
           8 : Edit_Config,
           9 : About_Me
}


while(True):
    MODE = int(input("\033[96m"+R"""Welcome to C.I.R.N.O. ⑨

______/\\\\\\\\\______        
 ____/\\\///////\\\____       
  ___/\\\______\//\\\___      
   __\//\\\_____/\\\\\___     
    ___\///\\\\\\\\/\\\___    
     _____\////////\/\\\___   
      ___/\\________/\\\____  
       __\//\\\\\\\\\\\/____ 
        ___\///////////____
"""
+
"""\033[0m
Selezionare una delle seguenti operazioni:
-1)Creare Rete Classless. [WIP]
-2)Creare Rete Classfull. [WIP]
-3)Creare Rete con Subnetting Statico/Dinamico. [WIP]
-4)Creare Rete con RIP/RIPv2. [WIP]
-5)Creare Rete con VLSM.
-6)Creare Rete con OSPFv2. [WIP]
-7)Caricare configurazione. [WIP]
-8)Modificare configurazione. [WIP]
-9)About Me.

-0)Exit.
"""))
    options[MODE]()
    Select=input("Vuoi uscire? [yes/no]: ")
    if Select.lower() == "yes": exit()