# -*- coding: utf-8 -*-
"""Project_Spring_22_group_11.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1TNR-7NK3AfXgWQlLCNXVbvwylx7CdHZv

# Import Libs
"""

# import modules
import pandas as pd
import numpy as np
from pylab import *
import shutil
import sys
import os.path
import seaborn as sns
if not shutil.which("pyomo"):
    !pip install -q pyomo
    assert(shutil.which("pyomo"))

if not (shutil.which("bonmin") or os.path.isfile("bonmin")):
    if "google.colab" in sys.modules:
        !wget -N -q "https://ampl.com/dl/open/bonmin/bonmin-linux64.zip"
        !unzip -o -q bonmin-linux64
        # !apt-get install -y -qq mindtpy
    else:
        try:
            !conda install -c conda-forge ipopt
        except:
            pass

assert(shutil.which("bonmin") or os.path.isfile("bonmin"))

# This is how you should setup the SolverFactory command to use Bonmin
# SolverFactory('bonmin', executable='/content/bonmin')

from pyomo.environ import *


# some stock-specific packages
!pip install yahoo_fin
!pip install requests_html
import yahoo_fin.stock_info as si

# install pyomo
!pip install -q pyomo
from pyomo.environ import *

try:
    import google.colab
    try:
        from pyomo.environ import *
    except:
        !pip install -q pyomo
    if not 'ipopt_executable' in vars():
        !wget -N -q "https://ampl.com/dl/open/ipopt/ipopt-linux64.zip"
        !unzip -o -q ipopt-linux64
        ipopt_executable = '/content/ipopt' # THIS IS NEW! We are using the IPOPT Solver.
except:
    pass

from pyomo.opt import SolverStatus, TerminationCondition

"""#Asset Selected
Stock:

Bed Bath & Beyond Inc. (BBBY).

https://finance.yahoo.com/quote/BBBY?p=BBBY


Gazit-Globe Ltd. (GZTGF)

https://finance.yahoo.com/quote/GZTGF?p=GZTGF

PSG Group Ltd (PSSGF)

https://finance.yahoo.com/quote/PSSGF?p=PSSGF

Veru Inc. (VERU)


https://finance.yahoo.com/quote/VERU?p=VERU

Cryto:

Crypto.com Coin USD (CRO-USD)

https://finance.yahoo.com/quote/CRO-USD?p=CRO-USD

Dogecoin USD (DOGE-USD)

https://finance.yahoo.com/quote/DOGE-USD?p=DOGE-USD

UNUS SED LEO USD (LEO-USD)

https://finance.yahoo.com/quote/LEO-USD?p=LEO-USD

Polygon USD (MATIC-USD)

https://finance.yahoo.com/quote/MATIC-USD?p=MATIC-USD
"""

# Assign the ticker list that we want to scrap
tickers_list = ['CRO-USD','DOGE-USD','LEO-USD','MATIC-USD','GZTGF','PSSGF','VERU','BBBY']
# pull historical price data for each stocks to match with our news score later
dow_prices = {ticker : si.get_data(ticker,start_date = '05/01/2016',end_date='04/22/2022',interval='1d') for ticker in tickers_list}
prep_data = pd.DataFrame(dow_prices['CRO-USD']['adjclose']).rename(columns = {"adjclose":"CRO-USD"})
# combine all the tickers (all the rest of the samples)
for i in tickers_list[1:]:
  prep_data[i] = pd.DataFrame(dow_prices[i]['adjclose'])
prep_data

return_data = pd.DataFrame()
for i in tickers_list:
  return_data[i] = prep_data[i].pct_change()
# drop the na records
return_data.dropna(inplace=True)

df = return_data
df.plot(subplots=True,
        grid=True,
        layout=(3,4),
         figsize=(15,15))
plt.show()

#check the avg return and std-dev
Avg_Return = pd.DataFrame(np.mean(df) ,columns=["Avg_Return"])
print(Avg_Return)#avg
Std_Dev_Return = pd.DataFrame(np.std(df) ,columns=["Std_Dev_Return"])
print(Std_Dev_Return)#std

