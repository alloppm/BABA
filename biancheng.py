# -*- coding: utf-8 -*-


#===================================================#
#                                                   #
#                        导                       #
#                                                   #
#===================================================#
from KancollePlayerSimulatorKaiCore import *
import time
import itertools
import math

#===================================================#
#                                                   #
#                        常量                       #
#                                                   #
#===================================================#
def getEquipConstId(name):
	return EquipmentConstUtility.Id([obj for obj in EquipmentConstUtility.All() if EquipmentConstUtility.Name(obj) == name][0])

DLC_CONST_ID = getEquipConstId("大発動艇") #大发的ID，能带特大发的船大发也能带
KHT_CONST_ID = getEquipConstId("甲標的 甲型")
TNN_CONST_ID = getEquipConstId("特二式内火艇")
SBC_CONST_ID = getEquipConstId("増設バルジ(中型艦)")
SEVEN_CONST_ID = getEquipConstId("7.7mm機銃")


def getShipConstId(name):
	return ShipConstUtility.Id([obj for obj in ShipConstUtility.All() if ShipConstUtility.Name(obj) == name][0])

MARUYU_CONST_ID = getShipConstId("まるゆ")


MAX_LEVEL = 180 # 等级上限

#===================================================#
#                                                   #
#                        工具                       #
#                                                   #
#===================================================#
# 属性获取助手
def getConst(shipObj):
	return ShipConstUtility.ShipConst(shipObj)

def getId(shipObj):
	return ShipUtility.Id(shipObj)

def getLevel(shipObj):
	return ShipUtility.Level(shipObj)

def getExperience(shipObj):
	return ShipUtility.Experience(shipObj)

def getAllowedEquipIds(shipConstObj):
	return ShipConstUtility.AllowedEquipmentConsts(shipConstObj, EquipmentSlot.Slot1)

def getBeforeUpgradeIds(shipConstObj):
	return ShipConstUtility.BeforeIds(shipConstObj)

def getIds(shipObjs):
	return [getId(shipObj) for shipObj in shipObjs]

# 复杂过滤器（界面里没提供的）
def filterLocked(shipObjs):
	return [shipObj for shipObj in shipObjs if ShipUtility.ShipLocked(shipObj)]

def filterEquiptable(shipObjs, equip_const_id): # 可以带某装备的
	return [shipObj for shipObj in shipObjs if equip_const_id in getAllowedEquipIds(getConst(shipObj))]

def filterNotEquiptable(shipObjs, equip_const_id): # 不可以带某装备的
	return [shipObj for shipObj in shipObjs if equip_const_id not in getAllowedEquipIds(getConst(shipObj))]

def filterLevelRange(shipObjs, low, high): # 筛选等级在范围内的船
	return [shipObj for shipObj in shipObjs if low <= getLevel(shipObj) and getLevel(shipObj) <= high]

def filterUpgraded(shipObjs): # 筛选至少一改过后的
	return [shipObj for shipObj in shipObjs if len([i for i in getBeforeUpgradeIds(getConst(shipObj))]) > 0]

def filterNotUpgraded(shipObjs): # 筛选没有一改的
	return [shipObj for shipObj in shipObjs if len([i for i in getBeforeUpgradeIds(getConst(shipObj))]) == 0]

def filterLevelAt(shipObjs, level): # 筛选对应等级
	return [shipObj for shipObj in shipObjs if getLevel(shipObj) == level]

def filterLevelNotAt(shipObjs, level): # 筛选非对应等级
	return [shipObj for shipObj in shipObjs if getLevel(shipObj) != level]

def filterLevelNotAt99(shipObjs): # 筛选非99级
	return filterLevelNotAt(shipObjs, 99)

def filterLevelAbove(shipObjs, level): # 筛选对应等级以上
	return [shipObj for shipObj in shipObjs if getLevel(shipObj) > level]

def filterLevelBelow(shipObjs, level): # 筛选对应等级以下
	return [shipObj for shipObj in shipObjs if getLevel(shipObj) < level]

def filterFrontProportion(shipObjs, proportion): # 保留前一定比例的船
	return shipObjs[:int(math.ceil(len(shipObjs) * proportion))]

