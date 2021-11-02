
from gurobipy import *
import pandas as pd
# Create the model
m = Model("project")

#Read in Species data
sData = pd.read_excel("/Users/cameronmoore/Downloads/zoo data.xlsx", sheet_name = "Species Data", header = 0)



#Get Food types index
col = list(sData.columns)
foods = []
for i in col:
    if "Food" in i:
        foods.append(i)
foods.pop(0)

# Get maturity levels index
maturities = []
r =sData.iloc[0].tolist()
r = r[2:4]
for i in r:
    maturities.append(i[0:5])

#Get species index
sData = sData.iloc[1:,:]
species = sData.iloc[:, 0].tolist()



#Get all parameters and turn to floats if needed
ahAge = sData.iloc[:, 1].tolist()

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



#Get Attractions data
fData = pd.read_excel("/Users/cameronmoore/Downloads/zoo data.xlsx", sheet_name = "Attractions", header = 0)


# Get facilities index
facilities = (fData.iloc[:, 0]).tolist()
investments = (fData.iloc[:, 1]).tolist()
investmentsDF = pd.DataFrame(investments, index = facilities)



#Get problem data
aData = pd.read_excel("/Users/cameronmoore/Downloads/zoo data.xlsx", sheet_name = "Animals", header = 0)



# Make decision variables
x = m.addVars(species, maturities, foods)
y = m.addVars(facilities)

#Make objective function



#Add Constraints
m.addConstrs(y[a] <= mqai for a in facilities)
m.addConstrs(quicksum(x[i, j, k] for k in foods) == foodDF.loc[i, j] for i in species for j in maturities)
m.addConstrs((quicksum(wvDF.loc[i, k] * x[i, "Child", k] for k in foods)/foodDF.loc[i, "Child"]) == (quicksum(wvDF.loc[i, k] * x[i, "Adult", k] for k in foods)/foodDF.loc[i, "Adult"]) for i in species)
m.addConstr(aqr + (3*float(ring)/10000) * quicksum(y[a] * investmentsDF.loc[a, 0] for a in facilities) >= (1 + mpm) * (aqc + quicksum(y[a] for a in facilities) + quicksum((costDF.loc[i, k]/10) * quicksum(x[i, j, k] for j in maturities) for k in foods for i in species)))





#print(investmentsDF)