"""# Build the Nonlinear Optimization Model
We would like to build a portfolio using a combinationon the asset selected above. First we have to construct many porfolio at different volatiles and select the profolio that have the highest return at given risk level  
"""

# creating covariance table on stock return dataframe
df_cov = df.cov()
print('Covariance Matrix:')
print(df_cov)
print('\n') # return/blank line

# create the average of each stock
# these are the objective function COEFFICIENTS!
df_return = df.mean()
print('Average Return:')
print(df_return)

#Optimization Model
m = ConcreteModel()

# defining variables
# each one is a asset selected above (CRO-USD, 'DOGE-USD','LEO-USD','MATIC-USD','GZTGF','PSSGF','VERU','BBBY')
m.CRO_USD = Var(within=NonNegativeReals, bounds=(0,1))#CRO-USD
m.DOGE_USD = Var(within=NonNegativeReals, bounds=(0,1))#DOGE-USD
m.LEO_USD = Var(within=NonNegativeReals, bounds=(0,1))#LEO-USD
m.MATIC_USD = Var(within=NonNegativeReals, bounds=(0,1))#MATIC-USD
m.GZTGF = Var(within=NonNegativeReals, bounds=(0,1))#GZTGF
m.PSSGF = Var(within=NonNegativeReals, bounds=(0,1))#PSSGF
m.VERU = Var(within=NonNegativeReals, bounds=(0,1))#VERU
m.BBBY = Var(within=NonNegativeReals, bounds=(0,1))#BBBY

"""Now we specify the objective function; **maximize your returns**

**The amount you invest in your portfolio** needs to sum to '1'

The **return floor** we set is 0.00% because more than half of the assets are less than zero

It would be interesting to see if any of the asse
ts with negative **avg_return** would be included
"""

# declare objective
m.objective = Objective(expr =
                        m.CRO_USD*df_return[0] +
                        m.DOGE_USD*df_return[1] +
                        m.LEO_USD*df_return[2] +
                        m.MATIC_USD*df_return[3] +
                        m.GZTGF*df_return[4]+
                        m.PSSGF*df_return[5]+
                        m.VERU*df_return[6]+
                        m.BBBY*df_return[7],
                        sense=maximize)

# declare constraints
# 1. Sum of all proportions = 1
m.sum_proportions = Constraint(expr = m.CRO_USD+ m.DOGE_USD+ m.LEO_USD+ m.MATIC_USD+ m.GZTGF+ m.PSSGF+ m.VERU+ m.BBBY == 1)

# 2. Minimum return should be 0%
m.return_floor = Constraint(expr = m.objective >= 0.00)
m.total_risk = Constraint(expr = m.CRO_USD+ m.DOGE_USD+ m.LEO_USD+ m.MATIC_USD+ m.GZTGF+ m.PSSGF+ m.VERU+ m.BBBY >= 0.0)

# creating calculations table for calculate the risk
# 3. Calculate risk
def calc_risk(m):
  variables = m.CRO_USD, m.DOGE_USD, m.LEO_USD, m.MATIC_USD, m.GZTGF, m.PSSGF, m.VERU, m.BBBY
  tickers = ['CRO-USD','DOGE-USD','LEO-USD','MATIC-USD','GZTGF','PSSGF','VERU','BBBY']
  risk_exp = 0
  for i in range(len(variables)):
    for j in range(len(variables)):
      risk_exp += variables[i]*df_cov.at[tickers[i],tickers[j]]*variables[j]
  return risk_exp

# We are going to use this expression to compute the risk
expr_risk = calc_risk(m)

# 3. Max risk should be less than 0.025
max_risk = 0.025
# Sequence of risk levels
risk_limits = np.arange(0.001, max_risk, 0.0005) # take tiny steps
risk_limits