def filterBackProportion(shipObjs, proportion): # 保留后一定比例的船
	return shipObjs[-int(math.ceil(len(shipObjs) * proportion)):]

def filterPracticalness(shipObjs): # 筛掉不实用的船
	global MARUYU_CONST_ID
	return [shipObj for shipObj in shipObjs if not (\
		getLevel(shipObj) < 100 and ShipConstUtility.Id(ShipConstUtility.Base(getConst(shipObj))) == MARUYU_CONST_ID \
	)]

# 排序
def sortByExperienceAsc(shipObjs): # 经验由低到高排序
	return sorted(shipObjs, key=lambda x: getExperience(x))

def sortByExperienceDesc(shipObjs): # 经验由高到低排序
	return sorted(shipObjs, key=lambda x: getExperience(x), reverse=True)

def sortByIdAsc(shipObjs): # ID由低到高排序
	return sorted(shipObjs, key=lambda x: getId(x))

def sortByLevelingPreference(shipObjs): # 以提升整体等级为目的的排序[改后99级以下，改前99级以下，改后99级以上，改前99级以上，其他]（同类内等级升序）
	shipObjs = sortByExperienceAsc(shipObjs)
	upgraded = filterUpgraded(shipObjs)
	notUpgraded = [shipObj for shipObj in shipObjs if shipObj not in upgraded]
	upgraded_below = filterLevelBelow(upgraded, 99)
	upgraded_above = filterLevelRange(upgraded, 99 + 1, MAX_LEVEL - 1)
	upgraded_max = filterLevelAt(notUpgraded, MAX_LEVEL)
	upgraded_99 = filterLevelAt(upgraded, 99)
	notUpgraded_below = filterLevelBelow(notUpgraded, 99)
	notUpgraded_above = filterLevelRange(notUpgraded, 99 + 1, MAX_LEVEL - 1)
	notUpgraded_max = filterLevelAt(notUpgraded, MAX_LEVEL)
	notUpgraded_99 = filterLevelAt(notUpgraded, 99)
	return upgraded_below + notUpgraded_below + upgraded_above + notUpgraded_above + upgraded_99 + notUpgraded_99 + upgraded_max + notUpgraded_max

def sortByForcePreference(shipObjs): # 强度排序[非99级， 满级， 99级]
	level_99 = filterLevelAt(shipObjs, 99)
	level_max = filterLevelAt(shipObjs, MAX_LEVEL)
	max_and_99 = level_max + level_99
	level_not_full = [shipObj for shipObj in shipObjs if shipObj not in max_and_99]
	return sortByExperienceDesc(level_not_full) + max_and_99

# 舰船集合（只列出了普遍用得着的；返回的舰船之后还会依据界面中的设置过滤一遍）
shipsState = None # ShipUtility的一个参数，不提供也可以，但会每次都查询这个值，此处复用的话可以加速执行
lambdas = {}
lists = {}

def getList(key):
	global lambdas
	global lists
	if key not in lists:
		lists[key] = lambdas[key]()
	return lists[key]

lambdas["all"] = lambda: sortByExperienceAsc(filterPracticalness(ShipUtility.All(shipsState))) # 所有舰船，经验升序
#lambdas["all"] = lambda: sortByExperienceAsc(ShipUtility.All(shipsState)) # 所有舰船，经验升序 # 暂时排除掉过滤马路油的函数调用，等待“宗谷”的问题解决后再恢复回来。

lambdas["ex_ss"] = lambda: [shipObj for shipObj in getList("all") if ShipUtility.Type(shipObj) != ShipType.Submarine] # 除去SS
lambdas["ex_ss_ssv"] = lambda: [shipObj for shipObj in getList("ex_ss") if ShipUtility.Type(shipObj) != ShipType.AircraftCarryingSubmarine] # 除去SS ssv

