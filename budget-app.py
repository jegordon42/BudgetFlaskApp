from flask import Flask # include the flask library 
from flask import request
from flask import json

app = Flask(__name__) 

import pyodbc 
conn = pyodbc.connect('Driver={ODBC Driver 17 for SQL Server};Server=tcp:budgetapp.database.windows.net,1433;Database=budgetDB;Uid=jegordon42;Pwd={Never4get42};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;')
cursor = conn.cursor()

@app.route("/") 
def index(): 
   return "Hello, World!" 

@app.route("/SignUp") 
def SignUp(): 
    username = ""
    firstName = request.args.get('firstName')
    lastName = request.args.get('lastName')
    email = request.args.get('email')
    password = request.args.get('password')

    getUserSQL = "SELECT UserId FROM BudgetDB.dbo.Users Where Email = '" + email + "'"
    cursor.execute(getUserSQL)
    row=cursor.fetchone()
    if (row is not None):
        response = app.response_class(
            response=json.dumps({'message' : 'User already exists!'}),
            mimetype='application/json'
        )
        return response

    addUserSQL =  "INSERT INTO BudgetDB.dbo.Users (Username, FirstName, LastName, Email, Password) VALUES " 
    addUserSQL += "(' " + username + "', '" + firstName + "', '" + lastName + "', '" + email + "', '" + password + "')"         
    cursor.execute(addUserSQL)
    conn.commit()

    getUserSQL = "SELECT UserId FROM BudgetDB.dbo.Users Where Email = '" + email + "' and password = '" + password + "'"
    cursor.execute(getUserSQL)
    row=cursor.fetchone()
    userId = row[0]

    addCategoriesSql = "INSERT INTO BudgetDB.dbo.UserCategories (UserId, CategoryName, CategoryType, PlannedSpending) VALUES "
    addCategoriesSql += "(" + str(userId) + ", 'Category 1', 'Expense', 100),"
    addCategoriesSql += "(" + str(userId) + ", 'Category 2', 'Expense', 100),"
    addCategoriesSql += "(" + str(userId) + ", 'Category 3', 'Expense', 100),"
    addCategoriesSql += "(" + str(userId) + ", 'Category 1', 'Income', 100),"
    addCategoriesSql += "(" + str(userId) + ", 'Category 2', 'Income', 100),"
    addCategoriesSql += "(" + str(userId) + ", 'Category 3', 'Income', 100)"
    cursor.execute(addCategoriesSql)
    conn.commit()

    userObj = GetUserObj(userId)

    response = app.response_class(
        response=json.dumps(userObj),
        mimetype='application/json'
    )

    return response

@app.route("/Login") 
def Login(): 
    email = request.args.get('email')
    password = request.args.get('password')

    getUserSQL = "SELECT * FROM BudgetDB.dbo.Users Where Email = '" + email + "' and password = '" + password + "'"
    cursor.execute(getUserSQL)
    userResult = cursor.fetchone()

    if(userResult is not None):
        userId = userResult[0]
        userObj = GetUserObj(userId)
        
        response = app.response_class(
            response=json.dumps(userObj),
            mimetype='application/json'
        )
    else:
        response = app.response_class(
            response=json.dumps({'message' : 'Invalid Email/Password'}),
            mimetype='application/json'
        )
    return response