# updating risk contraint for each limit and then solving the problem
param_analysis = {} # key=risk, value =stock allocations
returns = {} # key=risk, value = return
for r in risk_limits:
  # WE REMOVE AND RECALCULATE THE RISK IN EACH ITERATION
  m.del_component(m.total_risk)
  # The LHS remains unchanged; we only modify the RHS (risk threshold)
  m.total_risk = Constraint(expr = expr_risk <= r)
  # run solver
  result = SolverFactory('ipopt', executable=ipopt_executable).solve(m)
  # If solution is not feasible, ignore this run
  if result.solver.termination_condition == TerminationCondition.infeasible:
    continue

  result = result.write()
  # store our allocation proportions
  param_analysis[r] = [m.CRO_USD(), m.DOGE_USD(), m.LEO_USD(), m.MATIC_USD(), m.GZTGF(), m.PSSGF(), m.VERU(), m.BBBY()]
  # store our returns
  # returns[r] = m.objective()
  returns[r] =  m.CRO_USD()*df_return[0] + m.DOGE_USD()*df_return[1] + m.LEO_USD()*df_return[2] + m.MATIC_USD()*df_return[3] + m.GZTGF()*df_return[4]+m.PSSGF()*df_return[5]+m.VERU()*df_return[6]+m.BBBY()*df_return[7]

"""# Parameter Analysis

"""

# generating the dataframe for proportions of the portfolio for each risk limit
param_analysis = pd.DataFrame.from_dict(param_analysis, orient='index')
param_analysis.columns = ['CRO-USD','DOGE-USD','LEO-USD','MATIC-USD','GZTGF','PSSGF','VERU','BBBY']
param_analysis.plot()
plt.title('Optimal Stock Allocation for Different Risk Levels')
plt.show()

# subset
risk = list(returns.keys()) # coerce dict_keys to a list
print(risk)
reward = list(returns.values()) # coerce dict_values to a list
print(reward) # we aren't allowed to name our value 'return' - this is a reserved name.
# plot! pylab makes it easy
from pylab import *
plot(risk, reward, '-.')
title('The Efficient Frontier')
xlabel('Risk')
ylabel('Reward (Return)')
plt.show()

"""#Portfolio selection

Total of 40 risk level. we will select a portfolio consist of exactly 4 assets given the lowest risk level while return is maxmize on that risk level
"""

param_analysis
#select risk level at 0.004
rl=0.004
#CHOOSE DOGE-USD MATIC-USD VERU LEO-USD
pct_1=param_analysis.loc[rl,'DOGE-USD']#df_return[1]
pct_2=param_analysis.loc[rl,'MATIC-USD']#df_return[3]
pct_3=param_analysis.loc[rl,'VERU']#df_return[6]
pct_4=param_analysis.loc[rl,'LEO-USD']#df_return[2]
r_portfolio=returns[rl]

"""#Monte Carlos Simulation

We run 10000 simulations with the pecertage acquire from our model given the risk level equal 0.004
"""

#set seed
np.random.seed(1)
n_simulations = 10000 #10000 simulations
n_make=0
n_lose=0
simulated_returns=[]
#loop
for k in range(n_simulations):
  x = np.random.multivariate_normal(df_return, df_cov)#random generator
  Sm = pct_1*x[1]+pct_2*x[3]+pct_3*x[6]+pct_4*x[2]
  if Sm >0: #if the combination of percentage of four is greater than 0 then we make money
    n_make+=1
  else:
    n_lose+=1
  simulated_returns.append(Sm)
print(n_make/n_simulations)#percentage that we make money

sns.kdeplot(simulated_returns)#show density plot
plt.title('Density plot of Simulated Return', fontsize=18)
plt.xlabel('Return on the day')
plt.ylabel('Count')
plt.show()

"""Roughly 54% of simulated return is greater than 0 and the density plot show most of the return is between 0.1 and -0.1

#Analysis
1.Select one of the portfolio allocations returned by your model containing exactly four assets (it can be the same portfolio allocation used in the previous item). Create a table that shows the price of each asset composing this portfolio on the first day of each month from Jan 1, 2021 (when you would have done your allocation), February 1, 2021 …, through December 1, 2021 (when we imagine you sold your stocks), as well as the aggregate value of the entire portfolio (5 points). Did this portfolio do better than investing in the S&P 500 or Dow Jones Index (5 points)?
"""