lambdas["de"] = lambda: [shipObj for shipObj in getList("all") if ShipUtility.Type(shipObj) == ShipType.Escort] # DE
lambdas["dd"] = lambda: [shipObj for shipObj in getList("all") if ShipUtility.Type(shipObj) == ShipType.Destroyer] # DD
lambdas["cl"] = lambda: [shipObj for shipObj in getList("all") if ShipUtility.Type(shipObj) == ShipType.LightCruiser] # CL
lambdas["av"] = lambda: [shipObj for shipObj in getList("all") if ShipUtility.Type(shipObj) == ShipType.SeaplaneCarrier] # AV
lambdas["ca"] = lambda: [shipObj for shipObj in getList("all") if ShipUtility.Type(shipObj) == ShipType.HeavyCruiser] # CA
lambdas["cav"] = lambda: [shipObj for shipObj in getList("all") if ShipUtility.Type(shipObj) == ShipType.AircraftCruiser] # CAV
lambdas["ca_cav"] = lambda: sortByExperienceAsc(itertools.chain(getList("ca"), getList("cav"))) # CA 和 CAV
lambdas["bbc"] = lambda: [shipObj for shipObj in getList("all") if ShipUtility.Type(shipObj) == ShipType.BattleCruiser] # BB（高速）
lambdas["bb"] = lambda: [shipObj for shipObj in getList("all") if ShipUtility.Type(shipObj) in (ShipType.Battleship, ShipType.SuperDreadnoughts)] # BB（低速）
lambdas["bbv"] = lambda: [shipObj for shipObj in getList("all") if ShipUtility.Type(shipObj) == ShipType.AviationBattleship] # BBV
lambdas["bb_bbc_bbv"] = lambda: sortByExperienceAsc(itertools.chain(getList("bb"), getList("bbc"), getList("bbv"))) # BB 和 BBC 和 BBV
lambdas["cv"] = lambda: [shipObj for shipObj in getList("all") if ShipUtility.Type(shipObj) == ShipType.AircraftCarrier] # CV
lambdas["cvb"] = lambda: [shipObj for shipObj in getList("all") if ShipUtility.Type(shipObj) == ShipType.ArmouredAircraftCarrier] # CVB
lambdas["cv_cvb"] = lambda: sortByExperienceAsc(itertools.chain(getList("cv"), getList("cvb"))) # CV 和 CVB
lambdas["cvl"] = lambda: [shipObj for shipObj in getList("all") if ShipUtility.Type(shipObj) == ShipType.LightAircraftCarrier] # CVL
lambdas["cv_cvb_cvl"] = lambda: sortByExperienceAsc(itertools.chain(getList("cv"), getList("cvb"), getList("cvl"))) # CV 和 CVB 和 CVL
lambdas["ss"] = lambda: [shipObj for shipObj in getList("all") if ShipUtility.Type(shipObj) == ShipType.Submarine] # SS
lambdas["ssv"] = lambda: [shipObj for shipObj in getList("all") if ShipUtility.Type(shipObj) == ShipType.AircraftCarryingSubmarine] # SSV
lambdas["ss_ssv"] = lambda: sortByExperienceAsc(itertools.chain(getList("ss"), getList("ssv"))) # SS 和 SSV
lambdas["as"] = lambda: [shipObj for shipObj in getList("all") if ShipUtility.Type(shipObj) == ShipType.SubmarineTender] # AS
lambdas["ar"] = lambda: [shipObj for shipObj in getList("all") if ShipUtility.Type(shipObj) == ShipType.RepairShip] # AR
lambdas["ao"] = lambda: [shipObj for shipObj in getList("all") if ShipUtility.Type(shipObj) == ShipType.FleetOiler] # AO
lambdas["ct"] = lambda: [shipObj for shipObj in getList("all") if ShipUtility.Type(shipObj) == ShipType.TrainingCruiser] # CT
lambdas["clt"] = lambda: [shipObj for shipObj in getList("all") if ShipUtility.Type(shipObj) == ShipType.TorpedoCruiser] # CLT

lambdas["cvl_upgraded"] = lambda: filterUpgraded(getList("cvl")) # 至少一改之后的CVL
lambdas["av_upgraded"] = lambda: filterUpgraded(getList("av")) # 至少一改之后的AV
lambdas["cl_upgraded"] = lambda: filterUpgraded(getList("cl")) # 至少一改之后的CL
lambdas["dd_upgraded"] = lambda: filterUpgraded(getList("dd")) # 至少一改之后的DD
lambdas["de_upgraded"] = lambda: filterUpgraded(getList("de")) # 至少一改之后的DE
lambdas["ss_upgraded"] = lambda: filterUpgraded(getList("ss")) # 至少一改之后的SS
lambdas["ssv_upgraded"] = lambda: filterUpgraded(getList("ssv")) # 至少一改之后的SSV
lambdas["ss_ssv_upgraded"] = lambda: filterUpgraded(getList("ss_ssv")) # 至少一改之后的SS和SSV

