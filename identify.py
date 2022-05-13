#!/usr/lib/cgi-bin/venv/bin/python

''' identify.py
This script is just an example of a back-end web application to explode a relational database containing data on
customer and products (a kind of oversimplified Customer Relationship Management (CRM).

It is implemented to evaluate the use of Python CGIs to support web page interaction.

The solution implemented use a structured approach, where a set of functions are defined to perform the functionalities
requested.

Note: Debugging CGI is cumbersome because the web server does not provide too much information when the CGI fails.
It can be got some information on the CGI behaviour adding a print trace of data values at different places of
the CGI to identify the failures. To do that, simply add a function like:

def debugTrace(value):
    print(value)
    return

... and add at the beginning of the script execution:
import sys

cgitb.enable()
sys.stderr = sys.stdout
debugTrace("Content-Type:text/plain\r\n")
debugTrace('GCI start')
... and add call to debugTrace in points where you can trace execution.

This will allow you to examine the trace and other data in the web browser.

It can be useful to add:
LogLevel debug
in the /etc/apache2/sites-available/xxxx.conf you are using.
'''

import cgi
import cgitb
import sqlite3
import matplotlib
matplotlib.use('Agg')   # see 'Matplotlib in a web application server' for understanding this issue
import matplotlib.pyplot as plt
from jinja2 import Environment, FileSystemLoader, select_autoescape

# directories where application artifacts are placed (absolute paths). They are installation dependent
# they shall have adequate rwx permissions to allow web server access them
dirPages = "/var/www/html/"     # the place for html pages. It is the default apache2 config in ubuntu 18
dirImages = dirPages + "img/"   # where images referenced in html pages will be created by the script
dirCgi = "/usr/lib/cgi-bin/"    # the place for CGIs.  It is the default apache2 config in ubuntu 18
dirTemplates = dirCgi +"templates" # where application templates to be rendered are
dirData = "/var/lib/crmlite/"   # the place for specific applications data
dataBase = dirData + "crmlite.db"   # the database used by this application

def identify(env, userId):
    '''
    The identify view gets data from the 'identify' request sent by the browser from the index page, and
    triggers the action to show the related data, which depend on the type of user.
    :param env: the jinja environment of the request
    :param userId: the user identification
    :return: the web page with user related data, or the error page in case of erroneous input data
    '''
    userRegister, userType = getUserData(userId)
    if userType == 'A':
        return makeAdminPage(env)
    elif userType == 'P':
        return makeSupplierPage(env, userRegister)
    elif userType == 'C':
        return makeCustomerPage(env, userRegister)
    else:
        pass
    errorTemplate = env.get_template('error.html')
    return errorTemplate.render({'userId': userId})

def hbarsPlot (pltData, pltTitle, pltXlabel, pltYlable, fileName):
    '''
    hbarsPlot plots a simple horizontal bar chart with data passed
    :param pltData: a dictionary with keys (in y) and values (in x)
    :param pltTitle: title of the figure
    :param pltXlabel: the label for y
    :param pltYlable: the lable for x
    :param fileName: the name of the file to save the figure
    :return:
    '''
    global dirImages
    plt.clf()
    plt.title(pltTitle)
    plt.xlabel(pltXlabel)
    plt.ylabel(pltYlable)
    plt.barh(list(pltData.keys()), list(pltData.values()))
    plt.savefig(dirImages + fileName)

def getPeriod():
    '''
    Gets the initial and final date of the period activities in the BD belong
    :return: initial and final date
    '''
    global dataBase
    dbConexion = sqlite3.connect(dataBase)
    cursor = dbConexion.cursor()
    cursor.execute('SELECT MIN(date) FROM activity')
    initial = cursor.fetchone()
    cursor.execute('SELECT MAX(date) FROM activity')
    final = cursor.fetchone()
    dbConexion.close()
    return initial[0], final[0]

def queryActivity(user, inout):
    '''
    Performs the query on the DB extracting all products having activity (in or out) in the period, and it cost or price.
    :param user: the user identification
    :param inout: the activity movements to be computed: "C" (inputs), "V" (outputs)
    :return: a list of registers, each one containing the product name and cost or price
    '''
    global dataBase
    dbConexion = sqlite3.connect(dataBase)
    cursor = dbConexion.cursor()
    query = 'SELECT products.name, activity.price FROM products, activity WHERE activity.idproduct = products.id'
    if len(inout) != 0:
        query += ' AND activity.inout = "' + inout + '"'
    if len(user) != 0:
        query = query + ' AND activity.idsuppocust = "' + user + '"'
    cursor.execute(query)
    allActs = cursor.fetchall()
    dbConexion.close()
    return allActs

def makeAdminPage(request):
    '''
    makeAdminPage collect data related to all sales and purchases registered in the BD, and builds the web page
    to show this data.
    :param request: the HTTP request received by the server
    :return: the web page with administrator related data
    '''
    # put in a dictionary the sales per product during current period and plot them
    dicData = getValues('V')
    hbarsPlot(dicData, 'Sales per product', 'Sales', 'Product', 'graph-admin-sales.jpg')
    # compute the total amount of sales
    totalSales = 0
    for product, price in dicData.items():
        totalSales += price
    # put in a dictionary the accumulated outputs for each product and generate the graph
    dicData = getActivity('', 'V')
    hbarsPlot(dicData, 'Units sold', 'Units', 'Product', 'graph-admin-units-sold.jpg')
    # put in a dictionary the accumulated inputs for each product and compute balance
    balance = getActivity('', 'C')
    # compute the net balance of inventory
    for product, cant in dicData.items():
        if product in balance:
            balance[product] = balance[product] - cant
        else:
            balance[product] = -cant
    # plot balance
    hbarsPlot(balance, 'Product balance', 'Outputs minus inputs', 'Product', 'graph-admin-inventory.jpg')
    initialDate, finalDate = getPeriod()
    adminTemplate = env.get_template('admin.html')
    return adminTemplate.render({
        'initial': initialDate,
        'final': finalDate,
        'sales': totalSales,
        'alerts': stockAlert(balance)})