selected_port=['DOGE-USD','MATIC-USD','VERU','LEO-USD','^DJI','^GSPC']#selected stock and cryton and SP500 and Dow
dow_prices_1 = {ticker : si.get_data(ticker,start_date = '12/01/2020',end_date='12/01/2021',interval='1mo') for ticker in selected_port}
prep_data_1 = pd.DataFrame(dow_prices_1['DOGE-USD']['adjclose']).rename(columns = {"adjclose":"DOGE-USD"})
# combine all the tickers (all the rest of the samples)
for i in selected_port[1:]:
  prep_data_1[i] = pd.DataFrame(dow_prices_1[i]['adjclose'])
prep_data_1

return_data_1 = pd.DataFrame()
for i in selected_port:
  return_data_1[i] = prep_data_1[i].pct_change()
# drop the na records
return_data_1.dropna(inplace=True)
#rename colunms
return_data_1.rename(columns={'^DJI': 'Dow Jones Index', '^GSPC': 'S&P 500'},inplace=True)
#add aggregate
return_data_1['Aggregate Return']=return_data_1['DOGE-USD']*pct_1+return_data_1['MATIC-USD']*pct_2+return_data_1['VERU']*pct_3+return_data_1['LEO-USD']*pct_4
return_data_1

#made money!!! Aggregate return is greater 0

"""Change your optimization model to force allocations where at least two stocks will receive at least 10% of the budget each."""

#model2
m1 = ConcreteModel()

# defining variables
# each one is a asset selected above (CRO-USD, UST-USD, DAI-USD, LINK-USD, ZSAN, RLFTF, CLVS, BBBY)
m1.CRO_USD = Var(within=NonNegativeReals, bounds=(0,1))
m1.DOGE_USD = Var(within=NonNegativeReals, bounds=(0,1))
m1.LEO_USD = Var(within=NonNegativeReals, bounds=(0,1))
m1.MATIC_USD = Var(within=NonNegativeReals, bounds=(0,1))
m1.GZTGF = Var(within=NonNegativeReals, bounds=(0,1))
m1.PSSGF = Var(within=NonNegativeReals, bounds=(0,1))
m1.VERU = Var(within=NonNegativeReals, bounds=(0,1))
m1.BBBY = Var(within=NonNegativeReals, bounds=(0,1))

#logic constraint
m1.GZTGF_1= Var(domain=Binary)
m1.PSSGF_1 = Var(domain=Binary)
m1.VERU_1 = Var(domain=Binary)
m1.BBBY_1 =Var(domain=Binary)
# declare objective
m1.objective = Objective(expr =
                        m1.CRO_USD*df_return[0] +
                        m1.DOGE_USD*df_return[1] +
                        m1.LEO_USD*df_return[2] +
                        m1.MATIC_USD*df_return[3] +
                        m1.GZTGF*m1.GZTGF_1*df_return[4]+
                        m1.PSSGF*m1.PSSGF_1*df_return[5]+
                        m1.VERU*m1.VERU_1*df_return[6]+
                        m1.BBBY*m1.BBBY_1*df_return[7],
                        sense=maximize)

# declare constraints
# 1. Sum of all proportions = 1
m1.sum_proportions = Constraint(expr = m1.CRO_USD+ m1.DOGE_USD+ m1.LEO_USD+ m1.MATIC_USD+ m1.GZTGF+ m1.PSSGF+ m1.VERU+ m1.BBBY == 1)

# 2. Minimum return should be 0%
m1.return_floor = Constraint(expr = m1.objective >= 0.00)
m1.total_risk = Constraint(expr = m1.CRO_USD+ m1.DOGE_USD+ m1.LEO_USD+ m1.MATIC_USD+ m1.GZTGF+ m1.PSSGF+ m1.VERU+ m1.BBBY >= 0.0)



