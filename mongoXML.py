#driver mongoDB
import pymongo 
#drive postgreSQL
import psycopg2
#librairie pour serialiser les données en XML
from lxml import etree

#fonction vérification xsd
def xsdVerif(xml_file):
    with open(xml_file, 'rb') as f:
        xml_data = f.read()

    with open('orders.xsd', 'rb') as f:
        xsd_data = f.read()

    xsd = etree.XMLSchema(etree.fromstring(xsd_data))
    xml = etree.fromstring(xml_data)

    if xsd.validate(xml):
        print("Vérification du XML réussie")
    else:
        print("Vérification du XML échouée")
        print(xsd.error_log)

#fonction création xslt-html
def xslVerif(xml_file):
    xml = etree.parse(xml_file)
    xsl = etree.parse('orders.xsl')

    #création d'un objet XSLT
    transform = etree.XSLT(xsl)
    #transformation du xml
    result = transform(xml)

    if result:
        print("XSL fonctionnel")
    else:
        print("XSL erroné")

    with open("orders.html", "wb") as f:
        f.write(result)

#connexion à mongoDB
client = pymongo.MongoClient('mongodb://localhost:27017')
db = client['EchangeDonnees']
collection = db['e-commerce']

#Création de la racine du xml
root = etree.Element('Orders')
invoices = {}

#itération de la BD
for document in collection.find():
    invoice = document["InvoiceNo"]

    #Vérification si invoice n'est pas NaN car certains éléments sont InvoiceNo sont vides
    if invoice != 'NaN':
        #si InvoiceNo existe dans le dico, ajouter items et prix manquants
        #sinon créer nouvel enfant avec InvoiceNo
        if invoice in invoices:
            #création d'un enfant de la racine
            item_element = etree.SubElement(invoices[invoice], "Description")
            item_element.text = document["Description"]

            for k in ["Quantity","UnitPrice"]:
                #création d'enfants pour chaque item
                sub = etree.SubElement(item_element, k)
                sub.text = str(document[k])

        else:
            #création d'enfants à partir de la racine Orders->Order->OrderID,Description,...
            #InvoiceNo devient OrderID
            if "Description" in document:
                doc = etree.SubElement(root, "Order")
                doc1 = etree.SubElement(doc, "OrderID")
                doc1.text = str(invoice)
                for key,value in document.items():
                    if key == "Description":
                        sub = etree.SubElement(doc, key)
                        sub.text = str(value)
                        for k in ["Quantity","UnitPrice"]:
                            sub1 = etree.SubElement(sub, k)
                            sub1.text = str(document[k]) 
                        break
                invoices[invoice] = doc

#réitération de la BD pour récupérer les infos restantes
invoicesCopy = set()
for document in collection.find():
    invoice = document["InvoiceNo"]
    if invoice in invoices and invoice not in invoicesCopy: #pour ne pas revérifier si InvoiceNo=NaN
        for key in ["InvoiceDate","CustomerID"]:
            if key in document:
                sub = etree.SubElement(invoices[invoice], key)
                sub.text = str(document[key])
        invoicesCopy.add(invoice)


#création d'un ElementTree à partir de la racine Orders
element = etree.ElementTree(root)

#assignation du fichier xsl à utiliser
process = etree.ProcessingInstruction("xml-stylesheet","href='orders.xsl' type='text/xsl'")
#ajout de l'assignation avant la racine 
root.addprevious(process)

#conversion de l'arbre pour l'ajouter au document XML
xml_data = etree.tostring(element, encoding='utf-8',pretty_print=True, xml_declaration=True)
with open('orders.xml', 'wb') as f:
    f.write(xml_data)

xsdVerif('orders.xml')
xslVerif('orders.xml')

with open('orders.xml','r') as f:
    xml_data_str = f.read()

#connexion à postgreSQL
conn = psycopg2.connect(host="localhost", dbname="postgres", user="postgres", password="root")
cursor = conn.cursor()

#récupération d'un élément ElementTree pour avoir la racine
element = etree.parse('orders.xml')
root = element.getroot()

#vérification si la table existe déjà dans la BD
cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'orders');")
check = cursor.fetchone()[0]

#
if not check:
    cursor.execute("CREATE TABLE orders (order_id NUMERIC, invoice_date TEXT, customer_id NUMERIC);")
    cursor.execute("CREATE TABLE order_details (order_id NUMERIC, description TEXT, quantity INTEGER, unit_price NUMERIC);")

    #itération dans Order pour récupérer OrderID, InvoiceDate et CustomerID
    for order in root.findall('Order'):
        order_id = order.find('OrderID').text
        invoice_date = order.find('InvoiceDate').text
        customer_id_elem = order.find('CustomerID')
        customer_id = customer_id_elem.text if customer_id_elem is not None else None
        
        cursor.execute("INSERT INTO orders (order_id, invoice_date, customer_id) VALUES (%s, %s, %s)", (order_id, invoice_date, customer_id))

        # itération dans la description pour récupérer le nom, quantité et prix
        for description in order.findall('Description'):
            description_text = description.text
            quantity = description.find('Quantity').text
            unit_price = description.find('UnitPrice').text

            cursor.execute("INSERT INTO order_details (order_id, description, quantity, unit_price) VALUES (%s, %s, %s, %s)", (order_id, description_text, quantity, unit_price))
    
#validation des modifications
conn.commit()

#fermeture de la connexion
conn.close()