def GetUserObj(userId):
    getUserSQL = "SELECT * FROM BudgetDB.dbo.Users Where UserId = " + str(userId) 
    cursor.execute(getUserSQL)
    userResult = cursor.fetchone()

    user = {
        'userId' : userResult[0],
        'firstName' : userResult[2],
        'lastName' : userResult[3],
        'email' : userResult[4],
        'password' : userResult[5]
    }

    getUserCategoriesSQL = "SELECT * FROM BudgetDB.dbo.UserCategories Where UserId=" + str(userId)
    cursor.execute(getUserCategoriesSQL)
    userCategoriesResult = cursor.fetchall()
    expenseCategories = []
    incomeCategories = []
    if(userCategoriesResult is not None):
        for category in list(filter(lambda category: category[3] == "Expense", userCategoriesResult)):
            expenseCategories.append({'CategoryId' : category[0], 'CategoryName' : category[2], 'Planned' : float(category[4])})

        for category in list(filter(lambda category: category[3] == "Income", userCategoriesResult)):
            incomeCategories.append({'CategoryId' : category[0], 'CategoryName' : category[2], 'Planned' : float(category[4])})

    getTransactionsSQL = "SELECT T.TransactionId, T.UserCategoryId, T.Description, T.Amount, T.TransactionDate, T.TransactionType, T.UserId FROM dbo.Transactions T  Where T.UserId=" + str(userId) + " ORDER BY T.TransactionDate DESC, T.TransactionId DESC"
    cursor.execute(getTransactionsSQL)
    transactionsResult = cursor.fetchall()
    expenseTransactions = []
    incomeTransactions = []
    if(transactionsResult is not None):
        for transaction in list(filter(lambda transaction: transaction[5] == "Expense", transactionsResult)):
            expenseTransactions.append({'TransactionId' : transaction[0], 'CategoryId' : transaction[1], 'Description' : transaction[2], 'Amount' : float(transaction[3]), 'Date' : transaction[4]})

        for transaction in list(filter(lambda transaction: transaction[5] == "Income", transactionsResult)):
            incomeTransactions.append({'TransactionId' : transaction[0], 'CategoryId' : transaction[1], 'Description' : transaction[2], 'Amount' : float(transaction[3]), 'Date' : transaction[4]})

    return {
        'message' : 'Success', 
        'user' : user, 
        'expenseCategories' : expenseCategories, 
        'incomeCategories' : incomeCategories, 
        'expenseTransactions' : expenseTransactions, 
        'incomeTransactions' : incomeTransactions
    }

@app.route("/AddCategories", methods=['GET', 'POST']) 
def AddCategories():
    userId = request.json['userId']
    categoriesToAdd = request.json['categoriesToAdd']
    categoryType = request.json['categoryType']

    addCategoriesSql = "INSERT INTO BudgetDB.dbo.UserCategories (UserId, CategoryName, CategoryType, PlannedSpending) VALUES "
    for category in categoriesToAdd:
        addCategoriesSql += "( " + str(userId) + ", '" + str(category['CategoryName']) + "', '" + categoryType + "', " + str(category['PlannedSpending']) + "),"
    addCategoriesSql = addCategoriesSql[:-1]
    
    cursor.execute(addCategoriesSql)
    conn.commit()

    getCategoriesSQL =  "SELECT * FROM BudgetDB.dbo.UserCategories Where UserId="  + str(userId) + " and CategoryType='" + categoryType + "'" 
    cursor.execute(getCategoriesSQL)
    categoryResult = cursor.fetchall()
    categories = []
    for category in categoryResult:
        categories.append({'CategoryId' : category[0], 'UserId' : category[1], 'CategoryName' : category[2], 'Planned' : float(category[4])})

    response = app.response_class(
        response=json.dumps({'message' : 'Success', 'categories' : categories}),
        mimetype='application/json'
    )
    return response

@app.route("/DeleteCategories", methods=['GET', 'POST']) 
def DeleteCategories():
    categoryIdsToDelete = request.json['categoryIdsToDelete']

    inList = "("
    for categoryId in categoryIdsToDelete:
        inList += str(categoryId) + ','
    inList = inList[:-1]
    inList += ")"

    deleteCategoriesSQL =  "DELETE FROM BudgetDB.dbo.UserCategories WHERE UserCategoryId IN " +  inList
    cursor.execute(deleteCategoriesSQL)
    conn.commit()

    response = app.response_class(
        response=json.dumps({'message' : 'Success'}),
        mimetype='application/json'
    )
    return response