lambdas["cl_dlc"] = lambda: filterEquiptable(getList("cl_upgraded"), DLC_CONST_ID) # 可以带大发的CL
lambdas["dd_dlc"] = lambda: filterEquiptable(getList("dd_upgraded"), DLC_CONST_ID) # 可以带大发的DD
lambdas["cl_no_dlc"] = lambda: filterNotEquiptable(getList("cl_upgraded"), DLC_CONST_ID) # 不可以带大发的CL
lambdas["dd_no_dlc"] = lambda: filterNotEquiptable(getList("dd_upgraded"), DLC_CONST_ID) # 不可以带大发的DD
lambdas["cl_kht"] = lambda: filterEquiptable(getList("cl_upgraded"), KHT_CONST_ID) # 可以带甲标的CL

lambdas["cl_expedition"] = lambda: filterFrontProportion(sortByLevelingPreference(getList("cl_no_dlc")), 0.8) # 需要靠远征练级的CL
lambdas["dd_expedition"] = lambda: filterFrontProportion(sortByLevelingPreference(getList("dd_no_dlc")), 0.8) # 需要靠远征练级的DD
lambdas["cvl_expedition"] = lambda: filterFrontProportion(sortByLevelingPreference(getList("cvl_upgraded")), 0.8) # 需要靠远征练级的CVL
lambdas["av_expedition"] = lambda: filterFrontProportion(sortByLevelingPreference(getList("av_upgraded")), 0.8) # 需要靠远征练级的AV
lambdas["de_expedition"] = lambda: filterFrontProportion(sortByLevelingPreference(getList("de_upgraded")), 0.8) # 需要靠远征练级的DE
lambdas["ss_ssv_expedition"] = lambda: filterFrontProportion(sortByLevelingPreference(getList("ss_ssv_upgraded")), 0.8) # 需要靠远征练级的SS和SSV
lambdas["cl_leveling"] = lambdas["cl_expedition"] # 保持与旧版全自动远征配置兼容性 TODO: 以后删掉
lambdas["dd_leveling"] = lambdas["dd_expedition"] # 保持与旧版全自动远征配置兼容性 TODO: 以后删掉
lambdas["av_leveling"] = lambdas["av_expedition"] # 保持与旧版全自动远征配置兼容性 TODO: 以后删掉
lambdas["de_leveling"] = lambdas["de_expedition"] # 保持与旧版全自动远征配置兼容性 TODO: 以后删掉

lambdas["expedition"] = lambda: getList("cl_dlc") + getList("dd_dlc") + getList("cl_expedition") + getList("dd_expedition") + getList("cvl_expedition") + getList("av_expedition") + getList("de_expedition") + getList("ss_ssv_expedition") # 被用作全自动远征的船
lambdas["disposable"] = lambda: sortByIdAsc(filterLevelRange(getList("dd"), 1, 5)) # 狗粮