def makeSupplierPage(request, regCoP):
    '''
    makeSupplierPage collects data on all supplies from the BD for a given supplier and builds a web page to show them.
    :param regCoP: a register with the supplier identification data
    :return: the web page with supplier related data
    '''
    # the register to keep data of the client or supplier
    # put in a dictionary the supplies per product during period and plot them
    supplies = getActivity(regCoP[0], 'C')
    hbarsPlot(supplies, 'Supplies per product', 'Supply', 'Product', 'graph-supplier.jpg')
    initialDate, finalDate = getPeriod()
    return env.get_template('supplier.html').render({
        'name': regCoP[1],
        'street': regCoP[2],
        'city': regCoP[3],
        'state': regCoP[4],
        'initial': initialDate,
        'final': finalDate })

def makeCustomerPage(request, regCoP):
    '''
    makeCustomerPage collects data on all sales from the BD to a given customer and builds a web page to show them.
    :param regCoP: a register with the customer identification data
    :return: the web page with customer related data
    '''
    # put in a dictionary the sales per product during period and plot them
    sales = getActivity(regCoP[0], 'V')
    hbarsPlot(sales, 'Sales per product', 'Sales', 'Product', 'graph-customer.jpg')
    initialDate, finalDate = getPeriod()
    return env.get_template('customer.html').render({
                            'name': regCoP[1],
                            'street':  regCoP[2],
                            'city':  regCoP[3],
                            'state':  regCoP[4],
                            'initial':  initialDate,
                            'final':  finalDate})

def stockAlert(balance):
    '''
    stckAlert computes the current amount of existences for each product and determines if its level is below the
    minimum requested. In this case, an alert flag is raised for the product.
    :param balance: a dictionary with the net amount of inputs minus outputs for each product during the current period
    :return: the list of products below the alert level
    '''
    dbConexion = sqlite3.connect(dataBase)
    cursor = dbConexion.cursor()
    query = 'SELECT name, initialstock, minimumstock, location FROM products'
    cursor.execute(query)
    regProd= cursor.fetchall()
    dbConexion.close()
    # update balance of the period with the initial stock
    for reg in regProd:
        product = reg[0]
        if product in balance:
            balance[product] = balance[product] + reg[1]
        else:
            balance[product] = reg[1]
    # make a list with the products being below the minimum stock
    productsBelowLevel = []
    for reg in regProd:
        name = reg[0]
        min = reg[2]
        if name in balance:
            stock = balance[name]
            if stock < min:
                productsBelowLevel.append([name, reg[3], min, stock])
    return productsBelowLevel

def getUserData(identification):
    '''
    getUserData checks if the given identification is correct, and returns the type of user it is and the existing data.
    #TODO verify if the given password is correcto or not
    :param identification: the user identification
    :return: the user register and type -"A" (if Administrator), "C" (if Customer), "P" (if suPplier)-
    '''
    userData = []
    userType = 'A'
    if identification == 'admin':
        return userData, userType
    # get user data from the DB
    dbConexion = sqlite3.connect(dataBase)
    cursor = dbConexion.cursor()
    # check if it is a customer
    cursor.execute('SELECT * FROM customers WHERE id = "' + identification + '"')
    userData = cursor.fetchone()
    if userData != None and userData[0] == identification:
        userType = 'C'      # it is customer
    else:
        # check if it is a supplier
        cursor.execute('SELECT * FROM suppliers WHERE id = "' + identification + '"')
        userData = cursor.fetchone()
        if userData != None and userData[0] == identification:
            userType = 'P'  # it is supplier
        else:
            userType = 'E'  # identification is not valid
    dbConexion.close()
    return userData, userType

def getActivity(user, inout):
    '''
    getActivity computes the number of inputs or outputs for the existing products for a given user.
    :param user: the user identification
    :param inout: the activity movements to be computed: "C" (inputs), "V" (outputs)
    :return: a dictionary
    '''
    # get the requested inputs and/or outputs for the given user (if any)
    allActs = queryActivity(user, inout)
    # put in a dictionary products and total amount of units
    actProduct = {}
    for reg in allActs:
        # get product name and update counters in the dictionary
        product = reg[0]
        if product in actProduct:
            actProduct[product] = actProduct[product] + 1
        else:
            actProduct[product] = 1
    return actProduct

def getValues(inout):
    '''
    getValues computes the value of sales or purchases of each product for the period
    :param inout: the movements to be computed: "C" (inputs), "V" (outputs)
    :return: a dictionary with accumulated price values of each product for the period
    '''
    # get the requested inputs or outputs
    allActs = queryActivity('', inout)
    # a dictionary to accumulate amounts
    actProduct = {}
    for reg in allActs:
        # product name is in col 0 and price in col 1
        product = reg[0]
        if product in actProduct:
            actProduct[product] = actProduct[product] + reg[1]
        else:
            actProduct[product] = reg[1]
    return actProduct

# Start script
cgitb.enable()

formData = cgi.FieldStorage()
userId = formData.getvalue('userId', 'empty Id')
# get jinja environment to process templates
env = Environment(
    loader=FileSystemLoader(dirTemplates),
    autoescape=select_autoescape()
)
print("Content-Type:text/html\r\n")
print(identify(env, userId))

'''
    if request.method == 'POST':
        formData = request.POST
    else:
        formData = request.GET
    userId = formData.get('userId', '')
'''