@app.route("/UpdateCategory", methods=['GET', 'POST']) 
def UpdateCategory():
    category = request.json['category']

    updateCategorySQL = "UPDATE BudgetDB.dbo.UserCategories SET "
    updateCategorySQL += "CategoryName = '" + category['CategoryName'] + "', "
    updateCategorySQL += "PlannedSpending = " + str(category['Planned']) + " "
    updateCategorySQL += "WHERE UserCategoryId = " + str(category['CategoryId'])

    cursor.execute(updateCategorySQL)
    conn.commit()

    response = app.response_class(
        response=json.dumps({'message' : 'Success'}),
        mimetype='application/json'
    )
    return response

@app.route("/UpdateTransaction", methods=['GET', 'POST']) 
def UpdateTransaction():
    transaction = request.json['transaction']

    updateTransactionSQL = "UPDATE BudgetDB.dbo.Transactions SET "
    updateTransactionSQL += "UserCategoryId = " + str(transaction['CategoryId']) + ", "
    updateTransactionSQL += "Description = '" + transaction['Description'] + "', "
    updateTransactionSQL += "Amount = " + str(transaction['Amount']) + ", "
    updateTransactionSQL += "TransactionDate = '" + transaction['Date'] + "' "
    updateTransactionSQL += "WHERE TransactionId = " + str(transaction['TransactionId'])

    cursor.execute(updateTransactionSQL)
    conn.commit()

    response = app.response_class(
        response=json.dumps({'message' : 'Success'}),
        mimetype='application/json'
    )
    return response

@app.route("/AddTransactions", methods=['GET', 'POST']) 
def AddTransactions():
    userId = request.json['userId']
    transactionsToAdd = request.json['transactionsToAdd']
    transactionType = request.json['transactionType']

    addTransactionsSql = "INSERT INTO BudgetDB.dbo.Transactions (UserId, UserCategoryId, TransactionType, Description, Amount, TransactionDate) VALUES "
    for transaction in transactionsToAdd:
        addTransactionsSql += "( " + str(userId) + ", " + str(transaction['CategoryId']) + ", '" + transactionType + "', '" + transaction['Description'].replace("'", "''") + "', " + str(transaction['Amount']) + ", '" + transaction['Date'] + "'),"
    addTransactionsSql = addTransactionsSql[:-1]
    
    cursor.execute(addTransactionsSql)
    conn.commit()

    getTransactionsSQL = "SELECT T.TransactionId, T.UserCategoryId, T.Description, T.Amount, T.TransactionDate, T.TransactionType, T.UserId FROM dbo.Transactions T  Where T.UserId=" + str(userId) + " ORDER BY T.TransactionDate DESC, T.TransactionId DESC"
    cursor.execute(getTransactionsSQL)
    transactionsResult = cursor.fetchall()
    transactions = []
    for transaction in list(filter(lambda transaction: transaction[5] == transactionType, transactionsResult)):
        transactions.append({'TransactionId' : transaction[0], 'CategoryId' : transaction[1], 'Description' : transaction[2], 'Amount' : float(transaction[3]), 'Date' : transaction[4]})

    response = app.response_class(
        response=json.dumps({'message' : 'Success', 'transactions' : transactions}),
        mimetype='application/json'
    )
    return response

@app.route("/DeleteTransactions", methods=['GET', 'POST']) 
def DeleteTransactions():
    transactionIdsToDelete = request.json['transactionIdsToDelete']

    inList = "("
    for transactionId in transactionIdsToDelete:
        inList += str(transactionId) + ','
    inList = inList[:-1]
    inList += ")"

    deleteTransactionssSQL =  "DELETE FROM BudgetDB.dbo.Transactions WHERE TransactionId IN " +  inList
    cursor.execute(deleteTransactionssSQL)
    conn.commit()

    response = app.response_class(
        response=json.dumps({'message' : 'Success'}),
        mimetype='application/json'
    )
    return response

if __name__ == '__main__': 
   app.run(host='0.0.0.0',port="8000",debug=True)