lambdas["bb_asc"] = lambda: sortByLevelingPreference(filterLocked(getList("bb"))) # BB练级排序
lambdas["bbc_asc"] = lambda: sortByLevelingPreference(filterLocked(getList("bbc"))) # BBC练级排序
lambdas["bbv_asc"] = lambda: sortByLevelingPreference(filterLocked(getList("bbv"))) # BBV练级排序
lambdas["bb_bbc_bbv_asc"] = lambda: sortByLevelingPreference(filterLocked(getList("bb_bbc_bbv"))) # BB和BBC和BBV练级排序
lambdas["cv_cvb_asc"] = lambda: sortByLevelingPreference(filterLocked(getList("cv_cvb"))) # CV和CVB练级排序
lambdas["cvl_asc"] = lambda: sortByLevelingPreference(filterLocked(getList("cvl"))) # CVL练级排序
lambdas["cv_cvb_cvl_asc"] = lambda: sortByLevelingPreference(filterLocked(getList("cv_cvb_cvl"))) # CV和CVB和CVL练级排序
lambdas["ca_asc"] = lambda: sortByLevelingPreference(filterLocked(getList("ca"))) # CA练级排序
lambdas["cav_asc"] = lambda: sortByLevelingPreference(filterLocked(getList("cav"))) # CAV练级排序
lambdas["ca_cav_asc"] = lambda: sortByLevelingPreference(filterLocked(getList("ca_cav"))) # CA 和 CAV练级排序
lambdas["av_asc"] = lambda: sortByLevelingPreference(filterLocked(getList("av"))) # AV练级排序
lambdas["cl_asc"] = lambda: sortByLevelingPreference(filterLocked(getList("cl"))) # CL练级排序
lambdas["clt_asc"] = lambda: sortByLevelingPreference(filterLocked(getList("clt"))) # CLT练级排序
lambdas["ct_asc"] = lambda: sortByLevelingPreference(filterLocked(getList("ct"))) # CT练级排序
lambdas["dd_asc"] = lambda: sortByLevelingPreference(filterLocked(getList("dd"))) # DD练级排序
lambdas["de_asc"] = lambda: sortByLevelingPreference(filterLocked(getList("de"))) # DE练级排序
lambdas["ss_ssv_asc"] = lambda: sortByLevelingPreference(filterLocked(getList("ss_ssv"))) # SS和SSV练级排序

lambdas["bbc_desc"] = lambda: sortByForcePreference(filterLocked(getList("bbc"))) # BBC强度排序
lambdas["bbv_desc"] = lambda: sortByForcePreference(filterLocked(getList("bbv"))) # BBV强度排序
lambdas["bb_bbc_bbv_desc"] = lambda: sortByForcePreference(filterLocked(getList("bb_bbc_bbv"))) # BB和BBC和BBV强度排序
lambdas["cv_cvb_desc"] = lambda: sortByForcePreference(filterLocked(getList("cv_cvb"))) # CV和CVB强度排序
lambdas["cvl_desc"] = lambda: sortByForcePreference(filterLocked(getList("cvl"))) # CVL强度排序
lambdas["cv_cvb_cvl_desc"] = lambda: sortByForcePreference(filterLocked(getList("cv_cvb_cvl"))) # CV和CVB和CVL强度排序
lambdas["cav_desc"] = lambda: sortByForcePreference(filterLocked(getList("cav"))) # CAV强度排序
lambdas["ca_desc"] = lambda: sortByForcePreference(filterLocked(getList("ca"))) # CA强度排序
lambdas["ca_cav_desc"] = lambda: sortByForcePreference(filterLocked(getList("ca_cav"))) # CA和CAV强度排序
lambdas["av_desc"] = lambda: sortByForcePreference(filterLocked(getList("av"))) # AV强度排序
lambdas["cl_desc"] = lambda: sortByForcePreference(filterLocked(getList("cl"))) # CL强度排序
lambdas["clt_desc"] = lambda: sortByForcePreference(filterLocked(getList("clt"))) # CLT强度排序
lambdas["ct_desc"] = lambda: sortByForcePreference(filterLocked(getList("ct"))) # CT强度排序
lambdas["cl_kht_desc"] = lambda: sortByForcePreference(filterLocked(getList("cl_kht"))) # 可以带甲标的CL强度排序
lambdas["dd_desc"] = lambda: sortByForcePreference(filterLocked(getList("dd"))) # DD强度排序
lambdas["de_desc"] = lambda: sortByForcePreference(filterLocked(getList("de"))) # DE强度排序
lambdas["ss_ssv_desc"] = lambda: sortByForcePreference(filterLocked(getList("ss_ssv"))) # SS和SSV强度排序

# 迭代器
iters = {}
def reset():
	global shipsState
	global lists
	global iters
	shipsState = GameState.Ships()
	lists.clear()
	iters.clear()

def getIter(key):
	global iters
	if key not in iters: # 创建迭代器
		iters[key] = iter(getIds(getList(key)))
	return iters[key]

def getOne(key):
	try:
		return next(getIter(key))
	except StopIteration:
		iters.pop(key)
		return None # 返回-1也行