#at least two stocks will receive at least 10% of the budget each.
m1.constraints = ConstraintList()
m1.constraints.add(m1.GZTGF >= .1*m1.GZTGF_1) # activation
m1.constraints.add(m1.PSSGF >= .1*m1.PSSGF_1) # activation
m1.constraints.add(m1.VERU >= .1*m1.VERU_1) # activation
m1.constraints.add(m1.BBBY >= .1*m1.BBBY_1)# activation
m1.constraints.add(m1.GZTGF_1 + m1.PSSGF_1 + m1.VERU_1 + m1.BBBY_1 >=2)#at least 2 stocks

# creating calculations table for calculate the risk
# 3. Calculate risk
def calc_risk1(m1):
  variables1 = m1.CRO_USD, m1.DOGE_USD, m1.LEO_USD, m1.MATIC_USD, m1.GZTGF, m1.PSSGF, m1.VERU, m1.BBBY
  tickers1 = ['CRO-USD','DOGE-USD','LEO-USD','MATIC-USD','GZTGF','PSSGF','VERU','BBBY']
  risk_exp1 = 0
  for i in range(len(variables1)):
    for j in range(len(variables1)):
      risk_exp1 += variables1[i]*df_cov.at[tickers1[i],tickers1[j]]*variables1[j]
  return risk_exp1

# We are going to use this expression to compute the risk
expr_risk1 = calc_risk1(m1)

# 3. Max risk should be less than 0.05
max_risk1= 0.015
# Sequence of risk levels
risk_limits1 = np.arange(0.001, max_risk1, 0.0005) # take tiny steps
risk_limits1

# updating risk contraint for each limit and then solving the problem
param_analysis1 = {} # key=risk, value =stock allocations
returns1 = {} # key=risk, value = return
for r in risk_limits1:
  # WE REMOVE AND RECALCULATE THE RISK IN EACH ITERATION
  m1.del_component(m1.total_risk)
  # The LHS remains unchanged; we only modify the RHS (risk threshold)
  m1.total_risk = Constraint(expr = expr_risk1 <= r)
  # run solver
  result1 = SolverFactory('ipopt', executable=ipopt_executable).solve(m1)
  # If solution is not feasible, ignore this run
  if result1.solver.termination_condition == TerminationCondition.infeasible:
    continue

  result1 = result1.write()
  # store our allocation proportions
  param_analysis1[r] = [m1.CRO_USD(), m1.DOGE_USD(), m1.LEO_USD(), m1.MATIC_USD(), m1.GZTGF(), m1.PSSGF(), m1.VERU(), m1.BBBY()]
  # store our returns
  # returns[r] = m.objective()
  returns1[r] =  m1.CRO_USD()*df_return[0] + m1.DOGE_USD()*df_return[1] + m1.LEO_USD()*df_return[2] + m1.MATIC_USD()*df_return[3] + m1.GZTGF()*df_return[4]+m1.PSSGF()*df_return[5]+m1.VERU()*df_return[6]+m1.BBBY()*df_return[7]

param_analysis1 = pd.DataFrame.from_dict(param_analysis1, orient='index')#dataprep for the graph
param_analysis1.columns = ['CRO-USD','DOGE-USD','LEO-USD','MATIC-USD','GZTGF','PSSGF','VERU','BBBY']
param_analysis1.plot()
plt.title('Optimal Stock Allocation for Different Risk Levels')
plt.show()

"""At any risk level there will always be at least 2 stocks that have more than 10% of the budget. At the plateaus we assign 10% to Veru and 10% to PSSGF  """

# subset
risk1 = list(returns1.keys()) # coerce dict_keys to a list
print(risk)
reward1 = list(returns1.values()) # coerce dict_values to a list
print(reward) # we aren't allowed to name our value 'return' - this is a reserved name.
# plot! pylab makes it easy
from pylab import *
plot(risk1, reward1, '-.')
title('The Efficient Frontier')
xlabel('Risk')
ylabel('Reward (Return)')
plt.show()