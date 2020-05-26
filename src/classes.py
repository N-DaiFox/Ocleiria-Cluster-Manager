import a2s
import arrow
import json
import jsonpickle

class JSON: #base class
    def __init__(self):
        pass

    def toJSON(self):
        return jsonpickle.encode(self) # yeah pickles I know

    def fromJSON(JSONText):
        self = jsonpickle.decode(JSONText)
        return self

class ARKServer(JSON):
    # Class representing ARK server
    def __init__(self,ip):
        self.ip = ip
        self.address , self.port = ip.split(':') # split adress to ip and port
        self.port = int(self.port) # convert port to int
        pass
    
    def GetInfo(self):
        server = a2s.info((self.address,self.port)) # get server data
        #players = a2s.players(address) #this is list of players I will implement it in another class
        data = a2s.rules((self.address,self.port)) # custom ARK data

        version = server.server_name #get name
        first = version.find('(') # split out version
        second = version.rfind(')')
        self.version = version[first+1:second] # read https://ark.gamepedia.com/Server_Browser#Server_Name

        platform = server.platform # get platform server running on
        if (platform == 'w'): # decode
            platform = 'Windows'
        elif (platform == 'l'):
            platform = 'Linux'
        elif (platform == 'm' or platform == 'o'):
            platform = 'Mac' # =/
        self.platform = platform

        self.name = server.server_name # just extract data 
        self.online = server.player_count
        self.maxPlayers = server.max_players
        self.map = server.map_name
        self.password = server.password_protected
        self.PVE = bool(data['SESSIONISPVE_i']) # in data no so much interesting data so let`s parse into class
        try:
            self.clusterName = data['ClusterId_s'] # cluster name
        except KeyError:
            self.clusterName = None
        self.BattleEye = bool(data['SERVERUSESBATTLEYE_b']) # Is BattleEye used ?
        self.itemDownload = bool(data['ALLOWDOWNLOADITEMS_i'])  # can you download items to this ARK ?
        self.characterDownload = bool(data['ALLOWDOWNLOADCHARS_i']) # Can you download characters to this ARK ?
        self.hours = data['DayTime_s'][:2] # current in-game time
        self.minutes = data['DayTime_s'][2:]
        return self
    
class Player(JSON):
    def __init__(self,name,time):
        basetime= arrow.get(0)
        time = arrow.get(int(time)) #convert to int because of decimal digits later 
        time = time - basetime
        self.time = time.__str__()
        self.name = name
        pass  

class PlayersList(JSON):
    def __init__(self,ip):
        self.ip = ip
        self.address , self.port = ip.split(':') # split adress to ip and port
        self.port = int(self.port) # convert port to int
        pass

    def getPlayersList(self):
        players = a2s.players((self.address,self.port)) # get raw data
        result = [] 
        for player in players: # for each player in data
            result.append(Player(player.name,player.duration)) # construct player class and append it to our results
        self.list = result 
        return self