#===================================================#
#                                                   #
#                        导出                       #
#                                                   #
#===================================================#
# 入渠
def dock_expedition(id): # 用于刷闪修理防止入渠不用于远征的船
	# 每次都查询就太慢了，但这个确实需要更新，但又不需要更新得太频
	from random import random
	if random() <= 0.05:
		reset()
	return id in getIds(getList("expedition"))

# 编成舰队
def OnCandidate(): # 编成计算时会调用
	reset()

def disposable(): # 因为狗粮受拆船影响大，所以需要经常更新候选
	key = "disposable"
	id = getOne(key) 
	iterEnd = id is None
	isInvalidId = not iterEnd and ShipUtility.Ship(id) is None # 查找不到船了，就说明解体过一次
	if iterEnd or isInvalidId:
		reset()
		id = getOne(key)
	return id

def equip(ship):
	if not grantById(ship):
		return 0
	elif De(ship):
		return 0
	else:
		return 1

def expedition(ship):
	idList = [
	#远征禁用
	  	779,#ise
		242,#日向
		184584,12662,11436,#大和
		176820,21471,15570,#武藏
		17676,#初月改二
	]
	if (ship in idList):
		return 0
	elif not grantById(ship):
		return 0
	else:
		return 1

def grantById(ship): # 除去ID
  idList = [ 
	  # #7-1
	  # 697,#天津风
	  # 205602, #矢矧2
	  # #7-1-1
	  # 599, #雪风
	  # 10810, #照月
	  # 17732, #朝霜
	  # #7-2-2
	  # 17849, #冲波
	  # 40476, #凉月
	  # 10994, #秋云
	  #1-3
	  174644, #云鹰
	  160969, #宗谷
	  2, #时雨
	  933, #黑潮
	  697, #天津风
	  10695, #清霜
	  #4-5
	  100,#凤翔
	  814,#瑞凤
	  8192,#卷云
	  205602,#矢矧2
	  10695,#清霜
	  697,#天津风
	  #演习
	  220190,#矢矧3
	  52157,#JeanBart2
	  226302,#Phoenix
	  223414,#gloire
	  225383,#mogador
	  225381,#Lexington
  ]
  if (ship in idList):
    return 0
  else:
    return 1

def false(ship):
  return 0

def De(ship): # DE
  idList = [ 
	  28002,#国后
	  40400,#对马
	  40410,#佐渡
	  44024,#日振
	  44051,#大东
	  51219,#占守
	  69918,#八丈
	  69968,#福江
	  70445,#石垣
	  88853,#御藏
	  89237,#择捉
	  103352,#松轮
	  113572,#平户
	  173421,#屋代
	  173476,#昭南
	  184582,#仓桥
	  190373,#鹈来
	  194305,#能美
	  199727,#稻木
  ]
  if (ship in idList):
    return 1
  else:
    return 0

def exDeDual(ship):
	idList = [
		128303,#四号
		173451,#三⚪
		201550,#二二
	]
	if (ship in idList):
		return 0
	else:
		return 1
    
def ssDual(ship):
  idList = [ 
	  803,#ro500
	  887,#i168
	  950,#i8
	  1159,#i58
	  2713,#i19
	  18358,#i401
	  20830,#i401
	  20939,#u-511
	  20978,#i401
	  22921,#i26
	  26298,#i13
	  26302,#i14
	  32017,#i504
	  40514,#i400
	  125216,#i47
	  158574,#i203
	  173469,#scamp
	  184491,#i201
	  200609,#i503
	  201504,#Salmon
  ]
  if (ship in idList):
    return 1
  else:
    return 0
    
def avb1(ship):
  idList = [ 
	  10604,#瑞穗
	  24968,#CT
	  31981,#CT	
	  26646,#千代田	
	  53711,#千岁
	  53718,#千岁
	  58078,#日进
	  62407,#千代田
	  158423,#日进
	  158465,#日进
  ]
  if (ship in idList):
    return 1
  else:
    return 0    
    
def grantByLevel_65(ship): # 取自远征38的旗舰等级要求
	global shipsState
	return ShipUtility.Level(ship, shipsState) >= 65

