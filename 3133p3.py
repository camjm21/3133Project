from gurobipy import *
import pandas as pd
import numpy as np
# Create the model
m = Model("project")

#Read in data
sData = pd.read_excel("/Users/cameronmoore/Downloads/zoo data.xlsx", sheet_name = "Species Data", header = 0)
fData = pd.read_excel("/Users/cameronmoore/Downloads/zoo data.xlsx", sheet_name = "Attractions", header = 0)

#Make index data
col = list(sData.columns)
foods = []
for i in col:
    if "Food" in i:
        foods.append(i)

maturities = []
r =sData.iloc[0].tolist()
r = r[2:4]

sData = sData.iloc[1:,:]


#Make indices
#species
species = sData.iloc[:, 0].tolist()
#maturities
for i in r:
    maturities.append(i[0:5])
#foods
foods.pop(0)
#actions
actions = ["renovated", "retrofitted"]




#Get all parameters and turn to floats if needed
ahAge = sData.iloc[:, 1].tolist()
ahAgeDF = pd.DataFrame(ahAge, index = species)

cFood = sData.iloc[:, 2].tolist()
cFood = [float(i) for i in cFood]
aFood = sData.iloc[:, 3].tolist()
aFood = [float(i) for i in aFood]


f1cost = sData.iloc[:, 4].tolist()
f1cost = [float(i) for i in f1cost]
f1wv = sData.iloc[:, 5].tolist()
f1wv = [float(i) for i in f1wv]

f2cost = sData.iloc[:, 6].tolist()
f2cost = [float(i) for i in f2cost]
f2wv = sData.iloc[:, 7].tolist()
f2wv = [float(i) for i in f2wv]

f3cost = sData.iloc[:, 8].tolist()
f3cost = [float(i) for i in f3cost]
f3wv = sData.iloc[:, 9].tolist()
f3wv = [float(i) for i in f3wv]



#Make dataframes with parameter data
foodDict = {maturities[0] : cFood, maturities[1] : aFood}
foodDF = pd.DataFrame(data = foodDict, index = species, columns = maturities)

wvDict = {foods[0] : f1wv, foods[1] : f2wv, foods[2] : f3wv}
wvDF = pd.DataFrame(wvDict, index = species)

costDict = {foods[0] : f1cost, foods[1] : f2cost, foods[2] : f3cost}
costDF = pd.DataFrame(costDict, index = species)




#Constant paramaters
aqc = 100000
aqr = 200000
mqai = 20000
ring = 10
mpm = .05



# Get facilities index and investments parameter dataframe
facilities = (fData.iloc[:, 0]).tolist()
investments = (fData.iloc[:, 1]).tolist()
investmentsDF = pd.DataFrame(investments, index = facilities)


#Get problem data
aData = pd.read_excel("/Users/cameronmoore/Downloads/zoo data.xlsx", sheet_name = "Animals", header = 0)
zero_data = np.zeros(shape=(len(species),len(maturities)))
aCount = pd.DataFrame(zero_data, index = species, columns=maturities)

#set up the count of each species and maturity
aData = aData.iloc[:, 1:3]
ages = []
for i in range(0, len(aData.index)):
    a = aData.iloc[i].tolist()
    ages.append(a)


for i in ages:
    if i[1] < float(ahAgeDF.loc[i[0]]):
        aCount.loc[i[0], "Child"] = aCount.loc[i[0], "Child"] + 1
    else:
        aCount.loc[i[0], "Adult"] = aCount.loc[i[0], "Adult"] + 1

aCount["Total"] = aCount.sum(axis = 1)
aCount.loc["Totals", :] = aCount.sum(axis = 0)
#aCount now has number of children and adults per species

# Get indices for species in reserve and not in reserve
speciesNotInReserve = []
speciesInReserve = []
for index, row in aCount.iterrows():
    if row[0] + row[1] == 0:
        speciesNotInReserve.append(index)
    else:
        speciesInReserve.append(index)
del speciesInReserve[-1]


inReserveList = []
for i in species:
    if i in speciesNotInReserve:
        inReserveList.append(1)
    else:
        inReserveList.append(0)

inReserveDF = pd.DataFrame(inReserveList, index = species)

#Get index of Big Cat Species
bigCats = []
bigCats.append(species[4])
bigCats.append(species[5])
bigCats.append(species[6])
bigCats.append(species[9])

#get index for non-Big Cat species
nonBigCats = []
for i in species:
    if i in bigCats:
        pass
    else:
        nonBigCats.append(i)

#Have parameters equal the model specifications:
RF = foodDF
WV = wvDF
N = aCount
M = investmentsDF
C = costDF
A = ahAgeDF
I = inReserveDF


# Make decision variables
x = m.addVars(species, maturities, foods, name = 'X')
d = m.addVars(facilities, name = 'D')
y = m.addVars(species, maturities, vtype = GRB.INTEGER, name = 'Y')
z = m.addVars(species, vtype = GRB.BINARY, name = 'Z')
e = m.addVars(species, actions, vtype = GRB.BINARY, name = 'E')

#Make objective function
m.setObjective(quicksum(quicksum(WV.loc[i, k] * x[i, j, k] for k in foods) / RF.loc[i, j] for j in maturities for i in species), GRB.MAXIMIZE)

#Add original Constraints
m.addConstrs(d[a] <= mqai for a in facilities)

m.addConstr(aqr + (3*float(ring)/10000) * quicksum(d[a] * M.loc[a, 0] for a in facilities) >= (1 + mpm) * (aqc + quicksum(d[a] for a in facilities) + quicksum((9 * C.loc[i, k]) * quicksum(x[i, j, k] for j in maturities) for k in foods for i in species)))

#Part 3 Constraints
m.addConstrs(quicksum(x[i, j, k] for k in foods) / RF.loc[i, j] == N.loc[i, j] + y[i, j] for j in maturities for i in species)


m.addConstrs(y[i, j] <= 2 for i in nonBigCats for j in maturities)
m.addConstr(quicksum(y[i, j] for i in species for j in maturities) >= 5)
m.addConstr(quicksum(y[i, "Child"] for i in species) == 0)
m.addConstr(quicksum(z[i] for i in bigCats) <= 1)
m.addConstrs(z[i] == e[i, "renovated"] for i in bigCats)
m.addConstr(quicksum(z[i] * I.loc[i] for i in species) <= 1)
m.addConstr(quicksum(e[i, "renovated"] for i in nonBigCats) <= 2)
m.addConstrs(e[i, "retrofitted"] == z[i] * I.loc[i] for i in species)
m.addConstrs(e[i, "retrofitted"] + e[i, "renovated"] <= 1 for i in species)
m.addConstr(quicksum(e[i, "retrofitted"] for i in species) <= 1)
m.addConstrs(e[i, "retrofitted"] + e[i, "renovated"] == z[i] for i in species)

#Capacities
m.addConstrs(y[i, "Adult"] <= 5*e[i, "renovated"] - (quicksum(N.loc[i, j] for j in maturities) *e[i, "renovated"]) for i in speciesInReserve)
m.addConstrs(e[i, "renovated"] == 0 for i in speciesNotInReserve)

m.addConstrs(y[i, "Adult"] <= 2*e[i, "retrofitted"] for i in speciesNotInReserve)
m.addConstrs(e[i, "retrofitted"] == 0 for i in speciesInReserve)



#Solve the LP
m.optimize()

#Look at decision variables
for v in m.getVars():
    print("%s %g" % (v.varName, v.x))

#m.write("3133output.lp")

#Decision variables make sense!