def grantByLevel_50(ship): # 取自远征37、45的旗舰等级要求
	global shipsState
	return ShipUtility.Level(ship, shipsState) >= 50

def grantByLevel_40(ship): # 取自远征B1的旗舰等级要求
	global shipsState
	return ShipUtility.Level(ship, shipsState) >= 40

def grantByLevel_30(ship): # 取自远征41的旗舰等级要求
	global shipsState
	return ShipUtility.Level(ship, shipsState) >= 30

def grantByLevel_20(ship): # 取自远征A2的旗舰等级要求
	global shipsState
	return ShipUtility.Level(ship, shipsState) >= 20

dd_dlc = lambda : getOne("dd_dlc")
dd_no_dlc = lambda : getOne("dd_no_dlc")
cl_no_dlc = lambda : getOne("cl_no_dlc")
cl_dlc = lambda : getOne("cl_dlc")
cl_kht = lambda : getOne("cl_kht")

cvl_expedition = lambda : getOne("cvl_expedition")
av_expedition = lambda : getOne("av_expedition")
cl_expedition = lambda : getOne("cl_expedition")
dd_expedition = lambda : getOne("dd_expedition")
de_expedition = lambda : getOne("de_expedition")
ss_ssv_expedition = lambda : getOne("ss_ssv_expedition")
av_leveling = av_expedition # 保持与旧版全自动远征配置兼容性 TODO: 以后删掉
cl_leveling = cl_expedition # 保持与旧版全自动远征配置兼容性 TODO: 以后删掉
dd_leveling = dd_expedition # 保持与旧版全自动远征配置兼容性 TODO: 以后删掉
de_leveling = de_expedition # 保持与旧版全自动远征配置兼容性 TODO: 以后删掉

bb_asc = lambda : getOne("bb_asc")
bbc_asc = lambda : getOne("bbc_asc")
bbv_asc = lambda : getOne("bbv_asc")
bb_bbc_bbv_asc = lambda : getOne("bb_bbc_bbv_asc")
cv_cvb_asc = lambda : getOne("cv_cvb_asc")
cvl_asc = lambda : getOne("cvl_asc")
cv_cvb_cvl_asc = lambda : getOne("cv_cvb_cvl_asc")
ca_asc = lambda : getOne("ca_asc")
cav_asc = lambda : getOne("cav_asc")
ca_cav_asc = lambda : getOne("ca_cav_asc")
av_asc = lambda : getOne("av_asc")
cl_asc = lambda : getOne("cl_asc")
clt_asc = lambda : getOne("clt_asc")
ct_asc = lambda : getOne("ct_asc")
dd_asc = lambda : getOne("dd_asc")
de_asc = lambda : getOne("de_asc")
ss_ssv_asc = lambda : getOne("ss_ssv_asc")

bbc_desc = lambda : getOne("bbc_desc")
bbv_desc = lambda : getOne("bbv_desc")
bb_bbc_bbv_desc = lambda : getOne("bb_bbc_bbv_desc")
cv_cvb_desc = lambda : getOne("cv_cvb_desc")
cvl_desc = lambda : getOne("cvl_desc")
cv_cvb_cvl_desc = lambda : getOne("cv_cvb_cvl_desc")
cav_desc = lambda : getOne("cav_desc")
ca_desc = lambda : getOne("ca_desc")
ca_cav_desc = lambda : getOne("ca_cav_desc")
av_desc = lambda : getOne("av_desc")
cl_desc = lambda : getOne("cl_desc")
clt_desc = lambda : getOne("clt_desc")
ct_desc = lambda : getOne("ct_desc")
cl_kht_desc = lambda : getOne("cl_kht_desc")
dd_desc = lambda : getOne("dd_desc")
de_desc = lambda : getOne("de_desc")
ss_ssv_desc = lambda : getOne("ss_ssv_desc")
de = lambda : getOne("de")
dd = lambda : getOne("dd")
av = lambda : getOne("av")
ss_ssv = lambda : getOne("ss_ssv")
ex_ss_ssv = lambda : getOne("ex_ss_ssv")
bb = lambda : getOne("bb_bbc_bbv")
ca = lambda : getOne("ca")
cvl = lambda : getOne("cvl")
ass = lambda : getOne("as")


all = lambda : getOne("all")
